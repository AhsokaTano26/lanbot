from nonebot_plugin_orm import Model
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Sign(Model):
    __tablename__ = "Sign"
    name = Column(String(255), nullable=True)  # 姓名
    student_id = Column(String(255), primary_key=True, nullable=True)  # 用户学号
    sign_in_time = Column(String(255), nullable=False)  # 签到时间
    sign_out_time = Column(String(255), nullable=False)  # 签退时间
    morning = Column(String(255), nullable=True)  # 上午搬东西
    afternoon = Column(String(255), nullable=True)  # 下午搬东西
    full_time = Column(String(255) ,nullable=False)  # 总在线时间

class Trans(Model):
    __tablename__ = "Trans"
    name = Column(String(255), nullable=True)  # 姓名
    student_id = Column(String(255), primary_key=True, nullable=True)  # 用户学号
    morning = Column(String(255), nullable=False)  # 上午搬东西
    afternoon = Column(String(255), nullable=False)  # 下午搬东西
    flag = Column(String(255), nullable=True)

class Final(Model):
    __tablename__ = "Final"
    serial_number = Column(String(255), nullable=True) #序号
    name = Column(String(255), nullable=True)  # 活动名称
    id = Column(String(255), nullable=True)  #活动时间
    location = Column(String(255), nullable=True)  # 活动地点
    level = Column(String(255), nullable=True)  # 活动等级
    charge_man = Column(String(255), nullable=True)  # 活动负责人
    charge_man_unit = Column(String(255), nullable=True)  # 活动负责人单位
    phone_number = Column(String(255), nullable=True)  # 活动负责人电话
    student_name = Column(String(255), nullable=True)  # 志愿者姓名
    student_academy = Column(String(255), nullable=True)  # 志愿者学院
    student_id = Column(String(255), primary_key=True,nullable=True)  # 参与人学号
    sign_time = Column(String(255), nullable=True)  # 志愿服务时间段
    full_time = Column(String(255), nullable=True)  # 志愿服务时长
    Service_content = Column(String(255) ,nullable=True)  # 服务内容