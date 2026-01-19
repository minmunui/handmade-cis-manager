from sqlalchemy import String, Integer, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates
import uuid
import bcrypt

class Base(DeclarativeBase):
    pass

class User(Base):
    """
    사용자 table을 나타내는 orm 클래스입니다.
    """
    __tablename__ = "users"
    # Key 역할을 하는 ID
    id : Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default = uuid.uuid4
    )
    # 사용자의 이름
    username : Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # 사용자가 사용하는 이메일
    email : Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # 전화번호
    phone : Mapped[int] = mapped_column(Integer(), unique=False)
    # 학번
    student_id : Mapped[int] = mapped_column(Integer(), unique=False)
    # discord 시스템에서 식별 가능한 사용자 id
    discord_id : Mapped[int] = mapped_column(Integer(), unique=True)
    # notion 시스템에서 식별 가능한 사용자 id
    notion_id : Mapped[int] = mapped_column(Integer(), unique=True)
    # 웹 대쉬보드 로그인을 위한 비밀번호 
    hashed_password : Mapped[str] = mapped_column(String(255), nullable=False)

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
            "notion_id": self.notion_id
        }
    
    @validates('email')
    def validate_email(self, key, address):
        if "@" not in address:
            raise ValueError("유효하지 않은 이메일 형식입니다.")
        return address

    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        # 입력받은 비밀번호와 저장된 해시값을 비교
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
