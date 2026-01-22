import httpx
from enum import Enum
from backend.src.services.notion.schema import PropType
from src.utils.env import get_env


class DatabaseType(Enum):
    """Notion 데이터베이스 타입"""

    MEMBER = "member"
    EVENT = "event"
    GROUP = "group"


class Notion:
    """
    Notion API 요청을 위한 싱글톤 패턴의 클래스입니다.
    이 파일의 notion_client를 import하여 다른 파일에서 사용하십시오.
    """
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

    async def check_health(self) -> bool:
        response = await self.client.get(f"{self.base_url}/users/me")
        response.raise_for_status()  # 오류 발생 시 예외 처리
        return True

    async def get_database(self, id: str):
        """데이터베이스 정보 조회"""
        try:
            response = await self.client.get(f"{self.base_url}/databases/{id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Failed to get database {id}: {e}")
            raise e

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


#
class NotionDBInvalidPropError(Exception):
    def __init__(self, message: str, detail: dict = {}):
        super().__init__(message)
        self.message = message
        self.detail = detail

    def __str__(self):
        return f"NotionDBInvalidPropError({self.message}, {self.detail})"


# Notion Database 검증을 위해서 사용
def validate_db(target: dict, condition: dict) -> bool:
    """
    notion db가 조건에 맞게 구성되어 있는지 검증합니다.
    맞지 않는 형태가 있을 경우, 에러 메시지들을 반환합니다.

    :param target: 현재 db data_source.properties
    :type target: dict
    :param condition: data_source 조건 dictionary
    :type condition: dict
    :return: 검증 결과, 검증이 맞지 않을 경우, Error를 raise하고, 맞을 경우, True를 반환합니다.
    :rtype: bool
    """
    errors = []

    target = (
        target.get("properties") if target.get("properties") is not None else target
    )

    for c_key, c_item in condition.items():
        c_type = c_item["type"]
        t_value = target.get(c_key, {})
        t_type = t_value.get("type")
        # 존재 검증
        if t_type is None:
            errors.append(f"속성 {c_key}가 존재하지 않습니다.")
            continue
        # 타입 검증
        if c_type.value != t_type:
            errors.append(f"속성 {c_key}의 타입은 {c_type.value}이어야 합니다.")
            continue

        # relation 검증
        if c_type == PropType.relation:
            c_relations = c_item.get("relation")
            t_relations = t_value.get("relation")
            # condition의 relation 값과 target의 relation 값이 일치하는지 확인
            for c_rel_key, c_rel_value in c_relations.items():
                t_rel_value = t_relations.get(c_rel_key).replace("-", "")
                if t_rel_value != c_rel_value:
                    errors.append(
                        f"속성 {c_key}의 관계가 제대로 연결되지 않았습니다. "
                        f"ID `{t_rel_value}가 아닌 {c_rel_value}`와 연결되어야 합니다."
                    )
        # select 검증
        if c_type == PropType.select:
            c_selects = c_item.get("select")
            # notion api로 부터 select 속성의 options 가져오기
            t_selects = [i.get("name") for i in t_value.get("select").get("options")]
            # condition의 select값이 target에 모두 존재하는지 확인
            for c_sel in c_selects:
                if c_sel not in t_selects:
                    errors.append(
                        f"속성 {c_key}에 선택지 {c_sel}가 존재하지 않습니다. "
                        f"존재하는 선택지 : {t_selects}"
                    )

    if errors:
        raise NotionDBInvalidPropError(
            "Notion Database가 유효하지 않습니다. Notion의 Database가 제대로 설정되었는지 확인하십시오.",
            {"errors": errors},
        )
    else:
        return True


# 싱글톤 패턴
notion_client = Notion()
