import time
from datetime import datetime


class time_trans:
    def time_tran1(self,now_time: datetime) -> int:
        now_time = str(now_time)
        timeArray = time.strptime(now_time, "%Y-%m-%d %H:%M:%S")
        timestamp = int(time.mktime(timeArray))
        return timestamp
    def time_tran2(self,now_time: str) -> int:
        now_time = str(now_time)
        timeArray = time.strptime(now_time, "%Y-%m-%d %H:%M:%S")
        timestamp = int(time.mktime(timeArray))
        return timestamp