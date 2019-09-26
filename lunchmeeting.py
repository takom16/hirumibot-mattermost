import configparser
import json
from datetime import datetime, date

import jpholiday
import requests
from flask import Flask, request

config = configparser.ConfigParser()
config.read('./config.ini')
app = Flask(__name__)

MM_API_ADDRESS   = config['Mattermost']['MM_API_ADDRESS']
CHANNEL_ID_LUNCH = config['Mattermost']['CHANNEL_ID_LUNCH']
HIRUMIBOT_TOKEN  = config['Mattermost']['HIRUMIBOT_TOKEN']

def bot_reply_content(bot_reply_msg: str,
                      mm_posted_user: str, mm_posted_msg: str) -> str:
    """
    トリガーワードを含んだ投稿を引用する形式で、
    Botアカウントからメッセージを投稿する。

    :param bot_reply_msg  : Botアカウントが投稿するメッセージ
    :param mm_posted_user : 引用元のメッセージを投稿したユーザ名
    :param mm_posted_msg  : 引用元のメッセージ
    :return               : HTTPリクエスト(POST)
    """

    bot_reply_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + HIRUMIBOT_TOKEN,
    }

    bot_reply_data = {
        "channel_id": CHANNEL_ID_LUNCH,
        "message": bot_reply_msg,
        "props": {
            "attachments": [
                     {
                      "author_name": mm_posted_user,
                      "text": mm_posted_msg,
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

def set_help_msg() -> str:
    """
    ヘルプメッセージをセット

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg = ("##### ひるみちゃんの使い方\n"
                     "メッセージの先頭に #lunchmeeting とタグを付けて、"
                     "以下コマンドを含む文章を投稿してください。\n\n"
                     "| 項目 | コマンド |\n"
                     "| :--- | :------ |\n"
                     "| 参加する | 参加 |\n"
                     "| 参加を取り消す | 不参加 |\n"
                     "| 現在の参加人数を確認 | 人数は？ |\n"
                     "| 班分け＆出発 | 行くぞ |\n"
                     "| ヘルプを表示 | ヘルプ |")
    return bot_reply_msg

def accept_participant(mm_posted_user: str) -> str:
    """
    参加者の受付

    :param mm_posted_user : 引用元のメッセージを投稿したユーザ名
    :return               : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg  = "@{} さんの参加を受け付けました！".format(mm_posted_user)
    bot_reply_msg += "わーい！ :laughing: :raised_hands:"
    return bot_reply_msg

def set_outside_reception_hours_msg() -> str:
    """
    ランチミーティング受付時間外のメッセージをセット

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg = "現在はランチミーティングの受付時間外です。 :sweat:"
    return bot_reply_msg

def reception_possible_check() -> bool:
    """
    ランチミーティングを受付可能な時間帯かをチェックする

    :return : ランチミーティングを受付可能かの判定
    """
    holiday_jadge   = jpholiday.is_holiday(date.today())
    posted_datetime = datetime.now()
    posted_weekday  = posted_datetime.strftime('%A')

    # 平日の水曜日 11:00～13:00 の間のみランチミーティングを受け付ける
    reception_possible_jadge = True

    if holiday_jadge == True:
        reception_possible_jadge = False

    if posted_weekday != 'Wednesday' and not 11 <= posted_datetime.hour < 13:
        reception_possible_jadge = False

    return reception_possible_jadge

@app.route('/hirumibot', methods=['POST'])
def lunch_meeting_manage():
    """ ランチミーティングの管理 """
    mm_posted_user = request.json['user_name']
    mm_posted_msg  = request.json['text']

    # Helpは常に受け付ける
    if 'help' in mm_posted_msg:
        bot_reply_msg = set_help_msg()
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    #reception_possible_jadge = reception_possible_check()
    reception_possible_jadge = True

    if reception_possible_jadge == False:
        bot_reply_msg = set_outside_reception_hours_msg()
    else:
        # todo: 参加者受付処理の追加
        bot_reply_msg = accept_participant(mm_posted_user)

    bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')