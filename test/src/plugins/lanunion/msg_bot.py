from abc import ABC, abstractmethod
from typing import List, Union

NoneType = type(None)


class Msg(ABC):
    """消息的抽象基类"""

    def __init__(self):
        pass

    @abstractmethod
    def getStr(self) -> str:
        """获取消息的文本"""
        pass


class RawMsg(Msg):
    """单纯的字符串消息

    RawMsg(text)
    """

    def __init__(self, text: str = ''):
        self.text = text

    def getStr(self) -> str:
        """返回字符串"""
        return self.text


class Msg_sender(ABC):
    """消息发送器的抽象基类"""

    def __init__(self):
        pass

    @abstractmethod
    def sendMsg(self, msg: Union[str, Msg]) -> bool:
        """参数为要发送的消息"""
        pass


class Msg_printer(Msg_sender):
    """直接将消息打印到标准输出的`Msg_sender`子类（消息发送器）."""

    def __init__(self):
        super().__init__()

    def sendMsg(self, msg: Union[str, Msg]) -> bool:
        if isinstance(msg, Union[str]):
            print(msg)
        else:
            print(msg.getStr())
        return True


class Msgs_getter(ABC):
    """消息获取器的抽象基类"""

    def __init__(self):
        pass

    @abstractmethod
    def getMsgs(self) -> List[Msg]:
        """获取消息，并返回`Msg`对象所组成的列表，无特殊说明按照时间顺序升序排列。"""
        pass


"""
class Msgs_senders(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def sendMsgs(self) -> List[Msg]:
        pass

    @abstractmethod
    def revMsgs(self) -> List[Msg]:
        pass

    @abstractmethod
    def run(self):
        pass
"""


class Msg_bot(ABC):
    """消息处理机器人的抽象基类"""

    def __init__(self):
        pass

    @abstractmethod
    def run(self):
        pass
