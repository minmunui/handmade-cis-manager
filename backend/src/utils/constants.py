from enum import Enum
from discord import Colour as DiscordColour


class Color(Enum):
    """색상 정의 및 플랫폼별 색상 코드 관리"""

    # (value, hex_code, notion_color, discord_color)
    BASIC = (0, "#FFFFFF", "default", DiscordColour.light_grey())
    GREY = (1, "#808080", "gray", DiscordColour.dark_grey())
    BROWN = (2, "#8B4513", "brown", DiscordColour.dark_orange())
    ORANGE = (3, "#FF8C00", "orange", DiscordColour.orange())
    YELLOW = (4, "#FFD700", "yellow", DiscordColour.yellow())
    GREEN = (5, "#32CD32", "green", DiscordColour.green())
    BLUE = (6, "#4169E1", "blue", DiscordColour.blue())
    PURPLE = (7, "#9370DB", "purple", DiscordColour.purple())
    PINK = (8, "#FF69B4", "pink", DiscordColour.pink())
    RED = (9, "#FF0000", "red", DiscordColour.red())

    def __init__(
        self, value: int, hex_code: str, notion_color: str, discord_color: DiscordColour
    ):
        self._value_ = value
        self.hex_code = hex_code
        self.notion_color = notion_color
        self.discord_color = discord_color

    @property
    def color_code(self) -> str:
        """Hex 색상 코드 반환"""
        return self.hex_code

    @classmethod
    def from_value(cls, value: int) -> "Color":
        """정수 값으로 Color 찾기"""
        for color in cls:
            if color.value == value:
                return color
        return cls.BASIC

    @classmethod
    def from_notion_color(cls, notion_color: str) -> "Color":
        """Notion 색상 이름으로 Color 찾기"""
        for color in cls:
            if color.notion_color == notion_color:
                return color
        return cls.BASIC


class Sync(Enum):
    # 아래는 업데이트 하지 않음
    # (text, Color)
    Writing = ("Writing", Color.GREY)  # 작성 중
    Updating = ("Updating", Color.YELLOW)  # 업데이트 진행 중
    Deleted = ("Deleted", Color.BASIC)  # 삭제됨
    Invited = ("Invited", Color.GREEN)  # 초대됨
    Synced = ("Synced", Color.GREEN)  # 싱크 완료됨
    Error = ("Error", Color.RED)  # 에러

    # 아래는 업데이트 해야 함
    Update = ("Update", Color.PINK)  # 업데이트 준비/요청 됨
    Delete = ("Delete", Color.GREY)  # 삭제 요청

    @property
    def Notion(self) -> str:
        return self[1][2]
    
    @classmethod
    def text_to_sync(cls, text: str):
        for sync in cls:
            if text == sync.value[0]:
                return sync
        raise ValueError(f"{text}는 올바르지 않는 Sync Status입니다.")

class Role(Enum):
    Admin = "Admin"
    Member = "Member"
    Guest = "Guest"

    def __repr__(self):
        return f"Role<{self.value}>"
    def __str__(self):
        return self.__repr__()

    @classmethod
    def text_to_role(cls, text: str):
        for role in cls:
            if text == role.value:
                return role
        print(text)
        raise ValueError(f"{text}는 올바르지 않은 Role입니다.")
    
# 하위 호환성을 위한 딕셔너리 (deprecated)
ColorCode = {color.value: color.hex_code for color in Color}
NotionColor = {color.value: color.notion_color for color in Color}
DiscordColor = {color.value: color.discord_color for color in Color}
