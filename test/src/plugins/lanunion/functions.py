from datetime import datetime, timedelta
from typing import List, Optional

from nonebot import get_bot

from nonebot.log import logger

from nonebot_plugin_orm import get_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .config import lanunion_config
from .lanunion import LanMsgs_getter, LanMsg
from .models import Lanmsg
from .models_method import LanmsgManager, rssmsgManager
from .rss_get import rss_get

# --- 配置项 ---
username = lanunion_config.lanunion_username
password = lanunion_config.lanunion_password
CHECK_INTERVAL = 30  # 检查新报修单的间隔时间（秒）
NOTIFY_GROUPS = lanunion_config.lanunion_groups  # 需要通知的群号列表
# --- 配置项 ---


# 初始化 LanMsgs_getter
lan_getter = LanMsgs_getter(username, password)
sent_msgs: List[str] = []

async def update_lanmsgs_func():
    """更新数据库中的报修单信息"""
    async with get_session() as db_session:
        try:
            sheet_list = lan_getter.getSheetList()  # 获取简略的报修单数据
            sheet_no_set = {str(sheet_data['sheetNo']) for sheet_data in sheet_list}  # 从查询当前的保修单
            existing_sheet_nos = await LanmsgManager.get_all_sheet_nos(db_session)
            missing_sheet_nos = existing_sheet_nos - sheet_no_set

            if missing_sheet_nos:
                logger.info("有被删改的报修单")
                for sheet_no in missing_sheet_nos:
                    try:
                        lanmsg = await LanmsgManager.get_lanmsg_by_sheet_no(
                            db_session, sheet_no)
                        if not lanmsg.sent:
                            test_sheet = format_lanmsg_to_sheet(lanmsg)
                            lan_msg = LanMsg(test_sheet, httpSession=lan_getter.httpSession)
                            details = lan_msg.getDetails()
                            if details:
                                # 准备更新的数据
                                update_data = {}
                                if "分配给" in details and details["分配给"] is not None:
                                    update_data["assigned_to"] = details["分配给"]
                                    update_data["is_assigned"] = True
                                    update_data["status"] = "已派单"
                                    update_data["sent"] = True

                                    # 先尝试发送消息
                                    try:
                                        to_sent = await LanmsgManager.get_lanmsg_by_sheet_no(db_session, sheet_no)
                                        await send_message(
                                            f"---报修单状态更新---\n{to_sent.sheet_id}\n{to_sent.sheet_no}|{to_sent.name} \n"
                                            f"---已被分配给 {details['分配给']} ---",0)
                                        # 发送成功后再更新数据库
                                        await LanmsgManager.update_lanmsg(db_session, sheet_no, **update_data)
                                    except Exception as e:
                                        logger.error(f"发送消息失败: {e}")
                                else:
                                    logger.error(f"报修单 {sheet_no} 存在删改，但更新数据库失败，缺少'分配给'信息")
                            else:
                                logger.info(f"{sheet_no}被删除")
                                update_data = {"sent": True, "status": "已删除"}
                                try:
                                    to_sent = await LanmsgManager.get_lanmsg_by_sheet_no(db_session, sheet_no)
                                    await send_message(
                                        f"---报修单状态更新---\nNO:{to_sent.sheet_id}\n{to_sent.sheet_no}|{to_sent.name} \n---被删除---",0)
                                    # 发送成功后再更新数据库
                                    await LanmsgManager.update_lanmsg(db_session, sheet_no, **update_data)
                                except Exception as e:
                                    logger.error(f"发送消息失败: {e}")
                        else:
                            logger.info(f"{lanmsg.sheet_no}已被发送过")
                    except Exception as e:
                        logger.error(f"更新报修单 {sheet_no} 时发生错误: {e}")
            else:
                logger.info("未发现删改")

            for sheet_data in sheet_list:
                try:
                    # 检查数据库中是否已存在该 sheetId 的记录
                    existing_lanmsg = await LanmsgManager.get_lanmsg_by_sheet_no(
                        db_session, str(sheet_data['sheetNo'])
                    )

                    if existing_lanmsg:  # 更新记录
                        await check_and_send_reminder(existing_lanmsg)
                    else:
                        # 如果记录不存在，则创建新的记录
                        lan_msg = LanMsg(sheet_data, httpSession=lan_getter.httpSession)
                        details = lan_msg.getDetails()  # 获取详细数据
                        # 先尝试发送消息
                        try:
                            await send_message(
                                f"---新报修单|No{sheet_data['sheetId']}---\n"
                                f"单号: {sheet_data['sheetNo']}|未派单\n"
                                f"创建时间: {datetime.strptime(sheet_data['time'], '%Y-%m-%d %H:%M')}\n"
                                f"用户学号: {details['用户学号']}\n"
                                f"姓名: {details['姓名']}\n"
                                f"地址: {details['维修地点']}\n"
                                f"QQ: {details['QQ']}\n"
                                f"手机: {details['手机']}\n"
                                f"硬件信息: {details['硬件信息']}\n\n"
                                f"描述: {details['故障描述']}\n"
                                f"---新报修单---",0)
                            # 发送成功后再写入数据库
                            await LanmsgManager.create_lanmsg(
                                db_session,
                                sheet_id=sheet_data['sheetId'],
                                create_time=datetime.strptime(sheet_data['time'], '%Y-%m-%d %H:%M'),
                                sheet_no=sheet_data['sheetNo'],
                                name=details['姓名'],
                                student_id=details['用户学号'],
                                location=details['维修地点'],
                                qq=details['QQ'],
                                phone=details['手机'],
                                hardware=details['硬件信息'],
                                description=details['故障描述'],
                                update_time=datetime.now(),
                            )
                            logger.info(f"创建数据: {sheet_data['sheetId']}")
                        except Exception as e:
                            logger.error(f"发送消息失败: {e}")
                except Exception as e:
                    logger.error(f"处理报修单 {sheet_data.get('sheetNo', '未知')} 时发生错误: {e}")

        except SQLAlchemyError as e:
            logger.error(f"数据库操作错误: {e}")
            # 这里可以考虑回滚数据库操作: db_session.rollback()
        except Exception as e:
            logger.error(f"未知错误: {e}")


async def update_lanmsgs_initial():
    """初始化数据库中的报修单信息"""
    async with get_session() as db_session:
        try:
            # 获取所有页面的报修单数据
            sheet_list = lan_getter.getSheetList()

            for sheet_data in sheet_list:
                # 检查数据库中是否已存在该 sheetId 的记录
                existing_lanmsg = await LanmsgManager.get_lanmsg_by_sheet_no(
                    db_session, str(sheet_data['sheetNo'])
                )

                if existing_lanmsg:
                    pass
                else:
                    # 如果记录不存在，则创建新的记录
                    lan_msg = LanMsg(sheet_data, httpSession=lan_getter.httpSession)
                    details = lan_msg.getDetails()
                    await LanmsgManager.create_lanmsg(
                        db_session,
                        sheet_id=sheet_data['sheetId'],
                        create_time=datetime.strptime(sheet_data['time'], '%Y-%m-%d %H:%M'),
                        sheet_no=sheet_data['sheetNo'],
                        name=details['姓名'],
                        student_id=details['用户学号'],
                        location=details['维修地点'],
                        qq=details['QQ'],
                        phone=details['手机'],
                        hardware=details['硬件信息'],
                        description=details['故障描述'],
                        update_time=datetime.now(),

                    )
                    logger.info(f"新报修单: {sheet_data['sheetNo']}")

        except SQLAlchemyError as e:
            logger.error(f"数据库操作错误: {e}")
        except Exception as e:
            logger.error(f"未知错误: {e}")


async def send_message(message, group, targets: list[int] = None):
    """
    发送消息到指定目标。

    参数:
        message: 要发送的消息。
        targets: 目标列表，可以是群号或用户 ID。
        group: 要发送的群号,0为通知群，1为调度群，2为老调度群。
    """
    bot = get_bot()
    try:
        target = int
        group = int(group)
        target = NOTIFY_GROUPS[group]
        target = int(target)
        if isinstance(target, int):
            await bot.send_group_msg(group_id=target, message=message)
        else:
            logger.error(f"无效的目标类型: {type(target)}")
    except Exception as e:
        logger.error(f"发送消息到目标 {target} 失败: {e}")


def format_lanmsg_to_sheet(lanmsg: Lanmsg):
    """将 Lanmsg 对象格式化为与 sheet_data 相同的字典格式。"""
    return {
        'time': lanmsg.create_time.strftime('%Y-%m-%d %H:%M') if isinstance(lanmsg.create_time,
                                                                            datetime) else lanmsg.create_time,
        'sheetNo': lanmsg.sheet_no,
        'address': lanmsg.location,
        'description': lanmsg.description,
        'sheetId': lanmsg.sheet_id,
    }


def format_lanmsg(lanmsg: Lanmsg, at_search: bool = False):
    formatted_lines = [
        f"单号: {lanmsg.sheet_no}|{lanmsg.status}",
        f"创建时间: {lanmsg.create_time}",
        f"用户学号: {lanmsg.student_id}",
        f"姓名: {lanmsg.name}",
        f"地址: {lanmsg.location}",
        f"QQ: {lanmsg.qq}",
        f"手机: {lanmsg.phone}",
        f"硬件信息: {lanmsg.hardware}",
        f"\n"
        f"描述: {lanmsg.description}",
    ]
    if at_search:
        # 判断 lanmsg.assigned_to 是否为空
        if lanmsg.assigned_to:
            formatted_lines.insert(len(formatted_lines), f"---已被分配给 {lanmsg.assigned_to} ---")
        else:
            formatted_lines.insert(len(formatted_lines), "---未派单---")
    return "\n".join(formatted_lines)


def format_simple_lanmsg(lanmsg):
    formatted_lines = [
        f"单号: {lanmsg.sheet_no}|{lanmsg.status}",
        f"时间: {lanmsg.create_time}",
        f"姓名: {lanmsg.name}",
        f"地址: {lanmsg.location}",
    ]
    return "\n".join(formatted_lines)


async def handle_lanmsgs_between_time(
        db_session,
        time1: Optional[datetime] = None,
        time2: Optional[datetime] = None,
) -> List[Lanmsg]:
    """查询创建时间在 time1 和 time2 之间且未被指派的报修单,并按创建时间降序排列

    Args:
        db_session: 数据库会话对象
        time1: 开始时间，默认为 None
        time2: 结束时间，默认为 None

    Returns:
        List[Lanmsg]: 返回符合条件的报修单列表
    """
    stmt = select(Lanmsg).where(Lanmsg.status == "未派单")

    if time1 is not None:
        stmt = stmt.where(Lanmsg.create_time >= time1)
    if time2 is not None:
        stmt = stmt.where(Lanmsg.create_time <= time2)

    stmt = stmt.order_by(Lanmsg.create_time.desc())

    result = await db_session.scalars(stmt)
    lanmsgs = result.all()

    logger.debug(f"找到 {len(lanmsgs)} 个符合条件的报修单")
    return lanmsgs


async def check_and_send_reminder(lanmsg):
    """
    检查报修单创建时间，并在特定时间发送提醒消息。
    """
    if Lanmsg.status != "未派单":
        pass
    time_passed = datetime.now() - lanmsg.create_time

    # 定义提醒时间窗口
    one_day_window = timedelta(hours=23, minutes=55) <= time_passed < timedelta(days=1)
    two_day_window = timedelta(days=1, hours=23, minutes=55) <= time_passed < timedelta(days=2)
    three_day_window = timedelta(days=2, hours=23, minutes=55) <= time_passed < timedelta(days=3)

    if one_day_window:
        await send_message(
            f"---报修单提醒---\n{format_lanmsg(lanmsg)}\n---已创建 1 天，请及时处理---",0
        )
    elif two_day_window:
        await send_message(
            f"---报修单提醒---\n{format_lanmsg(lanmsg)}\n---已创建 2 天，请及时处理---",0
        )
    elif three_day_window:
        await send_message(
            f"---报修单提醒---\n{format_lanmsg(lanmsg)}\n---已创建 3 天，请及时处理---",0
        )

async def update_jwcrssmessage_func():
    """更新数据库中的教务rss信息"""
    async with get_session() as db_session:
        try:
            rss = rss_get()
            message = await rss.jwc()  # 获取简略的rss数据
            sendmessage = message["message"]
            try:
                # 检查数据库中是否已存在该 sheetId 的记录
                existing_lanmsg = await rssmsgManager.get_rss_by_rss_no(
                    db_session, str(message['id'])
                )
                if existing_lanmsg:  # 更新记录
                    print("已存在")
                else:
                # 先尝试发送消息
                    try:
                        await send_message(f"{sendmessage}",1)
                        await send_message(f"{sendmessage}", 2)
                        # 发送成功后再写入数据库
                        await rssmsgManager.create_rssmsg(
                            db_session,
                            id=message['id'],
                            message=message['message'],
                            update_time=datetime.now(),
                        )
                        logger.info(f"创建数据: {message['id']}")
                    except Exception as e:
                        logger.error(f"发送消息失败: {e}")
            except Exception as e:
                logger.error(f"处理报修单 {message.get('id', '未知')} 时发生错误: {e}")

        except SQLAlchemyError as e:
            logger.error(f"数据库操作错误: {e}")
            # 这里可以考虑回滚数据库操作: db_session.rollback()
        except Exception as e:
            logger.error(f"未知错误: {e}")

async def update_netrssmessage_func():
    """更新数据库中的信息办rss信息"""
    async with get_session() as db_session:
        try:
            rss = rss_get()
            message = await rss.net()  # 获取简略的rss数据
            sendmessage = message["message"]
            try:
                # 检查数据库中是否已存在该 sheetId 的记录
                existing_lanmsg = await rssmsgManager.get_rss_by_rss_no(
                    db_session, str(message['id'])
                )

                if existing_lanmsg:  # 更新记录
                    print("已存在")
                else:
                    # 先尝试发送消息
                    try:
                        await send_message(f"{sendmessage}", 0)
                        await send_message(f"{sendmessage}",1)
                        await send_message(f"{sendmessage}", 2)
                        # 发送成功后再写入数据库
                        await rssmsgManager.create_rssmsg(
                            db_session,
                            id=message['id'],
                            message=message['message'],
                            update_time=datetime.now(),
                        )
                        logger.info(f"创建数据: {message['id']}")
                    except Exception as e:
                        logger.error(f"发送消息失败: {e}")
            except Exception as e:
                logger.error(f"处理报修单 {message.get('id', '未知')} 时发生错误: {e}")

        except SQLAlchemyError as e:
            logger.error(f"数据库操作错误: {e}")
            # 这里可以考虑回滚数据库操作: db_session.rollback()
        except Exception as e:
            logger.error(f"未知错误: {e}")