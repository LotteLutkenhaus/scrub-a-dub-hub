import logging
import os
import random

import requests

MATTERMOST_WEBHOOK_URL = os.environ.get("MATTERMOST_WEBHOOK_URL")

logger = logging.getLogger(__name__)


def send_mattermost_coffee_webhook(username, test_mode=True):
    """
    Sends a message to the configured Mattermost incoming webhook, for the coffee bot.
    """

    greetings = ["Hey team!",
                 "Good afternoon, coffee lovers!",
                 "Your biweekly coffee reminder is here!",
                 "Hello everyone!",
                 "Time for our coffee care update!",
                 "Happy coffee week!",
                 "Ready for a fresh brew?",
                 "Greetings, coffee crew!"]

    if test_mode is True:
        message = (f"☕️ {random.choice(greetings)} ☕️\nIt's {username}'s turn to clean the coffee "
                   f"machine this week! ✨ Click [here](https://clean-office-command-center.vercel.app/) "
                   f"for instructions, and to mark the job as completed.")

    else:
        message = (f"☕️ {random.choice(greetings)} ☕️\nIt's @{username}'s turn to clean the coffee "
                   f"machine this week! ✨ Click [here](https://clean-office-command-center.vercel.app/) "
                   f"for instructions, and to mark the job as completed.")

    payload = {
        "text": message,
        "icon_url": "https://storage.cloud.google.com/public-images-java-janitor/java-janitor.png",
        "username": "Java Janitor"
    }

    if test_mode is True:
        payload.update({"channel": "@lotte_lutkenhaus"})
    else:
        payload.update({"channel": "nycoffice"})

    return send_mattermost_webhook(username, payload)

def send_mattermost_fridge_webhook(username, test_mode=True):
    """
    Sends a message to the configured Mattermost incoming webhook, for the fridge bot.
    """

    greetings = ["Hey team!",
                "Good afternoon, hungry folks!",
                "Your monthly fridge reminder is here!",
                "Hello everyone!",
                "Time for our fridge care update!",
                "Happy fridge cleaning day!",
                "Ready for a fresh fridge?",
                "Fridge cleaning time!",
                "Hello, clean fridge champions!"]

    if test_mode is True:
        message = (f"☕️ {random.choice(greetings)} :soap: \nIt's {username}'s turn to clean the fridge "
                   f"this week! ✨ Click [here](https://clean-office-command-center.vercel.app/) "
                   f"for instructions, and to mark the job as completed.")

    else:
        message = (f"☕️ {random.choice(greetings)} :soap: It's @{username}'s turn to clean the fridge "
                   f"this week! ✨ Click [here](https://clean-office-command-center.vercel.app/) "
                   f"for instructions, and to mark the job as completed.")

    payload = {
        "text": message,
        "icon_url": "https://storage.cloud.google.com/public-images-java-janitor/fridge-warden.jpg",
        "username": "Fridge Warden",
        "channel": "@lotte_lutkenhaus" if test_mode is True else "nycoffice",
    }

    return send_mattermost_webhook(username, payload)

def send_mattermost_webhook(username, payload):
    """
    Sends a message to the configured Mattermost incoming webhook.
    """
    if not MATTERMOST_WEBHOOK_URL:
        logger.error("Mattermost Webhook URL is not configured.")
        return False

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(MATTERMOST_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully sent webhook notification for user {username}.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Mattermost webhook: {e}")
        return False