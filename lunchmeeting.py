import json
import requests
import configparser
from flask import Flask, request

config = configparser.ConfigParser()
config.read('./config.ini')
app = Flask(__name__)

MM_API_ADDRESS   = config['Mattermost']['MM_API_ADDRESS']
CHANNEL_ID_LUNCH = config['Mattermost']['CHANNEL_ID_LUNCH']
HIRUMIBOT_TOKEN  = config['Mattermost']['HIRUMIBOT_TOKEN']

def bot_reply_content(reply_msg: str,
                      posted_user: str, posted_msg: str) -> str:
    """
    トリガーワードを含んだ投稿を引用する形式で、
    Botアカウントからメッセージを投稿する。

    :param reply_msg   : Botアカウントが投稿するメッセージ
    :param posted_user : 引用元のメッセージを投稿したユーザ名
    :param posted_msg  : 引用元のメッセージ
    :return            : HTTPリクエスト(POST)
    """

    bot_reply_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + HIRUMIBOT_TOKEN,
    }

    bot_reply_data = {
        "channel_id": CHANNEL_ID_LUNCH,
        "message": reply_msg,
        "props": {
            "attachments": [
                     {
                      "author_name": posted_user,
                      "text": posted_msg,
                     }
            ]
        },
    }

    bot_reply_request = requests.post(
        MM_API_ADDRESS,
        headers = bot_reply_headers,
        data = json.dumps(bot_reply_data)
    )

    return bot_reply_request

def accept_participant(posted_user: str) -> str:
    """
    参加者の受付

    :param posted_user : 引用元のメッセージを投稿したユーザ名
    :return            : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg  = "@{} さんの参加を受け付けました！".format(posted_user)
    bot_reply_msg += "わーい！ :laughing: :raised_hands:"
    return bot_reply_msg

def outside_reception_hours_notice() -> str:
    """
    ランチミーティング受付時間外のメッセージをセット

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg = "現在はランチミーティングの受付時間外です。 :sweat:"
    return bot_reply_msg

@app.route('/hirumibot', methods=['POST'])
def lunch_meeting_manage():
    """ ランチミーティングの管理 """
    posted_user = request.json['user_name']
    posted_msg = request.json['text']

    lunch_meeting_date_check = True
    #lunch_meeting_date_check = False

    if lunch_meeting_date_check == True:
        bot_reply_msg = accept_participant(posted_user)
    else:
        bot_reply_msg = outside_reception_hours_notice()

    bot_reply_content(bot_reply_msg, posted_user, posted_msg)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')