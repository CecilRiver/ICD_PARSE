"""
IEC 61850 ICD/CID/SCD 文件信息提取脚本 - 主入口

运行方式:
    python run.py input/61850ICD              # 摘要模式
    python run.py input/中科院.scd            # 解析单个SCD文件
    python run.py input/61850ICD -m full      # 完整提取
    python run.py input/61850ICD -m semantic  # 语义解析
    python run.py --show-reference            # 显示缩写参考表
"""

import sys
import os

# 将 icd_parse 目录添加到路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'icd_parse'))

from icd_parse.cli import main

if __name__ == '__main__':
    main()