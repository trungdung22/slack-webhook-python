import slack
import os
import hashlib
import hmac
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
import string

app = Flask(__name__)
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

client = slack.WebClient(token=os.getenv("SLACK_TOKEN"))
BOT_ID = client.api_call("auth.test")['user_id']

message_counts = {}
welcome_messages = {}


class WelcomeMessage:
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                'Welcome to this awesome channel! \n\n'
                '*Get started by completing the tasks!*'
            )
        }
    }

    DIVIDER = {'type': 'divider'}

    def __init__(self, channel):
        self.channel = channel
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False

    def get_message(self):
        return {
            'ts': self.timestamp,
            'channel': self.channel,
            'username': 'Welcome Robot!',
            'icon_emoji': self.icon_emoji,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]
        }

    def _get_reaction_task(self):
        checkmark = ':white_check_mark:'
        if not self.completed:
            checkmark = ':white_large_square:'

        text = f'{checkmark} *React to this message!*'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': text}}


def verify_signature(signing_secret, timestamp, signature):
    # Verify the request signature of the request sent from Slack
    # Generate a new hash using the app's signing secret and request data

    # Compare the generated hash and incoming request signature
    # Python 2.7.6 doesn't support compare_digest
    # It's recommended to use Python 2.7.7+
    # noqa See https://docs.python.org/2/whatsnew/2.7.html#pep-466-network-security-enhancements-for-python-2-7
    req = str.encode('v0:' + str(timestamp) + ':') + request.get_data()
    request_hash = 'v0=' + hmac.new(
        str.encode(signing_secret),
        req, hashlib.sha256
    ).hexdigest()

    if hasattr(hmac, "compare_digest"):
        # Compare byte strings for Python 2
        if (sys.version_info[0] == 2):
            return hmac.compare_digest(bytes(request_hash), bytes(signature))
        else:
            return hmac.compare_digest(request_hash, signature)
    else:
        if len(request_hash) != len(signature):
            return False
        result = 0
        if isinstance(request_hash, bytes) and isinstance(signature, bytes):
            for x, y in zip(request_hash, signature):
                result |= x ^ y
        else:
            for x, y in zip(request_hash, signature):
                result |= ord(x) ^ ord(y)
        return result == 0


def send_welcome_message(channel, user):
    if channel not in welcome_messages:
        welcome_messages[channel] = {}

    if user in welcome_messages[channel]:
        return

    welcome = WelcomeMessage(channel)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    welcome_messages[channel][user] = welcome


def reply_message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if user_id != None and BOT_ID != user_id:
        if user_id in message_counts:
            message_counts[user_id] += 1
        else:
            message_counts[user_id] = 1

        if text.lower() == 'start':
            send_welcome_message(f'@{user_id}', user_id)
        else:
            ts = event.get('ts')
            client.chat_postMessage(
                channel=channel_id, thread_ts=ts, text="THAT IS A BAD WORD!")


@app.route("/")
def hello():
    #client.chat_postMessage(channel="#dev", text="THAT IS A BAD WORD!")
    return "Hello there!"


@app.route("/slack/interactive", methods=['GET', 'POST'])
def slack_interactive():
    headers = request.headers
    print(headers)
    event_data = json.loads(request.form['payload'])
    print(event_data)
    #requests.post(event_data['response_url'])
    return "success", 200


@app.route("/slack/events", methods=['GET', 'POST'])
def slack_webhook():
    req_signature = request.headers.get('X-Slack-Signature')
    req_timestamp = request.headers.get('X-Slack-Request-Timestamp')

    if req_signature is None or not verify_signature(os.environ['SIGNING_SECRET'], req_timestamp, req_signature):
        return "", 403

    event_data = json.loads(request.data.decode('utf-8'))

    if "challenge" in event_data:
        return {"challenge": event_data.get("challenge")}, 200

    # Parse the Event payload and emit the event to the event listener
    if "event" in event_data:
        event_type = event_data["event"]["type"]
        reply_message(event_data)
        return "", 200


if __name__ == "__main__":
    app.run(port=5000)
