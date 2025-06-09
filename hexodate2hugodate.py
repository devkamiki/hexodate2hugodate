import os
import re
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime
from dateutil import tz

# 设定源文件夹和目标文件夹路径
source_dir = "/home/freya/obsp-hexo/source/_posts"  # Change it to your own
output_dir = "output_dir"  # Change it to your own

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
    new_content = content

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

    # JSON 文件头处理 - 转换为 YAML 格式
    elif content.strip().startswith('{'):
        try:
            # 分离 JSON 前端元数据和正文内容
            lines = content.split('\n')
            json_lines = []
            body_lines = []
            json_ended = False

            for line in lines:
                if not json_ended and (line.strip().endswith('}') or line.strip() == '}'):
                    json_lines.append(line)
                    json_ended = True
                elif not json_ended:
                    json_lines.append(line)
                else:
                    body_lines.append(line)

            json_content = '\n'.join(json_lines)
            body_content = '\n'.join(body_lines)

            json_obj = json.loads(json_content)

            # 转换日期格式
            if 'date' in json_obj:
                new_date = convert_date_to_iso(json_obj['date'])
                if new_date:
                    json_obj['date'] = new_date
                    modified = True

            # 转换为 YAML 格式
            yaml_header = yaml.dump(json_obj, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{yaml_header}---{body_content}"
            modified = True

        except (json.JSONDecodeError, yaml.YAMLError):
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