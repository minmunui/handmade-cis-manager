# CIS Handmade Backend

손으로 만든 CIS 백엔드 서버입니다. 정보 저장을 위한, Vector PostgresSQL와 Redis를 사용합니다.
백앤드로는 FastAPI를 사용하며, ORM을 위해 Alembic과 SQLAlchemy를 사용합니다.


### SQLAlchemy

SQLAlchemy 2.0 버전부터 도입된 `Mapped`를 사용할 경우, IDE와 정적 분석 도구가 해당 변수 타입을 정확하게 인식할 수 있으므로, Model 정의 시에는 `Mapped`를 사용하는 것을 권장합니다.

```python

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

```