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
