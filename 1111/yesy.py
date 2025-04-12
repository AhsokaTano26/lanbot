from datetime import datetime, time, timedelta
import timedeal
TimeDealSelector = timedeal.TimeDealSelector
dealtime = TimeDealSelector()


now = datetime.now()
# 调整签到时间
dic = {}
name = str(input())
Student_id = str(input())
if now.time() < time(0, 0):
    print("最早签到时间为 09:00，请稍后再试~")
else:
            sign_in_time = dealtime.adjust_sign_in_time(now)
            if name is not None and Student_id is not None:
                dic["name"] = name
                dic["Student_id"] = Student_id
                dic["sign_in_time"] = sign_in_time
                print(dic)
                print(dic["sign_in_time"])
            else:
                print(f"输入错误")
