from time import sleep

import schedule

import hirumibot

def bot_notice():
    """ Botアカウントから指定の時間にメッセージを通知 """
    # 毎日18:00に定時退社を通知
    schedule.every().day.at("18:00").do(hirumibot.leaving_on_time_notice)

    # 毎週月曜日・水曜日の09:30に朝会を通知
    schedule.every().monday.at("09:30").do(hirumibot.morning_assembly_notice)
    schedule.every().wednesday.at("09:30").do(hirumibot.morning_assembly_notice)

    # 毎週水曜日にランチミーティングを通知
    schedule.every().wednesday.at("11:00").do(hirumibot.lunch_meeting_notice)
    schedule.every().wednesday.at("12:00").do(hirumibot.lunch_time_notice)

    # 毎月末金曜日はプレミアムフライデーを通知
    schedule.every().friday.at("15:00").do(hirumibot.premium_friday_notice)

    while True:
        schedule.run_pending()
        sleep(10)

bot_notice()