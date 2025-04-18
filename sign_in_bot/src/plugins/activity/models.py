from nonebot_plugin_orm import Model
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Activity(Model):
    __tablename__ = "Activity"
    name = Column(String(255), nullable=True)  # 姓名
    student_id = Column(String(255), primary_key=True, nullable=True)  # 用户学号
    sign_in_time = Column(String(255), nullable=False)  # 签到时间
