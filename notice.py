import json
import requests
import configparser
import schedule
from time import sleep

config = configparser.ConfigParser()
config.read('./config.ini')

MM_API_ADDRESS   = config['Mattermost']['MM_API_ADDRESS']
CHANNEL_ID_ALL   = config['Mattermost']['CHANNEL_ID_ALL']
CHANNEL_ID_LUNCH = config['Mattermost']['CHANNEL_ID_LUNCH']
HIRUMIBOT_TOKEN  = config['Mattermost']['HIRUMIBOT_TOKEN']

def bot_posts_content(posts_msg: str, dst_chl_id: str) -> str:
    """
    botアカウントで指定のチャンネルにメッセージを投稿する。

    :param posts_msg   : botアカウントのメッセージ
    :param dst_chl_id  : 投稿先のチャンネルID
    :return            : HTTPリクエスト(POST)
    """

    bot_posts_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + HIRUMIBOT_TOKEN,
    }

    bot_posts_data = {
         "channel_id": dst_chl_id,
         "message": posts_msg,
    }

    bot_posts_request = requests.post(
        MM_API_ADDRESS,
        headers = bot_posts_headers,
        data = json.dumps(bot_posts_data)
    )

    return bot_posts_request

# 全体への周知
def morning_assembly_notice():
    """ 朝会の通知 """
    bot_posts_msg = "朝ミの時間です！"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_ALL)

def leaving_on_time_notice():
    """ 定時退社の通知 """
    bot_posts_msg = "18時です！\n残業申請をしていない人は帰りましょう！"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_ALL)

# ランチミーティング
def lunch_meeting_notice():
    """ ランチミーティングの通知 """
    bot_posts_msg = "今日はランチミーティングの日です！"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_LUNCH)

def lunch_time_notice():
    """ ランチ時間の通知 """
    bot_posts_msg = "ランチの時間です！"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_LUNCH)

if __name__ == '__main__':
    # 毎日18:00に定時退社を通知
    schedule.every().day.at("18:00").do(leaving_on_time_notice)

    # 毎週月曜日・水曜日の09:30に朝会を通知
    schedule.every().monday.at("09:30").do(morning_assembly_notice)
    schedule.every().wednesday.at("09:30").do(morning_assembly_notice)

    # 毎日水曜日にランチミーティングを通知
    schedule.every().wednesday.at("11:00").do(lunch_meeting_notice)
    schedule.every().wednesday.at("12:00").do(lunch_time_notice)

    while True:
        schedule.run_pending()
        #sleep(60)
        sleep(1)