from typing import Optional
from sqlalchemy import text
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from .models import Lanmsg, rss  # 导入你的模型定义


class LanmsgManager:
    @classmethod
    async def get_lanmsg_by_sheet_no(cls, session: async_scoped_session, sheet_no: str) -> Optional[Lanmsg]:
        """根据 sheet_id 获取单个报修单"""
        return await session.get(Lanmsg, sheet_no)

    @classmethod
    async def get_all_sheet_nos(cls, session: async_scoped_session) -> set:
        """获取数据库中所有 sheet_no"""
        result = await session.execute(select(Lanmsg.sheet_no))
        return {row[0] for row in result}

    @staticmethod
    async def is_database_empty(db_session):
        # 查询数据库，判断是否有数据
        result = await db_session.execute(text("SELECT 1 FROM lanmsgs LIMIT 1"))
        return not result.fetchone()

    @classmethod
    async def create_lanmsg(cls, session: async_scoped_session, **kwargs) -> Lanmsg:
        """创建新的报修单"""
        new_lanmsg = Lanmsg(**kwargs)
        session.add(new_lanmsg)
        await session.commit()
        return new_lanmsg

    @classmethod
    async def update_lanmsg(cls, session: async_scoped_session, sheet_id: str, **kwargs) -> Optional[Lanmsg]:
        """更新报修单信息"""
        lanmsg = await cls.get_lanmsg_by_sheet_no(session, sheet_id)
        if lanmsg:
            for key, value in kwargs.items():
                setattr(lanmsg, key, value)
            await session.commit()
        return lanmsg

    @classmethod
    async def delete_lanmsg(cls, session: async_scoped_session, sheet_id: str) -> bool:
        """删除报修单"""
        lanmsg = await cls.get_lanmsg_by_sheet_no(session, sheet_id)
        if lanmsg:
            await session.delete(lanmsg)
            await session.commit()
            return True
        return False

class rssmsgManager:
    @classmethod
    async def get_rss_by_rss_no(cls, session: async_scoped_session, id: str) -> Optional[rss]:
        """根据 id 获取单个信息"""
        return await session.get(rss, id)
    @staticmethod
    async def is_database_empty(db_session):
        # 查询数据库，判断是否有数据
        result = await db_session.execute(text("SELECT 1 FROM lanmsgs LIMIT 1"))
        return not result.fetchone()

    @classmethod
    async def create_rssmsg(cls, session: async_scoped_session, **kwargs) -> Lanmsg:
        """创建新的报修单"""
        new_rssmsg = rss(**kwargs)
        session.add(new_rssmsg)
        await session.commit()
        return new_rssmsg