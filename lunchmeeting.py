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
                      quoted_user: str, qouted_msg: str) -> str:
    """
    botアカウントで投稿元のメッセージを引用する形でメッセージを投稿する。

    :param reply_msg   : botアカウントのメッセージ
    :param quoted_user : 引用元のメッセージを投稿したユーザ名
    :param quoted_msg  : 引用元のメッセージ
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
                      "author_name": quoted_user,
                      "text": qouted_msg,
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

@app.route('/hirumibot', methods=['POST'])
def lunch_meeting():
    """ ランチミーティング """
    posted_user = request.json['user_name']
    posted_text = request.json['text']

    lunch_meeting_date_check = True
    #lunch_meeting_date_check = False

    if lunch_meeting_date_check == True:
        bot_reply_msg  = "@{} さんの参加を受け付けました！".format(posted_user)
        bot_reply_msg += "わーい！ :laughing: :raised_hands:"
    else:
        bot_reply_msg = "今日はランチミーティングの日ではありません :sweat:"

    bot_reply_content(bot_reply_msg, posted_user, posted_text)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')