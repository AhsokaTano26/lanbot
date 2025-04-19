import sqlite3
from typing import Optional
from pathlib import Path
import pandas as pd
from sqlalchemy import text, create_engine
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from xlsxwriter import Workbook
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
from .models import Activity  # 导入你的模型定义


class ActivityManger:
    @classmethod
    async def get_all_student_id(cls, session: async_scoped_session) -> set:
        """获取数据库中所有 student_id"""
        result = await session.execute(select(Activity.student_id))
        return {row[0] for row in result}

    @classmethod
    async def get_Sign_by_student_id(cls, session: async_scoped_session, student_id: str) -> Optional[Activity]:
        """根据 student_id 获取单个信息"""
        return await session.get(Activity, student_id)

    @staticmethod
    async def is_database_empty(db_session):
        # 查询数据库，判断是否有数据
        result = await db_session.execute(text("SELECT 1 FROM Activity LIMIT 1"))
        return not result.fetchone()

    @classmethod
    async def create_signmsg(cls, session: async_scoped_session, **kwargs) -> Activity:
        """创建新的数据"""
        new_signmsg = Activity(**kwargs)
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
    @classmethod
    async def Export(cls, session: async_scoped_session,outpot_name) -> str:
        """导出数据库"""
        output_file: str = f"file/{outpot_name}.xlsx"
        # 创建数据库连接
        engine = create_async_engine('sqlite+aiosqlite:///./data/db.sqlite3')
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        try:
            async with async_session() as session:
                # 异步执行查询
                result = await session.execute(text("SELECT * FROM Activity"))
                data = result.mappings().all()

                # 将结果转换为DataFrame
                def convert_to_df():
                    return pd.DataFrame([dict(row) for row in data])

                # 在异步环境中处理同步操作
                df = await asyncio.get_event_loop().run_in_executor(None, convert_to_df)

                # 保存到Excel
                def save_excel():
                    df.to_excel(output_file, index=False)

                await asyncio.get_event_loop().run_in_executor(None, save_excel)

            await engine.dispose()
        except Exception as e:
            return f"导出失败: {str(e)}"
        return f"数据已导出到 {Path(output_file).resolve()}"
