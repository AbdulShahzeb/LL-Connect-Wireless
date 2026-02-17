
from typing import List, Optional
from pydantic import BaseModel


class Fan(BaseModel):
    mac: str
    master_mac: str
    channel: int
    rx_type: int
    fan_count: int
    pwm: int
    rpm: List[int]
    target_pwm: int
    is_bound: bool

class SystemStatus(BaseModel):
    timestamp: float
    cpu_temp: Optional[float] = None
    fans: List[Fan]

class VersionInfo(BaseModel):
    semver: str
    rc: int
    release: int
    compile_ver: str
    raw_tag: str
    release_note: str | None
    installer_url: str | None

class VersionStatus(BaseModel):
    data: VersionInfo
    notified: bool
    outdated: bool