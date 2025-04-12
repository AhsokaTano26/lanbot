import nonebot
from nonebot import on_command, CommandSession, permission as perm
from nonebot.scheduler import scheduler
from datetime import datetime, time, timedelta
import sqlite3
from typing import Optional

# 数据库文件路径
DB_PATH = "sign_records.db"


# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sign_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,        -- 姓名
            student_id TEXT NOT NULL,  -- 学号
            sign_in_time TEXT,         -- 签到时间（格式：%Y-%m-%d %H:%M:%S）
            sign_out_time TEXT,        -- 签退时间（格式同上）
            total_time TEXT            -- 总在线时间（格式：X小时X分钟）
        )
    ''')
    conn.commit()
    conn.close()


# 时间处理工具函数
def adjust_sign_in_time(now: datetime) -> datetime:
    """调整签到时间：只退不进（取最近的整点或半点，向前取整）"""
    if now.minute < 30:
        return now.replace(minute=0, second=0, microsecond=0)
    else:
        return now.replace(minute=30, second=0, microsecond=0)


def adjust_sign_out_time(now: datetime) -> datetime:
    """调整签退时间：只进不退（取最近的整点或半点，向后取整）"""
    if now.minute < 30:
        return now.replace(minute=30, second=0, microsecond=0)
    else:
        return now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)


# 签到命令
@on_command("签到", aliases=("签到", "signin"), permission=perm.GROUP)
async def sign_in(session: CommandSession):
    name = session.current_arg_text.strip()
    if not name:
        await session.send("请在命令后输入姓名（例如：签到 张三）")
        return

    student_id = session.get("student_id", prompt="请输入你的学号：")
    now = datetime.now()

    # 检查最早签到时间
    if now.time() < time(9, 0):
        await session.send("最早签到时间为 09:00，请稍后再试~")
        return

    # 调整签到时间
    sign_in_time = adjust_sign_in_time(now)

    # 写入数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 检查是否已签到（未签退）
    cursor.execute(
        "SELECT id FROM sign_log WHERE name=? AND sign_out_time IS NULL", (name,)
    )
    if cursor.fetchone():
        await session.send(f"{name} 你已经签到过啦，无需重复签到~")
        conn.close()
        return

    cursor.execute(
        "INSERT INTO sign_log (name, student_id, sign_in_time) VALUES (?, ?, ?)",
        (name, student_id, sign_in_time.strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    await session.send(
        f"{name} 签到成功！\n签到时间：{sign_in_time.strftime('%H:%M')}"
    )


# 签退命令
@on_command("签退", aliases=("签退", "signout"), permission=perm.GROUP)
async def sign_out(session: CommandSession):
    name = session.current_arg_text.strip()
    if not name:
        await session.send("请在命令后输入姓名（例如：签退 张三）")
        return

    now = datetime.now()
    # 检查最晚签退时间
    if now.time() > time(16, 30):
        now = datetime.combine(now.date(), time(16, 30))  # 强制设为最晚时间

    # 调整签退时间
    sign_out_time = adjust_sign_out_time(now)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 查询未签退记录
    cursor.execute(
        "SELECT sign_in_time FROM sign_log WHERE name=? AND sign_out_time IS NULL",
        (name,)
    )
    result = cursor.fetchone()

    if not result:
        await session.send(f"{name} 你还没有签到哦，无法签退~")
        conn.close()
        return

    sign_in_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
    total_seconds = (sign_out_time - sign_in_time).total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    total_time = f"{int(hours)}小时{int(minutes)}分钟"

    # 更新签退时间和总时长
    cursor.execute(
        "UPDATE sign_log SET sign_out_time=?, total_time=? WHERE name=? AND sign_out_time IS NULL",
        (sign_out_time.strftime("%Y-%m-%d %H:%M:%S"), total_time, name)
    )
    conn.commit()
    conn.close()

    await session.send(
        f"{name} 签退成功！\n签退时间：{sign_out_time.strftime('%H:%M')}\n总在线时长：{total_time}"
    )


# 自动签退定时任务（每天16:30执行）
@scheduler.scheduled_job("daily", time="16:30:00")
def auto_sign_out():
    now = datetime.combine(datetime.now().date(), time(16, 30))
    sign_out_time = adjust_sign_out_time(now)  # 强制为16:30（已达最晚时间）

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 查找所有未签退记录
    cursor.execute(
        "SELECT id, name, sign_in_time FROM sign_log WHERE sign_out_time IS NULL"
    )
    records = cursor.fetchall()

    for record in records:
        sign_in_time = datetime.strptime(record[2], "%Y-%m-%d %H:%M:%S")
        total_seconds = (sign_out_time - sign_in_time).total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        total_time = f"{int(hours)}小时{int(minutes)}分钟"

        cursor.execute(
            "UPDATE sign_log SET sign_out_time=?, total_time=? WHERE id=?",
            (sign_out_time.strftime("%Y-%m-%d %H:%M:%S"), total_time, record[0])
        )

    conn.commit()
    conn.close()


# 导出数据库（管理员权限）
@on_command("导出签到数据", aliases=("导出数据", "export_sign"), permission=perm.GROUP_ADMIN)
async def export_data(session: CommandSession):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sign_log")
    columns = [col[0] for col in cursor.description]
    records = cursor.fetchall()
    conn.close()

    if not records:
        await session.send("当前没有签到记录哦~")
        return

    # 格式化输出
    data = ["| {:<4} | {:<6} | {:<10} | {:<16} | {:<16} | {:<12} |".format(
        "ID", "姓名", "学号", "签到时间", "签退时间", "总时长"
    )]
    data.append("-" * 72)
    for record in records:
        data.append("| {:<4} | {:<6} | {:<10} | {:<16} | {:<16} | {:<12} |".format(
            record[0], record[1], record[2],
            record[3] or "未签退", record[4] or "未签退", record[5] or "0分钟"
        ))

    await session.send("\n".join(data))


# 清空数据库（管理员权限）
@on_command("清空签到数据", aliases=("清空数据", "clear_sign"), permission=perm.GROUP_ADMIN)
async def clear_data(session: CommandSession):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sign_log")
    conn.commit()
    conn.close()
    await session.send("已清空所有签到记录~")


# 签到命令参数解析器
@sign_in.args_parser
async def _(session: CommandSession):
    arg = session.current_arg_text.strip()
    if session.is_first_run:
        if arg:
            session.state["name"] = arg  # 姓名从命令参数获取
        return

    if session.current_key == "student_id" and not arg:
        session.pause("学号不能为空，请重新输入~")
    session.state[session.current_key] = arg


# 初始化数据库（NoneBot启动时执行）
nonebot.get_bot().on_startup(init_db)