import pytest
from dataclasses import dataclass
from models import OfficeMember, DutyType, DutyConfig
from main import select_next_member, get_duty_config


@dataclass
class TestCase:
    rationale: str
    members: list[OfficeMember]
    assigned_ids: set[int]
    expected_id: int | set[int] | None

test_cases = [
    TestCase(
        rationale="Should select Abel as the only unassigned member",
        members=[
            OfficeMember(id=1, username="lotte"),
            OfficeMember(id=2, username="abel"),
        ],
        assigned_ids={1},
        expected_id=2
    ),
    TestCase(
        rationale="Should return None as all members have had a turn",
        members=[
            OfficeMember(id=1, username="lotte"),
            OfficeMember(id=2, username="abel"),
        ],
        assigned_ids={1, 2},
        expected_id=None
    ),
    TestCase(
        rationale="Should return None as we have no members available",
        members=[],
        assigned_ids={1, 2},
        expected_id=None
    ),
    TestCase(
        rationale="Should select from all as none have had a turn",
        members=[
            OfficeMember(id=1, username="lotte"),
            OfficeMember(id=2, username="abel"),
            OfficeMember(id=3, username="ellie"),
        ],
        assigned_ids=set(),
        expected_id={1, 2, 3}  # Can be any of 1, 2, 3
    ),
]

@pytest.mark.unit
@pytest.mark.parametrize("case", test_cases, ids=lambda case: case.rationale)
def test_select_next_member(case: TestCase):
    """
    Test member selection logic
    """
    result = select_next_member(case.members, case.assigned_ids)
    if len(case.expected_id) > 1:
        assert result in case.expected_id
    else:
        assert result == case.expected_id


@pytest.mark.unit
@pytest.mark.parametrize("duty_type", DutyType)
def test_get_duty_config(duty_type: DutyType):
    """
    Test getting duty configuration
    """
    config = get_duty_config(duty_type)
    
    assert isinstance(config, DutyConfig)
    if duty_type == DutyType.COFFEE:
        assert config.coffee_drinkers_only == True
    else:
        assert config.coffee_drinkers_only == False


@pytest.mark.unit
def test_get_duty_config_invalid_type():
    """
    Test that invalid duty type raises ValueError
    """
    with pytest.raises(ValueError, match="Unknown duty type"):
        get_duty_config("invalid_type")