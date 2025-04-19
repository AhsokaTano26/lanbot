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