from typing import Optional
from src.core.database import SessionLocal
from src.models.system_setting import SystemSetting

# 환경변수 캐시
_env_cache: dict[str, str] = {}


def get_env(key: str, default: Optional[str] = None, use_cache: bool = True) -> Optional[str]:
    """
    환경변수 가져오기
    
    SystemSetting 테이블에서 암호화된 환경변수를 복호화하여 반환합니다.
    캐시를 사용하여 반복적인 DB 접근을 방지합니다.
    
    :param key: 환경변수 키
    :type key: str
    :param default: 값이 없을 경우 반환할 기본값
    :type default: Optional[str]
    :param use_cache: 캐시 사용 여부
    :type use_cache: bool
    :return: 환경변수 값
    :rtype: Optional[str]
    
    Example:
        >>> db_host = get_env("DB_HOST")
        >>> notion_key = get_env("NOTION_API_KEY")
    """
    # 캐시에서 확인
    if use_cache and key in _env_cache:
        return _env_cache[key]
    
    # DB에서 가져오기
    db = SessionLocal()
    try:
        value = SystemSetting.get_config(db, key)
        if value and use_cache:
            _env_cache[key] = value
        return value if value else default
    except Exception as e:
        print(f"Error getting env variable {key}: {e}")
        return default
    finally:
        db.close()


def set_env(key: str, value: str, update_cache: bool = True) -> None:
    """
    환경변수 설정
    
    SystemSetting 테이블에 환경변수를 암호화하여 저장합니다.
    
    :param key: 환경변수 키
    :type key: str
    :param value: 환경변수 값
    :type value: str
    :param update_cache: 캐시 업데이트 여부
    :type update_cache: bool
    
    Example:
        >>> set_env("NOTION_API_KEY", "new_api_key")
    """
    db = SessionLocal()
    try:
        SystemSetting.update_config(db, key, value)
        if update_cache:
            _env_cache[key] = value
    finally:
        db.close()


def clear_env_cache():
    """
    환경변수 캐시 초기화
    
    Example:
        >>> clear_env_cache()  # 모든 캐시 삭제
    """
    _env_cache.clear()


def reload_env(key: Optional[str] = None):
    """
    환경변수 재로드
    
    특정 키만 재로드하거나, 모든 캐시를 초기화합니다.
    
    :param key: 재로드할 환경변수 키 (None이면 전체 캐시 초기화)
    :type key: Optional[str]
    
    Example:
        >>> reload_env("DB_HOST")  # DB_HOST만 재로드
        >>> reload_env()  # 전체 캐시 초기화
    """
    if key:
        if key in _env_cache:
            del _env_cache[key]
        get_env(key, use_cache=True)  # 다시 로드하여 캐시에 저장
    else:
        clear_env_cache()
