from nonebot_plugin_orm import Model
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Sign(Model):
    __tablename__ = "Sign"
    name = Column(String(255), nullable=True)  # 姓名
    student_id = Column(String(255), primary_key=True, nullable=True)  # 用户学号
    sign_in_time = Column(String(255), nullable=False)  # 签到时间
    sign_out_time = Column(String(255), nullable=False)  # 签退时间
    full_time = Column(String(255) ,nullable=False)  # 总在线时间

class Trans(Model):
    __tablename__ = "Trans"
    name = Column(String(255), nullable=True)  # 姓名
    student_id = Column(String(255), primary_key=True, nullable=True)  # 用户学号
    morning = Column(String(255), nullable=False)  # 签到时间
    afternoon = Column(String(255), nullable=False)  # 签退时间
    flag = Column(String(255), nullable=True)