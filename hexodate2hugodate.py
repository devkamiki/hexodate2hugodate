import os
import re
import shutil
import json
from pathlib import Path
from datetime import datetime
from dateutil import tz

# 设定源文件夹和目标文件夹路径
source_dir = "source_dir" # Change it to your own
output_dir = "output_dir" # Change it to your own

# 自动创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 获取本地时区
local_tz = tz.tzlocal()

# 日期识别和转换函数
def convert_date_to_iso(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
        dt = dt.replace(tzinfo=local_tz)
        return dt.isoformat()
    except ValueError:
        return None

# 识别 YAML 或 JSON 文件头
def process_file(file_path, output_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # YAML 文件头处理
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            header = parts[1]
            body = parts[2]
            # 查找 date 字段
            date_match = re.search(r'date:\s*["\']?([\d/:\s]+)["\']?', header)
            if date_match:
                old_date = date_match.group(1).strip()
                new_date = convert_date_to_iso(old_date)
                if new_date:
                    header = header.replace(old_date, new_date)
                    modified = True
            new_content = f"---{header}---{body}"

    # JSON 文件头处理（如为以 `{` 开始的 JSON 对象）
    elif content.strip().startswith('{'):
        try:
            json_obj = json.loads(content)
            if 'date' in json_obj:
                new_date = convert_date_to_iso(json_obj['date'])
                if new_date:
                    json_obj['date'] = new_date
                    new_content = json.dumps(json_obj, indent=2, ensure_ascii=False)
                    modified = True
                else:
                    new_content = content
            else:
                new_content = content
        except json.JSONDecodeError:
            new_content = content
    else:
        new_content = content

    # 写入新文件
    output_file = os.path.join(output_path, os.path.basename(file_path))
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content if modified else content)

# 遍历并处理所有 .md 文件
for file in os.listdir(source_dir):
    if file.endswith('.md'):
        process_file(os.path.join(source_dir, file), output_dir)

print("所有文件已处理并输出至:", output_dir)
