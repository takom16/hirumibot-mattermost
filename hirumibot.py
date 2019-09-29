import configparser
from subprocess import Popen

config = configparser.ConfigParser()
config.read('./config.ini')

GUNICORN_CONF = config['hirumibot']['GUNICORN_CONF']

if __name__ == '__main__':
    Popen(['python3', 'notice.py'])
    Popen(['gunicorn', 'lunch_meeting:app', '-c', GUNICORN_CONF])