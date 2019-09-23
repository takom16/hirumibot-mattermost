import json
import requests
import configparser
import schedule
from flask import Flask, request
from time import sleep

config = configparser.ConfigParser()
config.read('./config.ini')
app = Flask(__name__)

MM_SERVER_ADDRESS   = config['Mattermost']['MM_SERVER_ADDRESS']
MM_API_ADDRESS      = MM_SERVER_ADDRESS + '/api/v4/posts'
MM_CHANNEL_ID_ALL   = config['Mattermost']['MM_CHANNEL_ID_ALL']
MM_CHANNEL_ID_LUNCH = config['Mattermost']['MM_CHANNEL_ID_LUNCH']
MM_HIRUMIBOT_TOKEN  = config['Mattermost']['MM_HIRUMIBOT_TOKEN']

def bot_posts_content(posts_msg: str, dst_chl_id: str, quote_flg: bool, 
                      quoted_user: str = None, qouted_msg: str = None) -> str:
    """ botアカウントでMattermostに投稿する

    botアカウントで指定のチャンネルにメッセージを投稿する。
    引用フラグを True にした場合、投稿元のメッセージを引用する形でメッセージを投稿する。

    :param posts_msg   : botアカウントのメッセージ
    :param dst_chl_id  : 投稿先のチャンネルID
    :param quote_flg   : Mattermostで投稿されたメッセージを引用するかのフラグ
    :param quoted_user : 引用元のメッセージを投稿したユーザ名
    :param quoted_msg  : 引用元のメッセージ
    :return            : HTTPリクエスト(POST)
    """

    bot_posts_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + MM_HIRUMIBOT_TOKEN,
    }

    # 引用フラグが True の場合は投稿元のメッセージを引用して表示
    if quote_flg == True:
        bot_posts_data = {
            "channel_id": dst_chl_id, 
            "message": posts_msg,
            "props": {
                "attachments": [
                         {
                          "author_name": quoted_user,
                          "text": qouted_msg,
                         }
                ]
            },
        }
    else:
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
    bot_posts_message = "朝ミの時間です！"
    bot_posts_content(bot_posts_message, MM_CHANNEL_ID_ALL, False)

def leaving_on_time_notice():
    """ 定時退社の通知 """
    bot_posts_message = "18時です！\n残業申請をしていない人は帰りましょう！"
    bot_posts_content(bot_posts_message, MM_CHANNEL_ID_ALL, False)

# ランチミーティング
def lunch_meeting_notice():
    """ ランチミーティングの通知 """
    bot_posts_message = "今日はランチミーティングの日です！"
    bot_posts_content(bot_posts_message, MM_CHANNEL_ID_LUNCH, False)

def lunch_time_notice():
    """ ランチ時間の通知 """
    bot_posts_message = "ランチの時間です！"
    bot_posts_content(bot_posts_message, MM_CHANNEL_ID_LUNCH, False)

@app.route('/hirumibot', methods=['POST'])
def lunch_meeting():
    """ ランチミーティング """
    username_posted_in_mm = request.json['user_name']
    text_posted_in_mm = request.json['text']

    lunch_meeting_date_check = True
    #lunch_meeting_date_check = False

    if lunch_meeting_date_check == True:
        bot_posts_message = "@{} さんの参加を受け付けました。".format(username_posted_in_mm)
    else:
        bot_posts_message = "今日はランチミーティングの日ではありません。"

    bot_posts_content(bot_posts_message, MM_CHANNEL_ID_LUNCH, True, 
                      username_posted_in_mm, text_posted_in_mm)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

    ## 毎日18:00に定時退社を通知
    #schedule.every().day.at("18:00").do(leaving_on_time_notice)

    ## 毎週月曜日・水曜日の09:30に朝会を通知
    #schedule.every().monday.at("09:30").do(morning_assembly_notice)
    #schedule.every().wednesday.at("09:30").do(morning_assembly_notice)

    ## 毎日水曜日にランチミーティングを通知
    #schedule.every(1).minutes.do(lunch_meeting_notice)
    #schedule.every(3).minutes.do(lunch_time_notice)
    #schedule.every().wednesday.at("11:00").do(lunch_meeting_notice)
    #schedule.every().wednesday.at("12:00").do(lunch_time_notice)

    #while True:
    #    schedule.run_pending()
    #    sleep(1)