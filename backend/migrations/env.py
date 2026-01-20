from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
from pathlib import Path
from dotenv import load_dotenv

# docker-compose와 로컬 실행에서 공통된 .env를 참고하기 위한 파트입니다.
# 현재 env.py 위치에서 프로젝트 루트의 .env를 찾음
BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv_path = BASE_DIR / ".env"

# 위 방법을 통해 .env를 찾을 수 있다면, .env의 환경변수를 사용함
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# .env가 존재하면 위를 통해 설정된 루트 경로의 .env를, docker 환경이라면, 일반적인 환경변수를 아래 코드에서 불러오게 됩니다.
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
db_name = os.getenv("POSTGRES_DB")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")

database_url = f'postgresql://{user}:{password}@{db_host}:{db_port}/{db_name}'

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
# alembic.ini에서는 비어있는 database.url을 덮어씁니다.
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from src.models.base import Base
from src.models.user import User
from src.models.event import Event
from src.models.group import Group
from src.models.assiciation import user_event_association, user_group_association, group_event_association

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
