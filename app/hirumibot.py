import calendar
import configparser
import json
import sqlite3
from datetime import datetime, date
from pathlib import Path
from random import shuffle

import jpholiday
import requests

p = Path(__file__)
CONFIG_DIR = p.resolve().parent.parent / 'config'

config = configparser.ConfigParser()
config.read(CONFIG_DIR / 'setting.ini')

MM_API_ADDRESS   = config['Mattermost']['MM_API_ADDRESS']
CHANNEL_ID_ALL   = config['Mattermost']['CHANNEL_ID_ALL']
CHANNEL_ID_LUNCH = config['Mattermost']['CHANNEL_ID_LUNCH']
HIRUMIBOT_TOKEN  = config['Mattermost']['HIRUMIBOT_TOKEN']
HIRUMIBOT_DB     = config['hirumibot']['DATABASE_FILE']

# 投稿系
def bot_posts_content(posts_msg: str, dst_chl_id: str) -> str:
    """
    メッセージの投稿

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

def bot_reply_content(bot_reply_msg: str,
                      mm_posted_user: str, mm_posted_msg: str) -> str:
    """
    メッセージの返信

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


# 確認系
def keyword_check(category: str, mm_posted_msg: str) -> bool:
    """
    キーワードの確認

    指定されたカテゴリのキーワードをキーワードリストテーブルから取得し、
    投稿されたメッセージ内にキーワードが含まれているかをチェックする。

    :param category      : チェック対象キーワードのカテゴリ
    :param mm_posted_msg : 投稿されたメッセージ
    :return              : メッセージ内にキーワードが含まれているかの判定結果
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
    c = conn.cursor()
    target_category = (category,)

    query = 'SELECT keyword FROM keyword_list WHERE category = ?'
    c.execute(query, target_category)
    keyword_list = c.fetchall()
    conn.close()

    for keyword in keyword_list:
        if keyword[0] in mm_posted_msg:
            return True

    return False

def holiday_check() -> bool:
    """
    祝日判定

    実行された日が祝日かどうかを判定する。

    :return : 祝日判定の結果
    """
    holiday_jadge = jpholiday.is_holiday(date.today())
    return holiday_jadge

def premium_friday_check() -> bool:
    """
    プレミアムフライデー判定

    実行日がプレミアムフライデーかどうかを判定する。

    :return : プレミアムフライデー判定の結果
    """
    cal = calendar.Calendar(firstweekday=calendar.FRIDAY)
    today = datetime.now()

    for days in reversed(cal.monthdatescalendar(today.year, today.month)):
        premium_friday = days[0]
        break

    if today.day == premium_friday:
        return True
    else:
        return False

def reception_possible_check() -> bool:
    """
    ランチミーティング受付可能時間帯の判定

    実行日時が平日の水曜日 11:00～13:00 の間であるかどうかを判定する。

    :return : ランチミーティング受付可能時間帯の判定結果
    """
    posted_datetime = datetime.now()
    posted_weekday  = posted_datetime.strftime('%A')

    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return False

    if posted_weekday != 'Wednesday' or not 11 <= posted_datetime.hour < 13:
        return False

    return True


# ランチミーティング系
def participant_registration(mm_posted_user: str) -> str:
    """
    ランチミーティング参加者の登録

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
        bot_reply_msg = (
            f"@{mm_posted_user} さんはすでに参加表明済みだよ！:laughing:"
        )
        return bot_reply_msg

    # 未登録のユーザであれば、参加者登録を行う
    registration_query = 'INSERT INTO participant(username) VALUES(?)'
    c.execute(registration_query, target_user)
    conn.commit()
    conn.close()

    bot_reply_msg = (
        f"@{mm_posted_user} さんの参加を受け付けました！"
        "わーい！:laughing::raised_hands:"
    )
    return bot_reply_msg

def cancel_participation(mm_posted_user: str) -> str:
    """
    ランチミーティング参加のキャンセル

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
        bot_reply_msg = (
            f"@{mm_posted_user} さんはまだ参加表明してないよ！:innocent:"
        )
        return bot_reply_msg

    # 参加者登録済みのユーザであれば、参加取り消し処理を行う
    cancel_query = 'DELETE FROM participant WHERE username = ?'
    c.execute(cancel_query, target_user)
    conn.commit()
    conn.close()

    bot_reply_msg = (
        f"@{mm_posted_user} さんの参加を取り消したよ！"
        "また今度参加してね！:cry:"
    )
    return bot_reply_msg

def count_participant() -> str:
    """
    ランチミーティング参加人数の確認

　　参加者テーブルを参照し、参加表明済みのユーザの数と一覧を表示する。

    :return : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
    c = conn.cursor()

    count_query = 'SELECT count(*) FROM participant'
    c.execute(count_query)
    registerd_num = c.fetchall()[0][0]

    if registerd_num == 0:
        conn.close()
        bot_reply_msg = (
            "現在は参加予定者が一人もいません:disappointed_relieved:"
        )
    else:
        list_query = 'SELECT username FROM participant'
        c.execute(list_query)
        registerd_user = c.fetchall()
        conn.close()

        bot_reply_msg = (
            f"現在の参加予定者は{registerd_num}名です！:kissing_heart:\n"
            "###### +++ 参加予定メンバー +++\n"
        )
        for username in registerd_user:
            bot_reply_msg += f"@{username[0]}\n"

    return bot_reply_msg

def reset_participant() -> str:
    """
    ランチミーティング参加者のリセット

    参加者テーブルから全ユーザを削除する。

    :return : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
    c = conn.cursor()

    reset_query = 'DELETE FROM participant'
    c.execute(reset_query)
    conn.commit()
    conn.close()

    bot_reply_msg = "参加者をリセットしたよ！:expressionless:"
    return bot_reply_msg

def depart_lunch_meetig() -> str:
    """
    ランチミーティングの出発

    参加者テーブルに登録されているユーザをランダムに班分けして
    一覧を表示する。

    :return : Botアカウントが投稿するメッセージ
    """
    conn = sqlite3.connect(HIRUMIBOT_DB)
    c = conn.cursor()

    list_query = 'SELECT username FROM participant'
    c.execute(list_query)
    participants = c.fetchall()
    conn.close()

    participant_num = len(participants)
    if participant_num == 0:
        conn.close()
        bot_reply_msg = "参加者が一人もいません:sweat:"
        return bot_reply_msg

    bot_reply_msg = "はーい！参加メンバーはこちら！:smile:\n"

    # 参加者が6名以下なら一班にする
    if participant_num <= 6:
        bot_reply_msg += "###### +++ 参加メンバー +++\n"
        for participant_name in participants:
            bot_reply_msg += f"@{participant_name[0]}\n"

        return bot_reply_msg

    # 参加者が7名以上なら一班最大4名、最低3名となるよう班分けする
    participant_list = [username[0] for username in participants]
    shuffle(participant_list)
    MEMBER_MAX_NUM = 4
    MEMBER_MIN_NUM = 3

    # 班分けしてリストを作成
    p_idx = 0
    group_list = []
    while participant_num > 0:
        mod_max = int(participant_num % MEMBER_MAX_NUM)
        mod_min = int(participant_num % MEMBER_MIN_NUM)
        if mod_max == 0:
            group_list += [participant_list[p_idx : p_idx + MEMBER_MAX_NUM]]
            p_idx += MEMBER_MAX_NUM
            participant_num -= MEMBER_MAX_NUM
        elif mod_min == 0:
            group_list += [participant_list[p_idx : p_idx + MEMBER_MIN_NUM]]
            p_idx += MEMBER_MIN_NUM
            participant_num -= MEMBER_MIN_NUM
        else:
            group_list += [participant_list[p_idx : p_idx + MEMBER_MAX_NUM]]
            p_idx += MEMBER_MAX_NUM
            participant_num -= MEMBER_MAX_NUM

    # 班ごとにメンバーを出力
    for group_num, group in enumerate(group_list, 1):
        bot_reply_msg += f"###### +++ {group_num}班 +++\n"
        for participant_name in group:
            bot_reply_msg += f"@{participant_name}\n"

    # 班分けを出力したら、参加者テーブルを初期化
    reset_participant()

    return bot_reply_msg

# メッセージ系
def help_msg() -> str:
    """
    ヘルプメッセージ

    ヘルプメッセージをセットする。

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg = (
        "##### ひるみちゃんの使い方\n"
        "ひるみちゃん(@hirumibot)宛に"
        "キーワードを含む文章を投稿してください。\n"
        "下記キーワード以外でも反応できることがあります。"
        "いろいろ試してみてね！:wink:\n\n"
        "| アクション | キーワード |\n"
        "| :-------- | :-------- |\n"
        "| 参加する | 参加、出席、entry |\n"
        "| 参加を取り消す | キャンセル、欠席、cancle |\n"
        "| 現在の参加人数を確認 | 人数は？、何人？、count |\n"
        "| 参加メンバーのリセット | リセット、初期化、reset |\n"
        "| 班分け＆出発 | 行くぞ、出発、go |\n"
        "| ヘルプを表示 | ヘルプ、使い方、help |"
    )
    return bot_reply_msg

def outside_reception_hours_msg() -> str:
    """
    ランチミーティング受付時間時間外メッセージ

    ランチミーティング受付時間外の応答メッセージをセットする。

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg = "現在はランチミーティングの受付時間外です:sweat:"
    return bot_reply_msg

def no_keywords_msg() -> str:
    """
    キーワードが存在しない場合のメッセージ

    投稿されたメッセージにキーワードが含まれていなかった場合の
    応答メッセージをセットする。

    :return : Botアカウントが投稿するメッセージ
    """
    bot_reply_msg = (
        "キーワードがないので、何もできませんでした:dizzy_face:\n"
        "ひるみちゃんに使い方を聞いてみてね！"
    )
    return bot_reply_msg

def morning_assembly_notice():
    """
    朝会の通知

    実行日が祝日でなければ、朝会のメッセージを投稿する。
    """
    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return

    bot_posts_msg = "朝ミの時間です！:clock930:"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_ALL)

def leaving_on_time_notice():
    """
    定時退社の通知

    実行日が祝日でなければ、定時退社のメッセージを投稿する。
    """
    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return

    bot_posts_msg = (
        "18時です！:clock6:\n"
        "残業申請をしていない人は帰りましょう！:running_man::dash:"
    )
    bot_posts_content(bot_posts_msg, CHANNEL_ID_ALL)

def premium_friday_notice():
    """
    プレミアムフライデーの通知

    実行日が月末金曜日であれば、プレミアムフライデーのメッセージを投稿する。
    """
    premium_friday_jadge = premium_friday_check()
    if premium_friday_jadge == False:
        return

    bot_posts_msg = (
        "本日はプレミアムフライデーです！:clock3:\n"
        "早めに仕事を切り上げて、プレ金を満喫しましょう！:beers:"
    )
    bot_posts_content(bot_posts_msg, CHANNEL_ID_ALL)

def lunch_meeting_notice():
    """
    ランチミーティングの通知

    実行日が祝日でなければ、参加者テーブルを初期化した上で、
    ランチミーティングの受付開始メッセージを投稿する。
    """
    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return

    # 事前に参加者テーブルを初期化
    reset_participant()

    bot_posts_msg = (
        "本日はランチミーティングの日です！:clock11:\n"
        "参加する方はメッセージの先頭に"
        " #hirumi とタグを付けて投稿してください！:smiley:"
    )
    bot_posts_content(bot_posts_msg, CHANNEL_ID_LUNCH)

def lunch_time_notice():
    """
    ランチタイムの通知

    実行日が祝日でなければ、ランチタイムのメッセージを投稿する。
    """
    holiday_jadge = holiday_check()
    if holiday_jadge == True:
        return

    bot_posts_msg = "ランチの時間です！:clock12:"
    bot_posts_content(bot_posts_msg, CHANNEL_ID_LUNCH)