import json
import requests
import configparser
from flask import Flask, request

config = configparser.ConfigParser()
config.read('./config.ini')
app = Flask(__name__)

@app.route('/hirumibot', methods=['POST'])
def bot_response():
    MM_SERVER_ADDRESS = config['Mattermost']['MM_SERVER_ADDRESS']
    MM_API_ADDRESS = MM_SERVER_ADDRESS + '/api/v4/posts'
    MM_POST_CHANNEL_ID = config['Mattermost']['MM_POST_CHANNEL_ID']
    MM_HIRUMIBOT_TOKEN = config['Mattermost']['MM_HIRUMIBOT_TOKEN']
    post_user_from_mm = request.json['user_name']
    post_text_from_mm = request.json['text']

    bot_response_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + MM_HIRUMIBOT_TOKEN,
    }

    bot_response_data = {
        "channel_id":MM_POST_CHANNEL_ID, 
        "message":"@" + post_user_from_mm + " さんの参加を受け付けました。", 
        "props":{"attachments": [{"text": post_text_from_mm}]}
    }

    response = requests.post(MM_API_ADDRESS,
                             headers = bot_response_headers,
                             data = json.dumps(bot_response_data))

    return response

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')