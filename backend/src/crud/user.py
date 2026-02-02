import bcrypt
from uuid import UUID

from sqlalchemy.orm import Session
from src.models.user import UserORM
from src.schemas.user import UserCreate, UserUpdate, UserResponse


def create_user(db: Session, user_in: UserCreate):
    """새로운 사용자를 생성합니다.

    Args:
        db (Session): 데이터베이스 세션
        user_in (UserCreate): 생성할 사용자 정보

    Returns:
        UserORM: 생성된 사용자 객체
    """
    user_data = user_in.model_dump(exclude={"password"})
    hashed_password = hash_password(user_in.password)
    db_user = UserORM(**user_data, hashed_password=hashed_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: UUID) -> UserORM:
    """ID로 사용자를 조회합니다.

    Args:
        db (Session): 데이터베이스 세션
        user_id (UUID): 조회할 사용자의 ID

    Raises:
        ValueError: 사용자가 존재하지 않을 경우

    Returns:
        UserORM: 조회된 사용자 객체
    """
    db_user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not db_user:
        raise ValueError(f"해당 사용자는 존재하지 않습니다 : {user_id}")
    return db_user


def update_user(db: Session, user_id: UUID, user_in: UserUpdate):
    """사용자 정보를 수정합니다.

    Args:
        db (Session): 데이터베이스 세션
        user_id (UUID): 수정할 사용자의 ID
        user_in (UserUpdate): 수정할 사용자 정보 (설정된 필드만 업데이트)

    Raises:
        ValueError: 사용자가 존재하지 않을 경우 (find_user_by_id에서 발생)

    Returns:
        UserORM: 수정된 사용자 객체
    """
    db_user = get_user(db, user_id)

    update_data = user_in.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: UUID) -> bool:
    """사용자를 삭제합니다.

    Args:
        db (Session): 데이터베이스 세션
        user_id (UUID): 삭제할 사용자의 ID

    Raises:
        ValueError: 사용자가 존재하지 않을 경우 (find_user_by_id에서 발생)

    Returns:
        bool: 삭제 성공 시 True
    """
    db_user = get_user(db, user_id)
    db.delete(db_user)
    db.commit()
    return True


def change_password(db: Session, user_id: UUID, new_password: str):
    """사용자의 비밀번호를 변경합니다.

    Args:
        db (Session): 데이터베이스 세션
        user_id (UUID): 비밀번호를 변경할 사용자의 ID
        new_password (str): 새로운 비밀번호 (평문)

    Raises:
        ValueError: 사용자가 존재하지 않을 경우

    Returns:
        UserORM: 비밀번호가 변경된 사용자 객체
    """
    db_user = db.query(UserORM).filter(UserORM.id == user_id).first()
    hashed_password = hash_password(new_password)
    setattr(db_user, "hashed_password", hashed_password)
    db.commit()
    db.refresh(db_user)
    return db_user


def hash_password(password: str) -> str:
    """비밀번호를 bcrypt를 사용하여 해싱합니다.

    Args:
        password (str): 해싱할 평문 비밀번호

    Returns:
        str: bcrypt로 해싱된 비밀번호
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def check_password(password: str, hashed_password: str) -> bool:
    """입력받은 비밀번호와 저장된 해시값을 비교합니다.

    Args:
        password (str): 확인할 평문 비밀번호
        hashed_password (str): 저장된 해시된 비밀번호

    Returns:
        bool: 비밀번호가 일치하면 True, 아니면 False
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
