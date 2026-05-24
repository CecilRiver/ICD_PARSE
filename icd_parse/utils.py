"""
工具函数：显示和报告生成
"""

from collections import defaultdict
import json

from icd_parse.abbr_resolver import AbbrResolver
from icd_parse.abbr_dict import ABBREVIATIONS, LN_CLASS_MAP, FC_DETAIL


def print_extraction_info():
    """显示提取信息说明"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║          IEC 61850 ICD/CID 文件信息提取流程 (参考论文PICS解析方法)       ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  从ICD/CID文件顶部到底部顺序处理：                                        ║
║  ├── 1. 提取Header信息（文档元数据）                                      ║
║  ├── 2. 提取通信配置（SubNetwork、IP地址）                                ║
║  ├── 3. 提取IED基本信息（厂商、型号、版本）                               ║
║  ├── 4. 提取支持的服务列表（类似PICS的BIBBs）                             ║
║  ├── 5. 提取逻辑设备(LDevice)列表                                         ║
║  │   └── 对每个LDevice：                                                  ║
║  │       ├── 提取LN0（逻辑节点零）                                        ║
║  │       ├── 提取所有LN（逻辑节点）                                       ║
║  │       │   └── 提取数据集(DataSet)及FCDA成员                            ║
║  │       │   └── 提取报告控制块(ReportControl)                            ║
║  │       │   └── 提取GOOSE控制块(GSEControl)                              ║
║  │       │   └── 提取数据对象(DOI)及属性(DAI)                             ║
║  ├── 6. 提取数据类型模板(DataTypeTemplates)                               ║
║  │   ├── LNodeType（逻辑节点类型定义）                                    ║
║  │   ├── DOType（数据对象类型定义）                                       ║
║  │   ├── DAType（数据属性类型定义）                                       ║
║  │   └── EnumType（枚举类型定义）                                         ║
║  └── 输出结构化结果（JSON格式）                                           ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  提取的信息类型与用途：                                                   ║
║  ┌─────────────────────┬───────────────────────────────┐                 ║
║  │      信息类型       │             用途              │                 ║
║  ├─────────────────────┼───────────────────────────────┤                 ║
║  │ IED基本信息         │ 设备身份识别（厂商、型号）    │                 ║
║  │ 支持的服务          │ 定义允许的操作（Method Rule） │                 ║
║  │ 逻辑节点类型        │ 定义支持的功能（Type Rule）   │                 ║
║  │ 数据集定义          │ 数据分组与订阅配置            │                 ║
║  │ DOI描述             │ 数据点语义解释                │                 ║
║  │ 数据类型模板        │ 数据结构验证规则              │                 ║
║  └─────────────────────┴───────────────────────────────┘                 ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


def print_semantic_reference():
    """打印缩写参考表"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║              IEC 61850 缩写语义参考 (基于IEC 61850-2标准)                ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  功能约束(FC)说明:                                                        ║
║  ┌──────┬────────────────────┬──────────────────────────────────────┐    ║
║  │ 缩写 │     中文释义       │                描述                  │    ║
║  ├──────┼────────────────────┼──────────────────────────────────────┤    ║
║  │ MX   │ 测量模拟量值       │ 模拟量测量值(电流、电压、功率等)     │    ║
║  │ ST   │ 状态信息           │ 状态类数据(开关位置、保护动作等)     │    ║
║  │ CO   │ 控制               │ 控制操作类数据                       │    ║
║  │ CF   │ 配置               │ 配置参数(设备名称、版本信息等)       │    ║
║  │ DC   │ 描述               │ 描述性信息(设备描述、铭牌信息等)     │    ║
║  │ SG   │ 定值组             │ 定值组数据                           │    ║
║  │ SE   │ 定值组可编辑       │ 定值组编辑控制                       │    ║
║  │ SP   │ 设定点             │ 设定点控制                           │    ║
║  │ BR   │ 缓存报告           │ 缓存报告控制块                       │    ║
║  │ RP   │ 非缓存报告         │ 非缓存报告控制块                     │    ║
║  │ GO   │ GOOSE控制          │ GOOSE控制块                          │    ║
║  │ GS   │ GSSE控制           │ GSSE控制块                           │    ║
║  │ SV   │ 采样值替代         │ 采样值替代服务                       │    ║
║  │ MS   │ 多播采样值控制     │ 多播采样值控制                       │    ║
║  │ US   │ 单播采样值控制     │ 单播采样值控制                       │    ║
║  └──────┴────────────────────┴──────────────────────────────────────┘    ║
║                                                                          ║
║  逻辑节点类名(LN Class)前缀说明:                                          ║
║  ┌──────┬────────────────────┬──────────────────────────────────────┐    ║
║  │ 前缀 │     功能类型       │                示例                  │    ║
║  ├──────┼────────────────────┼──────────────────────────────────────┤    ║
║  │ L    │ 系统逻辑节点       │ LLN0(逻辑节点零), LPHD(物理装置)    │    ║
║  │ P    │ 保护功能           │ PDIF(差动), PDIS(距离), PTOC(过流)  │    ║
║  │ M    │ 测量计量           │ MMXU(测量), MMTR(计量)              │    ║
║  │ C    │ 监控控制           │ CSWI(开关控制), CILO(联锁)          │    ║
║  │ X    │ 开关设备           │ XCBR(断路器), XSWI(隔离开关)        │    ║
║  │ T    │ 互感器             │ TCTR(电流互感器), TVTR(电压互感器)  │    ║
║  │ Y    │ 电力变压器         │ YPTR(变压器)                        │    ║
║  │ G    │ 通用功能           │ GGIO(通用GOOSE I/O)                 │    ║
║  │ S    │ 传感器             │ STMP(温度传感器)                    │    ║
║  │ I    │ 输入输出接口       │ IHMI(人机接口), ITCI(远方控制)      │    ║
║  │ R    │ 保护相关           │ RREC(重合闸), RBRF(失灵保护)        │    ║
║  └──────┴────────────────────┴──────────────────────────────────────┘    ║
║                                                                          ║
║  常见数据对象(DO)名称说明:                                                ║
║  ┌──────────┬────────────────┬────────────────────────────────────┐      ║
║  │    名称   │    中文释义    │              描述                  │      ║
║  ├──────────┼────────────────┼────────────────────────────────────┤      ║
║  │ Beh      │ 行为           │ 设备运行行为                       │      ║
║  │ Mod      │ 模式           │ 设备运行模式                       │      ║
║  │ Health   │ 健康状况       │ 设备健康状态                       │      ║
║  │ stVal    │ 状态值         │ 状态信息值                         │      ║
║  │ q        │ 品质           │ 数据品质标志                       │      ║
║  │ t        │ 时间戳         │ 数据时间戳                         │      ║
║  │ ctlVal   │ 控制值         │ 控制命令值                         │      ║
║  │ ctlModel │ 控制模式       │ 控制方式(直接/SBO等)               │      ║
║  │ Pos      │ 位置           │ 开关/设备位置                      │      ║
║  │ Op       │ 动作           │ 保护动作                           │      ║
║  │ Str      │ 启动           │ 保护启动                           │      ║
║  └──────────┴────────────────┴────────────────────────────────────┘      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


def generate_semantic_report(results):
    """生成语义解析报告"""
    if not results:
        return {}

    resolver = AbbrResolver()

    ln_class_stats = defaultdict(lambda: {'count': 0, 'semantic': None})

    for result in results:
        for ied in result.get('ieds', []):
            for ld in ied.get('lDevices', []):
                ln0 = ld.get('ln0', {})
                if ln0 and ln0.get('lnClass'):
                    ln_class = ln0['lnClass']
                    ln_class_stats[ln_class]['count'] += 1
                    ln_class_stats[ln_class]['semantic'] = resolver.resolve_ln_class(ln_class)
                for ln in ld.get('lns', []):
                    if ln.get('lnClass'):
                        ln_class = ln['lnClass']
                        ln_class_stats[ln_class]['count'] += 1
                        ln_class_stats[ln_class]['semantic'] = resolver.resolve_ln_class(ln_class)

    fc_stats = defaultdict(lambda: {'count': 0, 'semantic': None})
    data_name_stats = defaultdict(lambda: {'count': 0, 'semantic': None})

    return {
        'total_files': len(results),
        'ln_class_semantics': dict(ln_class_stats),
        'fc_semantics': dict(fc_stats),
        'data_name_semantics': dict(data_name_stats),
        'abbreviation_reference': {
            'total_abbreviations': len(ABBREVIATIONS),
            'total_ln_classes': len(LN_CLASS_MAP),
            'total_fc_types': len(FC_DETAIL)
        }
    }


def print_ln_semantic_table(stats, limit=15):
    """打印逻辑节点语义对照表"""
    resolver = AbbrResolver()
    sorted_items = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:limit]

    print("\n逻辑节点语义对照表:")
    print("-" * 60)
    for ln_class, count in sorted_items:
        semantic = resolver.resolve_ln_class(ln_class)
        zh = semantic.get('zh', ln_class) if semantic else ln_class
        group = semantic.get('group', 'Unknown') if semantic else 'Unknown'
        print(f"  {ln_class:8s} | {zh:20s} | {group:15s} | 出现次数: {count}")