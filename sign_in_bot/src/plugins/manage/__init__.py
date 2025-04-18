from nonebot import get_plugin_config
from nonebot.internal.params import ArgPlainText, Arg
from nonebot.plugin import PluginMetadata
from datetime import datetime, time, timedelta,date
from sched import scheduler
from typing import List
from apscheduler.triggers.cron import CronTrigger
from nonebot import on_command, require
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent, Bot
from nonebot.internal.adapter import bot
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot_plugin_localstore import plugin_config
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER
from datetime import datetime, timedelta
from typing import List, Optional
import nonebot
from nonebot import get_plugin
from nonebot import get_bot, on_command

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot_plugin_orm import get_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from .models import Detail
from .models_method import DetailManger
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="manage",
    description="管理",
    usage="",
    config=Config,
)

NOTIFY_GROUPS = Config.lanunion_groups
dic = {"serial_number":0,
       "name":"【志愿服务】蓝盟志愿服务活动",
       "precision_name":None,
       "id":None,
       "location":None,
       "level":"校级",
       "charge_man":None,
       "charge_man_unit":"重庆大学蓝盟",
       "phone_number":None,
       "Service_content":"义诊服务"}


async def send_message(message, targets: list[int] = None):
    """
    发送消息到指定目标。

    参数:
        message: 要发送的消息。
        targets: 目标列表，可以是群号或用户 ID。
        group: 要发送的群号,0为通知群，1为调度群，2为老调度群。
    """
    bot = get_bot()
    try:
        target = NOTIFY_GROUPS[0]
        target = int(target)
        if isinstance(target, int):
            await bot.send_group_msg(group_id=target, message=message)
        else:
            logger.error(f"无效的目标类型: {type(target)}")
    except Exception as e:
        logger.error(f"发送消息到目标 {target} 失败: {e}")

lanunion = on_command("管理", priority=9, block=True,permission=GROUP_ADMIN | GROUP_OWNER)

@lanunion.handle()
async def handle_lanunion(bot: Bot, matcher: Matcher, event: MessageEvent, args: Message = CommandArg()):
    """
    主函数，用于处理主动发起的请求
    """

    async with (get_session() as db_session):
        command = args.extract_plain_text().strip()
        if await GROUP_ADMIN(bot, event) or await GROUP_OWNER(bot, event):
            if command.startswith("开始义诊"):
                if args.extract_plain_text():
                    matcher.set_arg("flag", args)
                elif command.startswith("开始活动"):
                    if args.extract_plain_text():
                        matcher.set_arg("flag", args)

@lanunion.got("flag", prompt="是否开始")
@lanunion.got("precision_name", prompt="请输入活动名称")
@lanunion.got("location", prompt="请输入活动地点")
@lanunion.got("charge_man", prompt="请输入负责人")
@lanunion.got("phone_number", prompt="请输入负责人手机")
async def got(location: str = ArgPlainText(),
              charge_man: str = ArgPlainText(),
              precision_name: str = ArgPlainText(),
              phone_number: str = ArgPlainText()):
    current_date = date.today()
    dic["id"] = current_date
    dic["precision_name"] = precision_name
    dic["phone_number"] = phone_number
    dic["charge_man"] = charge_man
    dic["location"] = location
    async with (get_session() as db_session):
        try:
            # 检查数据库中是否已存在该 Student_id 的记录
            existing_lanmsg = await DetailManger.get_Sign_by_student_id(
                db_session, dic["id"])
            if existing_lanmsg:  # 更新记录
                logger.info(f"{dic.get('precision_name')}已存在")
            else:  # 创建新记录
                try:
                    # 写入数据库
                    await DetailManger.create_signmsg(
                        db_session,
                        serial_number=int(dic["serial_number"]) + 1,
                        name=dic["name"],
                        precision_name=dic["precision_name"],
                        id=dic["id"],
                        location=dic["location"],
                        level=dic["level"],
                        charge_man=dic["charge_man"],
                        charge_man_unit=dic["charge_man_unit"],
                        phone_number=dic["phone_number"],
                        Service_content=dic["Service_content"],
                    )
                    logger.info(f"创建活动数据数据: {dic.get('precision_name')}")
                    # 发生成功签到信息
                    await lanunion.send(f"{dic.get('precision_name')} 已开始")
                except Exception as e:
                    logger.error(f"处理 {dic.get('precision_name')} 时发生错误: {e}")
        except SQLAlchemyError as e:
            logger.error(f"数据库操作错误: {e}")
