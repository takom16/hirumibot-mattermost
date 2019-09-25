from subprocess import Popen

if __name__ == '__main__':
    Popen(['python3', 'notice.py'])
    Popen(['gunicorn', 'lunchmeeting:app', '-c', 'gunicorn-hirumibot.conf'])