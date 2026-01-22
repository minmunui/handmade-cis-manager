import discord
from discord.guild import Guild
from discord.ext import commands
import httpx
import asyncio
import os
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

from src.utils.env import get_env
from src.utils.constants import Color

class Discord:
    def __init__(self):
        """
        Discord 봇과 HTTP 클라이언트를 초기화합니다.
        
        기본 권한(Intents)을 설정하고, API 통신을 위한 HTTP 클라이언트와
        Discord Bot 객체를 생성합니다.
        """
        # discord bot 권한 설정
        intents = discord.Intents.default()
        intents.message_content = True  # 메시지 읽기
        intents.members = True          # 멤버 관리

        # 현재 실행중인 이벤트 루프 가져오기 (없으면 새로 생성하지 않음 - asyncio.run()이나 uvicorn 실행 시 자동 생성됨)
        try:
           self.loop = asyncio.get_running_loop()
        except RuntimeError:
           self.loop = None

        # Httpx 클라이언트 -> REST API 사용
        self.httpx_client : httpx.AsyncClient = httpx.AsyncClient()
        self.httpx_client.headers.update({
            "Authorization": f"Bot {get_env("DISCORD_BOT_TOKEN")}"
        })

        # discord 봇 설정
        self.bot : commands.Bot = None # Lazy initialization
        self.url : str = "https://discord.com/api"
        
        self.guild : Guild = None

    def change_api_key(self, api_key:str):
        """런타임 중 API 키 변경"""
        self.httpx_client.headers.update({
            "Authorization": f"Bot {api_key}"
        })

    async def init_bot(self):
        """Discord Bot 객체 초기화 (이벤트 루프 내부에서 호출해야 함)"""
        if self.bot is None:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            self.bot = commands.Bot(command_prefix='!', intents=intents)
            if get_env("DISCORD_BOT_TOKEN"):
                await self.bot.login(get_env("DISCORD_BOT_TOKEN"))

    async def check_health(self) -> bool:
        """
        Discord 봇 API 상태를 확인합니다.

        :return: 상태가 정상이면 True 반환
        :raises Exception: 인증 실패(401), 잘못된 요청(400), 호출 한도 초과(429) 등의 경우 예외 발생
        """
        response = await self.httpx_client.get(f"{self.url}/v10/users/@me")
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            raise Exception("인증되지 않음, 디스코드 봇 토큰이 유효한지 확인해 주십시오")
        elif response.status_code == 400:
            raise Exception("잘못된 요청입니다.")
        elif response.status_code == 429:
            raise Exception("Discord API 한도 도달. 잠시 후(약 10초) 수행해 주세요.")
        else:
            response.raise_for_status()
            return False
        
    async def start_bot(self) -> bool:
        """
        Discord 봇을 실행합니다.

        :return: 실행 성공 시 True
        :rtype: bool
        """
        if not get_env("DISCORD_BOT_TOKEN"):
             print("Discord Bot Token is missing")
             return False

        try:
            if self.bot is None or not self.bot.is_ready():
                 # init_bot에서 login까지 수행됨
                 if self.bot is None:
                     await self.init_bot()
            
            # login은 init_bot에서 했으므로 connect만 수행
            await self.bot.connect()
            return True
        except Exception as e:
            print(f"Failed to start Discord bot: {e}")
            return False

    async def _init_guild(self, guild_id:int=None):
        """
        Discord 길드(서버) 정보를 초기화합니다.

        :param guild_id: 초기화할 길드 ID (기본값: None, 환경변수에서 로드)
        :type guild_id: int, optional
        """
        self.guild = self._get_guild(guild_id)
        

    async def _get_guild(self, guild_id:int= None):
        """
        지정된 ID의 길드 객체를 반환합니다. 
        guild_id가 없으면 환경변수 DISCORD_GUILD_ID를 사용합니다.

        :param guild_id: 조회할 길드 ID
        :type guild_id: int, optional
        :return: Discord Guild 객체
        :raises ValueError: 길드가 존재하지 않을 경우
        """
        if self.guild:
             return self.guild

        guild_id = guild_id or int(get_env("DISCORD_GUILD_ID"))
        
        # 먼저 캐시에서 확인
        guild = self.bot.get_guild(guild_id)
        
        # 캐시에 없으면 API로 요청
        if not guild:
            try:
                guild = await self.bot.fetch_guild(guild_id)
            except discord.Forbidden:
                raise ValueError(f"서버(ID: {guild_id})에 접근할 권한이 없습니다.")
            except discord.HTTPException:
                raise ValueError(f"서버(ID: {guild_id}) 정보를 가져오는 중 오류가 발생했습니다.")
        
        if not guild:
            raise ValueError(f"서버(ID: {guild_id})가 존재하지 않거나, 봇이 해당 서버에 존재하지 않습니다.")
            
        self.guild = guild
        return guild

    # --- [ 역할 관리 ] ---
        
    async def create_role(self, name:str, color:discord.Colour=Color.BASIC.discord_color) -> discord.Role:
        """
        새로운 역할을 생성합니다.

        :param name: 역할 이름
        :param color: 역할 색상 (기본값: Color.BASIC)
        :return: 생성된 discord.Role 객체
        :raises Exception: 권한이 없을 경우
        """
        guild = await self._get_guild()
        try:
            role = await guild.create_role(name=name, color=color)
            return role
        except discord.Forbidden:
            raise Exception("봇에게 역할 관리 권한이 없습니다.")
        
    async def delete_role(self, role_id: int):
        """
        역할을 삭제합니다.

        :param role_id: 삭제할 역할 ID
        :return: 삭제 성공 시 True, 실패 시 False
        """
        guild = await self._get_guild()
        role = guild.get_role(role_id)

        if role:
            await role.delete()
            return True
        return False

    async def update_role(self, guild_id: int, role_id: int, **kwargs):
        """
        역할 정보를 수정합니다.

        :param guild_id: 길드 ID
        :param role_id: 수정할 역할 ID
        :param kwargs: 수정할 속성 (예: name='새이름', color=...)
        :return: 수정된 discord.Role 객체
        :raises ValueError: 역할을 찾을 수 없는 경우
        """
        guild = await self._get_guild(guild_id)
        role = guild.get_role(role_id)
        if role:
            await role.edit(**kwargs)
            return role
        raise ValueError("해당 역할을 찾을 수 없습니다.")
    
    # --- [ 카테고리 관리 ] ---

    async def create_category(self, name: str, role_ids_allowed: list[int] = None):
        """
        새로운 카테고리를 생성합니다.

        :param name: 카테고리 이름
        :param role_ids_allowed: 카테고리에 접근 가능한 역할 ID 목록
        :return: 생성된 discord.CategoryChannel 객체
        """
        guild = await self._get_guild()
        overwrites = {}
        
        # 특정 역할만 볼 수 있게 설정
        if role_ids_allowed:
            overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
            for rid in role_ids_allowed:
                role = guild.get_role(rid)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True)

        return await guild.create_category(name=name, overwrites=overwrites)

    async def delete_category(self, category_id: int):
        """
        카테고리를 삭제합니다.

        :param category_id: 삭제할 카테고리 ID
        :return: 삭제 성공 시 True, 실패(카테고리 아님/없음) 시 False
        """
        # get_channel은 카테고리도 포함하여 검색함
        guild = await self._get_guild()
        category = guild.get_channel(category_id)
        if isinstance(category, discord.CategoryChannel):
            await category.delete()
            return True
        return False

    async def update_category(self, category_id: int, name: str):
        """
        카테고리 이름을 변경합니다.

        :param category_id: 카테고리 ID
        :param name: 변경할 이름
        :return: 수정된 discord.CategoryChannel 객체
        :raises ValueError: 유효한 카테고리가 아닌 경우
        """
        guild = await self._get_guild()
        category = guild.get_channel(category_id)
        if isinstance(category, discord.CategoryChannel):
            await category.edit(name=name)
            return category
        raise ValueError("유효한 카테고리가 아닙니다.")

    # --- [ (음성, 대화)채널 ] ---

    async def create_channel(self, name: str, category_id: int = None):
        """
        텍스트 채널을 생성합니다.

        :param name: 채널 이름
        :param category_id: 채널이 속할 카테고리 ID (옵션)
        :return: 생성된 discord.TextChannel 객체
        """
        guild = await self._get_guild()
        category = guild.get_channel(category_id) if category_id else None
        
        return await guild.create_text_channel(name=name, category=category)

    async def update_channel(self, channel_id: int, name: str = None):
        """
        채널 정보를 수정합니다.

        :param channel_id: 채널 ID
        :param name: 변경할 채널 이름
        :return: 수정된 discord.abc.GuildChannel 객체
        :raises ValueError: 채널을 찾을 수 없는 경우
        """
        channel = self.bot.get_channel(channel_id)
        if not channel:
            raise ValueError("채널을 찾을 수 없습니다.")
        
        # 변경할 값만 딕셔너리로 구성
        options = {}
        if name: options['name'] = name
        
        return await channel.edit(**options)

    async def delete_channel(self, channel_id: int):
        """
        채널을 삭제합니다.

        :param channel_id: 삭제할 채널 ID
        :return: 삭제 성공 시 True, 채널이 없으면 False
        """
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.delete()
            return True
        return False

    # --- [ User 관리 ] ---

    async def kick_user(self, guild_id: int, user_id: int, reason: str = None):
        """
        사용자를 추방(Kick)합니다.

        :param guild_id: 길드 ID
        :param user_id: 추방할 사용자 ID
        :param reason: 추방 사유
        :return: 성공 시 True, 사용자 없음 시 False
        """
        guild = await self._get_guild(guild_id)
        member = await guild.fetch_member(user_id) # 멤버 정보는 API로 최신화
        if member:
            await member.kick(reason=reason)
            return True
        return False

    async def add_user_role(self, guild_id: int, user_id: int, role_id: int):
        """
        사용자에게 역할을 부여합니다.

        :param guild_id: 길드 ID
        :param user_id: 사용자 ID
        :param role_id: 부여할 역할 ID
        :return: 성공 시 True, 멤버나 역할이 없으면 False
        """
        guild = await self._get_guild(guild_id)
        member = await guild.fetch_member(user_id)
        role = guild.get_role(role_id)
        
        if member and role:
            await member.add_roles(role)
            return True
        return False

    async def delete_user_role(self, guild_id: int, user_id: int, role_id: int):
        """
        사용자의 역할을 회수합니다.

        :param guild_id: 길드 ID
        :param user_id: 사용자 ID
        :param role_id: 회수할 역할 ID
        :return: 성공 시 True, 멤버나 역할이 없으면 False
        """
        guild = await self._get_guild(guild_id)
        member = await guild.fetch_member(user_id)
        role = guild.get_role(role_id)
        
        if member and role:
            await member.remove_roles(role)
            return True
        return False

    # --- [ 메시지 관리 ] ---

    async def send_message(self, channel_id: int, content: str = None, embed: dict = None):
        """
        특정 채널에 메시지를 전송합니다.

        :param channel_id: 메시지를 보낼 채널 ID
        :param content: 메시지 텍스트 내용
        :param embed: 임베드 메시지 (dict 또는 discord.Embed 객체)
        :return: 전송 성공 시 True
        :raises ValueError: 채널을 찾을 수 없는 경우
        :raises discord.Forbidden: 전송 권한이 없는 경우
        """
        # channel = self.bot.get_channel(channel_id)
        # get_channel은 캐시에서만 찾으므로, fetch_channel을 사용하여 API로 직접 가져옴
        try:
            channel = await self.bot.fetch_channel(channel_id)
        except discord.NotFound:
             channel = None
        except discord.Forbidden:
             raise discord.Forbidden("채널에 접근할 권한이 없습니다.")
             
        if not channel:
            raise ValueError(f"채널(ID: {channel_id})을 찾을 수 없어 메시지를 보내지 못했습니다.")

        discord_embed = discord.Embed.from_dict(embed) if isinstance(embed, dict) else embed

        try:
            await channel.send(content=content, embed=discord_embed)
            return True
        except discord.Forbidden:
            raise discord.Forbidden("메시지 전송 실패: 권한이 없습니다.")
    
    async def create_invite(self, max_age=86400, max_uses=1):
        """
        특정 서버의 초대 링크를 생성하여 반환합니다.
        기본값: 24시간 유효(86400초), 1회 사용 가능
        """
        
        # invite_url 생성을 위해 길드 정보 확인 (lazy load)
        guild = await self._get_guild()

        # 초대장을 만들 채널 선정 (시스템 채널 -> 첫번째 텍스트 채널 순)
        channel = guild.system_channel
        if not channel:
            # 텍스트 채널 중 첫 번째 채널 선택
            text_channels = guild.text_channels
            if text_channels:
                channel = text_channels[0]
        
        if not channel:
            raise Exception("초대장을 생성할 텍스트 채널이 없습니다.")

        try:
            invite = await channel.create_invite(max_age=max_age, max_uses=max_uses)
            return invite.url
        except discord.Forbidden:
            raise Exception("권한 부족: 봇에게 '초대 코드 만들기(Create Instant Invite)' 권한을 주세요.")

    async def close(self):
        """
        Discord 봇 연결을 종료합니다.
        """
        if self.bot:
            await self.bot.close()

# 싱글턴 패턴
discord_client = Discord()