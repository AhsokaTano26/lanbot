from datetime import datetime, timedelta
from typing import List
from apscheduler.triggers.cron import CronTrigger
from nonebot import on_command, require
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent, Bot
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot_plugin_orm import get_session
from .rss_get import rss_get
from .config import lanunion_config
from .lanunion import LanMsgs_getter, LanMsg
from .models import Lanmsg
from .models_method import LanmsgManager
from .functions import update_lanmsgs_func, update_lanmsgs_initial, send_message, format_simple_lanmsg, \
    format_lanmsg_to_sheet, format_lanmsg, handle_lanmsgs_between_time, update_jwcrssmessage_func, update_netrssmessage_func

# --- 配置项 ---
username = lanunion_config.lanunion_username
password = lanunion_config.lanunion_password
NOTIFY_GROUPS = lanunion_config.lanunion_groups  # 需要通知的群号列表
# --- 配置项 ---


# 初始化 LanMsgs_getter
lan_getter = LanMsgs_getter(username, password)
sent_msgs: List[str] = []
# 定时任务，每隔一段时间检查一次新报修单
scheduler = require("nonebot_plugin_apscheduler").scheduler


async def handle_lanmsgs_within_days(db_session, days: int, use_send_message: bool = False) -> List[Lanmsg]:
    """处理 x 天内创建的报修单查询

    Args:
        db_session: 数据库会话对象
        days: 天数

    Returns:
        List[Lanmsg]: 返回 x 天内创建的报修单列表
        :param days:
        :param db_session:
        :param use_send_message:
    """
    logger.debug(f"开始查询 {days} 天内创建的报修单")
    start_time = datetime.now() - timedelta(days=days)
    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # 调用 handle_lanmsgs_between_time 函数查询 x 天内创建的报修单
    lanmsgs = await handle_lanmsgs_between_time(db_session, time1=start_time)

    if lanmsgs:
        MAX_MESSAGE_LENGTH = 1500  # 定义最大消息长度
        message = f"最近{days}天有{len(lanmsgs)}个未维修报修单\n"
        logger.debug(f"找到 {len(lanmsgs)} 个 {days} 天内创建的报修单")

        for lanmsg in lanmsgs:
            time_passed = datetime.now() - lanmsg.create_time
            days = time_passed.days
            hours, remainder = divmod(time_passed.seconds, 3600)
            time_passed_str = f"{days}天{hours}小时"
            lanmsg_str = f"\n------\n" + format_simple_lanmsg(lanmsg) + f"\n---{time_passed_str}未处理---\n"

            # 如果当前消息加上新的报修单信息超过最大长度，则发送当前消息并重置消息
            if len(message) + len(lanmsg_str) > MAX_MESSAGE_LENGTH:
                if use_send_message:
                    await send_message(message,0)  # 使用 send_message 发送
                else:
                    await lanunion.send(message)  # 使用 lanunion.send 发送
                message = lanmsg_str  # 重置消息
            else:
                message += lanmsg_str

        # 发送剩余的消息
        if message:
            if use_send_message:
                await send_message(message,0)  # 使用 send_message 发送
            else:
                await lanunion.send(message)  # 使用 lanunion.send 发送
    else:
        logger.debug(f"未找到 {days} 天内创建的报修单")
        await lanunion.send(f"未找到 {days} 天内创建的报修单")

    return lanmsgs


lanunion = on_command("lanunion", priority=10, block=True)


@lanunion.handle()
async def handle_lanunion(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """
    主函数，用于处理主动发起的请求
    """

    async with get_session() as db_session:
        command = args.extract_plain_text().strip()
        if command == "refresh":
            if await LanmsgManager.is_database_empty(db_session):
                await update_lanmsgs_initial()
                await lanunion.finish("初始化完成")
            else:
                await update_lanmsgs_func()  # 调用更新函数
                await update_netrssmessage_func()
                await update_jwcrssmessage_func()
                await lanunion.finish("刷新完成")  # 调用具体的刷新函数

        elif command.startswith("search "):
            sheet_id = command[len("search "):].strip()
            if sheet_id:
                result = await LanmsgManager.get_lanmsg_by_sheet_no(db_session, sheet_no=sheet_id)  # 调用具体的搜索函数
                if result:
                    await lanunion.finish(f"---查询到---\n{format_lanmsg(result, at_search=True)}")
                else:
                    await lanunion.finish("查询为空")
            else:
                await lanunion.finish("请输入单号")

        elif command.startswith("最近"):
            try:
                days = int(command.split(" ")[1])
            except (IndexError, ValueError):
                await lanunion.finish("请指定天数，例如：/lanunion 最近 7")
                return
            if days <= 0:
                await lanunion.finish("无效的指令,请输入大于0的值")
            if days > 30:
                await lanunion.finish("为防止消息过长，暂不支持手动查询超过30的值")
            else:
                result = await handle_lanmsgs_within_days(db_session=db_session, days=days)
                logger.debug(result)

        elif command.startswith("rss"):
            try:
                id = str(command.split(" ")[1])
            except (IndexError, ValueError):
                await lanunion.finish("请指定id，例如：/lanunion rss jwc")
                return
            if id == "jwc":
                #result = await update_jwcrssmessage_func()
                rss = rss_get()
                rssmag = await rss.jwc()
                massage = rssmag["message"]
                await lanunion.finish(f"---查询到---\n{massage}")
            elif id == "net":
                #result = await update_netrssmessage_func()
                rss = rss_get()
                rssmag = await rss.net()
                massage = rssmag["message"]
                await lanunion.finish(f"---查询到---\n{massage}")
            else:
                await lanunion.finish("无效的指令,请输入jwc或net")

        else:
            await lanunion.finish(
                "无效的指令，请使用 /lanunion refresh 或 /lanunion search 单号 或/lanunion 最近 <天数>")


@scheduler.scheduled_job(CronTrigger(minute="*/5"))
async def auto_update_lanmsgs_func():
    """
    定时任务函数，用于每间隔5分钟检查更新报修单信息。
    """
    await update_lanmsgs_func()


@scheduler.scheduled_job(CronTrigger(day_of_week="sat", hour=19, minute=0))  # 设置触发时间为每周末晚上 7 点
async def auto_send_7days():
    """
    定时任务函数，用于每周末晚上 7 点自动发送过去 7 天内创建的报修单信息。
    """
    logger.info("开始执行定时任务：发送 7 天内的报修单")
    async with get_session() as db_session:
        await handle_lanmsgs_within_days(db_session, 7, True)
    logger.info("定时任务执行完毕：发送 7 天内的报修单")

@scheduler.scheduled_job(CronTrigger(minute="*/10"))
async def auto_update_jwcrssmessage_func():
    """
    定时任务函数，用于每间隔10分钟检查更新教务RSS信息。
    """
    await update_jwcrssmessage_func()

@scheduler.scheduled_job(CronTrigger(minute="*/10"))
async def auto_update_netrssmessage_func():
    """
    定时任务函数，用于每间隔10分钟检查更新信息办RSS信息。
    """
    await update_netrssmessage_func()