import os

from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent, Bot

from .models_method import DetailManger
from nonebot_plugin_orm import get_session

class get_output_name():
    async def get_output_name(self, precision_name):        #返回文件名
        async with (get_session() as db_session):
            dic = {}
            sheet = await DetailManger.get_Sign_by_student_id(db_session,precision_name)
            output_name = sheet.precision_name
            name = sheet.name
            id = sheet.id
            location = sheet.location
            level = sheet.level
            charge_man = sheet.charge_man
            charge_man_unit = sheet.charge_man_unit
            phone_number = sheet.phone_number
            Service_content = sheet.Service_content

            dic["output_name"] = precision_name + "_" + output_name
            dic["name"] = name
            dic["id"] = id
            dic["location"] = location
            dic["level"] = level
            dic["charge_man"] = charge_man
            dic["charge_man_unit"] = charge_man_unit
            dic["phone_number"] = phone_number
            dic["Service_content"] = Service_content
            return dic

class send_file():
    async def send_xlsx_file(self, file_name):
        group_id = 925265706  # 发送到小团体
        file_path = f"file/{file_name}.xlsx"  # 替换为实际文件绝对路径
        upload_filename = f"{file_name}.xlsx"  # 替换为上传时的文件名
        try:
            # 使用绝对路径上传
            abs_path = f"file://{os.path.abspath(file_path)}"
            await Bot.call_api(self,api="upload_group_file", group_id=group_id, file=abs_path, name=upload_filename)
            msg = "文件发送成功！"
        except Exception as e:
            msg = f"文件发送失败：{str(e)}"
        return msg