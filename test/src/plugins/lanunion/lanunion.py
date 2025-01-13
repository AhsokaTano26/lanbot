#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8
__author__ = "Hagb (郭俊余)"
__copyright__ = f"Copyright 2020, {__author__}"
__credits__ = ["CQU Lanunion"]
__license__ = "GNU AGPL v3"
__version__ = "2.0"
__maintainer__ = __author__
__email__ = "hagb_green@qq.com"
__status__ = "Development"

from .msg_bot import Msg, Msgs_getter, NoneType
from typing import Union, List, Callable, Optional
import requests
import bs4
import re
import datetime
import pytz

TIMEZONE = pytz.timezone('Asia/Shanghai')


def defaultLanFormat(**args) -> str:
    """蓝盟报修单原始数据格式化成文本的默认方式

    参数中以关键字参数形式传入蓝盟单子的 details 和 data 字典.
    """
    hwInfo = args["details"]['硬件信息']
    isMac = 'mac' in hwInfo.lower()
    if hwInfo[:3] == '台式机':
        computer = '台式机' + (' Mac' if isMac else '')
    elif hwInfo[:3] == '笔记本':
        computer = '笔记本' + (' Mac' if isMac else '')
    else:
        computer = hwInfo
    if 'prefix' not in args:
        args['prefix'] = '新保修单'
    fotmatStr = """{prefix} {data[sheetId]}:
单号：{data[sheetNo]}
姓名：{details[姓名]}
学号：{details[用户学号]}
地址：{details[维修地点]}
ＱＱ：{details[QQ]}
手机：{details[手机]}
硬件：{computer}

描述：{details[故障描述]}"""
    return fotmatStr.format(**args, computer=computer)


class LanMsg(Msg):
    """蓝盟报修单的`Msg`子类."""

    def __init__(self,
                 data: dict,
                 way2str: Union[Callable, str] = defaultLanFormat,
                 withDetails: bool = True,
                 httpSession: Union[requests.sessions.Session,
                 NoneType] = None,
                 username: Union[str, NoneType] = None,
                 password: Union[str, NoneType] = None):
        super().__init__()
        self.data = data
        self.way2str = way2str
        self.withDetails = withDetails
        self.httpSession = httpSession
        self.username = username
        self.password = password
        self.origin_time = TIMEZONE.localize(datetime.datetime.fromisoformat(data['time'])).astimezone().replace(
            tzinfo=None)
        self.notify_time = datetime.datetime.now()  # + datetime.timedelta(days=1)
        # max(datetime.datetime.now() + datetime.timedelta(days=1),
        #    self.origin_time + datetime.timedelta(days=2))
        self.deleted = False
        self.longest_notify_time = datetime.timedelta(days=5, hours=10)

    def isNeedNotify(self) -> bool:
        return self.notify_time <= datetime.datetime.now() <= self.origin_time + self.longest_notify_time

    def nextNotify(self) -> None:
        self.notify_time += datetime.timedelta(days=1)

    def notifyMsg(self) -> str:
        days = (datetime.datetime.now() -
                self.origin_time) // datetime.timedelta(days=1)
        return f"{self.getStr(prefix=f'{days} 天未处理')}"

    def getDetails(self) -> Union[dict, bool]:
        """从蓝盟官网获取报修单的原始详细信息。如果单子已被删除，则返回`False`。"""
        httpSheet = self.httpSession.get(
            'http://lanunion.cqu.edu.cn/repair/admin/index.php/'
            'custom_assessment/'
            f'show/{self.data["sheetId"]}',
            allow_redirects=False)
        tmpn = 0
        while httpSheet.status_code == 302:
            LanMsgs_getter.login(self)
            httpSheet = self.httpSession.get(
                'http://lanunion.cqu.edu.cn/repair/admin/index.php/'
                'custom_assessment/'
                f'show/{self.data["sheetId"]}',
                allow_redirects=False)
            tmpn += 1
            if tmpn == 10:
                raise (RuntimeError('Lanunion login failed!'))
        if httpSheet.status_code == 500:
            self.deleted = True
            return False
        httpSheet.encoding = httpSheet.apparent_encoding
        bs = bs4.BeautifulSoup(httpSheet.text, features="lxml")
        details = {}
        for i in bs.find_all('tr')[:-1]:
            tds = [td.text.strip() for td in i.find_all('td')]
            for n in range(len(tds) // 2):
                details[tds[2 * n]] = tds[2 * n + 1]
        return details

    def getStr(self, way2str: Union[Callable, str, NoneType] = None, prefix='新报修单'):
        if self.withDetails:
            details = self.getDetails()
        else:
            details = {}
        if way2str is None:
            way2str = self.way2str
        if isinstance(way2str, Union[Callable]):
            return way2str(data=self.data, details=details, prefix=prefix)
        elif isinstance(way2str, Union[str]):
            return way2str.format(data=self.data, details=details)

    def __eq__(self, rhs) -> bool:
        if type(self) == type(rhs):
            if self.data == rhs.data and self.way2str == rhs.way2str \
                    and self.withDetails == rhs.withDetails:
                return True
        return False


class LanMsgs_getter(Msgs_getter):
    """从蓝盟官网爬取报修单列表的`Msgs_getter`子类."""

    def __init__(self,
                 username: str,
                 password: str,
                 way2str: Union[Callable, str] = defaultLanFormat,
                 withDetails: bool = True):
        super().__init__()
        self.username = username
        self.password = password
        self.httpSession = requests.session()
        self.way2str = way2str
        self.withDetails = withDetails

    def login(self):
        """登录蓝盟官网。使用 cookie 可调用实例变量`httpSession`."""
        loginpost = self.httpSession.post(
            'http://lanunion.cqu.edu.cn/repair/admin/index.php/user/loginpost',
            data={
                'username': self.username,
                'password': self.password
            })
        if loginpost.status_code == 200:
            loginpost.encoding = loginpost.apparent_encoding
            if "用户名或密码错误" in loginpost.text:
                raise RuntimeError("Error lanunion username or password")
            else:
                return True
        else:
            raise RuntimeError(
                "Unexpected status code when trying to login: " +
                str(loginpost.status_code))

    def getSheetList(self, page: int = 1, nextPage: bool = True) -> List[dict]:
        """获取蓝盟官网报修单列表上的报修单原始数据，以字典形式，时间倒序排列在列表中返回"""
        httpSheet = self.httpSession.get(
            'http://lanunion.cqu.edu.cn/repair/admin/index.php/bxsheet/'
            f'datatable/{page}',
            allow_redirects=False)
        tmpn = 0
        while httpSheet.status_code == 302:
            self.login()
            httpSheet = self.httpSession.get(
                'http://lanunion.cqu.edu.cn/repair/admin/index.php/bxsheet/'
                f'datatable/{page}',
                allow_redirects=False)
            tmpn += 1
            if tmpn == 10:
                raise (RuntimeError('Lanunion login failed!'))
        sheetList = []
        httpSheet.encoding = httpSheet.apparent_encoding
        bs = bs4.BeautifulSoup(httpSheet.text, features="lxml")
        table = bs.find('table', attrs={
            'class': 'flexi_grid'
        }).find('tbody').find_all('tr')
        if len(table[-1].find_all()) < 6:
            table.pop()
        for sheet in table:
            tds = sheet.find_all('td')
            if tds[4].text.strip() != "分配蓝客":
                continue
            sheetId = re.search(
                "'http://lanunion.cqu.edu.cn/repair/admin/index.php/bxsheet/"
                "(show|edit)/(\\d+)'",
                tds[5].find('a').attrs['onclick'])[2]
            sheetList.append({
                'time': tds[0].text.strip(),
                'sheetNo': tds[1].text.strip(),
                'address': tds[2].text.strip(),
                'description': tds[3].text.strip(),
                'sheetId': sheetId
            })
        if nextPage:
            nextPage = re.match(
                'http://lanunion.cqu.edu.cn/repair/admin/index.php/bxsheet'
                '/index/(.*)',
                bs.find('a', attrs={
                    "class": "next"
                }).attrs['href'])[1]
            if nextPage != str(page):
                sheetList += self.getSheetList(page=page + 1)
        return sheetList

    def getMsgs(self) -> List[LanMsg]:
        return [
            LanMsg(data,
                   way2str=self.way2str,
                   withDetails=self.withDetails,
                   httpSession=self.httpSession,
                   username=self.username,
                   password=self.password)
            for data in self.getSheetList()[::-1]
        ]
