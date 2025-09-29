import logging
import os
import random

import requests

from models import DutyType

MATTERMOST_WEBHOOK_URL = os.environ.get("MATTERMOST_WEBHOOK_URL")

logger = logging.getLogger(__name__)

COFFEE_GREETINGS = [
    "Hey team!",
    "Good afternoon, coffee lovers!",
    "Your biweekly coffee reminder is here!",
    "Hello everyone!",
    "Time for our coffee care update!",
    "Happy coffee week!",
    "Ready for a fresh brew?",
    "Greetings, coffee crew!",
]

FRIDGE_GREETINGS = [
    "Hey team!",
    "Good afternoon, hungry folks!",
    "Your monthly fridge reminder is here!",
    "Hello everyone!",
    "Time for our fridge care update!",
    "Happy fridge cleaning day!",
    "Ready for a fresh fridge?",
    "Fridge cleaning time!",
    "Hello, clean fridge champions!",
]


def configure_and_send_mattermost_webhook(username: str, duty_type: DutyType, test_mode: bool = True) -> bool:
    """
    Build and send a message to the configured Mattermost incoming webhook.
    """
    if duty_type == DutyType.COFFEE:
        greetings = COFFEE_GREETINGS
        machine_to_clean = "coffee machine"
        emoji = "✨"
    elif duty_type == DutyType.FRIDGE:
        greetings = FRIDGE_GREETINGS
        machine_to_clean = "fridge"
        emoji = "🧼"
    else:
        raise ValueError("Unsupported duty type for Mattermost")

    if test_mode is True:
        message = (
            f"{emoji} {random.choice(greetings)} {emoji}\nIt's {username}'s turn to clean the "
            f"{machine_to_clean} this week! ✨ Click "
            f"[here](https://clean-office-command-center.vercel.app/) for instructions, and "
            f"to mark the job as completed."
        )

    else:
        message = (
            f"{emoji} {random.choice(greetings)} {emoji}\nIt's @{username}'s turn to clean the "
            f"{machine_to_clean} this week! ✨ Click "
            f"[here](https://clean-office-command-center.vercel.app/) for instructions, and "
            f"to mark the job as completed."
        )

    payload = {
        "text": message,
        "icon_url": "https://storage.cloud.google.com/public-images-java-janitor/java-janitor.png",
        "username": "Java Janitor",
    }

    if test_mode is True:
        payload.update({"channel": "@lotte_lutkenhaus"})
    else:
        payload.update({"channel": "nycoffice"})

    return send_mattermost_webhook(username, payload)


def send_mattermost_webhook(username: str, payload: dict[str, str]) -> bool:
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
