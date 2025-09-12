import logging
from typing import List, Optional, Any, Generator
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

from google_utils import get_secret
from models import OfficeMember, DutyAssignment, DutyType, CycleInfo, AssignmentResult

logger = logging.getLogger(__name__)

Base = declarative_base()


class MemberTable(Base):
    __tablename__ = 'members'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100))
    coffee_drinker = Column(Boolean, default=True)
    active = Column(Boolean, default=True)


class DutyAssignmentTable(Base):
    __tablename__ = 'duty_assignments'

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    duty_type = Column(String(20), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now())
    cycle_id = Column(Integer, nullable=False)


def get_database_url(test_mode: bool = False) -> str:
    """
    Get database connection URL from Google Secret Manager.
    """
    secret_name = "neon-database-connection-string-dev" if test_mode else "neon-database-connection-string"
    connection_string = get_secret(secret_name)

    return connection_string


@contextmanager
def get_db_session(test_mode: bool = False) -> Generator[Session, Any, None]:
    """
    Context manager for database sessions.
    """
    engine = create_engine(get_database_url(test_mode))
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def get_office_members(coffee_drinkers_only: bool = False, test_mode: bool = False) -> List[
    OfficeMember]:
    """
    Fetch office members from database.
    """
    with get_db_session(test_mode) as session:
        query = session.query(MemberTable).filter(MemberTable.active == True)

        if coffee_drinkers_only:
            query = query.filter(MemberTable.coffee_drinker == True)

        members = query.all()

        return [OfficeMember.model_validate(member.__dict__) for member in members]


def get_current_cycle_info(duty_type: DutyType, test_mode: bool = False) -> CycleInfo:
    """
    Get information about the current assignment cycle.
    """
    with get_db_session(test_mode) as session:
        # Get the current cycle ID
        current_cycle = session.query(func.max(DutyAssignmentTable.cycle_id)).filter(
            DutyAssignmentTable.duty_type == duty_type
        ).scalar() or 0

        # Get assigned user IDs in current cycle
        assigned_ids = session.query(DutyAssignmentTable.member_id).filter(
            DutyAssignmentTable.duty_type == duty_type,
            DutyAssignmentTable.cycle_id == current_cycle
        ).distinct().all()

        return CycleInfo(
            cycle_id=current_cycle,
            duty_type=duty_type,
            assigned_member_ids={row[0] for row in assigned_ids}
        )


def start_new_cycle(duty_type: DutyType, test_mode: bool = False) -> CycleInfo:
    """
    Start a new assignment cycle and return the cycle info.
    """
    with get_db_session(test_mode) as session:
        # Get the current max cycle ID
        current_max = session.query(func.max(DutyAssignmentTable.cycle_id)).filter(
            DutyAssignmentTable.duty_type == duty_type
        ).scalar() or 0

        new_cycle_id = current_max + 1
        logger.info(f"Started new cycle {new_cycle_id} for {duty_type}")

        return CycleInfo(
            cycle_id=new_cycle_id,
            duty_type=duty_type,
            assigned_member_ids=set()
        )


def record_duty_assignment(member_id: int, username: str, duty_type: DutyType,
                           cycle_id: int | None = None,
                           test_mode: bool = False) -> AssignmentResult:
    """
    Record a duty assignment in the database.
    """
    try:
        with get_db_session(test_mode) as session:
            # If no cycle_id provided, get the current one
            if cycle_id is None:
                cycle_id = session.query(func.max(DutyAssignmentTable.cycle_id)).filter(
                    DutyAssignmentTable.duty_type == duty_type
                ).scalar() or 1

            # Create new assignment
            assignment_record = DutyAssignmentTable(
                member_id=member_id,
                duty_type=duty_type,
                cycle_id=cycle_id
            )
            session.add(assignment_record)
            session.commit()
            logger.info(
                f"Recorded {duty_type} assignment for {username} (ID: {member_id}) in cycle {cycle_id}")

            return AssignmentResult(
                success=True,
                message=f"Successfully assigned {duty_type} duty to {username}",
            )

    except Exception as e:
        logger.error(f"Failed to record assignment: {e}")
        return AssignmentResult(
            success=False,
            message=f"Failed to record assignment: {str(e)}",
        )
