from sqlalchemy import Uuid, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session

import uuid
import os
from dotenv import dotenv_values
from datetime import datetime
from src.utils.crypto import decrypt_value, encrypt_value
from src.models.base import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    # 환경변수 키
    key: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    # 환경변수 값
    value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 생성시간
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # 업데이트 시간
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    # 환경변수 설명
    description: Mapped[str | None] = mapped_column(
        String(128), unique=False, nullable=True
    )

    @staticmethod
    def get_config(db: Session, key: str):
        """
        db에서 특정 환경변수를 가져옵니다. 해당 값이 없을 경우, 환경변수에서 해당 값을 가져오고, DB에 저장합니다.

        :param db: DB Session
        :type db: Session
        :param key: 가져올 환경변수 Key값
        :type key: str
        :param default: 설명
        :type default: str
        """
        db_setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if db_setting:
            return decrypt_value(db_setting.value)
        else:
            value = os.getenv(key)
            SystemSetting.update_config(db, key, value)
            return value

    @staticmethod
    def update_config(db: Session, key: str, value: str):
        """
        db의 특정 환경변수를 추가합니다. 이를 직접적으로 사용하지 말고, utils/env.py의 함수를 사용하시길 바랍니다.

        :param db: 설명
        :type db: Session
        :param key: 설명
        :type key: str
        :param value: 설명
        :type value: str
        """
        db_setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()

        # cipher value
        c_value = encrypt_value(value)

        if db_setting:
            db_setting.value = c_value
        else:
            db_setting = SystemSetting(key=key, value=c_value)
            db.add(db_setting)


        db.commit()
        db.refresh(db_setting)
        os.environ[key] = value
        return db_setting

    @staticmethod
    def init_config(db: Session):
        """
        db에 환경변수가 존재하지 않는다면, .env의 환경변수를 이용하여, db에 환경변수를 추가합니다.

        :param db: Database Session
        :type db: Session
        """
        env_dict = dotenv_values()
        print(f"Dict detected : \n{env_dict}")

        for key, value in env_dict.items():
            # ENC_KEY는 저장하지 않음
            if key == "ENC_KEY":
                continue

            record = db.query(SystemSetting).filter(SystemSetting.key == key).first()

            # 해당 환경변수 값이 존재
            if record:
                os.environ[key] = decrypt_value(record.value)
                print(f"  ✓ {key} already exists")

            # 해당 환경변수 값이 존재하지 않음
            else:
                c_value = encrypt_value(value)
                new_setting = SystemSetting(key=key, value=c_value)
                db.add(new_setting)
                print(f"  + Added {key}")

        db.commit()
        print("\n✓ System settings initialized successfully")