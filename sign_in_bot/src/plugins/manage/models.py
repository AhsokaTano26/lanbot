from nonebot_plugin_orm import Model
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Detail(Model):
    __tablename__ = "Detail"
    serial_number = Column(String(255), nullable=True) #序号
    name = Column(String(255), nullable=True)  # 活动名称
    precision_name = Column(String(255), nullable=True)  # 精确活动名称
    id = Column(String(255), primary_key=True, nullable=True)  #活动时间
    location = Column(String(255), nullable=True)  # 活动地点
    level = Column(String(255), nullable=True)  # 活动等级
    charge_man = Column(String(255), nullable=True)  # 活动负责人
    charge_man_unit = Column(String(255), nullable=True)  # 活动负责人单位
    phone_number = Column(String(255), nullable=True)  # 活动负责人电话
    Service_content = Column(String(255) ,nullable=True)  # 服务内容
