import json
import requests
import logging
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SAMPLE_PAYLOAD = {
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "You have a new issue:\n*<fakeLink.toEmployeeProfile.com|Cloudformation service>*"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Approve"
                    },
                    "style": "primary",
                    "value": "click_me_123"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Deny"
                    },
                    "style": "danger",
                    "value": "click_me_123"
                }
            ]
        }
    ]
}


class SlackBot:

    def __init__(self, webhook_url, timeout=15, **kwargs):
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.headers = {
            'Content-Type': 'application/json',
        }

    def send_message(self, payload: Any):
        success = False

        try:
            requests.post(
                self.webhook_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
        except requests.Timeout:
            logger.error('Timeout occurred when trying to send message to Slack.')
        except requests.RequestException as e:
            logger.error(f'Error occurred when communicating with Slack: {e}.')
        else:
            success = True
            logger.info('Successfully sent message to Slack.')

        return success


WEBHOOK_URL = "https://hooks.slack.com/services/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"
bot = SlackBot(webhook_url=WEBHOOK_URL)
bot.send_message(SAMPLE_PAYLOAD)
