from pathlib import Path
from os import path
import re
import pandas as pd
from requests import get
import yaml

# TG相关信息
with open('../conf/chat.yaml') as f:
    content = yaml.safe_load(f)

bot_token = content['bot_token']
chat_id = content['chat_id']

# 找log 位置
log_path = path.join(content['MAA_path'], 'debug')

# 读取log
with open(f'{log_path}/gui.log', encoding='utf-8', errors='ignore') as f:
    content = f.read()
content = content.split('\n')

# 切片log 到最后一次运行
content_rev = []
for c in content[::-1]:
    content_rev.append(c)
    if '正在运行中' in c:
        break
content = content_rev[::-1]

print(content)

# 辅助列表
list_logging = []
fight_log = []
items = []
operator_log = []
important_message = ('出错', '开始任务', '完成任务')

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

        if '掉落统计' in message:
            fight_log = [dt, lvl, display, source, message]

        elif '公招识别结果' in message:
            operator_log = [dt, lvl, display, source, message]

        # 公招结果
        elif '★' in c:
            operator_log[-1] += message

        # 结果为其他时,公招或者掉落统计结束
        else:
            if len(fight_log) > 0:
                items_dict = {}
                # 统计总战斗掉落
                for i in items:
                    k, v = i.split(':')
                    k = k.strip()
                    v = int(v.split('(+')[0].strip())
                    items_dict.update({k: v})
                fight_log[-1] += str(items_dict)
                list_logging.append(fight_log)
                fight_log = []
                items = []

            # 统计公招结果
            if len(operator_log) > 0:
                list_logging.append(operator_log)
                operator_log = []

        # 其他重要信息, 开始, 结束, 报错
        if any(s in message for s in important_message):
            list_logging.append([dt, lvl, display, source, message])

    # 战斗统计为另起一行的信息
    except IndexError:
        if len(fight_log) > 0 and '(+' in c:
            items.append(c)
        else:
            pass
    except:
        pass

# 列表转DF
df_logging = pd.DataFrame(list_logging, columns=['datetime', 'level', 'display', 'source', 'message'])
df_logging['datetime'] = pd.to_datetime(df_logging['datetime'])
df_logging = df_logging[df_logging['display'] == '1']

# 战斗掉落统计只要最后一行
indices = df_logging[df_logging['message'].str.contains('掉落统计')].index[0:-1]
df_logging = df_logging.drop(indices)

# DF转字符串
text = '\n'.join(df_logging['message'].values)

# GET 发送给 TG
url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={text}"
get(url)
