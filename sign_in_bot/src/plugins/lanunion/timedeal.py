from datetime import datetime
from .time_trans import time_trans

class TimeDealSelector:
    def adjust_sign_in_time(self,now: datetime) -> datetime:
        """调整签退时间：只进不退（取最近的整点或半点，向后取整）"""
        if now.minute < 30:
            return now.replace(minute=0, second=0, microsecond=0)
        else:
            return now.replace(minute=30, second=0, microsecond=0)
    def adjust_sign_out_time(self,now: datetime) -> datetime:
        """调整签退时间：只进不退（取最近的整点或半点，向后取整）"""
        if now.minute < 30:
            return now.replace(minute=30, second=0, microsecond=0)
        else:
            return now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)

    def adjust_full_time(self,sign_in_time,sign_out_time,full_time,morning,evening) -> str:
        if float(full_time) <= 8.0 and morning == 0 and evening == 0:
            dt_in = datetime.strptime(sign_in_time, "%Y-%m-%d %H:%M:%S")
            dt_out = datetime.strptime(sign_out_time, "%Y-%m-%d %H:%M:%S")

            # 提取并格式化日期部分（去掉前导零）
            formatted_date = f"{dt_in.year}.{dt_in.month}.{dt_in.day}"

            # 格式化时间部分
            time_in = dt_in.strftime("%H:%M")
            time_out = dt_out.strftime("%H:%M")

            # 组合最终结果
            return f"{formatted_date} {time_in}-{time_out}"
        elif morning != 0 or evening != 0:
            extral_time = morning * 3600 + evening * 3600
            dt_in1 = datetime.strptime(sign_in_time, "%Y-%m-%d %H:%M:%S")
            dt_out1 = datetime.strptime(sign_out_time, "%Y-%m-%d %H:%M:%S")
            # 提取并格式化日期部分（去掉前导零）
            formatted_date1 = f"{dt_in1.year}.{dt_in1.month}.{dt_in1.day}"

            # 格式化时间部分
            time_in1 = dt_in1.strftime("%H:%M")
            time_out1 = dt_out1.strftime("%H:%M")

            # 处理超时部分
            t = time_trans()
            outtimestamp = t.time_tran2(sign_out_time) - 86400  # 转换为时间戳且加一天
            intimestamp = outtimestamp - extral_time

            dateArray1 = datetime.fromtimestamp(intimestamp)
            # 将datetime对象格式化为字符串
            dtin = dateArray1.strftime("%Y-%m-%d %H:%M:%S")

            dateArray2 = datetime.fromtimestamp(outtimestamp)
            # 将datetime对象格式化为字符串
            dtout = dateArray2.strftime("%Y-%m-%d %H:%M:%S")

            dt_in2 = datetime.strptime(dtin, "%Y-%m-%d %H:%M:%S")
            dt_out2 = datetime.strptime(dtout, "%Y-%m-%d %H:%M:%S")
            # 提取并格式化日期部分（去掉前导零）
            formatted_date2 = f"{dt_in2.year}.{dt_in2.month}.{dt_in2.day}"

            # 格式化时间部分
            time_in2 = dt_in2.strftime("%H:%M")
            time_out2 = dt_out2.strftime("%H:%M")
            return f"{formatted_date1} {time_in1}-{time_out1}\n{formatted_date2} {time_in2}-{time_out2}"
        else:
            extral_time = (float(full_time) - 8.0) * 3600
            dt_in1 = datetime.strptime(sign_in_time, "%Y-%m-%d %H:%M:%S")
            dt_out1 = datetime.strptime(sign_out_time, "%Y-%m-%d %H:%M:%S")
            # 提取并格式化日期部分（去掉前导零）
            formatted_date1 = f"{dt_in1.year}.{dt_in1.month}.{dt_in1.day}"

            # 格式化时间部分
            time_in1 = dt_in1.strftime("%H:%M")
            time_out1 = dt_out1.strftime("%H:%M")



            #处理超时部分
            t = time_trans()
            outtimestamp = t.time_tran2(sign_out_time) + 86400  # 转换为时间戳且加一天
            intimestamp = outtimestamp - extral_time

            dateArray1 = datetime.fromtimestamp(intimestamp)
            # 将datetime对象格式化为字符串
            dtin = dateArray1.strftime("%Y-%m-%d %H:%M:%S")

            dateArray2 = datetime.fromtimestamp(outtimestamp)
            # 将datetime对象格式化为字符串
            dtout = dateArray2.strftime("%Y-%m-%d %H:%M:%S")

            dt_in2 = datetime.strptime(dtin, "%Y-%m-%d %H:%M:%S")
            dt_out2 = datetime.strptime(dtout, "%Y-%m-%d %H:%M:%S")
            # 提取并格式化日期部分（去掉前导零）
            formatted_date2 = f"{dt_in2.year}.{dt_in2.month}.{dt_in2.day}"

            # 格式化时间部分
            time_in2 = dt_in2.strftime("%H:%M")
            time_out2 = dt_out2.strftime("%H:%M")
            return f"{formatted_date1} {time_in1}-{time_out1}\n{formatted_date2} {time_in2}-{time_out2}"


    def adjust_research_time(self,sign_in_time,sign_out_time) -> str:
        if sign_out_time != "1":
            dt_in = datetime.strptime(sign_in_time, "%Y-%m-%d %H:%M:%S")
            dt_out = datetime.strptime(sign_out_time, "%Y-%m-%d %H:%M:%S")

            # 提取并格式化日期部分（去掉前导零）
            formatted_date = f"{dt_in.year}.{dt_in.month}.{dt_in.day}"

            # 格式化时间部分
            time_in = dt_in.strftime("%H:%M")
            time_out = dt_out.strftime("%H:%M")

            # 组合最终结果
            return f"{formatted_date} {time_in}-{time_out}"
        else:
            dt_in = datetime.strptime(sign_in_time, "%Y-%m-%d %H:%M:%S")
            # 提取并格式化日期部分（去掉前导零）
            formatted_date = f"{dt_in.year}.{dt_in.month}.{dt_in.day}"

            # 格式化时间部分
            time_in = dt_in.strftime("%H:%M")

            # 组合最终结果
            return f"{formatted_date} {time_in}-None"