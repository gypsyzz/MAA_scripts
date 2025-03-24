from pathlib import Path
from os import path
import re
import pandas as pd
from requests import get
import yaml
import sys

# TG相关信息
with open(Path(sys.argv[0]).parent.joinpath('conf', 'chat.yaml')) as f:
    content = yaml.safe_load(f)

bot_token = content['bot_token']
chat_id = content['chat_id']

# 找log 位置
log_path = Path(content['MAA_path']).joinpath('debug', 'gui.log')

# 读取log
with open(log_path, encoding='utf-8', errors='ignore') as f:
    content = f.read()
content = content.split('\n')

# 切片log 到最后一次运行
content_rev = []
for c in content[::-1]:
    content_rev.append(c)
    if '正在运行中' in c:
        break
content = content_rev[::-1]

# 辅助列表
list_logging = []
operator_log = []
important_message = ('出错', '6 ★')

# 逐行搜索,如果需要加入到输出
for c in content:
    try:
        datetime_lvl = re.findall(r'\[(.*?)\]', c)

        dt = datetime_lvl[0]
        lvl = datetime_lvl[1]

        display_source = re.findall(r'\<(.*?)\>', c)
        display = display_source[0]
        source = display_source[1]

        message = c.split('>')[-1]

        # 其他重要信息, 开始, 结束, 报错
        if any(s in message for s in important_message):
            list_logging.append([dt, lvl, display, source, message])

    except:
        pass

# 列表转DF
df_logging = pd.DataFrame(list_logging, columns=['datetime', 'level', 'display', 'source', 'message'])
df_logging['datetime'] = pd.to_datetime(df_logging['datetime'])
df_logging = df_logging[df_logging['display'] == '1']

# DF转字符串
text = '\n'.join(df_logging['message'].values)

# GET 发送给 TG
url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={text}"

if text.replace('\n', '').strip():
    get(url)
