import os
import sqlite3

import pandas as pd
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from datetime import datetime, time, timedelta, date
from sched import scheduler
from typing import List
from apscheduler.triggers.cron import CronTrigger
from nonebot import on_command, require
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent, Bot
from nonebot.internal.adapter import bot
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER
from datetime import datetime, timedelta
from typing import List, Optional
import nonebot
from xlsxwriter.workbook import Workbook
from nonebot import get_bot, on_command
from nonebot.log import logger
from nonebot_plugin_orm import get_session
from sqlalchemy import select, create_engine
from sqlalchemy.exc import SQLAlchemyError
from .models import Activity
from .models_method import ActivityManger
from .Activity_config import Config
from ..manage import function

from typing import Tuple
from nonebot.params import Command


__plugin_meta__ = PluginMetadata(
    name="activity",
    description="日常活动插件",
    usage="",
    config=Config,
)

SQLALCHEMY_DATABASE_URL = Config.SQLALCHEMY_DATABASE_URL
plugin_config = get_plugin_config(Config)
f = function.get_output_name()

async def is_enable() -> bool:
    return plugin_config.Activity_plugin_enabled

manage = on_command(
    ("活动", "开始"),
    aliases={("活动", "结束")},
    permission=GROUP_ADMIN | GROUP_OWNER,
)

@manage.handle()
async def control(cmd: Tuple[str, str] = Command()):
    _, action = cmd
    if action == "开始":
        plugin_config.Activity_plugin_enabled = True
        await manage.finish("活动已开启")
    elif action == "结束":
        plugin_config.Activity_plugin_enabled = False
        await manage.finish("活动已结束")



lanunion = on_command("sign",rule=is_enable, priority=10, block=True)


@lanunion.handle()
async def handle_lanunion(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """
    主函数，用于处理主动发起的请求
    """

    async with (get_session() as db_session):
        command = args.extract_plain_text().strip()
        if command.startswith("签到"):
            dic = {"name": None}
            dic = dict(dic)
            name = str(command.split(" ")[1])
            student_id = str(command.split(" ")[2])
            now = datetime.now()
            lenth = len(student_id)
            if name is not None and student_id is not None: #判断输入是否正确
                if lenth in [8,12,13]:   #判断学号是否正确
                    dic["name"] = name
                    dic["student_id"] = student_id
                    dic["sign_in_time"] = now

                    async with get_session() as db_session: #处理数据库
                        message = dic
                        try:
                            # 检查数据库中是否已存在该 Student_id 的记录
                            existing_lanmsg = await ActivityManger.get_Sign_by_student_id(
                                db_session, message["student_id"])
                            if existing_lanmsg:  # 更新记录
                                logger.info(f"{message.get('student_id')}已签到")
                                await lanunion.send(f"{message.get('name')} 你已经签到了，不需要再签到哟~")
                            else:
                                try:
                                    # 写入数据库
                                    await ActivityManger.create_signmsg(
                                        db_session,
                                        name=message["name"],
                                        student_id=message['student_id'],
                                        sign_in_time=message['sign_in_time'],
                                    )
                                    logger.info(f"创建签到数据: {message.get('student_id')}")
                                    #发生成功签到信息
                                    await lanunion.send(f"{message.get('name')} 签到成功")
                                except Exception as e:
                                    logger.error(f"处理签到 {message.get('student_id')} 时发生错误: {e}")
                        except SQLAlchemyError as e:
                            logger.error(f"数据库操作错误: {e}")
                            # 这里可以考虑回滚数据库操作: db_session.rollback()
                else:
                    await lanunion.finish(f"学号输入错误")
            else:
                await lanunion.finish(f"输入错误")

        elif command.startswith("管理"):
            flag = str(command.split(" ")[1])
            if await GROUP_ADMIN(bot, event) or await GROUP_OWNER(bot, event):
                if flag == "删除":    #删除所有数据
                    """
                    参考指令：/sign 管理 删除
                    """
                    await ActivityManger.delete_all_student_id(db_session)
                    await lanunion.send(f"所有数据已删除")
                elif flag == "导出":
                    current_date = date.today()
                    flag = str(current_date)
                    sheet = await f.get_output_name(flag)
                    output_name = sheet["output_name"]
                    a = await ActivityManger.Export(db_session,output_name)
                    group_id = 925265706  # 发送到小团体
                    file_path = f"file/{output_name}.xlsx"  # 替换为实际文件绝对路径
                    upload_filename = f"{output_name}.xlsx"  # 替换为上传时的文件名
                    try:
                        # 使用绝对路径上传
                        abs_path = f"file://{os.path.abspath(file_path)}"
                        await bot.call_api("upload_group_file", group_id=group_id, file=abs_path, name=upload_filename)
                        await lanunion.send("文件发送成功！")
                    except Exception as e:
                        await lanunion.send(f"文件发送失败：{str(e)}")
                    await lanunion.send(f"{a}")
                else:
                    await lanunion.finish(f"无效的指令")
            else:
                await lanunion.finish("您没有权限使用此指令")


        else:
            await lanunion.finish(
                "无效的指令，请输入 \n /sign 签到 姓名 学号"
            )