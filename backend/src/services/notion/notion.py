import httpx
from enum import Enum
from typing import Any, TypeVar, Type
from pydantic import BaseModel, Field, model_validator

from src.services.notion.schema import PropType
from src.utils.env import get_env
from src.utils.constants import Sync, Role


def extract_title(properties: dict, key: str) -> str:
    """Notion title 타입 속성에서 plain_text를 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리
        key: 추출할 속성의 키 이름

    Returns:
        추출된 텍스트, 없으면 빈 문자열
    """
    prop = properties.get(key, {})
    title_list = prop.get("title", [])
    return title_list[0].get("plain_text", "") if title_list else ""


def extract_rich_text(properties: dict, key: str) -> str:
    """Notion rich_text 타입 속성에서 plain_text를 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리
        key: 추출할 속성의 키 이름

    Returns:
        추출된 텍스트, 없으면 빈 문자열
    """
    prop = properties.get(key, {})
    text_list = prop.get("rich_text", [])
    return text_list[0].get("plain_text", "") if text_list else ""


def extract_select(properties: dict, key: str) -> str | None:
    """Notion select 타입 속성에서 선택된 값의 name을 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리
        key: 추출할 속성의 키 이름

    Returns:
        선택된 옵션의 name, 없으면 None
    """
    prop = properties.get(key, {})
    select_obj = prop.get("select")
    return select_obj.get("name") if select_obj else None


def extract_relation(properties: dict, key: str) -> list[str]:
    """Notion relation 타입 속성에서 연결된 페이지 ID 리스트를 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리
        key: 추출할 속성의 키 이름

    Returns:
        연결된 페이지 ID 리스트
    """
    prop = properties.get(key, {})
    relation_list = prop.get("relation", [])
    return [item.get("id", "") for item in relation_list]


def extract_email(properties: dict, key: str) -> str:
    """Notion email 타입 속성에서 이메일 주소를 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리
        key: 추출할 속성의 키 이름

    Returns:
        이메일 주소, 없으면 빈 문자열
    """
    prop = properties.get(key, {})
    return prop.get("email", "") or ""


def extract_phone(properties: dict, key: str) -> str:
    """Notion phone_number 타입 속성에서 전화번호를 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리
        key: 추출할 속성의 키 이름

    Returns:
        전화번호, 없으면 빈 문자열
    """
    prop = properties.get(key, {})
    return prop.get("phone_number", "") or ""


def extract_date(properties: dict, key: str) -> tuple[str, str]:
    """Notion date 타입 속성에서 시작일과 종료일을 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리
        key: 추출할 속성의 키 이름

    Returns:
        (시작일, 종료일) 튜플, 없으면 빈 문자열
    """
    prop = properties.get(key, {})
    date_obj = prop.get("date")
    if date_obj:
        return date_obj.get("start", ""), date_obj.get("end", "") or ""
    return "", ""


def extract_sync_status(properties: dict) -> Sync:
    """Notion Sync Status select 속성에서 Sync enum 값을 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리

    Returns:
        Sync enum 값, 없거나 잘못된 경우 Sync.Writing
    """
    status_name = extract_select(properties, "Sync Status")
    return Sync.text_to_sync(status_name) if status_name else Sync.Writing


def extract_role(properties: dict, key: str = "Role") -> Role:
    """Notion Role select 속성에서 Role enum 값을 추출합니다.

    Args:
        properties: Notion row의 properties 딕셔너리
        key: 추출할 속성의 키 이름 (기본값: "Role")

    Returns:
        Role enum 값, 없거나 잘못된 경우 Role.Guest
    """
    role_name = extract_select(properties, key)
    if role_name:
        try:
            return Role.text_to_role(role_name)
        except ValueError:
            pass
    return Role.Guest


# =============================================================================
# Record 모델 클래스들
# =============================================================================


class NotionRecord(BaseModel):
    """Notion 데이터베이스 레코드의 기본 클래스입니다.

    모든 Notion 레코드가 공통으로 가지는 속성들을 정의합니다.

    Attributes:
        status: 동기화 상태를 나타내는 Sync enum 값
        notion_id: Notion 페이지의 고유 ID
        log: 레코드의 로그 메시지
    """

    status: Sync
    notion_id: str
    log: str


class MemberRecord(NotionRecord):
    """멤버 데이터베이스 레코드를 나타내는 클래스입니다.

    Attributes:
        name: 멤버 이름
        student_id: 학번
        email: 이메일 주소
        role: 멤버 역할 (Role enum)
        groups: 소속 그룹 ID 리스트
        phone: 전화번호
        discord_id: Discord 사용자 ID
    """

    name: str = ""
    student_id: int = 0
    email: str = ""
    role: Role = Role.Guest
    groups: list[str] = Field(default_factory=list)
    phone: str = ""
    discord_id: str = ""

    @model_validator(mode="before")
    @classmethod
    def transform(cls, data: dict) -> dict:
        """API로 받은 member database의 record를 단순화합니다.

        Notion API 응답을 MemberRecord 생성에 필요한 형식으로 변환합니다.
        results 리스트가 있으면 첫 번째 결과를 추출하고,
        단일 row인 경우 직접 추출합니다.

        Args:
            data: Notion data_source query 결과 또는 단일 row

        Returns:
            MemberRecord 생성을 위한 딕셔너리
        """
        if "results" in data:
            results = data.get("results", [])
            return [cls._extract_row(result) for result in results]
        return cls._extract_row(data)

    @classmethod
    def _extract_row(cls, row: dict) -> dict:
        """단일 Notion row에서 MemberRecord 데이터를 추출합니다.

        Args:
            row: Notion data source query의 결과물 record

        Returns:
            MemberRecord 생성을 위한 딕셔너리
        """
        properties = row.get("properties", {})
        student_id_str = extract_rich_text(properties, "Student ID")

        return {
            "status": extract_sync_status(properties),
            "name": extract_title(properties, "Name"),
            "student_id": int(student_id_str) if student_id_str else 0,
            "email": extract_email(properties, "Email"),
            "role": extract_role(properties),
            "groups": extract_relation(properties, "Groups"),
            "phone": extract_phone(properties, "Phone"),
            "notion_id": row.get("id", ""),
            "discord_id": extract_rich_text(properties, "Discord ID"),
            "log": extract_rich_text(properties, "Log"),
        }


class GroupRecord(NotionRecord):
    """그룹 데이터베이스 레코드를 나타내는 클래스입니다.

    Attributes:
        name: 그룹 이름
        description: 그룹 설명
        discord_id: Discord 역할 ID (discord_role_id와 동일)
        discord_role_id: Discord 역할 ID
    """

    name: str = ""
    description: str = ""
    discord_id: str = ""
    discord_role_id: str = ""

    @model_validator(mode="before")
    @classmethod
    def transform(cls, data: dict) -> dict:
        """API로 받은 group database의 record를 단순화합니다.

        Notion API 응답을 GroupRecord 생성에 필요한 형식으로 변환합니다.

        Args:
            data: Notion data_source query 결과 또는 단일 row

        Returns:
            GroupRecord 생성을 위한 딕셔너리
        """
        if "results" in data:
            results = data.get("results", [])
            return [cls._extract_row(result) for result in results]
        return cls._extract_row(data)

    @classmethod
    def _extract_row(cls, row: dict) -> dict:
        """단일 Notion row에서 GroupRecord 데이터를 추출합니다.

        Args:
            row: Notion data source query의 결과물 record

        Returns:
            GroupRecord 생성을 위한 딕셔너리
        """
        properties = row.get("properties", {})
        discord_role_id = extract_rich_text(properties, "Discord Role ID")

        return {
            "status": extract_sync_status(properties),
            "name": extract_title(properties, "Name"),
            "notion_id": row.get("id", ""),
            "discord_id": discord_role_id,
            "log": extract_rich_text(properties, "Log"),
            "description": extract_rich_text(properties, "Description"),
            "discord_role_id": discord_role_id,
        }


class EventRecord(NotionRecord):
    """이벤트 데이터베이스 레코드를 나타내는 클래스입니다.

    Attributes:
        name: 이벤트 이름 (title과 동일)
        title: 이벤트 제목
        date_start: 이벤트 시작일
        date_end: 이벤트 종료일
        location: 이벤트 장소
        description: 이벤트 설명
        attendees: 참석자 ID 리스트
        groups: 관련 그룹 ID 리스트
    """

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
    def transform(cls, data: dict) -> dict:
        """API로 받은 event database의 record를 단순화합니다.

        Notion API 응답을 EventRecord 생성에 필요한 형식으로 변환합니다.

        Args:
            data: Notion data_source query 결과 또는 단일 row

        Returns:
            EventRecord 생성을 위한 딕셔너리
        """
        if "results" in data:
            results = data.get("results", [])
            return [cls._extract_row(result) for result in results]
        return cls._extract_row(data)

    @classmethod
    def _extract_row(cls, row: dict) -> dict:
        """단일 Notion row에서 EventRecord 데이터를 추출합니다.

        Args:
            row: Notion data source query의 결과물 record

        Returns:
            EventRecord 생성을 위한 딕셔너리
        """
        properties = row.get("properties", {})
        title = extract_title(properties, "Title")
        date_start, date_end = extract_date(properties, "Date")

        return {
            "status": extract_sync_status(properties),
            "name": title,
            "groups": extract_relation(properties, "Groups"),
            "notion_id": row.get("id", ""),
            "log": extract_rich_text(properties, "Log"),
            "title": title,
            "date_start": date_start,
            "date_end": date_end,
            "location": extract_rich_text(properties, "Location"),
            "description": extract_rich_text(properties, "Description"),
            "attendees": extract_relation(properties, "Attendees"),
        }


class DatabaseType(Enum):
    """Notion 데이터베이스 타입을 정의하는 열거형입니다.

    Attributes:
        MEMBER: 멤버 데이터베이스
        EVENT: 이벤트 데이터베이스
        GROUP: 그룹 데이터베이스
    """

    MEMBER = "member"
    EVENT = "event"
    GROUP = "group"


# Record 타입을 위한 TypeVar 정의
T = TypeVar("T", bound=NotionRecord)

# DatabaseType과 관련 정보 매핑
_DB_CONFIG: dict[DatabaseType, dict[str, Any]] = {
    DatabaseType.MEMBER: {
        "env_key": "NOTION_MEMBER_DB_ID",
        "source_attr": "member_source",
        "record_class": MemberRecord,
    },
    DatabaseType.EVENT: {
        "env_key": "NOTION_EVENT_DB_ID",
        "source_attr": "event_source",
        "record_class": EventRecord,
    },
    DatabaseType.GROUP: {
        "env_key": "NOTION_GROUP_DB_ID",
        "source_attr": "group_source",
        "record_class": GroupRecord,
    },
}


class Notion:
    """Notion API 요청을 위한 싱글톤 패턴의 클래스입니다.

    이 클래스는 Notion API와의 통신을 담당하며, 멤버, 그룹, 이벤트
    데이터베이스에 대한 CRUD 작업을 지원합니다.

    Note:
        이 파일의 notion_client를 import하여 다른 파일에서 사용하십시오.

    Attributes:
        base_url: Notion API의 기본 URL
        client: httpx 비동기 클라이언트
        member_source: 멤버 데이터소스 ID
        group_source: 그룹 데이터소스 ID
        event_source: 이벤트 데이터소스 ID
    """

    def __init__(self):
        """Notion 클라이언트를 초기화합니다.

        환경 변수에서 API 키를 가져와 HTTP 클라이언트를 설정합니다.
        """
        self.base_url = "https://api.notion.com/v1"
        self.client = httpx.AsyncClient()
        self.client.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {get_env('NOTION_API_KEY')}",
                "Notion-Version": "2025-09-03",
            }
        )
        self.member_source: str | None = None
        self.group_source: str | None = None
        self.event_source: str | None = None

    def update_header(self, params: dict) -> None:
        """HTTP 클라이언트의 헤더를 업데이트합니다.

        Args:
            params: 업데이트할 헤더 키-값 딕셔너리
        """
        self.client.headers.update(params)

    def change_api_key(self, api_key: str) -> None:
        """Notion API 키를 변경합니다.

        Args:
            api_key: 새로운 Notion API 키
        """
        self.update_header({"Authorization": f"Bearer {api_key}"})

    def change_version(self, version: str) -> None:
        """Notion API 버전을 변경합니다.

        Args:
            version: 사용할 Notion API 버전 (예: "2025-09-03")
        """
        self.update_header({"Notion-Version": version})

    async def get(self, url: str) -> dict:
        """지정된 URL로 GET 요청을 보냅니다.

        Args:
            url: 요청을 보낼 URL

        Returns:
            API 응답을 딕셔너리로 변환한 결과

        Raises:
            httpx.HTTPStatusError: HTTP 상태 에러 발생 시
            httpx.RequestError: 요청 에러 발생 시
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

    async def post(self, url: str, payload: dict | None = None) -> dict:
        """지정된 URL로 POST 요청을 보냅니다.

        Args:
            url: 요청을 보낼 URL
            payload: 요청 본문에 포함할 데이터 (기본값: None)

        Returns:
            API 응답을 딕셔너리로 변환한 결과

        Raises:
            httpx.HTTPStatusError: HTTP 상태 에러 발생 시
            httpx.RequestError: 요청 에러 발생 시
        """
        try:
            response = await self.client.post(url, json=payload or {})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP 에러 발생 : {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"잘못된 요청 에러 : {e}")
            raise

    async def check_health(self) -> bool:
        """Notion API 연결 상태를 확인합니다.

        현재 API 키로 인증된 사용자 정보를 조회하여 API가 정상 작동하는지 확인합니다.

        Returns:
            API가 정상 작동하면 True

        Raises:
            httpx.HTTPStatusError: API 연결 실패 시
        """
        await self.get(f"{self.base_url}/users/me")
        return True

    async def get_database(self, db_id: str) -> dict:
        """데이터베이스 정보를 조회합니다.

        Args:
            db_id: 조회할 Notion 데이터베이스 ID

        Returns:
            데이터베이스 메타데이터를 포함한 딕셔너리
        """
        return await self.get(f"{self.base_url}/databases/{db_id}")

    async def _ensure_data_source(self, db_type: DatabaseType) -> str:
        """특정 데이터베이스 타입의 데이터소스 ID를 확보합니다.

        데이터소스 ID가 캐시되어 있지 않으면 API에서 가져와 캐시합니다.

        Args:
            db_type: 확보할 데이터베이스 타입

        Returns:
            데이터소스 ID 문자열
        """
        config = _DB_CONFIG[db_type]
        source_attr = config["source_attr"]
        current_value = getattr(self, source_attr)

        if current_value is None:
            print(f"{source_attr} id is None -> retrieve database")
            response = await self.get_database(get_env(config["env_key"]))
            new_value = (
                response.get("data_sources", [{}])[0].get("id", "").replace("-", "")
            )
            setattr(self, source_attr, new_value)
            return new_value

        return current_value

    async def validate_ds_ids(self) -> None:
        """모든 데이터소스 ID가 설정되어 있는지 확인합니다.

        설정되어 있지 않은 데이터소스 ID는 데이터베이스에서 가져와 설정합니다.

        Note:
            25년 버전 이후 Notion API에는 data source라는 객체가 추가되었습니다.
        """
        for db_type in DatabaseType:
            await self._ensure_data_source(db_type)

    async def get_data_source(self, db_type: DatabaseType) -> dict:
        """특정 데이터베이스 타입의 데이터소스 정보를 조회합니다.

        Args:
            db_type: 조회할 데이터베이스 타입

        Returns:
            데이터소스 메타데이터를 포함한 딕셔너리
        """
        source_id = await self._ensure_data_source(db_type)
        return await self.get(f"{self.base_url}/data_sources/{source_id}")

    async def get_records(
        self, db_type: DatabaseType, payload: dict | None = None
    ) -> list[T]:
        """특정 데이터베이스 타입의 레코드들을 조회합니다.

        Args:
            db_type: 조회할 데이터베이스 타입
            payload: 쿼리 필터 및 정렬 옵션 (기본값: None)

        Returns:
            해당 데이터베이스 타입에 맞는 Record 객체 리스트
        """
        source_id = await self._ensure_data_source(db_type)
        config = _DB_CONFIG[db_type]
        results = await self.post(
            f"{self.base_url}/data_sources/{source_id}/query", payload
        )
        return config["record_class"].transform(results)

    # 하위 호환성을 위한 편의 메서드들
    async def get_member_ds(self) -> dict:
        """멤버 데이터소스 정보를 조회합니다.

        Returns:
            멤버 데이터소스 메타데이터
        """
        return await self.get_data_source(DatabaseType.MEMBER)

    async def get_group_ds(self) -> dict:
        """그룹 데이터소스 정보를 조회합니다.

        Returns:
            그룹 데이터소스 메타데이터
        """
        return await self.get_data_source(DatabaseType.GROUP)

    async def get_event_ds(self) -> dict:
        """이벤트 데이터소스 정보를 조회합니다.

        Returns:
            이벤트 데이터소스 메타데이터
        """
        return await self.get_data_source(DatabaseType.EVENT)

    async def get_member_records(
        self, payload: dict | None = None
    ) -> list[MemberRecord]:
        """멤버 레코드들을 조회합니다.

        Args:
            payload: 쿼리 필터 및 정렬 옵션 (기본값: None)

        Returns:
            MemberRecord 객체 리스트
        """
        return await self.get_records(DatabaseType.MEMBER, payload)

    async def get_group_records(self, payload: dict | None = None) -> list[GroupRecord]:
        """그룹 레코드들을 조회합니다.

        Args:
            payload: 쿼리 필터 및 정렬 옵션 (기본값: None)

        Returns:
            GroupRecord 객체 리스트
        """
        return await self.get_records(DatabaseType.GROUP, payload)

    async def get_event_records(self, payload: dict | None = None) -> list[EventRecord]:
        """이벤트 레코드들을 조회합니다.

        Args:
            payload: 쿼리 필터 및 정렬 옵션 (기본값: None)

        Returns:
            EventRecord 객체 리스트
        """
        return await self.get_records(DatabaseType.EVENT, payload)

    async def sync_datasource(self, db_type: DatabaseType) -> None:
        """노션의 데이터소스를 동기화하여 전체 시스템에 반영합니다.

        Args:
            db_type (DatabaseType): 동기화할 데이터베이스 타입
        """
        # TODO : 이거 만들기. 노션에서 데이터 불러와서 동기화하기
        records = await self.get_records(db_type)
        records_to_update = [
            record for record in records if record.status == Sync.Update
        ]
        # 동기화 수행
        await self.sync_records(db_type, records)
        # 삭제 데이터 동기화 수행
        records_to_delete = [
            record for record in records if not is_exist(db_type, record)
        ]
        await self.delete_records(db_type, records)

    async def is_exist(self, db_type: DatabaseType, record: NotionRecord) -> bool:
        """해당 record가 db에 존재하는지를 확인합니다.

        Args:
            db_type (DatabaseType):
            record (NotionRecord): _description_
        """
        

    async def sync_records(db_type: DatabaseType, records: list[NotionRecord]):
        """해당 record들을 db에 싱크시킵니다.

        Args:
            db_type (DatabaseType): _description_
            record (NotionRecord): _description_
        """
    
    async def delete_records(db_type: DatabaseType, records:list[NotionRecord]):
        """해당 record들을 db에서 삭제하고 동기화시킵니다.

        Args:
            db_type (DatabaseType): _description_
            records (list[NotionRecord]): _description_
        """


    async def close(self) -> None:
        """HTTP 클라이언트를 종료합니다.

        리소스 정리를 위해 사용이 끝난 후 반드시 호출해야 합니다.
        """
        await self.client.aclose()


class NotionDBInvalidPropError(Exception):
    """Notion 데이터베이스 속성이 유효하지 않을 때 발생하는 예외입니다.

    데이터베이스 스키마 검증 실패 시 상세 에러 정보와 함께 발생합니다.

    Attributes:
        message: 에러 메시지
        detail: 상세 에러 정보를 담은 딕셔너리
    """

    def __init__(self, message: str, detail: dict | None = None):
        """NotionDBInvalidPropError를 초기화합니다.

        Args:
            message: 에러 메시지
            detail: 상세 에러 정보 (기본값: None)
        """
        super().__init__(message)
        self.message = message
        self.detail = detail or {}

    def __str__(self) -> str:
        """에러의 문자열 표현을 반환합니다."""
        return f"NotionDBInvalidPropError({self.message}, {self.detail})"


def validate_db(target: dict, condition: dict) -> bool:
    """Notion 데이터베이스가 요구 조건에 맞게 구성되어 있는지 검증합니다.

    데이터베이스의 속성들이 지정된 조건(타입, relation, select 옵션 등)을
    만족하는지 확인합니다.

    Args:
        target: 검증할 데이터베이스의 data_source.properties
        condition: 검증 조건을 정의한 딕셔너리. 각 키는 속성 이름이고,
            값은 다음 키들을 포함할 수 있습니다:
            - type: PropType enum 값 (필수)
            - relation: relation 타입일 경우 연결된 데이터베이스 정보
            - select: select 타입일 경우 필요한 옵션 이름 리스트

    Returns:
        검증 성공 시 True

    Raises:
        NotionDBInvalidPropError: 검증 실패 시 상세 에러 목록과 함께 발생

    Example:
        >>> condition = {
        ...     "Name": {"type": PropType.title},
        ...     "Role": {"type": PropType.select, "select": ["Admin", "Member"]},
        ... }
        >>> validate_db(db_properties, condition)
        True
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
