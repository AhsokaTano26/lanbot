from typing import List

from nonebot import get_driver  # 导入 get_driver 函数，用于获取 NoneBot 驱动器
from pydantic import BaseModel, Extra  # 导入 BaseModel 和 Extra，用于定义配置类


class Config(BaseModel):
    """
    配置类，用于存储从环境变量中读取的蓝联相关配置。
    """
    SQLALCHEMY_DATABASE_URL: str = ""  # 群组列表，定义为字符串列表类型，默认为空列表
    Activity_plugin_enabled: bool = False
# 从 NoneBot 驱动器的配置字典中解析配置对象
Config = Config.parse_obj(get_driver().config.dict())
