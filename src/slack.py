import json
import requests
import logging
from typing import Any
from templates import SlackTemplateBuilder

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SlackBot:
    def __init__(self, webhook_url, timeout=15, **kwargs):
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.headers = {
            'Content-Type': 'application/json',
        }

    def send_message(self, message: Any):
        success = False

        try:
            requests.post(
                self.webhook_url,
                headers=self.headers,
                json=message,
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


def slack_event_handler(payload):
    webhook_url = payload.pop("webhook_url")
    template_builder = SlackTemplateBuilder(payload)
    bot = SlackBot(webhook_url=webhook_url)
    bot.send_message(template_builder.build_template())
