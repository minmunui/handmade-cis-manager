from sqlalchemy import String, Integer, Uuid, DateTime
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from sqlalchemy import Enum as SaEnum, func

from datetime import datetime
import uuid
import bcrypt
from enum import Enum
from typing import List, TYPE_CHECKING

from src.models.base import Base
from src.models.assiciation import user_event_association, user_group_association

if TYPE_CHECKING:
    from src.models.group import Group
    from src.models.event import Event


class UserStatus(Enum):
    WRITING = ("Writing",)
    UPDATE_NEEDED = ("Update Needed",)
    UPDATING = ("Updating",)
    SYNCED = ("Synced",)
    INVITED = ("Invited",)
    DELETE = ("Delete",)
    DELETED = "Deleted"


class User(Base):
    """
    사용자 table을 나타내는 orm 클래스입니다.
    """

    __tablename__ = "users"
    # Key 역할을 하는 ID
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # 사용자의 이름
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # 사용자가 사용하는 이메일
    email: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # 전화번호
    phone: Mapped[int | None] = mapped_column(Integer(), unique=False)
    # 학번
    student_id: Mapped[int | None] = mapped_column(Integer(), unique=False)
    # discord 시스템에서 식별 가능한 사용자 id
    discord_id: Mapped[int | None] = mapped_column(Integer(), unique=True)
    # notion 시스템에서 식별 가능한 사용자 id
    notion_id: Mapped[int | None] = mapped_column(Integer(), unique=True)
    # 웹 대쉬보드 로그인을 위한 비밀번호
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # 상태. native_enum이 True일 경우, db에서 고유 타입을 생성. 이 경우, 새로운 enum을 추가할 경우, 마이그레이션이 어려울 수 있음
    status: Mapped[UserStatus] = mapped_column(
        SaEnum(UserStatus, native_enum=False),
        default=UserStatus.WRITING,
        nullable=False,
    )
    # 그룹. 유저가 속한 그룹을 N:M으로... secondary를 user_group_association로 설정할 경우, orm을 이용하여 관계를 자동으로 가져올 수 있음
    groups: Mapped[List["Group"]] = relationship(
        secondary=user_group_association, back_populates="users"
    )
    # 일정. 유저가 할당된 이벤트를 N:M으로...
    evnets: Mapped[List["Event"]] = relationship(
        secondary=user_event_association, back_populates="users"
    )
    # event. 유저가 속한 event를 N:M으로
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        # onupdate를 이용할 경우, UPDATE될 때마다 실행
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"{self.to_dict()}"

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": str(self.username),
            "student_id": self.student_id,
            "email": self.email,
            "phone": self.phone,
            "discord_id": self.discord_id,
            "notion_id": self.notion_id,
        }

    @validates("email")
    def validate_email(self, key, address):
        if "@" not in address:
            raise ValueError("유효하지 않은 이메일 형식입니다.")
        return address

    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode(
            "utf-8"
        )

    def check_password(self, password: str) -> bool:
        # 입력받은 비밀번호와 저장된 해시값을 비교
        return bcrypt.checkpw(
            password.encode("utf-8"), self.hashed_password.encode("utf-8")
        )
