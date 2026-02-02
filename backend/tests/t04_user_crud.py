"""User CRUD 테스트 모듈

이 모듈은 사용자 생성, 조회, 수정, 삭제 기능을 테스트합니다.
"""

from src.core.database import SessionLocal, engine
from src.models.base import Base

# 모든 모델을 import해야 relationship이 올바르게 설정됨
from src.models.user import UserORM
from src.models.group import GroupORM
from src.models.event import EventORM
from src.schemas.user import UserCreate, UserUpdate
from src.crud.user import create_user, get_user, update_user, delete_user

# 1. 테스트용 테이블 생성 (기존 테이블이 없으면 생성함)
Base.metadata.create_all(bind=engine)


def test_crud_flow():
    """사용자 CRUD 전체 플로우를 테스트합니다."""
    # 2. 세션 직접 생성
    db = SessionLocal()

    try:
        print("=== User CRUD Test ===\n")

        print("--- [1] Create Test ---")
        user_in = UserCreate(
            username="tester",
            email="test@example.com",
            phone="01012345678",
            student_id="20240001",
            password="password123",
        )
        new_user = create_user(db, user_in)
        print(f"✓ Created User: {new_user.email}, ID: {new_user.id}")
        print(f"  Username: {new_user.username}")

        print("\n--- [2] Read Test ---")
        found_user = get_user(db, new_user.id)
        print(f"✓ Found User: {found_user.username}")
        print(f"  Email: {found_user.email}")
        print(f"  Phone: {found_user.phone}")

        print("\n--- [3] Update Test ---")
        update_data = UserUpdate(username="updated_tester", phone="01087654321")
        updated_user = update_user(db, new_user.id, update_data)
        print(f"✓ Updated Username: {updated_user.username}")
        print(f"  Updated Phone: {updated_user.phone}")

        print("\n--- [4] Delete Test ---")
        success = delete_user(db, new_user.id)
        print(f"✓ Delete Success: {success}")

        # 삭제 확인
        print("\n--- [5] Verify Deletion ---")
        try:
            deleted_user = get_user(db, new_user.id)
            print(f"✗ User still exists: {deleted_user is not None}")
        except ValueError as e:
            print(f"✓ User successfully deleted: {e}")

        print("\n=== All tests passed! ===")

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # 3. 세션 닫기 (매우 중요)
        db.close()


if __name__ == "__main__":
    test_crud_flow()
