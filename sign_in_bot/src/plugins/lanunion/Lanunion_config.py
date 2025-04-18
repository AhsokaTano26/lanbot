from typing import List

from nonebot import get_driver  # 导入 get_driver 函数，用于获取 NoneBot 驱动器
from pydantic import BaseModel, Extra  # 导入 BaseModel 和 Extra，用于定义配置类


class Config(BaseModel):
    """
    配置类，用于存储从环境变量中读取的蓝联相关配置。
    """
    lanunion_plugin_enabled: bool = False

