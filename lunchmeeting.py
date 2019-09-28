import configparser
import json
import sqlite3
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

def keyword_check(category: str, mm_posted_msg: str) -> bool:
    """
    指定されたカテゴリのキーワードリストをデータベースから取得し、
    投稿されたメッセージ内にキーワードが含まれているかをチェックする。

    :param category      : チェック対象キーワードのカテゴリ
    :param mm_posted_msg : 投稿されたメッセージ
    :return              : メッセージ内にキーワードが含まれているかの判定
    """
    conn = sqlite3.connect('hirumibot.sqlite3')
    c = conn.cursor()
    target_category = (category,)

    query = 'SELECT keyword FROM keyword_list WHERE category = ?'
    c.execute(query, target_category)
    keyword_list = c.fetchall()
    conn.close()

    keyword_check_jadge = False
    for keyword in keyword_list:
        if keyword[0] in mm_posted_msg:
            keyword_check_jadge = True
            break

    return keyword_check_jadge

def set_help_msg() -> str:
    """
    ヘルプメッセージをセットする。

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg = (
        "##### ひるみちゃんの使い方\n"
        "メッセージの先頭に #hirumi とタグを付けて、"
        "キーワードを含む文章を投稿してください。\n"
        "下記キーワード以外でも反応できることがあります。"
        "いろいろ試してみてね！:wink:\n\n"
        "| アクション | キーワード |\n"
        "| :-------- | :-------- |\n"
        "| 参加する | 参加、出席、entry |\n"
        "| 参加を取り消す | キャンセル、欠席、cancle |\n"
        "| 現在の参加人数を確認 | 人数は？、何人？、count |\n"
        "| 班分け＆出発 | 行くぞ、出発、go |\n"
        "| 参加メンバーのリセット | リセット、初期化、reset |\n"
        "| ヘルプを表示 | ヘルプ、使い方、help |"
    )
    return bot_reply_msg

def set_outside_reception_hours_msg() -> str:
    """
    ランチミーティング受付時間外のメッセージをセットする。

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg = "現在はランチミーティングの受付時間外です。 :sweat:"
    return bot_reply_msg

def reception_possible_check() -> bool:
    """
    ランチミーティングを受付可能な時間帯かをチェックする。

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

def accept_participant(mm_posted_user: str) -> str:
    """
    参加表明したユーザを参加者テーブルに登録する。

    :param mm_posted_user : メッセージを投稿したユーザ名
    :return               : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect('hirumibot.sqlite3')
    c = conn.cursor()
    target_user = (mm_posted_user,)

    # すでに参加者として登録済みのユーザか確認
    check_query = 'SELECT count(*) FROM participant WHERE username = ?'
    c.execute(check_query, target_user)
    registerd_num = c.fetchall()[0][0]

    if registerd_num != 0:
        conn.close()
        bot_reply_msg  = "@{} さんは".format(mm_posted_user)
        bot_reply_msg += "すでに参加表明済みだよ！"
        return bot_reply_msg

    # 未登録のユーザであれば、参加者登録を行う
    registration_query = 'INSERT INTO participant(username) VALUES(?)'
    c.execute(registration_query, target_user)
    conn.commit()
    conn.close()

    bot_reply_msg  = "@{} さんの参加を受け付けました！".format(mm_posted_user)
    bot_reply_msg += "わーい！:laughing::raised_hands:"
    return bot_reply_msg

@app.route('/hirumibot', methods=['POST'])
def lunch_meeting_manage():
    """ ランチミーティングの管理 """
    mm_posted_user = request.json['user_name']
    mm_posted_msg  = request.json['text']

    # ヘルプはいつでも受け付ける
    keyword_check_jadge = keyword_check('help', mm_posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = set_help_msg()
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    #reception_possible_jadge = reception_possible_check()
    reception_possible_jadge = True
    if reception_possible_jadge == False:
        bot_reply_msg = set_outside_reception_hours_msg()
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    # todo: ランチミーティング受付処理の追加
    # 人数確認

    # 参加取り消し

    # 参加
    keyword_check_jadge = keyword_check('entry', mm_posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = accept_participant(mm_posted_user)
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    # 出発

    # リセット

    # その他


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')