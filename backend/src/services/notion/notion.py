import httpx
from enum import Enum
from pydantic import BaseModel, Field, model_validator

from src.services.notion.schema import PropType
from src.utils.env import get_env
from src.utils.constants import Sync, Role


class NotionRecord(BaseModel):
    status: Sync
    notion_id: str
    log: str


class MemberRecord(NotionRecord):
    name: str = ""
    student_id: int = 0
    email: str = ""
    role: Role = Role.Guest
    groups: list[str] = Field(default_factory=list)
    phone: str = ""
    discord_id: str = ""

    @model_validator(mode="before")
    @classmethod
    def transform(cls, data: dict) -> list["MemberRecord"]:
        """API로 받은 member database의 record를 단순화합니다.

        Args:
            data (dict): notion data_source query 결과

        Returns:
            list[MemberRecord]: 변환된 MemberRecord 리스트
        """
        results = data.get("results", [])
        return [cls.extract(result) for result in results]

    @staticmethod
    def extract(row: dict) -> dict:
        """Data_source의 행을 NotionRecord 타입으로 변경합니다.

        Args:
            row (dict): Data source query의 결과물 record

        Raises:
            NotionDBInvalidPropError: 필수 속성이 없거나 형식이 잘못된 경우

        Returns:
            dict: MemberRecord 생성을 위한 데이터
        """
        properties = row.get("properties", {})

        # Sync Status 추출
        sync_status_prop = properties.get("Sync Status", {})
        sync_select = sync_status_prop.get("select")
        status = (
            Sync.text_to_sync(sync_select.get("name")) if sync_select else Sync.Writing
        )

        # Name 추출
        name_prop = properties.get("Name", {})
        title_list = name_prop.get("title", [])
        name = title_list[0].get("plain_text", "") if title_list else ""

        # Student ID 추출
        student_id_prop = properties.get("Student ID", {})
        student_id_list = student_id_prop.get("rich_text", [])
        student_id = (
            int(student_id_list[0].get("plain_text", "0")) if student_id_list else 0
        )

        # Email 추출
        email_prop = properties.get("Email", {})
        email = email_prop.get("email", "")

        # Role 추출
        role_prop = properties.get("Role", {})
        role_select = role_prop.get("select")
        try:
            role = (
                Role.text_to_role(role_select.get("name"))
                if role_select
                else Role.Guest
            )
        except ValueError:
            role = Role.Guest

        # Groups 추출
        groups_prop = properties.get("Groups", {})
        groups_relation = groups_prop.get("relation", [])
        groups = [g.get("id", "") for g in groups_relation]

        # Phone 추출
        phone_prop = properties.get("Phone", {})
        phone = phone_prop.get("phone_number", "") or ""

        # Notion ID
        notion_id = row.get("id", "")

        # Discord ID 추출
        discord_id_prop = properties.get("Discord ID", {})
        discord_id_list = discord_id_prop.get("rich_text", [])
        discord_id = discord_id_list[0].get("plain_text", "") if discord_id_list else ""

        # Log 추출
        log_prop = properties.get("Log", {})
        log_list = log_prop.get("rich_text", [])
        log = log_list[0].get("plain_text", "") if log_list else ""

        return {
            "status": status,
            "name": name,
            "student_id": student_id,
            "email": email,
            "role": role,
            "groups": groups,
            "phone": phone,
            "notion_id": notion_id,
            "discord_id": discord_id,
            "log": log,
        }


class GroupRecord(NotionRecord):
    name: str = ""
    description: str = ""

    @model_validator(mode="before")
    @classmethod
    def transform(cls, data: dict) -> list["GroupRecord"]:
        """API로 받은 group database의 record를 단순화합니다.

        Args:
            data (dict): notion data_source query 결과

        Returns:
            list[GroupRecord]: 변환된 GroupRecord 리스트
        """
        results = data.get("results", [])
        return [cls.extract(result) for result in results]

    @staticmethod
    def extract(row: dict) -> dict:
        """Data_source의 행을 GroupRecord 타입으로 변경합니다.

        Args:
            row (dict): Data source query의 결과물 record

        Returns:
            dict: GroupRecord 생성을 위한 데이터
        """
        properties = row.get("properties", {})

        # Sync Status 추출
        sync_status_prop = properties.get("Sync Status", {})
        sync_select = sync_status_prop.get("select")
        status = (
            Sync.text_to_sync(sync_select.get("name")) if sync_select else Sync.Writing
        )

        # Name 추출
        name_prop = properties.get("Name", {})
        title_list = name_prop.get("title", [])
        name = title_list[0].get("plain_text", "") if title_list else ""

        # Description 추출
        desc_prop = properties.get("Description", {})
        desc_list = desc_prop.get("rich_text", [])
        description = desc_list[0].get("plain_text", "") if desc_list else ""

        # Discord Role ID 추출
        discord_role_prop = properties.get("Discord Role ID", {})
        discord_role_list = discord_role_prop.get("rich_text", [])
        discord_role_id = (
            discord_role_list[0].get("plain_text", "") if discord_role_list else ""
        )

        # Log 추출
        log_prop = properties.get("Log", {})
        log_list = log_prop.get("rich_text", [])
        log = log_list[0].get("plain_text", "") if log_list else ""

        # Notion ID
        notion_id = row.get("id", "")

        return {
            "status": status,
            "name": name,
            "notion_id": notion_id,
            "discord_id": discord_role_id,
            "log": log,
            "description": description,
            "discord_role_id": discord_role_id,
        }


class EventRecord(NotionRecord):
    name: str = ""
    title: str = ""
    date_start: str = ""
    date_end: str = ""
    location: str = ""
    description: str = ""
    attendees: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def transform(cls, data: dict) -> list["EventRecord"]:
        """API로 받은 event database의 record를 단순화합니다.

        Args:
            data (dict): notion data_source query 결과

        Returns:
            list[EventRecord]: 변환된 EventRecord 리스트
        """
        results = data.get("results", [])
        return [cls.extract(result) for result in results]

    @staticmethod
    def extract(row: dict) -> dict:
        """Data_source의 행을 EventRecord 타입으로 변경합니다.

        Args:
            row (dict): Data source query의 결과물 record

        Returns:
            dict: EventRecord 생성을 위한 데이터
        """
        properties = row.get("properties", {})

        # Sync Status 추출
        sync_status_prop = properties.get("Sync Status", {})
        sync_select = sync_status_prop.get("select")
        status = (
            Sync.text_to_sync(sync_select.get("name")) if sync_select else Sync.Writing
        )

        # Title 추출
        title_prop = properties.get("Title", {})
        title_list = title_prop.get("title", [])
        title = title_list[0].get("plain_text", "") if title_list else ""

        # Date 추출
        date_prop = properties.get("Date", {})
        date_obj = date_prop.get("date")
        date_start = date_obj.get("start", "") if date_obj else ""
        date_end = date_obj.get("end", "") if date_obj else ""

        # Groups 추출
        groups_prop = properties.get("Groups", {})
        groups_relation = groups_prop.get("relation", [])
        groups = [g.get("id", "") for g in groups_relation]

        # Attendees 추출
        attendees_prop = properties.get("Attendees", {})
        attendees_relation = attendees_prop.get("relation", [])
        attendees = [a.get("id", "") for a in attendees_relation]

        # Location 추출
        location_prop = properties.get("Location", {})
        location_list = location_prop.get("rich_text", [])
        location = location_list[0].get("plain_text", "") if location_list else ""

        # Description 추출
        desc_prop = properties.get("Description", {})
        desc_list = desc_prop.get("rich_text", [])
        description = desc_list[0].get("plain_text", "") if desc_list else ""

        # Log 추출
        log_prop = properties.get("Log", {})
        log_list = log_prop.get("rich_text", [])
        log = log_list[0].get("plain_text", "") if log_list else ""

        # Notion ID
        notion_id = row.get("id", "")

        return {
            "status": status,
            "name": title,  # Title을 name으로 매핑
            "groups": groups,
            "notion_id": notion_id,
            "log": log,
            "title": title,
            "date_start": date_start,
            "date_end": date_end,
            "location": location,
            "description": description,
            "attendees": attendees,
        }


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

    async def get(self, url: int) -> dict:
        """해당 url로 request를 보냅니다.

        Args:
            url (int): url

        Returns:
            _type_: json을 dict로 변경하여 반환합니다.
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP 에러 발생 : {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"잘못된 요청 에러 : {e}")
            raise

    async def post(self, url: int, payload: dict = {"data": {}}) -> dict:
        try:
            response = await self.client.post(url, data=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP 에러 발생 : {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"잘못된 요청 에러 : {e}")
            raise

    async def check_health(self) -> bool:
        """Notion API가 작동하는지 확인합니다. 정상적으로 작동하지 않을 경우, 에러를 발생시킵니다.

        Returns:
            bool:
        """
        await self.get(f"{self.base_url}/users/me")
        return True

    async def get_database(self, id: str) -> dict:
        """데이터베이스 정보 조회"""
        response = await self.get(f"{self.base_url}/databases/{id}")
        return response

    async def validate_ds_ids(self):
        if self.member_source is None:
            print(f"member_source id is None -> retrieve database")
            response = await self.get_database(get_env("NOTION_MEMBER_DB_ID"))
            self.member_source = (
                response.get("data_sources", [{}])[0].get("id").replace("-", "")
            )

        if self.group_source is None:
            print(f"group_source id is None -> retrieve database")
            response = await self.get_database(get_env("NOTION_GROUP_DB_ID"))
            self.group_source = (
                response.get("data_sources", [{}])[0].get("id").replace("-", "")
            )

        if self.event_source is None:
            print(f"event_source id is None -> retrieve database")
            response = await self.get_database(get_env("NOTION_EVENT_DB_ID"))
            self.event_source = (
                response.get("data_sources", [{}])[0].get("id").replace("-", "")
            )

    # 25년 notion에는 data source라는 객체가 추가되었음
    async def get_member_ds(self):
        await self.validate_ds_ids()
        response = await self.get(f"{self.base_url}/data_sources/{self.member_source}")
        return response

    async def get_group_ds(self):
        await self.validate_ds_ids()
        response = await self.get(f"{self.base_url}/data_sources/{self.group_source}")
        return response

    async def get_event_ds(self):
        await self.validate_ds_ids()
        response = await self.get(f"{self.base_url}/data_sources/{self.event_source}")
        return response

    async def get_member_records(self, payload: dict = None):
        await self.validate_ds_ids()
        return await self.post(
            f"{self.base_url}/data_sources/{self.member_source}/query", payload
        )

    async def get_group_records(self, payload: dict = None):
        await self.validate_ds_ids()
        return await self.post(
            f"{self.base_url}/data_sources/{self.group_source}/query", payload
        )

    async def get_event_records(self, payload: dict = None):
        await self.validate_ds_ids()
        return await self.post(
            f"{self.base_url}/data_sources/{self.event_source}/query", payload
        )

    async def close(self):
        await self.client.aclose()


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
