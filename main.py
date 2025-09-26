import datetime
import logging
import random

import functions_framework
from flask import Request

from database import get_current_cycle_info, get_office_members, record_duty_assignment, start_new_cycle
from mattermost import (
    configure_and_send_mattermost_webhook,
)
from models import DutyConfig, DutyType, OfficeMember

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_coffee_execution_week(date: datetime.date) -> bool:
    """
    Determines if given date's week is odd (coffee duty week).
    """
    iso_week_number = date.isocalendar()[1]
    is_current_week_odd = iso_week_number % 2 == 1
    logger.info(
        f"Week number {iso_week_number} is {'odd' if is_current_week_odd else 'even'} "
        f"so {'we are' if is_current_week_odd else 'not'} executing coffee job..."
    )
    return is_current_week_odd


def is_fridge_execution_week(date: datetime.date) -> bool:
    """
    Determines if the given date is the last Wednesday of the month.
    """
    next_week = date + datetime.timedelta(days=7)
    is_last_wednesday = date.month != next_week.month
    logger.info(
        f"{date} is {'the' if is_last_wednesday else 'not the'} last Wednesday "
        f"of the month so {'we are' if is_last_wednesday else 'not'} executing fridge job"
    )
    return is_last_wednesday


def get_duty_config(duty_type: DutyType) -> DutyConfig:
    """
    Get configuration for a specific duty type.
    """
    if duty_type == DutyType.COFFEE:
        return DutyConfig(coffee_drinkers_only=True, duty_name="coffee machine cleaning")
    elif duty_type == DutyType.FRIDGE:
        return DutyConfig(coffee_drinkers_only=False, duty_name="fridge cleaning")
    else:
        raise ValueError(f"Unknown duty type {duty_type}")


def select_next_member(members: list[OfficeMember], assigned_member_ids: set[int]) -> OfficeMember | None:
    """
    Select the next member for duty from available members.
    Returns None if all members have been assigned.
    """
    member_lookup = {member.id: member for member in members}
    all_member_ids = set(member_lookup.keys())
    available_user_ids = list(all_member_ids - assigned_member_ids)

    if not available_user_ids:
        return None

    selected_user_id = random.choice(available_user_ids)
    return member_lookup[selected_user_id]


def _assign_duty(duty_type: DutyType, test_mode: bool = False) -> tuple[dict[str, str], int]:
    """
    Assign a duty, track it in the database, and send a notification on Mattermost.
    """
    # Get duty configuration
    config = get_duty_config(duty_type)

    # Get eligible members from database
    members = get_office_members(coffee_drinkers_only=config.coffee_drinkers_only, test_mode=test_mode)
    if not members:
        logger.warning(f"No members eligible for {config.duty_name}. Aborting.")
        return {"status": "error", "message": f"No members eligible for {config.duty_name}"}, 500

    # Get current cycle and select member
    cycle_info = get_current_cycle_info(duty_type, test_mode)
    selected_member = select_next_member(members, cycle_info.assigned_member_ids)

    # Start new cycle if needed
    if selected_member is None:
        logger.info(f"All users have had a turn for {config.duty_name}. Starting new cycle.")
        cycle_info = start_new_cycle(duty_type, test_mode)
        selected_member = select_next_member(members, cycle_info.assigned_member_ids)

        if selected_member is None:
            logger.error(f"No users available for {config.duty_name} even after cycle reset.")
            return {"status": "error", "message": f"No users available for {config.duty_name} after cycle reset."}, 500

    logger.info(f"Selected user for {config.duty_name}: {selected_member.username} (ID: {selected_member.id})")

    # Send notification
    if not configure_and_send_mattermost_webhook(selected_member.username, duty_type=duty_type, test_mode=test_mode):
        logger.error(f"Failed to send Mattermost webhook for {selected_member.username}")

    # Record assignment
    result = record_duty_assignment(
        member_id=selected_member.id,
        username=selected_member.username,
        duty_type=duty_type,
        cycle_id=cycle_info.cycle_id,
        test_mode=test_mode,
    )

    if not result.success:
        logger.error(f"Failed to record {selected_member.username} in database: {result.message}")
        return {"status": "error", "message": result.message}, 500

    logger.info(f"{config.duty_name} assignment process completed successfully.")
    return {"status": "success", "message": f"Assigned {config.duty_name} to {selected_member.username}."}, 200


@functions_framework.http
def assign_coffee_duty(request: Request) -> tuple[str, int] | tuple[dict[str, str], int]:
    """
    HTTP Cloud Function for assigning coffee machine cleaning duty.
    Expected payload: {"test_mode": true | false}
    """
    if request.method != "POST":
        return "Java Janitor is alive! Use POST to trigger.", 200

    request_json = request.get_json(silent=True) or {}
    test_mode = request_json.get("test_mode", True)

    # Check if it's execution week
    today = datetime.date.today()
    if not is_coffee_execution_week(today):
        if test_mode:
            logger.info("Would not have assigned coffee duty this week.")
        else:
            return {"status": "success", "message": "Not assigning coffee duty this week."}, 200

    logger.info(f"Coffee duty assignment process started (test mode = {test_mode})")
    return _assign_duty(DutyType.COFFEE, test_mode)


@functions_framework.http
def assign_fridge_duty(request: Request) -> tuple[str, int] | tuple[dict[str, str], int]:
    """
    HTTP Cloud Function for assigning fridge cleaning duty.
    Expected payload: {"test_mode": true | false}
    """
    if request.method != "POST":
        return "Fridge Warden is alive! Use POST to trigger.", 200

    request_json = request.get_json(silent=True) or {}
    test_mode = request_json.get("test_mode", True)

    # Check if it's execution week
    today = datetime.date.today()
    if not is_fridge_execution_week(today):
        if test_mode:
            logger.info("Would not have assigned fridge duty this week.")
        else:
            return {"status": "success", "message": "Not executing fridge duty this week."}, 200

    logger.info(f"Fridge duty assignment process started (test mode = {test_mode})")
    return _assign_duty(DutyType.FRIDGE, test_mode)
