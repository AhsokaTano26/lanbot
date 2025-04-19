import time
from datetime import datetime


class time_trans:
    def time_tran1(self,now_time: datetime) -> int:     #传入datetime
        now_time = str(now_time)
        timeArray = time.strptime(now_time, "%Y-%m-%d %H:%M:%S")
        timestamp = int(time.mktime(timeArray))     # 转换为时间戳(秒)
        return timestamp
    def time_tran2(self,now_time: str) -> int:      #传入str
        now_time = str(now_time)
        timeArray = time.strptime(now_time, "%Y-%m-%d %H:%M:%S")
        timestamp = int(time.mktime(timeArray))     # 转换为时间戳(秒)
        return timestamp