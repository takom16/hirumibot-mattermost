import configparser
import json
from datetime import date
from time import sleep

import jpholiday
import requests
import schedule

config = configparser.ConfigParser()
config.read('./config.ini')

MM_API_ADDRESS   = config['Mattermost']['MM_API_ADDRESS']
CHANNEL_ID_ALL   = config['Mattermost']['CHANNEL_ID_ALL']
CHANNEL_ID_LUNCH = config['Mattermost']['CHANNEL_ID_LUNCH']
HIRUMIBOT_TOKEN  = config['Mattermost']['HIRUMIBOT_TOKEN']

def bot_posts_content(posts_msg: str, dst_chl_id: str) -> str:
    """
    Botアカウントで指定のチャンネルにメッセージを投稿する。

    :param posts_msg  : Botアカウントが投稿するメッセージ
    :param dst_chl_id : 投稿先のチャンネルID
    :return           : HTTPリクエスト(POST)
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

def holiday_check() -> bool:
    """
    祝日判定

    : return : 実行日が祝日かどうかの判定
    """
    holiday_jadge = jpholiday.is_holiday(date.today())
    return holiday_jadge

# 全体への周知
def morning_assembly_notice():
    """ 朝会の通知 """
    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return

    bot_posts_msg = "朝ミの時間です！"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_ALL)

def leaving_on_time_notice():
    """ 定時退社の通知 """
    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return

    bot_posts_msg = "18時です！\n残業申請をしていない人は帰りましょう！"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_ALL)

# ランチミーティング
def lunch_meeting_notice():
    """ ランチミーティングの通知 """
    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return

    bot_posts_msg  = "今日はランチミーティングの日です！\n"
    bot_posts_msg += "参加する方はメッセージの先頭に"
    bot_posts_msg += " #lunchmeeting とタグを付けて投稿してください！"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_LUNCH)

def lunch_time_notice():
    """ ランチ時間の通知 """
    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return

    bot_posts_msg = "ランチの時間です！"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_LUNCH)

def bot_notice():
    """ Botアカウントから指定の時間にメッセージを通知 """
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
        sleep(60)

bot_notice()