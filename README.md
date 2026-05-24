# IEC 61850 ICD/CID/SCD Parser

IEC 61850 ICD/CID/SCD 文件信息提取工具，用于从智能电子设备(IED)配置文件中提取结构化信息，并基于IEC 61850-2标准对解析结果进行语义解析。

## 功能特性

- 解析 ICD/CID/SCD 等 IEC 61850 配置文件
- 支持单文件或目录批量解析
- 支持 SCD 文件多 IED 解析（一个 SCD 可包含多个 IED）
- 提取 IED 基本信息（厂商、型号）
- 提取通信配置（IP地址、子网等）
- 解析逻辑设备(LDevice)、逻辑节点(LN)
- 提取数据集(DataSet)、控制块配置
- **语义解析功能** - 基于IEC 61850-2标准缩写字典，自动解析：
  - 逻辑节点类名（如 LLN0 → 逻辑节点零）
  - 功能约束（如 MX → 测量模拟量值）
  - 数据对象名称（如 Beh → 行为）
- 导出 JSON/CSV 格式结果

## 项目结构

```
ICD_parse/
├── run.py                # 主入口脚本
├── icd_parse/            # 核心解析模块
│   ├── __init__.py       # 包入口
│   ├── parser.py         # ICDParser 类（单文件解析，支持多IED）
│   ├── extractor.py      # ICDExtractor 类（批量提取，支持单文件）
│   ├── abbr_resolver.py  # AbbrResolver 类（语义解析）
│   ├── abbr_dict.py      # IEC 61850-2 缩写字典
│   ├── utils.py          # 工具函数（显示、报告）
│   └── cli.py            # 命令行接口
├── input/                # 输入文件目录
├── output/               # 输出文件目录
├── docs/                 # 文档
├── requirements.txt      # 依赖列表
└── README.md             # 项目说明
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/ICD_parse.git
cd ICD_parse

# (可选) 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

无需额外依赖，仅使用 Python 标准库。

## 使用方法

### 命令行用法

```bash
# 摘要模式（默认） - 解析目录下所有文件，生成统计报告和语义对照表
python run.py input/61850ICD

# 解析单个 SCD/ICD/CID 文件
python run.py input/中科院.scd

# 完整模式 - 每个文件单独保存JSON
python run.py input/中科院.scd -m full

# 语义解析模式 - 完整提取 + 语义标注
python run.py input/中科院.scd -m semantic

# 仅统计
python run.py input/中科院.scd -m stats

# 显示详细信息
python run.py input/中科院.scd -v

# 显示缩写参考表
python run.py --show-reference

# 禁用语义解析
python run.py input/中科院.scd --no-semantic

# 指定输出目录
python run.py input/中科院.scd -o output
```

### Python API 用法

```python
from icd_parse import ICDParser, ICDExtractor, AbbrResolver

# 解析单个文件（启用语义解析）
parser = ICDParser('path/to/file.scd', enable_semantic=True)
result = parser.extract_all()

# SCD 文件包含多个 IED，遍历所有 IED
for ied in result['ieds']:
    print(f"IED: {ied['name']}, 厂商: {ied['manufacturer']}")
    for ld in ied.get('lDevices', []):
        if 'ln0' in ld:
            semantic = ld['ln0'].get('lnClass_semantic')
            print(f"  LLN0 -> {semantic['zh']}")

# 批量提取（支持目录或单文件路径）
extractor = ICDExtractor('input/中科院.scd', 'output')
extractor.extract_and_save_separately()

# 使用语义解析器
resolver = AbbrResolver()
print(resolver.resolve_ln_class('MMXU'))  # {'zh': '测量值', ...}
print(resolver.resolve_fc('ST'))          # {'zh': '状态信息', ...}
```

### 输出结构

ICD/CID 文件（单 IED）和 SCD 文件（多 IED）统一使用 `ieds` 列表输出：

```json
{
  "file_name": "中科院.scd",
  "header": { "id": "中科院", "version": "1.3" },
  "communication": { "subNetworks": [...] },
  "ieds": [
    {
      "name": "PL101",
      "desc": "中科院测试10kV线路",
      "manufacturer": "SAC",
      "type": "SAC IED",
      "services": [...],
      "lDevices": [
        {
          "inst": "CTRL01",
          "ln0": { "lnClass": "LLN0", "lnClass_semantic": {...} },
          "lns": [...]
        }
      ]
    }
  ],
  "dataTypeTemplates": { "lnTypes": [...], "doTypes": [...], ... }
}
```

### 语义解析示例

解析结果中会自动添加语义解释：

```json
{
  "lnClass": "GGIO",
  "lnClass_semantic": {
    "lnClass": "GGIO",
    "en": "Generic GOOSE I/O",
    "zh": "通用GOOSE输入输出",
    "group": "Generic"
  },
  "fc": "ST",
  "fc_semantic": {
    "fc": "ST",
    "zh": "状态信息",
    "desc": "状态类数据，如开关位置、保护动作状态等"
  }
}
```

## 语义解析字典

基于 IEC 61850-2 标准的缩写字典包含：

| 类别 | 词条数 | 说明 |
|------|--------|------|
| 通用缩写 | 281+ | 功能约束、数据对象名称、设备类型等 |
| 逻辑节点类名 | 44+ | IEC 61850-7-4 定义的标准逻辑节点 |
| 功能约束 | 17 | MX、ST、CO、CF、DC 等 |

### 逻辑节点类名前缀

| 前缀 | 功能类型 | 示例 |
|------|----------|------|
| L | 系统逻辑节点 | LLN0(逻辑节点零), LPHD(物理装置) |
| P | 保护功能 | PDIF(差动), PDIS(距离), PTOC(过流) |
| M | 测量计量 | MMXU(测量), MMTR(计量) |
| C | 监控控制 | CSWI(开关控制), CILO(联锁) |
| X | 开关设备 | XCBR(断路器), XSWI(隔离开关) |
| T | 互感器 | TCTR(电流互感器), TVTR(电压互感器) |
| Y | 电力变压器 | YPTR(变压器) |
| G | 通用功能 | GGIO(通用GOOSE I/O) |

### 功能约束说明

| 缩写 | 中文释义 | 描述 |
|------|----------|------|
| MX | 测量模拟量值 | 模拟量测量值(电流、电压、功率等) |
| ST | 状态信息 | 状态类数据(开关位置、保护动作等) |
| CO | 控制 | 控制操作类数据 |
| CF | 配置 | 配置参数(设备名称、版本信息等) |
| DC | 描述 | 描述性信息(设备描述、铭牌信息等) |
| SG | 定值组 | 定值组数据 |
| BR | 缓存报告 | 缓存报告控制块 |
| RP | 非缓存报告 | 非缓存报告控制块 |

## 支持的文件类型

| 文件类型 | 说明 | IED数量 |
|---------|------|---------|
| ICD | IED Configuration Description - IED能力描述文件 | 单个 |
| CID | Configured IED Description - IED配置描述文件 | 单个 |
| SCD | Substation Configuration Description - 变电站配置文件 | 多个 |
| IID | IED Instantiation Description - IED实例化描述文件 | 单个 |

## 许可证

MIT License

## 参考

- IEC 61850 标准
- IEC 61850-2: Glossary (术语)
- IEC 60870-5-103 规约