from enum import Enum
from src.utils.env import get_env


class PropType(Enum):
    rich_text = "rich_text"
    email = "email"
    relation = "relation"
    select = "select"
    title = "title"
    phone_number = "phone_number"
    date = "date"


#
class NotionDBInvalidPropError(Exception):
    def __init__(self, message: str, detail: dict = {}):
        super().__init__(message)
        self.message = message
        self.detail = detail

    def __str__(self):
        return f"NotionDBInvalidPropError({self.message}, {self.detail})"


# Notion Database 검증을 위해서 사용
def validate_db(target: dict, condition: dict) -> list[str]:
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

    target = target.get("properties") if target.get("properties") is not None else target

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
                    errors.append(f"속성 {c_key}에 선택지 {c_sel}가 존재하지 않습니다. "
                                  f"존재하는 선택지 : {t_selects}")
    return errors


def MemberCondition():
    return {
        "Discord ID": {"type": PropType.rich_text},
        "Email": {"type": PropType.email},
        "Groups": {
            "type": PropType.relation,
            "relation": {
                "database_id": get_env("NOTION_GROUP_DB_ID")
            },  # 매 호출마다 최신 환경변수를 반영하기 위함
        },
        "Log": {"type": PropType.rich_text},
        "Member Status": {
            "type": PropType.select,
            "select": ["Pending", "Active"],
        },
        "Name": {"type": PropType.title},
        "Phone": {"type": PropType.phone_number},
        "Role": {"type": PropType.select, "select": ["Member", "Guest", "Admin"]},
        "Student ID": {"type": PropType.rich_text},
        "Sync Status": {
            "type": PropType.select,
            "select": [
                "Update",
                "Synced",
                "Writing",
                "Updating",
                "Deleted",
                "Delete",
                "Invited",
                "Error",
            ],
        },
    }


def GroupCondition():
    return {
        "Description": {"type": PropType.rich_text},
        "Discord Role ID": {"type": PropType.rich_text},
        "Log": {"type": PropType.rich_text},
        "Name": {"type": PropType.title},
        "Sync Status": {
            "type": PropType.select,
            "select": [
                "Update",
                "Writing",
                "Updating",
                "Delete",
                "Deleted",
                "Synced",
                "Error",
            ],
        },
    }


def EventCondition():
    return {
        "Attendees": {
            "type": PropType.relation,
            "relation": {
                "database_id": get_env("NOTION_MEMBER_DB_ID")
            },  # 매 호출마다 최신 환경변수를 반영하기 위함
        },
        "Date": {"type": PropType.date},
        "Description": {"type": PropType.rich_text},
        "Groups": {
            "type": PropType.relation,
            "relation": {
                "database_id": get_env("NOTION_GROUP_DB_ID")
            },  # 매 호출마다 최신 환경변수를 반영하기 위함
        },
        "Location": {"type": PropType.rich_text},
        "Log": {"type": PropType.rich_text},
        "Sync Status": {
            "type": PropType.select,
            "select": [
                "Update",
                "Writing",
                "Updating",
                "Delete",
                "Deleted",
                "Synced",
                "Error",
            ],
        },
        "Title": {"type": PropType.title},
    }
