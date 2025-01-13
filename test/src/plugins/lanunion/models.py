from nonebot_plugin_orm import Model
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Lanmsg(Model):
    __tablename__ = "lanmsgs"
    sheet_no = Column(String(255), primary_key=True, nullable=False)  # 报修单流水号
    sheet_id = Column(String(255), unique=True, nullable=False)  # 报修单号
    create_time = Column(DateTime, nullable=False)  # 创建时间
    name = Column(String(255), nullable=True)  # 姓名
    student_id = Column(String(255), nullable=True)  # 用户学号
    location = Column(String(255), nullable=True)  # 维修地点
    qq = Column(String(255), nullable=True)  # QQ 号码
    phone = Column(String(255), nullable=True)  # 手机号码
    hardware = Column(String(255), nullable=True)  # 笔记本
    description = Column(Text, nullable=False)  # 故障描述
    status = Column(String(255), nullable=True, default="未派单")  # 处理状态
    update_time = Column(DateTime, nullable=False)  # 更新时间
    sent = Column(Boolean, default=False)  # 是否已发送通知
    is_assigned = Column(Boolean, default=False)
    assigned_to = Column(String(255), nullable=True)



