from flask import Flask, request

import hirumibot

app = Flask(__name__)

@app.route('/hirumibot', methods=['POST'])
def lunch_meeting_manage():
    """ ランチミーティングの管理 """
    posted_user = request.json['user_name']
    posted_msg  = request.json['text']

    # ヘルプはいつでも受け付ける
    keyword_check_jadge = hirumibot.keyword_check('help', posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = hirumibot.help_msg()
        hirumibot.bot_reply_content(bot_reply_msg, posted_user, posted_msg)
        return

    # ランチミーティング受付時間の確認
    reception_possible_jadge = hirumibot.reception_possible_check()
    if 'debug' in posted_msg:
        reception_possible_jadge = True

    if reception_possible_jadge == False:
        bot_reply_msg = hirumibot.outside_reception_hours_msg()
        hirumibot.bot_reply_content(bot_reply_msg, posted_user, posted_msg)
        return

    # 人数確認
    keyword_check_jadge = hirumibot.keyword_check('count', posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = hirumibot.count_participant()
        hirumibot.bot_reply_content(bot_reply_msg, posted_user, posted_msg)
        return

    # 参加取り消し
    keyword_check_jadge = hirumibot.keyword_check('cancel', posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = hirumibot.cancel_participation(posted_user)
        hirumibot.bot_reply_content(bot_reply_msg, posted_user, posted_msg)
        return

    # 参加登録
    keyword_check_jadge = hirumibot.keyword_check('entry', posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = hirumibot.participant_registration(posted_user)
        hirumibot.bot_reply_content(bot_reply_msg, posted_user, posted_msg)
        return

    # 出発
    keyword_check_jadge = hirumibot.keyword_check('go', posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = hirumibot.depart_lunch_meetig()
        hirumibot.bot_reply_content(bot_reply_msg, posted_user, posted_msg)
        return

    # リセット
    keyword_check_jadge = hirumibot.keyword_check('reset', posted_msg)
    if keyword_check_jadge == True:
        bot_reply_msg = hirumibot.reset_participant()
        hirumibot.bot_reply_content(bot_reply_msg, posted_user, posted_msg)
        return

    # キーワードなし
    bot_reply_msg = hirumibot.no_keywords_msg()
    hirumibot.bot_reply_content(bot_reply_msg, posted_user, posted_msg)
    return

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')