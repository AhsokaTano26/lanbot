import feedparser
import html2text
import re
from bs4 import BeautifulSoup

def add_indentation(text):      #将各段前添加两个空格
    # 以换行符为分隔符将字符串分成多行
    lines = text.split('\n')

    # 对于每一行，在行首添加两个空格
    indented_lines = ['  ' + line for line in lines]

    # 将所有行连接成一个字符串，并在每行之间添加换行符
    indented_text = '\n'.join(indented_lines)

    # 返回修改后的字符串
    return indented_text

def get_links(description):     #提取附件链接
    soup = BeautifulSoup(description, 'html.parser')
    links = []

    # 提取iframe中的PDF链接
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src')
        if src:
            links.append(src)

    # 提取a标签中的PDF链接
    for a in soup.find_all('a'):
        href = a.get('href')
        if href:
            links.append(href)

    # 过滤并去重：仅保留学校域名下的PDF文件
    filtered_links = []
    seen = set()
    for link in links:
        if 'jwc.cqu.edu.cn' in link and link.endswith('.pdf'):
            if link not in seen:
                seen.add(link)
                filtered_links.append(link)

    return filtered_links

class rss_get:
    def jwc(self) -> None:       #获取重庆大学信息化办公室通知
        net = "http://10.244.132.34:6600/cqu/jwc/"  # Rss地址
        NewsFeed = feedparser.parse(net)        # 解析RSS
        entry = NewsFeed.entries[0]  # 取第一条新闻

        text_maker = html2text.HTML2Text()      # 解析RSS
        text_maker.ignore_links = True  # 忽略HTML中的链接

        published = entry.published     # 发布时间
        title = entry.title     # 标题
        link = entry.link       # 链接
        links = get_links(entry.summary)        # 附件链接

        summary1 = text_maker.handle(entry.summary)     #get内容
        bbb = re.sub(r'\n+', '\\n', summary1)  # 去连续空行
        bbb = re.sub(r'^\n', '', bbb)  # 去开头空行
        bbb = re.sub(r'\n$', '', bbb)  # 去末尾空行
        summary = add_indentation(bbb)  # 缩进处理
        a = len(bbb)        # 内容长度
        message1 = published + "\n" + title + "\n" + summary + "\n------News Link--------\n" + link     #有内容的信息
        message2 = published + "\n" + title + "\n------News Link--------\n" + link      #无内容的信息

        if a > 300:     # 内容长度大于300
            if len(links) > 0:  # 有附件
                return published + "\n" + title + "\n" + links[0] + "\n------News Link--------\n" + link  # 有附件
            else:
                return message2
        else:
            if len(links) > 0:       # 有附件
                return published + "\n" + title + "\n" + links[0] + "\n------News Link--------\n" + link        # 有附件
            else:
                return message1     # 无附件


    def net(self) -> None:      #获取重庆大学教务通知
        net = "http://10.244.132.34:6600/cqu/net/tzgg"  # Rss地址
        NewsFeed = feedparser.parse(net)        # 解析RSS
        entry = NewsFeed.entries[0]  # 取第一条新闻

        text_maker = html2text.HTML2Text()      # 解析RSS
        text_maker.ignore_links = True  # 忽略HTML中的链接

        published = entry.published     # 发布时间
        title = entry.title     # 标题
        link = entry.link       # 链接
        links = get_links(entry.summary)        # 附件链接

        summary1 = text_maker.handle(entry.summary)     #获取内容
        bbb = re.sub(r'\n+', '\\n', summary1)  # 去连续空行
        bbb = re.sub(r'^\n', '', bbb)  # 去开头空行
        bbb = re.sub(r'\n$', '', bbb)  # 去末尾空行
        summary = add_indentation(bbb)  # 缩进处理
        a = len(bbb)        # 内容长度
        message1 = published + "\n" + title + "\n" + summary + "\n------News Link--------\n" + link     #有内容的信息
        message2 = published + "\n" + title + "\n------News Link--------\n" + link      #无内容的信息

        if a > 300:     # 内容长度大于300
            if len(links) > 0:  # 有附件
                return published + "\n" + title + "\n" + links[0] + "\n------News Link--------\n" + link  # 有附件
            else:
                return message2
        else:
            if len(links) > 0:       # 有附件
                return published + "\n" + title + "\n" + links[0] + "\n------News Link--------\n" + link        # 有附件
            else:
                return message1