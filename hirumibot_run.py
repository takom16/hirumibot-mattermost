import atexit
import configparser
from pathlib import Path
from subprocess import Popen, PIPE
from time import sleep

p = Path(__file__)
APP_DIR    = p.resolve().parent / 'app'
CONFIG_DIR = p.resolve().parent / 'config'

config = configparser.ConfigParser()
config.read(CONFIG_DIR / 'setting.ini')

HIRUMI_NOTICE = APP_DIR / 'notice.py'
GUNICORN_CONF = CONFIG_DIR / config['hirumibot']['GUNICORN_CONF']

# 子プロセス起動
p_notice = Popen(['python3', HIRUMI_NOTICE])

p_lunch = f"gunicorn --chdir {APP_DIR} lunch_meeting:app -c {GUNICORN_CONF}"
Popen(p_lunch.split())

def endprocess():
    """
    プロセスの停止

    全ての子プロセスを停止した後に処理を終了させる。
    """
    p_notice.terminate()
    Popen(['pkill', 'gunicorn'])
    exit(1)

def process_monitor():
    """
    プロセス監視

    子プロセスの起動状況を定期的に確認する。
    いずれかの子プロセスが停止していた場合、
    全てのプロセスを停止し、処理を終了させる。
    """
    gunicorn_proc = str(2)
    while True:
        sleep(10)

        if p_notice.poll() is not None:
            endprocess()

        p_lunch_chk = "pgrep -c gunicorn"
        p_lunch_num = Popen(p_lunch_chk.split(), stdout=PIPE).communicate()
        if gunicorn_proc not in str(p_lunch_num[0].decode('utf-8')):
            endprocess()

atexit.register(endprocess)
process_monitor()