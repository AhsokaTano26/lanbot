from typing import Optional
from sqlalchemy import text
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from .models import Sign, Trans  # 导入你的模型定义


class SignManger:
    @classmethod
    async def get_all_student_id(cls, session: async_scoped_session) -> set:
        """获取数据库中所有 student_id"""
        result = await session.execute(select(Sign.student_id))
        return {row[0] for row in result}

    @classmethod
    async def get_Sign_by_student_id(cls, session: async_scoped_session, student_id: str) -> Optional[Sign]:
        """根据 student_id 获取单个信息"""
        return await session.get(Sign, student_id)

    @staticmethod
    async def is_database_empty(db_session):
        # 查询数据库，判断是否有数据
        result = await db_session.execute(text("SELECT 1 FROM Sign LIMIT 1"))
        return not result.fetchone()

    @classmethod
    async def create_signmsg(cls, session: async_scoped_session, **kwargs) -> Sign:
        """创建新的数据"""
        new_signmsg = Sign(**kwargs)
        session.add(new_signmsg)
        await session.commit()
        return new_signmsg

    @classmethod
    async def delete_student_id(cls, session: async_scoped_session, student_id: str) -> bool:
        """删除数据"""
        lanmsg = await cls.get_Sign_by_student_id(session, student_id)
        if lanmsg:
            await session.delete(lanmsg)
            await session.commit()
            return True
        return False

    @classmethod
    async def delete_all_student_id(cls, session: async_scoped_session) -> bool:
        """删除所有数据"""
        sheet = await cls.get_all_student_id(session)
        for student_id in sheet:
            lanmsg = await cls.get_Sign_by_student_id(session, student_id)
            if lanmsg:
                await session.delete(lanmsg)
                await session.commit()
        return True


class TansManger:
    @classmethod
    async def get_all_id(cls, session: async_scoped_session) -> set:
        """获取数据库中所有 student_id"""
        result = await session.execute(select(Trans.student_id))
        return {row[0] for row in result}

    @classmethod
    async def get_trans_by_id(cls, session: async_scoped_session, student_id: str) -> Optional[Trans]:
        """根据 student_id 获取单个信息"""
        return await session.get(Trans, student_id)

    @staticmethod
    async def is_database_empty(db_session):
        # 查询数据库，判断是否有数据
        result = await db_session.execute(text("SELECT 1 FROM Sign LIMIT 1"))
        return not result.fetchone()

    @classmethod
    async def create_Transmsg(cls, session: async_scoped_session, **kwargs) -> Trans:
        """创建新的数据"""
        new_Transmsg = Trans(**kwargs)
        session.add(new_Transmsg)
        await session.commit()
        return new_Transmsg

    @classmethod
    async def delete_id(cls, session: async_scoped_session, student_id: str) -> bool:
        """删除数据"""
        lanmsg = await cls.get_trans_by_id(session, student_id)
        if lanmsg:
            await session.delete(lanmsg)
            await session.commit()
            return True
        return False

    @classmethod
    async def delete_all_id(cls, session: async_scoped_session) -> bool:
        """删除所有数据"""
        sheet = await cls.get_all_id(session)
        for student_id in sheet:
            lanmsg = await cls.get_trans_by_id(session, student_id)
            if lanmsg:
                await session.delete(lanmsg)
                await session.commit()
        return True