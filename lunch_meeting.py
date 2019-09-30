import configparser
import json
import sqlite3
from datetime import datetime, date
from random import shuffle

import jpholiday
import requests
from flask import Flask, request

config = configparser.ConfigParser()
config.read('./config.ini')
app = Flask(__name__)

MM_API_ADDRESS   = config['Mattermost']['MM_API_ADDRESS']
CHANNEL_ID_LUNCH = config['Mattermost']['CHANNEL_ID_LUNCH']
HIRUMIBOT_TOKEN  = config['Mattermost']['HIRUMIBOT_TOKEN']
HIRUMIBOT_DB     = config['hirumibot']['DATABASE_FILE']

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
    指定されたカテゴリのキーワードをキーワードリストテーブルから取得し、
    投稿されたメッセージ内にキーワードが含まれているかをチェックする。

    :param category      : チェック対象キーワードのカテゴリ
    :param mm_posted_msg : 投稿されたメッセージ
    :return              : メッセージ内にキーワードが含まれているかの判定
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
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

def help_msg() -> str:
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

def outside_reception_hours_msg() -> str:
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

def count_participant() -> str:
    """
    参加表明済みのユーザの数と一覧を表示する。

    :return : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
    c = conn.cursor()

    count_query = 'SELECT count(*) FROM participant'
    c.execute(count_query)
    registerd_num = c.fetchall()[0][0]

    if registerd_num == 0:
        conn.close()
        bot_reply_msg  = (
            "現在は参加予定者が一人もいません:disappointed_relieved:"
        )
    else:
        list_query = 'SELECT username FROM participant'
        c.execute(list_query)
        registerd_user = c.fetchall()
        conn.close()

        bot_reply_msg = "現在の参加予定者は{}名です！\n".format(registerd_num)
        bot_reply_msg += "###### +++ 参加予定メンバー +++\n"
        for username in registerd_user:
            bot_reply_msg += "@" + username[0] + "\n"

    return bot_reply_msg

def participant_registration(mm_posted_user: str) -> str:
    """
    参加表明したユーザを参加者テーブルに登録する。

    :param mm_posted_user : メッセージを投稿したユーザ名
    :return               : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
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

def cancel_participation(mm_posted_user: str) -> str:
    """
    参加をキャンセルしたユーザを参加者テーブルから削除する。

    :param mm_posted_user : メッセージを投稿したユーザ名
    :return               : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
    c = conn.cursor()
    target_user = (mm_posted_user,)

    # すでに参加者として登録済みのユーザか確認
    check_query = 'SELECT count(*) FROM participant WHERE username = ?'
    c.execute(check_query, target_user)
    registerd_num = c.fetchall()[0][0]

    if registerd_num == 0:
        conn.close()
        bot_reply_msg  = "@{} さんは".format(mm_posted_user)
        bot_reply_msg += "まだ参加表明してないよ！"
        return bot_reply_msg

    # 参加者登録済みのユーザであれば、参加取り消し処理を行う
    cancel_query = 'DELETE FROM participant WHERE username = ?'
    c.execute(cancel_query, target_user)
    conn.commit()
    conn.close()

    bot_reply_msg  = "@{} さんの参加を取り消したよ！".format(mm_posted_user)
    bot_reply_msg += "また今度参加してね！"
    return bot_reply_msg

def reset_participant() -> str:
    """
    参加者テーブルから全ユーザを削除する。

    :return : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
    c = conn.cursor()

    reset_query = 'DELETE FROM participant'
    c.execute(reset_query)
    conn.commit()
    conn.close()

    bot_reply_msg  = "参加者をリセットしたよ！"
    return bot_reply_msg

def lunch_grouping(participant_list: list, member_max: int) -> str:
    """
    ランチミーティングの班分けを行う。

    :param participant_list : 参加者リスト
    :param member_max       : 一班の最大人数
    :return                 : Botアカウントが投稿するメッセージ
    """
    participant_num = len(participant_list)
    team_num_max = int(participant_num / member_max) + 1

    bot_reply_msg = ""
    p_begin = 0
    p_end = member_max
    for team_num in range(1, team_num_max):
        participant_name = participant_list[p_begin:p_end]
        bot_reply_msg += "###### +++ {}班 +++\n".format(team_num)
        for p_name in participant_name:
            bot_reply_msg += "@" + p_name + "\n"

        p_begin = p_end
        p_end += member_max

    return bot_reply_msg

def depart_lunch_meetig() -> str:
    """
    ランチミーティングに出発する。

    :return : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
    c = conn.cursor()

    count_query = 'SELECT count(*) FROM participant'
    c.execute(count_query)
    participant_num = c.fetchall()[0][0]

    if participant_num == 0:
        conn.close()
        bot_reply_msg = "参加者が一人もいません:sweat:"
        return bot_reply_msg

    list_query = 'SELECT username FROM participant'
    c.execute(list_query)
    participants = c.fetchall()
    conn.close()

    bot_reply_msg = "はーい！参加メンバーはこちら！\n"

    # 参加者が5名以下なら一班にする
    if participant_num <= 5:
        bot_reply_msg += "###### +++ 参加メンバー +++\n"
        for participant_name in participants:
            bot_reply_msg += "@" + participant_name[0] + "\n"

        return bot_reply_msg

    # 参加者が6名以上なら人数が均等になるように班分けする
    participant_list = [username[0] for username in participants]
    shuffle(participant_list)
    MEMBER_MAX_NUM = 4
    MEMBER_MIN_NUM = 3

    mod_mem_max = int(participant_num % MEMBER_MAX_NUM)
    mod_mem_min = int(participant_num % MEMBER_MIN_NUM)
    if mod_mem_max == 0:
        bot_reply_msg += lunch_grouping(participant_list, MEMBER_MAX_NUM)
    elif mod_mem_min == 0:
        bot_reply_msg += lunch_grouping(participant_list, MEMBER_MIN_NUM)
    else:
        if mod_mem_max >= MEMBER_MIN_NUM:
            bot_reply_msg += lunch_grouping(participant_list, MEMBER_MAX_NUM)
        else:
            bot_reply_msg += lunch_grouping(participant_list, MEMBER_MIN_NUM)

    return bot_reply_msg

def no_keywords_msg() -> str:
    """
    ランチミーティング受付時間外のメッセージをセットする。

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg  = (
        "キーワードがないので、何もできませんでした:dizzy_face:\n"
        "ひるみちゃんに使い方を聞いてみてね！"
    )
    return bot_reply_msg

@app.route('/hirumibot', methods=['POST'])
def lunch_meeting_manage():
    """ ランチミーティングの管理 """
    mm_posted_user = request.json['user_name']
    mm_posted_msg  = request.json['text']

    # ヘルプはいつでも受け付ける
    keyword_check_jadge = keyword_check('help', mm_posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = help_msg()
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    #reception_possible_jadge = reception_possible_check()
    reception_possible_jadge = True
    if reception_possible_jadge == False:
        bot_reply_msg = outside_reception_hours_msg()
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    # 人数確認
    keyword_check_jadge = keyword_check('count', mm_posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = count_participant()
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    # 参加取り消し
    keyword_check_jadge = keyword_check('cancel', mm_posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = cancel_participation(mm_posted_user)
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    # 参加登録
    keyword_check_jadge = keyword_check('entry', mm_posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = participant_registration(mm_posted_user)
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    # 出発
    keyword_check_jadge = keyword_check('go', mm_posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = depart_lunch_meetig()
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    # リセット
    keyword_check_jadge = keyword_check('reset', mm_posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = reset_participant()
        bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
        return

    # キーワードなし
    bot_reply_msg = no_keywords_msg()
    bot_reply_content(bot_reply_msg, mm_posted_user, mm_posted_msg)
    return

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')