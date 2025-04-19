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
from nonebot_plugin_orm import get_session
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER
from .models import Sign
from . import timedeal
from .models_method import SignManger
from typing import List, Optional
import nonebot
from nonebot.plugin import Plugin, PluginMetadata
from nonebot import get_bot, on_command

from nonebot.log import logger
from nonebot import get_plugin_config
from nonebot_plugin_orm import get_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from .models import Sign, Trans, Final
from .models_method import SignManger, TansManger, FinalManger
from .time_trans import time_trans
from .Lanunion_config import Config
from ..manage import function

from typing import Tuple
from nonebot.params import Command


__plugin_meta__ = PluginMetadata(
    name="lanunion",
    description="义诊插件",
    usage="",
    config=Config,
)

TimeDealSelector = timedeal.TimeDealSelector
plugin_config = get_plugin_config(Config)
f = function.get_output_name()

async def is_enable() -> bool:
    return plugin_config.lanunion_plugin_enabled


# 定时任务，每隔一段时间检查一次新报修单
scheduler = require("nonebot_plugin_apscheduler").scheduler

TimeDealSelector = timedeal.TimeDealSelector
dealtime = TimeDealSelector()


manage = on_command(
    ("义诊", "开始"),
    aliases={("义诊", "结束")},
    permission=GROUP_ADMIN | GROUP_OWNER,
)

@manage.handle()
async def control(cmd: Tuple[str, str] = Command()):
    _, action = cmd
    if action == "开始":
        plugin_config.lanunion_plugin_enabled = True
        await manage.finish("义诊已开启")
    elif action == "结束":
        plugin_config.lanunion_plugin_enabled = False
        await manage.finish("义诊已结束")

lanunion = on_command("sign",rule=is_enable, priority=10, block=True)

@lanunion.handle()
async def handle_lanunion(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """
    主函数，用于处理主动发起的请求
    """

    async with (get_session() as db_session):
        command = args.extract_plain_text().strip()
        from datetime import datetime, time, timedelta
        if command.startswith("签到"):
            dic = {"name": None}
            dic = dict(dic)
            name = str(command.split(" ")[1])
            student_id = str(command.split(" ")[2])
            now = datetime.now()
            lenth = len(student_id)
            if now.time() < time(9, 0): #判断是否是早上9点之前签到
                await lanunion.send("最早签到时间为 09:00，请稍后再试~")
                return
            sign_in_time = dealtime.adjust_sign_in_time(now)    # 调整签到时间
            if name is not None and student_id is not None: #判断输入是否正确
                if lenth in [8,12,13]:   #判断学号是否正确
                    dic["name"] = name
                    dic["student_id"] = student_id
                    dic["sign_in_time"] = sign_in_time

                    async with get_session() as db_session: #处理数据库
                        message = dic
                        try:
                            # 检查数据库中是否已存在该 Student_id 的记录
                            existing_lanmsg = await SignManger.get_Sign_by_student_id(
                                db_session, message["student_id"])
                            if existing_lanmsg:  # 更新记录
                                logger.info(f"{message.get('student_id')}已签到")
                                await lanunion.send(f"{message.get('name')} 你已经签到了，不需要再签到哟~")
                            else:
                                try:
                                    # 写入数据库
                                    await SignManger.create_signmsg(
                                        db_session,
                                        name=message["name"],
                                        student_id=message['student_id'],
                                        sign_in_time=message['sign_in_time'],
                                        sign_out_time=1,
                                        full_time=100,
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



        elif command.startswith("签退"):
            dic = {"name": None}
            dic = dict(dic)
            name = str(command.split(" ")[1])
            student_id = str(command.split(" ")[2])
            now = datetime.now()
            lenth = len(student_id)
            if now.time() > time(16, 30):   # 判断是否是下午4点之后签退
                now = datetime.combine(now.date(), time(16, 30))  # 强制设为最晚时间
            sign_out_time = dealtime.adjust_sign_out_time(now)
            if name is not None and student_id is not None: #判断输入是否正确
                if lenth in [8, 12, 13]:    #判断学号是否正确
                    dic["name"] = name
                    dic["student_id"] = student_id
                    dic["sign_out_time"] = sign_out_time
                    async with get_session() as db_session: #处理数据库
                        message = dic
                        try:
                            # 检查数据库中是否已存在该 student_id 的记录
                            existing_lanmsg = await SignManger.get_Sign_by_student_id(
                                db_session, message["student_id"])

                            if not existing_lanmsg:  # 更新记录
                                logger.info(f"{message.get('student_id')}未签到")
                                await lanunion.send(f"{message.get('name')} 你还没有签到哦，无法签退~")
                            else:
                                flag = existing_lanmsg.full_time
                                if flag == "100":
                                    try:
                                        sign_in_time = existing_lanmsg.sign_in_time  # 获取签到时间
                                        dic["sign_in_time"] = sign_in_time
                                        t = time_trans()    # 实例化
                                        outtimestamp = t.time_tran1(sign_out_time)  # 转换为时间戳
                                        intimestamp = t.time_tran2(sign_in_time)    # 转换为时间戳
                                        full_time = outtimestamp - intimestamp  # 计算时间
                                        full_time = full_time / 3600    # 计算时间
                                        dic["full_time"] = full_time

                                        # 先删除数据，再写入数据库
                                        await SignManger.delete_student_id(
                                            db_session, message["student_id"]
                                        )

                                        await SignManger.create_signmsg(
                                            db_session,
                                            name=message["name"],
                                            student_id=message['student_id'],
                                            sign_in_time=message['sign_in_time'],
                                            sign_out_time=message['sign_out_time'],
                                            full_time=message['full_time'],
                                        )
                                        logger.info(f"创建签到数据: {message.get('student_id')}")
                                        # 发送成功签退信息
                                        await lanunion.send(f"{message.get('name')} 签退成功")
                                    except Exception as e:
                                        logger.error(f"处理签到 {message.get('student_id')} 时发生错误: {e}")
                                else:
                                    print(existing_lanmsg.full_time)
                                    print(type(existing_lanmsg.full_time))
                                    await lanunion.send(f"{message.get('name')} 你已经签退了，请勿重复签退~")

                        except SQLAlchemyError as e:
                            logger.error(f"数据库操作错误: {e}")
                            # 这里可以考虑回滚数据库操作: db_session.rollback()
                else:
                    await lanunion.finish(f"学号输入错误")
            else:
                await lanunion.finish(f"输入错误")





        elif command.startswith("上午"):
            dic = {"name": None}
            dic = dict(dic)
            name = str(command.split(" ")[1])
            student_id = str(command.split(" ")[2])
            lenth = len(student_id)
            if name is not None and student_id is not None: #判断输入是否正确
                if lenth in [8, 12, 13]:    #判断学号是否正确
                    dic["name"] = name
                    dic["student_id"] = student_id
                    dic["morning"] = 1
                    dic["afternoon"] = 0
                    async with get_session() as db_session: #处理数据库
                        message = dic
                        try:
                            # 检查数据库中是否已存在该 student_id 的记录
                            existing_lanmsg = await TansManger.get_trans_by_id(
                                db_session, message["student_id"])

                            if existing_lanmsg:  # 更新记录
                                if existing_lanmsg.morning == "1":
                                    logger.info(f"{message.get('student_id')}已签到")
                                    await lanunion.send(f"{message.get('name')} 你已经签到了，切勿重复签到哟~")
                                else:
                                    try:
                                        flag = existing_lanmsg.afternoon
                                        dic["afternoon"] = flag
                                        # 先删除数据，再写入数据库
                                        await TansManger.delete_id(
                                            db_session, message["student_id"]
                                        )

                                        await TansManger.create_Transmsg(
                                            db_session,
                                            name=message["name"],
                                            student_id=message['student_id'],
                                            morning=message['morning'],
                                            afternoon=message['afternoon'],
                                        )
                                        logger.info(f"创建签到数据: {message.get('student_id')}")
                                        # 发送成功签退信息
                                        await lanunion.send(f"{message.get('name')} 早上搬东西签到成功")
                                    except Exception as e:
                                        logger.error(f"处理上午签到 {message.get('student_id')} 时发生错误: {e}")
                            else:
                                try:
                                    await TansManger.create_Transmsg(
                                        db_session,
                                        name=message["name"],
                                        student_id=message['student_id'],
                                        morning=message['morning'],
                                        afternoon=message['afternoon'],
                                    )
                                    logger.info(f"创建签到数据: {message.get('student_id')}")
                                    # 发送成功签退信息
                                    await lanunion.send(f"{message.get('name')} 早上搬东西签到成功")
                                except Exception as e:
                                    logger.error(f"处理上午签到 {message.get('student_id')} 时发生错误: {e}")

                        except SQLAlchemyError as e:
                            logger.error(f"数据库操作错误: {e}")
                            # 这里可以考虑回滚数据库操作: db_session.rollback()
                else:
                    await lanunion.finish(f"学号输入错误")
            else:
                await lanunion.finish(f"输入错误")



        elif command.startswith("下午"):
            dic = {"name": None}
            dic = dict(dic)
            name = str(command.split(" ")[1])
            student_id = str(command.split(" ")[2])
            lenth = len(student_id)
            if name is not None and student_id is not None:  # 判断输入是否正确
                if lenth in [8, 12, 13]:  # 判断学号是否正确
                    dic["name"] = name
                    dic["student_id"] = student_id
                    dic["morning"] = 0
                    dic["afternoon"] = 1
                    async with get_session() as db_session:  # 处理数据库
                        message = dic
                        try:
                            # 检查数据库中是否已存在该 student_id 的记录
                            existing_lanmsg = await TansManger.get_trans_by_id(
                                db_session, message["student_id"])

                            if existing_lanmsg:  # 更新记录
                                if existing_lanmsg.afternoon == "1":
                                    logger.info(f"{message.get('student_id')}已签到")
                                    await lanunion.send(f"{message.get('name')} 你已经签到了，切勿重复签到哟~")
                                else:
                                    try:
                                        flag = existing_lanmsg.morning
                                        dic["morning"] = flag
                                        # 先删除数据，再写入数据库
                                        await TansManger.delete_id(
                                            db_session, message["student_id"]
                                        )

                                        await TansManger.create_Transmsg(
                                            db_session,
                                            name=message["name"],
                                            student_id=message['student_id'],
                                            morning=message['morning'],
                                            afternoon=message['afternoon'],
                                        )
                                        logger.info(f"创建签到数据: {message.get('student_id')}")
                                        # 发送成功签退信息
                                        await lanunion.send(f"{message.get('name')} 下午搬东西签到成功")
                                    except Exception as e:
                                        logger.error(f"处理下午签到 {message.get('student_id')} 时发生错误: {e}")
                            else:
                                try:
                                    await TansManger.create_Transmsg(
                                        db_session,
                                        name=message["name"],
                                        student_id=message['student_id'],
                                        morning=message['morning'],
                                        afternoon=message['afternoon'],
                                    )
                                    logger.info(f"创建签到数据: {message.get('student_id')}")
                                    # 发送成功签退信息
                                    await lanunion.send(f"{message.get('name')} 下午搬东西签到成功")
                                except Exception as e:
                                    logger.error(f"处理下午签到 {message.get('student_id')} 时发生错误: {e}")

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
                    await SignManger.delete_all_student_id(db_session)
                    await TansManger.delete_all_id(db_session)
                    await FinalManger.delete_all_student_id(db_session)
                    await lanunion.send(f"所有数据已删除")
                elif flag == "查询":      #查询指定学号数据
                    """
                    参考指令：/sign 管理 查询 学号
                    """
                    student_id = str(command.split(" ")[2])
                    existing_lanmsg1 = await TansManger.get_trans_by_id(db_session, student_id)
                    existing_lanmsg2 = await SignManger.get_Sign_by_student_id(db_session, student_id)
                    if existing_lanmsg1 and existing_lanmsg2:
                        name = existing_lanmsg2.name
                        student_id = existing_lanmsg2.student_id
                        sign_in_time = existing_lanmsg2.sign_in_time
                        sign_out_time = existing_lanmsg2.sign_out_time
                        full_time = existing_lanmsg2.full_time
                        morning = existing_lanmsg1.morning
                        afternoon = existing_lanmsg1.afternoon
                        await lanunion.send(
                            f"姓名: {name}\n学号: {student_id}\n签到时间: {sign_in_time}\n签退时间: {sign_out_time}"
                            f"\n总在线时间: {full_time}\n上午签到: {morning}\n下午签到: {afternoon}")
                    elif existing_lanmsg1:
                        name = existing_lanmsg1.name
                        student_id = existing_lanmsg1.student_id
                        morning = existing_lanmsg1.morning
                        afternoon = existing_lanmsg1.afternoon
                        await lanunion.send(
                            f"姓名: {name}\n学号: {student_id}\n上午签到: {morning}\n下午签到: {afternoon}")
                    elif existing_lanmsg2:
                        name = existing_lanmsg2.name
                        student_id = existing_lanmsg2.student_id
                        sign_in_time = existing_lanmsg2.sign_in_time
                        sign_out_time = existing_lanmsg2.sign_out_time
                        full_time = existing_lanmsg2.full_time
                        await lanunion.send(
                            f"姓名: {name}\n学号: {student_id}\n签到时间: {sign_in_time}"
                            f"\n签退时间: {sign_out_time}\n总在线时间: {full_time}")
                    else:
                        await lanunion.send(f"未找到该用户")
                        return

                elif flag == "结算":      #将签到时间与搬东西时间进行计算
                    """
                    参考指令：/sign 管理 结算
                    """
                    dic1 = {"name": None}
                    dic2 = {"name": None}
                    sheet1 = await TansManger.get_all_id(db_session)
                    sheet2 = await SignManger.get_all_student_id(db_session)
                    for student_id in sheet1:
                        message = await TansManger.get_trans_by_id(db_session, student_id)
                        flag = message.flag
                        if flag == "0":
                            logger.info(f"{student_id} 已经结算")
                        else:
                            if student_id in sheet2:
                                existing_lanmsg1 = await TansManger.get_trans_by_id(db_session, student_id)
                                existing_lanmsg2 = await SignManger.get_Sign_by_student_id(db_session, student_id)
                                dic2["name"] = existing_lanmsg2.name
                                dic2["student_id"] = student_id
                                dic2["sign_in_time"] = existing_lanmsg2.sign_in_time
                                dic2["sign_out_time"] = existing_lanmsg2.sign_out_time
                                morning = float(existing_lanmsg1.morning)
                                afternoon = float(existing_lanmsg1.afternoon)
                                full_time = morning + afternoon + float(existing_lanmsg2.full_time)
                                dic2["full_time"] = full_time

                                dic1["name"] = dic2["name"]
                                dic1["student_id"] = dic2["student_id"]
                                dic1["morning"] = existing_lanmsg1.morning
                                dic1['afternoon'] = existing_lanmsg1.afternoon
                                dic1["flag"] = "0"
                                try:
                                    # 先删除数据，再写入数据库
                                    await TansManger.delete_id(
                                        db_session, dic1["student_id"]
                                    )

                                    await TansManger.create_Transmsg(
                                        db_session,
                                        name=dic1["name"],
                                        student_id=dic1['student_id'],
                                        morning=dic1['morning'],
                                        afternoon=dic1['afternoon'],
                                        flag = dic1["flag"],
                                    )
                                    logger.info(f"创建签到数据: {dic1.get('student_id')}")


                                    await SignManger.delete_student_id(
                                        db_session, dic2["student_id"]
                                    )

                                    await SignManger.create_signmsg(
                                        db_session,
                                        name=dic2["name"],
                                        student_id=dic2['student_id'],
                                        sign_in_time=dic2['sign_in_time'],
                                        sign_out_time=dic2['sign_out_time'],
                                        morning = dic1['morning'],
                                        afternoon=dic1['afternoon'],
                                        full_time=dic2['full_time'],
                                    )
                                    logger.info(f"创建签到数据: {dic2.get('student_id')}")
                                    # 发送成功签退信息
                                    logger.info(f"{dic2.get('name')} 签退成功")
                                    #await lanunion.send(f"{dic2.get('student_id')} 结算成功")
                                except Exception as e:
                                    logger.error(f"发送消息失败: {e}")
                            else:
                                existing_lanmsg = await TansManger.get_trans_by_id(db_session, student_id)
                                dic2["name"] = existing_lanmsg.name
                                dic2["student_id"] = student_id
                                dic2["sign_in_time"] =  0
                                dic2["sign_out_time"] = 0
                                morning = int(existing_lanmsg.morning)
                                afternoon = int(existing_lanmsg.afternoon)
                                full_time = morning + afternoon
                                dic2["full_time"] = full_time

                                dic1["name"] = dic2["name"]
                                dic1["student_id"] = dic2["student_id"]
                                dic1["morning"] = existing_lanmsg.morning
                                dic1['afternoon'] = existing_lanmsg.afternoon
                                dic1["flag"] = "0"
                                try:
                                    await TansManger.delete_id(
                                        db_session, dic1["student_id"]
                                    )

                                    await TansManger.create_Transmsg(
                                        db_session,
                                        name=dic1["name"],
                                        student_id=dic1['student_id'],
                                        morning=dic1['morning'],
                                        afternoon=dic1['afternoon'],
                                        flag=dic1["flag"],
                                    )
                                    logger.info(f"创建签到数据: {dic1.get('student_id')}")

                                    #写入数据库
                                    await SignManger.create_signmsg(
                                        db_session,
                                        name=dic2["name"],
                                        student_id=dic2['student_id'],
                                        sign_in_time=dic2['sign_in_time'],
                                        sign_out_time=dic2['sign_out_time'],
                                        full_time=dic2['full_time'],
                                    )
                                    logger.info(f"创建签到数据: {dic2.get('student_id')}")
                                    # 发送成功签退信息
                                    logger.info(f"{dic2.get('name')} 签退成功")
                                    #await lanunion.send(f"{dic2.get('student_id')} 结算成功")
                                except Exception as e:
                                    logger.error(f"发送消息失败: {e}")
                    await lanunion.send(f"全部结算成功")


                elif flag == "加班":      #加班增加时长
                    """
                    参考指令：/sign 管理 加班 学号 时长
                    """
                    student_id = str(command.split(" ")[2])
                    time = str(command.split(" ")[3])
                    dic = {"name": None}
                    sheet = await TansManger.get_all_id(db_session)
                    if student_id not in sheet:
                        await lanunion.finish(f"未找到该用户")
                    else:
                        existing_lanmsg = await SignManger.get_Sign_by_student_id(db_session, student_id)
                        dic["name"] = existing_lanmsg.name
                        dic["student_id"] = existing_lanmsg.student_id
                        dic["sign_in_time"] = existing_lanmsg.sign_in_time
                        dic["sign_out_time"] = existing_lanmsg.sign_out_time
                        old_full_time = existing_lanmsg.full_time
                        new_full_time = float(old_full_time) + float(time)
                        dic["full_time"] = new_full_time
                        try:
                            await SignManger.delete_student_id(
                                db_session, dic["student_id"]
                            )
                            await SignManger.create_signmsg(
                                db_session,
                                name=dic["name"],
                                student_id=dic['student_id'],
                                sign_in_time=dic['sign_in_time'],
                                sign_out_time=dic['sign_out_time'],
                                full_time=dic['full_time'],
                            )
                            logger.info(f"创建签到数据: {dic.get('student_id')}")
                            await lanunion.finish(f"给{dic.get('name')} 加班{time}小时成功")
                        except Exception as e:
                            logger.error(f"发送消息失败: {e}")


                elif flag == "导出":
                    current_date = date.today()
                    flag = str(current_date)
                    dic = await f.get_output_name(flag)
                    all = await SignManger.get_all_student_id(db_session)
                    serial_number = 0
                    print(all)
                    for student_id in all:
                        print(student_id)
                        serial_number += 1
                        message = await SignManger.get_Sign_by_student_id(db_session, student_id)
                        student_name = message.name
                        student_id = message.student_id
                        sign_in_time = message.sign_in_time
                        sign_out_time = message.sign_out_time
                        full_time = message.full_time
                        sign_time = dealtime.adjust_full_time(sign_in_time, sign_out_time, full_time)

                        dic["serial_number"] = serial_number
                        dic["student_name"] = student_name
                        dic["student_id"] = student_id
                        dic["sign_time"] = sign_time
                        dic["full_time"] = full_time
                        try:
                            await FinalManger.create_signmsg(
                                db_session,
                                serial_number=dic["serial_number"],
                                id=dic['id'],
                                name=dic['name'],
                                location=dic['location'],
                                level=dic['level'],
                                charge_man=dic['charge_man'],
                                charge_man_unit=dic['charge_man_unit'],
                                phone_number=dic['phone_number'],
                                Service_content=dic['Service_content'],
                                student_name=dic["student_name"],
                                student_id=dic['student_id'],
                                sign_time=dic['sign_time'],
                                full_time=dic['full_time'],
                            )
                            logger.info(f"创建签到数据: {dic.get('student_id')}")
                        except Exception as e:
                            logger.error(f"发送消息失败: {e}")
                    output_name1 = dic["output_name"] + "原始数据"
                    a = await SignManger.Export(db_session, output_name1)
                    await lanunion.send(f"{a}")
                    output_name2 = dic["output_name"]
                    b = await FinalManger.Export(db_session, output_name2)
                    await lanunion.send(f"{b}")


                else:
                    await lanunion.finish("无效的flag，管理指令：\n /sign 签到 管理 结算 \n /sign 签到 管理 加班 学号 时长 \n /sign 签到 管理 查询 学号 \n /sign签到 管理 删除 \n /sign 删除 学号")
            else:
                await lanunion.finish("您没有权限使用此指令")

        elif command.startswith("删除"):       #删除指定学号数据
            """
            参考指令：/sign 删除 学号
            """
            flag = str(command.split(" ")[1])
            lenth = len(flag)
            if await GROUP_ADMIN(bot, event) or await GROUP_OWNER(bot, event):
                if lenth in [8, 12, 13]:
                    await SignManger.delete_student_id(db_session, flag)
                    await lanunion.send(f"已删除{flag}的签到数据")
                else:
                    await lanunion.finish("无效的flag")
            else:
                await lanunion.finish("无效的flag，管理指令：\n /sign 签到 管理 结算 \n /sign 签到 管理 加班 学号 时长 \n /sign 签到 管理 查询 学号 \n /sign 签到 管理 删除 \n /sign 删除 学号")


        else:
            await lanunion.finish(
                "无效的指令，请输入 \n /sign 签到 姓名 学号 \n /sign 签退 姓名 学号 \n /sign 上午 姓名 学号 \n /sign 下午 姓名 学号"
            )




@scheduler.scheduled_job(CronTrigger(hour=16, minute=30),rule=is_enable)
async def auto_send_charge_func():
    """
    定时任务函数，用于义诊下午16:00进行签到。
    """
    async with get_session() as db_session:
        sheet = await SignManger.get_all_student_id(db_session)
        now = datetime.now()
        bot = nonebot.get_bot()
        if sheet is None:
            return
        else:
            for id_s in sheet:
                existing_lanmsg = await SignManger.get_Sign_by_student_id(db_session, id_s)
                lanmsg_fulltime = existing_lanmsg.full_time

                dic = {"name": None}
                name = existing_lanmsg.name
                student_id = existing_lanmsg.student_id
                sign_in_time = existing_lanmsg.sign_in_time
                sign_out_time = dealtime.adjust_sign_in_time(now)
                full_time = existing_lanmsg.full_time
                dic["name"] = name
                dic["student_id"] = student_id
                dic["sign_in_time"] = sign_in_time
                dic["sign_out_time"] = sign_out_time

                if lanmsg_fulltime == "100":        # 100 表示未签退
                    t = time_trans()  # 实例化
                    outtimestamp = t.time_tran1(sign_out_time)  # 转换为时间戳
                    intimestamp = t.time_tran2(sign_in_time)  # 转换为时间戳
                    full_time = outtimestamp - intimestamp  # 计算时间
                    full_time = full_time / 3600  # 计算时间
                    dic["full_time"] = full_time
                    try:
                        await SignManger.delete_student_id(
                            db_session, dic["student_id"]
                        )

                        await SignManger.create_signmsg(
                            db_session,
                            name=dic["name"],
                            student_id=dic['student_id'],
                            sign_in_time=dic['sign_in_time'],
                            sign_out_time=dic['sign_out_time'],
                            full_time=dic['full_time'],
                        )
                        logger.info(f"创建签到数据: {dic.get('student_id')}")
                        # 发送成功签退信息
                        logger.info(f"{dic.get('name')} 签退成功")
                    except Exception as e:
                        logger.error(f"发送消息失败: {e}")
            await bot.send_group_msg(group_id=925265706, message="已全部自动签退")