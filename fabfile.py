from fabric.api import *
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
env.hosts = [os.getenv('SERVER_ADDRESS')]
env.user = os.getenv('USER')
env.key_filename = os.getenv('SSH_KEY_FILEPATH')
git_repo = os.getenv('GIT_REPO')
git_branch = os.getenv('GIT_BRANCH')
code_dir = os.getenv('CODE_DIR')
base_dir = os.getenv('BASE_DIR')
supervisor_dir = os.getenv('SUPERVISOR_DIR')
supervisor_config = os.getenv('SUPERVISOR_CONFIG')


def commit():
    local("git add -p && git add . && git commit")


def push():
    local("git push origin %s" % git_branch)


def prepare_deploy():
    commit()
    push()


def deploy():
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            with cd(base_dir):
                run("mkdir current releases")
                run("cd current && git clone %s" % git_repo)
        else:
            with cd(code_dir):
                cur_time = datetime.datetime.now().timestamp()
                run("mkdir %s/releases/%s" % (base_dir, cur_time))
                run("rsync -av %s %s/releases/%s --exclude={env,log}" % (code_dir, base_dir, cur_time))
    with cd(code_dir):
        run("git checkout %s" % git_branch)
        run("git pull")
        run("virtualenv env")
        with prefix("source env/bin/activate"):
            run("pip install -r requirements.txt")
            with settings(warn_only=True):
                if run("test -d %s/env/etc" % code_dir).failed:
                    run("mkdir env/etc")
                    run("touch env/etc/supervisord.conf")
                    run("mkdir log")
                    run("touch log/app.log log/error.log")
                    run("echo_supervisord_conf > env/etc/supervisord.conf")
                    run("tee -a env/etc/supervisord.conf << %s" % supervisor_config)
                    run("supervisord")
                else:
                    run('env/bin/supervisorctl restart all')

