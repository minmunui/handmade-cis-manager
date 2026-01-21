import httpx
from enum import Enum
from src.utils.env import get_env


class DatabaseType(Enum):
    """Notion 데이터베이스 타입"""

    MEMBER = "member"
    EVENT = "event"
    GROUP = "group"


class Notion:
    def __init__(self):
        self.base_url = "https://api.notion.com/v1"
        self.client = httpx.AsyncClient()
        self.client.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {get_env("NOTION_API_KEY")}",
                "Notion-Version": "2025-09-03",
            }
        )
        self.member_source = None
        self.group_source = None
        self.event_source = None

    def update_header(self, params: dict):
        self.client.headers.update(params)

    def change_api_key(self, api_key: str):
        self.update_header({"Authorization": f"Bearer {api_key}"})

    def change_version(self, version: str):
        self.update_header({"Notion-Version": version})

    async def check_health(self):
        response = await self.client.get(f"{self.base_url}/users/me")
        response.raise_for_status()  # 오류 발생 시 예외 처리

    async def get_database(self, id: str):
        """데이터베이스 정보 조회"""
        try:
            response = await self.client.get(f"{self.base_url}/databases/{id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Failed to get database {id}: {e}")
            raise

    async def _load_database_source(self, db_type: DatabaseType, env_key: str):
        """데이터베이스 로드 및 source ID 저장"""
        response = await self.get_database(get_env(env_key))
        source_id = response.get("data_sources", [{}])[0].get("id")

        if source_id:
            if db_type == DatabaseType.MEMBER:
                self.member_source = source_id
            elif db_type == DatabaseType.EVENT:
                self.event_source = source_id
            elif db_type == DatabaseType.GROUP:
                self.group_source = source_id

        return response

    async def get_member_db(self):
        """멤버 데이터베이스 조회"""
        return await self._load_database_source(
            DatabaseType.MEMBER, "NOTION_MEMBER_DB_ID"
        )

    async def get_event_db(self):
        """이벤트 데이터베이스 조회"""
        return await self._load_database_source(
            DatabaseType.EVENT, "NOTION_EVENT_DB_ID"
        )

    async def get_group_db(self):
        """그룹 데이터베이스 조회"""
        return await self._load_database_source(
            DatabaseType.GROUP, "NOTION_GROUP_DB_ID"
        )
    
    # 25년 notion에는 data source라는 객체가 추가되었음
    async def get_member_ds(self):
        if self.member_source is None:
            print(f"member_source id is None -> retrieve database")
            await self.get_member_db()
        response = await self.client.get(f"{self.base_url}/data_sources/{self.member_source}")
        return response.json()
    
    async def get_group_ds(self):
        if self.group_source is None:
            print(f"group_source id is None -> retrieve database")
            await self.get_group_db()
        response = await self.client.get(f"{self.base_url}/data_sources/{self.group_source}")
        return response.json()
    
    async def get_event_ds(self):
        if self.event_source is None:
            await self.get_event_db()
        response = await self.client.get(f"{self.base_url}/data_sources/{self.event_source}")
        return response.json()
    
    async def close(self):
        await self.client.aclose()


# 싱글톤 패턴
notion_client = Notion()
