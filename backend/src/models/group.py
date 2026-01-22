from datetime import date, datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Integer, Uuid, DateTime, func, Enum as SaEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.assiciation import user_group_association, group_event_association
from src.utils.constants import Color

import uuid
from enum import Enum

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.event import Event


class GroupStatus(Enum):
    WRITING = ("Writing",)
    UPDATE_NEEDED = ("Update Needed",)
    UPDATING = ("Updating",)
    SYNCED = ("Synced",)
    DELETE = ("Delete",)
    DELETED = "Deleted"


class Group(Base):
    """
    그룹 table을 나타내는 orm 클래스입니다.
    """

    __tablename__ = "groups"

    # 그룹 Id
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # 그룹 이름
    title: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # 색상
    color: Mapped[Color] = mapped_column(
        SaEnum(Color, native_enum=False), nullable=False, default=Color.BASIC
    )
    # 설명
    description: Mapped[str | None] = mapped_column(
        String(128), unique=False, nullable=True
    )
    # 상태
    ststus: Mapped[GroupStatus] = mapped_column(
        SaEnum(GroupStatus, native_enum=False),
        default=GroupStatus.WRITING,
        nullable=False,
    )
    # 유저. 그룹에 할당된 사용자를 N:M으로.
    users: Mapped[List["User"]] = relationship(
        secondary=user_group_association, back_populates="groups"
    )
    # 이벤트. 그룹에 할당된 이벤트를 N:M으로.
    groups: Mapped[List["Event"]] = relationship(
        secondary=group_event_association, back_populates="groups"
    )
    # 노션 record id
    notion_id: Mapped[int] = mapped_column(Integer(), unique=True, nullable=False)
    # 디스코드 role id
    discord_id: Mapped[int | None] = mapped_column(
        Integer(), unique=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        # onupdate를 이용할 경우, UPDATE될 때마다 실행
        onupdate=func.now(),
    )
