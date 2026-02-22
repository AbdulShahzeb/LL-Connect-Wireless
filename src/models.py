
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    last_notified: float | None

class VersionStatus(BaseModel):
    data: VersionInfo
    notified: bool
    outdated: bool

class LinearMode(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    min_temp: int = Field(default=35, ge=20, le=100)
    max_temp: int = Field(default=80, ge=20, le=100)

    min_pwm: int = Field(default=10, ge=0, le=100)
    max_pwm: int = Field(default=70, ge=0, le=100)

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.min_temp >= self.max_temp:
            raise ValueError("min_temp must be less than max_temp")
        if self.min_pwm > self.max_pwm:
            raise ValueError("min_pwm must be less than or equal to max_pwm")
        return self

class FanMode(str, Enum):
    linear = "linear"

class Settings(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    mode: FanMode = FanMode.linear
    linear: LinearMode = LinearMode()