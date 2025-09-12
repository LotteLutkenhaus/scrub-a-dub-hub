import datetime
import logging
import random

import functions_framework

from database import (
    get_office_members,
    get_current_cycle_info,
    start_new_cycle,
    record_duty_assignment
)
from models import OfficeMember, DutyType
from mattermost import send_mattermost_coffee_webhook, send_mattermost_fridge_webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_coffee_execution_week():
    """
    Determines if current week is odd (coffee duty week).
    """
    today = datetime.date.today()
    iso_week_number = today.isocalendar()[1]
    is_current_week_odd = (iso_week_number % 2 == 1)
    logger.info(
        f"Week number {iso_week_number} is {'odd' if is_current_week_odd else 'even'} "
        f"so {'we are' if is_current_week_odd else 'not'} executing coffee job..."
    )
    return is_current_week_odd


def is_fridge_execution_week():
    """
    Determines if this is the last Wednesday of the month.
    """
    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)
    is_last_wednesday = (today.month != next_week.month)
    logger.info(
        f"{today} is {'the' if is_last_wednesday else 'not the'} last Wednesday "
        f"of the month so {'we are' if is_last_wednesday else 'not'} executing fridge job"
    )
    return is_last_wednesday


def _assign_duty(duty_type: DutyType, test_mode: bool = False):
    """
    Assign a duty, track it in the database, and send a notification on Mattermost.
    """
    # Get eligible members from database
    if duty_type == DutyType.COFFEE:
        members = get_office_members(coffee_drinkers_only=True, test_mode=test_mode)
        notification_func = send_mattermost_coffee_webhook
        duty_name = "coffee machine cleaning"
    else:
        members = get_office_members(coffee_drinkers_only=False, test_mode=test_mode)
        notification_func = send_mattermost_fridge_webhook
        duty_name = "fridge cleaning"

    if not members:
        logger.warning(f"No members eligible for {duty_name}. Aborting.")
        return {"status": "error", "message": f"No members eligible for {duty_name}"}, 500

    # Create member lookup
    member_lookup = {member.id: member for member in members}
    all_member_ids = set(member_lookup.keys())

    # Get cycle info
    cycle_info = get_current_cycle_info(duty_type, test_mode)
    available_user_ids = list(all_member_ids - cycle_info.assigned_member_ids)

    # Start new cycle if needed
    if not available_user_ids:
        logger.info(f"All users have had a turn for {duty_name}. Starting new cycle.")
        cycle_info = start_new_cycle(duty_type, test_mode)
        available_user_ids = list(all_member_ids)

        if not available_user_ids:
            logger.error(f"No users available for {duty_name} even after cycle reset.")
            return {"status": "error",
                    "message": f"No users available for {duty_name} after cycle reset."}, 500

    # Select random user
    selected_user_id = random.choice(available_user_ids)
    selected_member = member_lookup[selected_user_id]

    logger.info(
        f"Selected user for {duty_name}: {selected_member.username} (ID: {selected_user_id})")

    # Send notification
    if not notification_func(selected_member.username, test_mode=test_mode):
        logger.error(f"Failed to send Mattermost webhook for {selected_member.username}")

    # Record assignment
    result = record_duty_assignment(
        member_id=selected_user_id,
        username=selected_member.username,
        duty_type=duty_type,
        cycle_id=cycle_info.cycle_id,
        test_mode=test_mode
    )

    if not result.success:
        logger.error(f"Failed to record {selected_member.username} in database: {result.message}")
        return {"status": "error", "message": result.message}, 500

    logger.info(f"{duty_name} assignment process completed successfully.")
    return {"status": "success",
            "message": f"Assigned {duty_name} to {selected_member.username}."}, 200


@functions_framework.http
def assign_coffee_duty(request):
    """
    HTTP Cloud Function for assigning coffee machine cleaning duty.
    Expected payload: {"test_mode": true | false}
    """
    if request.method != "POST":
        return "Java Janitor is alive! Use POST to trigger.", 200

    request_json = request.get_json(silent=True) or {}
    test_mode = request_json.get("test_mode", True)

    # Check if it's execution week
    if not is_coffee_execution_week():
        if test_mode:
            logger.info("Would not have assigned coffee duty this week.")
        else:
            return {"status": "success", "message": "Not assigning coffee duty this week."}, 200

    logger.info(f"Coffee duty assignment process started (test mode = {test_mode})")
    return _assign_duty(DutyType.COFFEE, test_mode)


@functions_framework.http
def assign_fridge_duty(request):
    """
    HTTP Cloud Function for assigning fridge cleaning duty.
    Expected payload: {"test_mode": true | false}
    """
    if request.method != "POST":
        return "Fridge Warden is alive! Use POST to trigger.", 200

    request_json = request.get_json(silent=True) or {}
    test_mode = request_json.get("test_mode", True)

    # Check if it's execution week
    if not is_fridge_execution_week():
        if test_mode:
            logger.info("Would not have assigned fridge duty this week.")
        else:
            return {"status": "success", "message": "Not executing fridge duty this week."}, 200

    logger.info(f"Fridge duty assignment process started (test mode = {test_mode})")
    return _assign_duty(DutyType.FRIDGE, test_mode)
