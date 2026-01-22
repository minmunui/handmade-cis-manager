from datetime import date, datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Integer, Uuid, DateTime, func, Enum as SaEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.assiciation import user_event_association, group_event_association

import uuid
from enum import Enum

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.group import Group


class EventStatus(Enum):
    WRITING = ("Writing",)
    UPDATE_NEEDED = ("Update Needed",)
    UPDATING = ("Updating",)
    SYNCED = ("Synced",)
    DELETE = ("Delete",)
    DELETED = "Deleted"


class Event(Base):
    """
    사용자 table을 나타내는 orm 클래스입니다.
    """

    __tablename__ = "events"

    # 이벤트 Id
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # 이벤트 이름
    title: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # 시작 시간
    start_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # 종료 시간
    end_time: Mapped[datetime] = mapped_column()
    # 위치
    location: Mapped[str] = mapped_column(String(64), unique=False, nullable=True)
    # 설명
    description: Mapped[str] = mapped_column(String(128), unique=False, nullable=True)
    # 유저. 일정에 할당된 사용자를 N:M으로.
    users: Mapped[List["User"]] = relationship(
        secondary=user_event_association, back_populates="evnets"
    )
    # 그룹. 일정에 할당된 그룹을 N:M으로.
    groups: Mapped[List["Group"]] = relationship(
        secondary=group_event_association, back_populates="groups"
    )

    ststus: Mapped[EventStatus] = mapped_column(
        SaEnum(EventStatus, native_enum=False),
        default=EventStatus.WRITING,
        nullable=False,
    )

    # notion id
    notion_id: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        # onupdate를 이용할 경우, UPDATE될 때마다 실행
        onupdate=func.now(),
    )
