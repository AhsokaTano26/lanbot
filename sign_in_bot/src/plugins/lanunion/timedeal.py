from datetime import datetime

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