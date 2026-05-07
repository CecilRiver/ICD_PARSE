"""
ICD Parse - IEC 61850 ICD/CID 文件解析工具包

模块结构:
- parser.py: ICDParser 类，解析单个ICD/CID文件
- extractor.py: ICDExtractor 类，批量提取多个文件
- abbr_resolver.py: AbbrResolver 类，缩写语义解析
- abbr_dict.py: IEC 61850-2 缩写字典
- utils.py: 工具函数（显示、报告）
- cli.py: 命令行入口
"""

from .parser import ICDParser
from .extractor import ICDExtractor
from .abbr_resolver import AbbrResolver
from .abbr_dict import ABBREVIATIONS, LN_CLASS_MAP, FC_DETAIL
from .utils import (
    print_extraction_info,
    print_semantic_reference,
    generate_semantic_report,
    print_ln_semantic_table
)

__version__ = '1.0.0'
__all__ = [
    'ICDParser',
    'ICDExtractor',
    'AbbrResolver',
    'ABBREVIATIONS',
    'LN_CLASS_MAP',
    'FC_DETAIL',
    'print_extraction_info',
    'print_semantic_reference',
    'generate_semantic_report',
    'print_ln_semantic_table'
]