# IEC 61850 ICD/CID Parser

IEC 61850 ICD/CID 文件信息提取工具，用于从智能电子设备(IED)配置文件中提取结构化信息。

## 功能特性

- 解析 ICD/CID/SCD 等 IEC 61850 配置文件
- 提取 IED 基本信息（厂商、型号）
- 提取通信配置（IP地址、子网等）
- 解析逻辑设备(LDevice)、逻辑节点(LN)
- 提取数据集(DataSet)、控制块配置
- 导出 JSON/CSV 格式结果

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/ICD_parse.git
cd ICD_parse

# (可选) 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

```python
from icd_parser import ICDParser

# 解析 ICD 文件
parser = ICDParser('path/to/your/file.icd')
parser.parse()

# 提取信息
header_info = parser.extract_header_info()
ied_info = parser.extract_ied_info()
logical_devices = parser.extract_logical_devices()
```

或直接运行脚本：

```bash
python icd_parser.py
```

## 项目结构

```
ICD_parse/
├── icd_parser.py      # 主解析脚本
├── input/            # 输入文件目录
│   └── 61850ICD/     # ICD 文件存放
├── output/           # 输出文件目录
│   └── 61850ICD/     # 解析结果输出
├── docs/             # 文档
├── requirements.txt  # 依赖列表
└── README.md         # 项目说明
```

## 支持的文件类型

| 文件类型 | 说明 |
|---------|------|
| ICD | IED Configuration Description - IED能力描述文件 |
| CID | Configured IED Description - IED配置描述文件 |
| SCD | Substation Configuration Description - 变电站配置文件 |
| IID | IED Instantiation Description - IED实例化描述文件 |

## 提取的信息类型

- IED 基本信息
- 通信配置参数
- 支持的服务列表
- 逻辑设备(LDevice)
- 逻辑节点(LN)
- 数据集(DataSet)
- 控制块配置
- 数据对象(DOI)
- 数据类型模板

## 依赖

- Python >= 3.8
- 仅使用 Python 标准库，无需额外依赖

## 许可证

MIT License

## 参考

- IEC 61850 标准
- IEC 60870-5-103 规约