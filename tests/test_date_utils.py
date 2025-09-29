import datetime
import pytest

from main import is_coffee_execution_week, is_fridge_execution_week


@pytest.mark.unit
@pytest.mark.parametrize(
    "test_date,expected",
    [
        (datetime.date(2024, 1, 3), True),  # Week 1 (odd) - Wednesday
        (datetime.date(2024, 1, 10), False),  # Week 2 (even) - Wednesday
        (datetime.date(2024, 1, 17), True),  # Week 3 (odd) - Wednesday
        (datetime.date(2023, 12, 27), False),  # Week 52 (even) - Wednesday
    ],
)
def test_coffee_execution_week(test_date, expected):
    assert is_coffee_execution_week(test_date) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "test_date,expected",
    [
        (datetime.date(2024, 1, 31), True),  # Last Wednesday of January
        (datetime.date(2024, 1, 24), False),  # Not the last Wednesday
        (datetime.date(2024, 3, 27), True),  # Last Wednesday of March
        (datetime.date(2024, 3, 20), False),  # Not last Wednesday of March
        (datetime.date(2024, 12, 25), True),  # Last Wednesday of December
        (datetime.date(2024, 6, 18), False),  # Not last Wednesday of December
    ],
)
def test_fridge_execution_week(test_date, expected):
    assert is_fridge_execution_week(test_date) == expected
