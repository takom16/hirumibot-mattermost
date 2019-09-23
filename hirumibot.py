import json
import requests
import configparser
import schedule
from flask import Flask, request
from time import sleep

config = configparser.ConfigParser()
config.read('./config.ini')
app = Flask(__name__)

MM_SERVER_ADDRESS = config['Mattermost']['MM_SERVER_ADDRESS']
MM_API_ADDRESS    = MM_SERVER_ADDRESS + '/api/v4/posts'
CHANNEL_ID_ALL    = config['Mattermost']['CHANNEL_ID_ALL']
CHANNEL_ID_LUNCH  = config['Mattermost']['CHANNEL_ID_LUNCH']
HIRUMIBOT_TOKEN   = config['Mattermost']['HIRUMIBOT_TOKEN']

def bot_posts_content(posts_msg: str, dst_chl_id: str, 
                      quoted_user: str = None, qouted_msg: str = None) -> str:
    """ botアカウントでMattermostに投稿する

    botアカウントで指定のチャンネルにメッセージを投稿する。
    オプション引数(quoted_user, quoted_msg)が指定された場合、
    投稿元のメッセージを引用する形でメッセージを投稿する。

    :param posts_msg   : botアカウントのメッセージ
    :param dst_chl_id  : 投稿先のチャンネルID
    :param quoted_user : 引用元のメッセージを投稿したユーザ名
    :param quoted_msg  : 引用元のメッセージ
    :return            : HTTPリクエスト(POST)
    """

    bot_posts_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + HIRUMIBOT_TOKEN,
    }

    # オプション引数が指定されている場合は投稿元のメッセージを引用して表示
    if quoted_user != None:
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

@app.route('/hirumibot', methods=['POST'])
def lunch_meeting():
    """ ランチミーティング """
    posted_user = request.json['user_name']
    posted_text = request.json['text']

    lunch_meeting_date_check = True
    #lunch_meeting_date_check = False

    if lunch_meeting_date_check == True:
        bot_posts_msg = "@{} さんの参加を受け付けました。".format(posted_user)
    else:
        bot_posts_msg = "今日はランチミーティングの日ではありません。"

    bot_posts_content(bot_posts_msg, CHANNEL_ID_LUNCH, posted_user, posted_text)

if __name__ == '__main__':
    lunch_meeting_notice()
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