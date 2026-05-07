"""
IEC 61850 缩写字典
基于 IEC 61850-2: Glossary (术语) 标准
包含英文缩写、全称及中文释义
"""

# IEC 61850-2 缩写字典
# 格式: {缩写: {"en": 英文全称, "zh": 中文释义, "source": 来源标准}}

ABBREVIATIONS = {
    # 逻辑节点类名相关
    "LN": {"en": "Logical Node", "zh": "逻辑节点", "source": "IEC 61850-1"},
    "LN0": {"en": "Logical Node Zero", "zh": "逻辑节点零", "source": "IEC 61850-7-1"},
    "LLN0": {"en": "Logical Node Zero", "zh": "逻辑节点零", "source": "IEC 61850-7-1"},
    "LPHD": {"en": "Logical Node PHysical Device", "zh": "逻辑节点物理装置", "source": "IEC 61850-7-1"},
    "LD": {"en": "Logical Device", "zh": "逻辑设备", "source": "IEC 61850-7-1"},
    "LD0": {"en": "Logical Device Zero", "zh": "逻辑设备零", "source": "IEC 61850-7-2"},
    "LNC": {"en": "Logical Node Class", "zh": "逻辑节点类", "source": "IEC 61850-7-2"},
    "LNG": {"en": "Logical Node Group", "zh": "逻辑节点组", "source": "IEC 61850-7-4"},
    "LNData": {"en": "Logical Node Data", "zh": "逻辑节点数据", "source": "IEC 61850-8-1"},

    # 功能约束
    "MX": {"en": "Measurand analogue value X", "zh": "测量模拟量值", "source": "IEC 61850-7-2"},
    "ST": {"en": "STatus Information", "zh": "状态信息", "source": "IEC 61850-7-2"},
    "CO": {"en": "ContrOl", "zh": "控制", "source": "IEC 61850-7-2"},
    "CF": {"en": "ConFiguration", "zh": "配置", "source": "IEC 61850-7-2"},
    "DC": {"en": "DesCripation", "zh": "描述", "source": "IEC 61850-7-2"},
    "EX": {"en": "Extended definition", "zh": "扩展定义", "source": "IEC 61850-7-2"},
    "LG": {"en": "LoGging", "zh": "日志", "source": "IEC 61850-7-2"},
    "BR": {"en": "Buffer Report", "zh": "缓存报告", "source": "IEC 61850-7-2"},
    "RP": {"en": "Unbuffered RePort", "zh": "非缓存报告", "source": "IEC 61850-7-2"},
    "SE": {"en": "Setting Group Editable", "zh": "定值组可编辑", "source": "IEC 61850-7-2"},
    "SG": {"en": "Setting Group", "zh": "定值组", "source": "IEC 61850-7-2"},
    "SP": {"en": "Set Point", "zh": "设定点", "source": "IEC 61850-7-2"},
    "SV": {"en": "Sampled Value", "zh": "采样值", "source": "IEC 61850-7-2"},
    "GS": {"en": "GSSE Control", "zh": "通用变电站状态事件控制", "source": "IEC 61850-7-2"},
    "GO": {"en": "GOose Control", "zh": "GOOSE控制", "source": "IEC 61850-7-2"},
    "US": {"en": "Unicast Sampled Value Control", "zh": "单播采样值控制", "source": "IEC 61850-7-2"},
    "MS": {"en": "Multicast Sampled value control", "zh": "多播采样值控制", "source": "IEC 61850-7-2"},

    # 数据对象/数据属性相关
    "DA": {"en": "Data Attribute", "zh": "数据属性", "source": "IEC 61850-7-2"},
    "DAT": {"en": "Data Attribute Type", "zh": "数据属性类型", "source": "IEC 61850-7-2"},
    "DO": {"en": "Data Object", "zh": "数据对象", "source": "IEC 61850-1"},
    "DOI": {"en": "Data Object Instance", "zh": "数据对象实例", "source": "IEC 61850-7-2"},
    "DAI": {"en": "Data Attribute Instance", "zh": "数据属性实例", "source": "IEC 61850-7-2"},
    "SDI": {"en": "Sub Data Instance", "zh": "子数据实例", "source": "IEC 61850-7-2"},
    "CDC": {"en": "Common Data Class", "zh": "共用数据类", "source": "IEC 61850-1"},
    "DS": {"en": "Data Set", "zh": "数据集", "source": "IEC 61850-7-2"},
    "FCD": {"en": "Functional Constrained Data", "zh": "功能约束数据", "source": "IEC 61850-7-2"},
    "FCDA": {"en": "Functional Constrained Data Attribute", "zh": "功能约束数据属性", "source": "IEC 61850-7-2"},

    # 控制块相关
    "BRCB": {"en": "Buffer Report Control Block", "zh": "缓存报告控制块", "source": "IEC 61850-7-2"},
    "URCB": {"en": "Unbuffered Report Control Block", "zh": "非缓存报告控制块", "source": "IEC 61850-7-2"},
    "GoCB": {"en": "Goose Control Block", "zh": "GOOSE控制块", "source": "IEC 61850-7-2"},
    "GsCB": {"en": "GSSE Control Block", "zh": "通用变电站状态事件控制块", "source": "IEC 61850-7-2"},
    "SGCB": {"en": "Setting Group Control Block", "zh": "定值组控制块", "source": "IEC 61850-7-2"},
    "MSVCB": {"en": "Multicast Sampled value control Block", "zh": "多播采样值控制块", "source": "IEC 61850-7-2"},
    "USVCB": {"en": "Unicast Sampled Value Control Block", "zh": "单播采样值控制块", "source": "IEC 61850-7-2"},
    "LCB": {"en": "Log Control Block", "zh": "日志控制块", "source": "IEC 61850-7-2"},

    # IED相关
    "IED": {"en": "Intelligent Electronic Device", "zh": "智能电子设备", "source": "IEC 61850-1"},
    "ICD": {"en": "IED Configuration Description", "zh": "IED能力描述文件", "source": "IEC 61850-10"},
    "CID": {"en": "Configured IED Description", "zh": "IED配置描述文件", "source": "IEC 61850-10"},
    "SCD": {"en": "Substation Configuration Description", "zh": "变电站配置描述", "source": "IEC 61850-10"},
    "IID": {"en": "IED Instantiation Description", "zh": "IED实例化描述", "source": "IEC 61850-10"},
    "SCL": {"en": "Substation Configuration description Language", "zh": "变电站配置描述语言", "source": "IEC 61850-1"},

    # GOOSE/GSE相关
    "GOOSE": {"en": "Generic Object Oriented Substation Events", "zh": "通用面向变电站事件对象", "source": "IEC 61850-5"},
    "GSE": {"en": "Generic Substation Event", "zh": "通用变电站事件", "source": "IEC 61850-7-2"},
    "GSSE": {"en": "Generic Substation Status Event", "zh": "通用变电站状态事件", "source": "IEC 61850-7-2"},
    "GSEM": {"en": "Generic Substation Event Model", "zh": "通用变电站事件模型", "source": "IEC 61850-7-2"},

    # 采样值相关
    "SMV": {"en": "Sampled Measured Value", "zh": "采样测量值", "source": "IEC 61850-6"},
    "SAV": {"en": "Sampled Analogue Value", "zh": "被采样模拟值", "source": "IEC 61850-9"},
    "MU": {"en": "Merging Unit", "zh": "合并单元", "source": "IEC 61850-9-1"},

    # 服务/接口相关
    "ACSI": {"en": "Abstract Communication Service Interface", "zh": "抽象通信服务接口", "source": "IEC 61850-1"},
    "SCSM": {"en": "Specific Communication Service Mapping", "zh": "特定通信服务映射", "source": "IEC 61850-1"},
    "MMS": {"en": "Manufacturing Message Specification", "zh": "制造报文规范", "source": "IEC 61850-5"},
    "API": {"en": "Application Program Interface", "zh": "应用程序接口", "source": "IEC 61850-7-1"},
    "SAP": {"en": "Service Access Point", "zh": "服务访问点", "source": "IEC 61850-8-1"},

    # 通信相关
    "LAN": {"en": "Local Area Network", "zh": "局域网", "source": "IEC 61850-5"},
    "TCP": {"en": "Transmission Control Protocol", "zh": "传输控制协议", "source": "IEC 61850-3"},
    "IP": {"en": "Internet Protocol", "zh": "网际协议", "source": "IEC 61850-3"},
    "OSI": {"en": "Open Systems Interconnection", "zh": "开放式系统互连", "source": "IEC 61850-1"},
    "MAC": {"en": "Media Access Control", "zh": "介质访问控制", "source": "IEC 61850-9-1"},
    "VLAN": {"en": "Virtual Local Area Network", "zh": "虚拟局域网", "source": "IEC 61850-9-2"},

    # 一致性测试相关
    "PICS": {"en": "Protocol Implementation Conformance Statement", "zh": "协议实现一致性陈述", "source": "IEC 61850-7-2"},
    "PIXIT": {"en": "Protocol Implementation eXtra Information for Testing", "zh": "测试用协议实现额外信息", "source": "IEC 61850-10"},
    "MICS": {"en": "Model Implementation Conformance Statement", "zh": "模型实现一致性陈述", "source": "IEC 61850-10"},
    "FAT": {"en": "Factory Acceptance Test", "zh": "工厂验收测试", "source": "IEC 61850-4"},
    "SAT": {"en": "Site Acceptance Test", "zh": "现场验收测试", "source": "IEC 61850-4"},

    # 变电站自动化系统
    "SAS": {"en": "Substation Automation System", "zh": "变电站自动化系统", "source": "IEC 61850-1"},
    "SA": {"en": "Substation Automation", "zh": "变电站自动化", "source": "IEC 61850-1"},
    "HMI": {"en": "Human Machine Interface", "zh": "人机接口", "source": "IEC 61850-3"},
    "RTU": {"en": "Remote Terminal Unit", "zh": "远方终端单元", "source": "IEC 61850-4"},
    "SCADA": {"en": "Supervisory Control and Data Acquisition", "zh": "数据采集与监控", "source": "IEC 61850-3"},
    "NCC": {"en": "Network Control Center", "zh": "电网控制中心", "source": "IEC 61850-5"},
    "TCI": {"en": "TeleControl Interface", "zh": "远方控制接口", "source": "IEC 61850-5"},
    "TMI": {"en": "TeleMonitoring Interface", "zh": "远方监视接口", "source": "IEC 61850-5"},

    # 设备相关
    "CB": {"en": "Circuit Breaker", "zh": "断路器", "source": "IEC 61850-1"},
    "CT": {"en": "Current Transformer/Transducer", "zh": "电流互感器/变送器", "source": "IEC 61850-4"},
    "VT": {"en": "Voltage Transformer/Transducer", "zh": "电压互感器/变送器", "source": "IEC 61850-4"},
    "ECT": {"en": "Electronic Current Transformer", "zh": "电子式电流互感器", "source": "IEC 61850-9-1"},
    "EVT": {"en": "Electronic Voltage Transformer", "zh": "电子式电压互感器", "source": "IEC 61850-9-1"},
    "GIS": {"en": "Gas Insulated Switchgear", "zh": "气体绝缘开关", "source": "IEC 61850-1"},
    "AIS": {"en": "Air Insulated Switchgear", "zh": "空气绝缘开关", "source": "IEC 61850-1"},
    "SF6": {"en": "Sulphur HexaFloride Gas", "zh": "六氟化硫气体", "source": "IEC 61850-3"},
    "LTC": {"en": "Load Tap Changer", "zh": "有载分接开关", "source": "IEC 61850-7-4"},

    # 保护功能相关
    "ACT": {"en": "Protection ACTivation information", "zh": "保护起动信息", "source": "IEC 61850-7-3"},
    "ACD": {"en": "ACtivation information of Direction protection", "zh": "方向保护起动信息", "source": "IEC 61850-7-3"},
    "Op": {"en": "Operate/Operating", "zh": "运行/动作", "source": "IEC 61850-7-4"},
    "Tr": {"en": "Trip", "zh": "跳闸", "source": "IEC 61850-7-4"},
    "Str": {"en": "Start", "zh": "启动", "source": "IEC 61850-7-4"},
    "Flt": {"en": "Fault", "zh": "故障", "source": "IEC 61850-7-4"},
    "EF": {"en": "Earth Fault", "zh": "接地故障", "source": "IEC 61850-7-4"},
    "FA": {"en": "Fault Arc", "zh": "故障电弧", "source": "IEC 61850-7-4"},
    "FD": {"en": "Fault Distance", "zh": "故障距离", "source": "IEC 61850-7-4"},

    # 状态/位置相关
    "Pos": {"en": "Position", "zh": "位置", "source": "IEC 61850-7-4"},
    "DPC": {"en": "Double Point Control", "zh": "双点控制", "source": "IEC 61850-7-2"},
    "DPS": {"en": "Double Point Status", "zh": "双点状态信息", "source": "IEC 61850-7-1"},
    "SPC": {"en": "Single Point Control", "zh": "单点控制", "source": "IEC 61850-7-4"},
    "SPS": {"en": "Single Point Status", "zh": "单点状态信息", "source": "IEC 61850-7-1"},
    "ISC": {"en": "Integer Step Controlled", "zh": "整数步进受控位置", "source": "IEC 61850-7-3"},
    "INC": {"en": "Integer status – Controllable", "zh": "整数状态—可控", "source": "IEC 61850-7-3"},
    "ISI": {"en": "Integer Status Information", "zh": "整数状态信息", "source": "IEC 61850-7-3"},

    # 测量相关
    "A": {"en": "Current in Amperes", "zh": "电流，单位：安培", "source": "IEC 61850-7-4"},
    "V": {"en": "Voltage", "zh": "电压", "source": "IEC 61850-7-4"},
    "W": {"en": "Watts active power", "zh": "瓦(有功功率)", "source": "IEC 61850-7-4"},
    "VA": {"en": "Volt Amperes", "zh": "伏安", "source": "IEC 61850-7-4"},
    "Var": {"en": "Volt Amperes Reactive", "zh": "乏", "source": "IEC 61850-7-4"},
    "Hz": {"en": "Hertz", "zh": "赫兹", "source": "IEC 61850-7-4"},
    "PF": {"en": "Power Factor", "zh": "功率因数", "source": "IEC 61850-7-4"},
    "Amp": {"en": "Current – non phase related", "zh": "电流(相别无关)", "source": "IEC 61850-7-4"},
    "Watt": {"en": "active power (non phase related)", "zh": "有功功率(相别无关)", "source": "IEC 61850-7-4"},
    "Vol": {"en": "Voltage (non phase related)", "zh": "电压(相别无关)", "source": "IEC 61850-7-4"},
    "Rms": {"en": "Root mean square", "zh": "均方根", "source": "IEC 61850-7-4"},
    "Rms": {"en": "Root mean square", "zh": "均方根", "source": "IEC 61850-7-4"},
    "Ph": {"en": "Phase", "zh": "相别", "source": "IEC 61850-7-4"},
    "PhPh": {"en": "Phase to Phase", "zh": "相间", "source": "IEC 61850-7-4"},
    "PP": {"en": "Phase to Phase", "zh": "相间", "source": "IEC 61850-7-4"},
    "PPV": {"en": "Phase to Phase Voltage", "zh": "相间电压", "source": "IEC 61850-7-4"},
    "H": {"en": "Harmonics (phase related)", "zh": "谐波(相别有关)", "source": "IEC 61850-7-4"},
    "Ha": {"en": "Harmonics (non phase related)", "zh": "谐波(相别无关)", "source": "IEC 61850-7-4"},
    "Thd": {"en": "Total harmonic distortion", "zh": "总谐波失真", "source": "IEC 61850-7-4"},
    "Td": {"en": "Total distortion", "zh": "总失真", "source": "IEC 61850-7-4"},

    # 阻抗/电阻/电抗相关
    "Z": {"en": "impedance", "zh": "阻抗", "source": "IEC 61850-7-4"},
    "Z0": {"en": "Zero sequence impedance", "zh": "零序阻抗", "source": "IEC 61850-7-4"},
    "Z1": {"en": "Positive sequence impedance", "zh": "正序阻抗", "source": "IEC 61850-7-4"},
    "R0": {"en": "Zero Sequence Resistance", "zh": "零序电阻", "source": "IEC 61850-7-4"},
    "R1": {"en": "Positive Sequence Resistance", "zh": "正序电阻", "source": "IEC 61850-7-4"},
    "X0": {"en": "Zero Sequence reactance", "zh": "零序电抗", "source": "IEC 61850-7-4"},
    "X1": {"en": "Positive Sequence Reactance", "zh": "正序电抗", "source": "IEC 61850-7-4"},
    "React": {"en": "Reactance", "zh": "电抗", "source": "IEC 61850-7-4"},
    "Rest": {"en": "Resistance", "zh": "电阻", "source": "IEC 61850-7-4"},
    "Imp": {"en": "Impedance (phase related)", "zh": "阻抗(相别有关)", "source": "IEC 61850-7-4"},

    # 时间相关
    "Tm": {"en": "Time", "zh": "时间", "source": "IEC 61850-7-4"},
    "Tmh": {"en": "Time in hours", "zh": "小时", "source": "IEC 61850-7-4"},
    "Tmm": {"en": "Time in minutes", "zh": "分钟", "source": "IEC 61850-7-4"},
    "Tms": {"en": "Time in seconds", "zh": "秒", "source": "IEC 61850-7-4"},
    "Tmms": {"en": "Time in milliseconds", "zh": "毫秒", "source": "IEC 61850-7-4"},
    "ms": {"en": "Milliseconds", "zh": "毫秒", "source": "IEC 61850-7-4"},
    "m": {"en": "Minutes", "zh": "分钟", "source": "IEC 61850-7-4"},
    "UTC": {"en": "Co-ordinated Universal Time", "zh": "协调世界时", "source": "IEC 61850-7-2"},
    "GPS": {"en": "Global Positioning System", "zh": "全球定位系统(时间源)", "source": "IEC 61850-5"},
    "SNTP": {"en": "Simple Network Time Protocol", "zh": "简单网络时间协议", "source": "IEC 61850-8-1"},
    "SoE": {"en": "Sequence of Events", "zh": "事件顺序", "source": "IEC 61850-7-1"},

    # 定值/设定相关
    "ASG": {"en": "Analog SettinG", "zh": "模拟量定值", "source": "IEC 61850-7-3"},
    "Set": {"en": "Setting", "zh": "定值/设定", "source": "IEC 61850-7-4"},
    "SGC": {"en": "Setting Group Control Class", "zh": "定值组控制类", "source": "IEC 61850-6"},

    # 触发选项
    "TrgOp": {"en": "Trigger Option", "zh": "触发选项", "source": "IEC 61850-7-2"},
    "dchg": {"en": "Trigger Option for data-change", "zh": "数据变化触发", "source": "IEC 61850-7-1"},
    "qchg": {"en": "Trigger Option for Quality-change", "zh": "品质变化触发", "source": "IEC 61850-7-2"},
    "dupd": {"en": "Trigger Option for data update", "zh": "数据更新触发", "source": "IEC 61850-7-2"},
    "fchg": {"en": "Trigger Option for Filtered-data change", "zh": "过滤数据变化触发", "source": "IEC 61850-7-2"},
    "Trg": {"en": "Trigger", "zh": "触发", "source": "IEC 61850-7-4"},

    # 控制/操作相关
    "Ctl": {"en": "Control", "zh": "控制", "source": "IEC 61850-7-4"},
    "SBO": {"en": "Select Before Operate", "zh": "操作前选择", "source": "IEC 61850-9-1"},
    "Cls": {"en": "Close", "zh": "合闸", "source": "IEC 61850-7-4"},
    "Opn": {"en": "Open", "zh": "分闸", "source": "IEC 61850-7-4"},
    "Blk": {"en": "Block/Blocked", "zh": "闭锁", "source": "IEC 61850-7-4"},
    "LO": {"en": "Lockout", "zh": "切断/分离", "source": "IEC 61850-7-4"},
    "Lok": {"en": "Locked", "zh": "锁住", "source": "IEC 61850-7-4"},
    "Inh": {"en": "Inhibit", "zh": "禁止", "source": "IEC 61850-7-4"},
    "Ena": {"en": "Enabled", "zh": "被允许", "source": "IEC 61850-7-4"},

    # 状态/品质
    "Beh": {"en": "Behaviour", "zh": "行为/性能", "source": "IEC 61850-7-4"},
    "Mod": {"en": "Mode", "zh": "模式", "source": "IEC 61850-7-4"},
    "Health": {"en": "Health", "zh": "健康状况", "source": "IEC 61850-7-4"},
    "stVal": {"en": "status Value", "zh": "状态值", "source": "IEC 61850-7-3"},
    "q": {"en": "quality", "zh": "品质", "source": "IEC 61850-7-3"},
    "t": {"en": "time", "zh": "时间戳", "source": "IEC 61850-7-3"},
    "ctlVal": {"en": "control Value", "zh": "控制值", "source": "IEC 61850-7-3"},
    "origin": {"en": "origin", "zh": "来源", "source": "IEC 61850-7-3"},

    # 报告相关
    "GI": {"en": "General Interrogation", "zh": "总查询", "source": "IEC 61850-7-2"},
    "RptID": {"en": "Report ID", "zh": "报告标识", "source": "IEC 61850-8-1"},
    "BufTime": {"en": "Buffer Time", "zh": "缓存时间", "source": "IEC 61850-7-2"},
    "ConfRev": {"en": "Configuration Revision", "zh": "配置版本", "source": "IEC 61850-7-2"},

    # GOOSE应用标识
    "AppID": {"en": "Application ID", "zh": "应用标识", "source": "IEC 61850-8-1"},

    # 描述/铭牌
    "NPL": {"en": "Name Plate", "zh": "铭牌", "source": "IEC 61850-7-2"},
    "Nam": {"en": "Name", "zh": "名称", "source": "IEC 61850-7-4"},
    "d": {"en": "description", "zh": "描述", "source": "IEC 61850-7-3"},
    "desc": {"en": "description", "zh": "描述", "source": "IEC 61850-7-3"},

    # 变压器相关
    "Tmp": {"en": "Temperature", "zh": "温度", "source": "IEC 61850-7-4"},
    "HP": {"en": "Hot Point", "zh": "热点", "source": "IEC 61850-7-4"},
    "To": {"en": "Top", "zh": "顶部", "source": "IEC 61850-7-4"},
    "Bo": {"en": "Bottom", "zh": "底部", "source": "IEC 61850-7-4"},
    "Lo": {"en": "Low", "zh": "低", "source": "IEC 61850-7-4"},
    "Hi": {"en": "High/Highest", "zh": "高/最高", "source": "IEC 61850-7-4"},
    "Avg": {"en": "Average", "zh": "平均", "source": "IEC 61850-7-4"},
    "MT": {"en": "Main Tank", "zh": "主油箱", "source": "IEC 61850-7-4"},
    "B": {"en": "Bushing", "zh": "套管", "source": "IEC 61850-7-4"},
    "CG": {"en": "Core Ground", "zh": "铁芯接地", "source": "IEC 61850-7-4"},
    "Ex": {"en": "Excitation", "zh": "激磁", "source": "IEC 61850-7-4"},
    "DEX": {"en": "De-Excitation", "zh": "去磁", "source": "IEC 61850-7-4"},

    # 压力/密度
    "Pres": {"en": "Pressure", "zh": "压力", "source": "IEC 61850-7-4"},
    "Den": {"en": "Density", "zh": "密度", "source": "IEC 61850-7-4"},
    "Mst": {"en": "Moisture", "zh": "潮湿", "source": "IEC 61850-7-4"},
    "H2": {"en": "Hydrogen", "zh": "氢气", "source": "IEC 61850-7-4"},

    # 电源/电池
    "Bat": {"en": "Battery", "zh": "电池", "source": "IEC 61850-7-4"},
    "Sup": {"en": "Supply", "zh": "电源", "source": "IEC 61850-7-4"},
    "Cha": {"en": "Charger", "zh": "充电器", "source": "IEC 61850-7-4"},
    "SCO": {"en": "Supply Change Over", "zh": "电源转换", "source": "IEC 61850-7-4"},

    # 电动机/泵/风扇
    "Mot": {"en": "Motor", "zh": "电动机", "source": "IEC 61850-7-4"},
    "Pmp": {"en": "Pump", "zh": "泵", "source": "IEC 61850-7-4"},
    "Fan": {"en": "Fan", "zh": "风扇", "source": "IEC 61850-7-4"},
    "Sp": {"en": "Speed", "zh": "速度", "source": "IEC 61850-7-4"},

    # 冷却设备
    "CE": {"en": "Cooling Equipment", "zh": "冷却设备", "source": "IEC 61850-7-4"},
    "Cir": {"en": "Circulating", "zh": "循环", "source": "IEC 61850-7-4"},
    "Thm": {"en": "Thermal", "zh": "热力学的", "source": "IEC 61850-7-4"},
    "Wrm": {"en": "Warm", "zh": "温暖", "source": "IEC 61850-7-4"},

    # 线路/潮流
    "Lin": {"en": "Line", "zh": "线路", "source": "IEC 61850-7-4"},
    "Flw": {"en": "Flow", "zh": "流动/潮流", "source": "IEC 61850-7-4"},
    "FPF": {"en": "Forward Power Flow", "zh": "正向潮流", "source": "IEC 61850-7-2"},
    "RPF": {"en": "Reverse Power Flow", "zh": "反向潮流", "source": "IEC 61850-7-4"},
    "Fwd": {"en": "Forward", "zh": "正向", "source": "IEC 61850-7-4"},
    "Rv": {"en": "Reverse", "zh": "反向", "source": "IEC 61850-7-4"},
    "LDC": {"en": "Line Drop Compensation", "zh": "线路压降补偿", "source": "IEC 61850-7-4"},

    # 接地/中性点
    "Gnd": {"en": "Ground", "zh": "地", "source": "IEC 61850-7-4"},
    "N": {"en": "Neutral", "zh": "中性点", "source": "IEC 61850-7-4"},
    "EC": {"en": "Earth Coil", "zh": "接地线圈", "source": "IEC 61850-7-4"},

    # 区域/区间
    "Zn": {"en": "Zone", "zh": "区间", "source": "IEC 61850-7-4"},
    "Zro": {"en": "Zero sequence method", "zh": "零序方法", "source": "IEC 61850-7-4"},
    "Zer": {"en": "Zero", "zh": "零", "source": "IEC 61850-7-4"},

    # 方向
    "Dir": {"en": "Directional", "zh": "方向", "source": "IEC 61850-7-4"},
    "Pol": {"en": "Polar", "zh": "极性", "source": "IEC 61850-7-4"},

    # 开关设备
    "Sw": {"en": "Switch", "zh": "开关", "source": "IEC 61850-7-4"},
    "Swg": {"en": "Swing", "zh": "振荡", "source": "IEC 61850-7-4"},

    # 统计/计数
    "Cnt": {"en": "Counter", "zh": "计数器", "source": "IEC 61850-7-4"},
    "Tot": {"en": "Total", "zh": "总的", "source": "IEC 61850-7-4"},
    "Ts": {"en": "Total Signed", "zh": "代数和", "source": "IEC 61850-7-4"},
    "Tu": {"en": "Total Unsigned", "zh": "绝对值和", "source": "IEC 61850-7-4"},
    "Stat": {"en": "Statistics", "zh": "统计", "source": "IEC 61850-7-4"},
    "Rcd": {"en": "Record", "zh": "记录", "source": "IEC 61850-7-4"},

    # 限值/范围
    "Lim": {"en": "Limit", "zh": "限值", "source": "IEC 61850-7-4"},
    "Rch": {"en": "Range", "zh": "范围", "source": "IEC 61850-7-4"},
    "Max": {"en": "Maximum", "zh": "最大", "source": "IEC 61850-7-4"},
    "Min": {"en": "Minimum", "zh": "最小", "source": "IEC 61850-7-4"},
    "Nom": {"en": "Nominal", "zh": "标称", "source": "IEC 61850-7-4"},
    "Rtg": {"en": "Rating", "zh": "额定值", "source": "IEC 61850-7-4"},

    # 超出/越限
    "Exc": {"en": "Exceeded", "zh": "超出", "source": "IEC 61850-7-4"},
    "Ov": {"en": "Over/Override/Overflow", "zh": "越过/覆盖/溢出", "source": "IEC 61850-7-4"},

    # 逻辑节点类名前缀 (IEC 61850-7-4定义的LN类)
    # 保护功能 P前缀
    # P: {"en": "Protection", "zh": "保护功能", "source": "IEC 61850-7-4"},

    # 测量计量 M前缀
    # M: {"en": "Measuring/Metering", "zh": "测量计量", "source": "IEC 61850-7-4"},

    # 监控 C前缀
    # C: {"en": "Control", "zh": "监控控制", "source": "IEC 61850-7-4"},

    # 开关设备 X前缀 (Switchgear)
    # X: {"en": "Switchgear", "zh": "开关设备", "source": "IEC 61850-7-4"},

    # 互感器 T前缀 (Instrument Transformer)
    # T: {"en": "Instrument Transformer", "zh": "互感器", "source": "IEC 61850-7-4"},

    # 电力变压器 Y前缀 (Power Transformer)
    # Y: {"en": "Power Transformer", "zh": "电力变压器", "source": "IEC 61850-7-4"},

    # 其他功能相关
    "Alm": {"en": "Alarm", "zh": "报警", "source": "IEC 61850-7-4"},
    "Wrn": {"en": "Warning", "zh": "告警", "source": "IEC 61850-7-4"},
    "Diag": {"en": "Diagnostics", "zh": "诊断", "source": "IEC 61850-7-4"},

    # 指示/输入输出
    "Ind": {"en": "Indication", "zh": "指示", "source": "IEC 61850-7-4"},
    "In": {"en": "Input", "zh": "输入", "source": "IEC 61850-7-4"},
    "Out": {"en": "Output", "zh": "输出", "source": "IEC 61850-7-4"},
    "I/O": {"en": "Input/Output", "zh": "输入/输出", "source": "IEC 61850-5"},

    # 值/数量
    "Val": {"en": "Value", "zh": "值", "source": "IEC 61850-7-4"},
    "Vlv": {"en": "Value", "zh": "值", "source": "IEC 61850-7-4"},
    "Qty": {"en": "Quality", "zh": "品质", "source": "IEC 61850-7-4"},
    "Num": {"en": "Number", "zh": "编号", "source": "IEC 61850-7-4"},

    # 同步/同期
    "Syn": {"en": "Synchronisation", "zh": "同步", "source": "IEC 61850-7-4"},

    # 其他常用缩写
    "XX": {"en": "Wildcard characters", "zh": "通配符", "source": "IEC 61850-7-2"},
    "M/O": {"en": "Mandatory or Optional", "zh": "指定或可选", "source": "IEC 61850-7-4"},
    "M": {"en": "Mandatory", "zh": "指定/强制", "source": "IEC 61850-7-2"},
    "O": {"en": "Optional", "zh": "可选", "source": "IEC 61850-7-2"},
    "Tx": {"en": "Transmit", "zh": "发送", "source": "IEC 61850-7-4"},
    "Rx": {"en": "Receive", "zh": "接收", "source": "IEC 61850-7-4"},
    "Src": {"en": "Source", "zh": "源", "source": "IEC 61850-7-4"},
    "Ref": {"en": "Reference", "zh": "引用", "source": "IEC 61850-7-2"},

    # 协议数据单元
    "PDU": {"en": "Protocol Data Unit", "zh": "协议数据单元", "source": "IEC 61850-7-2"},
    "ASDU": {"en": "Application Service Data Unit", "zh": "应用服务数据单元", "source": "IEC 61850-1"},
    "APDU": {"en": "Application Protocol Data Unit", "zh": "应用协议数据单元", "source": "IEC 61850-9-2"},
    "LSDU": {"en": "Link layer Service Data Unit", "zh": "链路层服务数据单元", "source": "IEC 61850-9-1"},

    # CRC校验
    "CRC": {"en": "Cyclic Redundancy Check", "zh": "循环冗余校验", "source": "IEC 61850-2"},

    # 标准化组织
    "IEC": {"en": "International Electrotechnical Commission", "zh": "国际电工委员会", "source": "IEC 61850-1"},
    "ISO": {"en": "International Standard Organisation", "zh": "国际标准化组织", "source": "IEC 61850-1"},
    "IEEE": {"en": "Institute of Electrical and Electronic Engineers", "zh": "电气电子工程师协会", "source": "IEC 61850-1"},

    # XML相关
    "XML": {"en": "eXtensible Mark-up Language", "zh": "可扩展标志语言", "source": "IEC 61850-1"},
    "DTD": {"en": "Document Type Definition", "zh": "文件类型定义", "source": "IEC 61850-6"},
    "UML": {"en": "Unified Modelling Language", "zh": "统一建模语言", "source": "IEC 61850-7-1"},
    "ASN.1": {"en": "Abstract Syntax Notation one", "zh": "抽象语法标志1", "source": "IEC 61850-7-1"},

    # 其他
    "Vac": {"en": "Vacuum", "zh": "真空", "source": "IEC 61850-7-4"},
    "Wac": {"en": "Watchdog", "zh": "监视器", "source": "IEC 61850-7-4"},
    "LED": {"en": "Light Emitting Diode", "zh": "光发射二极管", "source": "IEC 61850-7-4"},
    "Mem": {"en": "Memory", "zh": "存储器", "source": "IEC 61850-7-4"},
    "Cap": {"en": "Capability", "zh": "能力", "source": "IEC 61850-7-4"},
    "Len": {"en": "Length", "zh": "长度", "source": "IEC 61850-7-4"},
    "Wid": {"en": "Width", "zh": "宽", "source": "IEC 61850-7-4"},
    "Win": {"en": "Windows", "zh": "窗口", "source": "IEC 61850-7-4"},
}

# 逻辑节点类名映射 (IEC 61850-7-4)
LN_CLASS_MAP = {
    # 系统逻辑节点
    "LLN0": {"en": "Logical Node Zero", "zh": "逻辑节点零(系统逻辑节点)", "group": "System"},
    "LPHD": {"en": "Logical Node Physical Device", "zh": "物理装置逻辑节点", "group": "System"},

    # 保护功能 P系列
    "PDIF": {"en": "Differential Protection", "zh": "差动保护", "group": "Protection"},
    "PDIS": {"en": "Distance Protection", "zh": "距离保护", "group": "Protection"},
    "PDIR": {"en": "Directional Protection", "zh": "方向保护", "group": "Protection"},
    "PTOC": {"en": "Time Overcurrent Protection", "zh": "定时限过流保护", "group": "Protection"},
    "PIOC": {"en": "Instantaneous Overcurrent Protection", "zh": "瞬时过流保护", "group": "Protection"},
    "PTUV": {"en": "Time Undervoltage Protection", "zh": "定时限欠压保护", "group": "Protection"},
    "PTOV": {"en": "Time Overvoltage Protection", "zh": "定时限过压保护", "group": "Protection"},
    "PDUP": {"en": "Directional Under Power Protection", "zh": "逆功率保护", "group": "Protection"},
    "PDOP": {"en": "Directional Over Power Protection", "zh": "方向过功率保护", "group": "Protection"},
    "PPRF": {"en": "Power Protection", "zh": "功率保护", "group": "Protection"},
    "PZOP": {"en": "Zero Sequence Overvoltage Protection", "zh": "零序过压保护", "group": "Protection"},
    "PSCH": {"en": "Schematic Protection", "zh": "保护方案", "group": "Protection"},
    "PTRC": {"en": "Trip Conditioning", "zh": "跳闸条件", "group": "Protection"},
    "RREC": {"en": "Reclosing", "zh": "重合闸", "group": "Protection"},
    "RBRF": {"en": "Breaker Failure Protection", "zh": "断路器失灵保护", "group": "Protection"},

    # 测量计量 M系列
    "MMXU": {"en": "Measurement", "zh": "测量值", "group": "Measuring"},
    "MMTR": {"en": "Metering", "zh": "计量", "group": "Measuring"},
    "MHAI": {"en": "Harmonic Analysis", "zh": "谐波分析", "group": "Measuring"},
    "MVIZ": {"en": "Visual Indication", "zh": "可视化指示", "group": "Measuring"},

    # 监控控制 C系列
    "CILO": {"en": "Interlocking", "zh": "联锁", "group": "Control"},
    "CSWI": {"en": "Switch Control", "zh": "开关控制", "group": "Control"},
    "CPOW": {"en": "Power Control", "zh": "功率控制", "group": "Control"},
    "CCAP": {"en": "Capacitor Control", "zh": "电容器控制", "group": "Control"},
    "CALH": {"en": "Alarm Handling", "zh": "报警处理", "group": "Control"},
    "CST": {"en": "Status Control", "zh": "状态控制", "group": "Control"},

    # 开关设备 X系列
    "XCBR": {"en": "Circuit Breaker", "zh": "断路器", "group": "Switchgear"},
    "XSWI": {"en": "Switch", "zh": "隔离开关", "group": "Switchgear"},

    # 互感器 T系列
    "TCTR": {"en": "Current Transformer", "zh": "电流互感器", "group": "Instrument Transformer"},
    "TVTR": {"en": "Voltage Transformer", "zh": "电压互感器", "group": "Instrument Transformer"},

    # 电力变压器 Y系列
    "YPTR": {"en": "Power Transformer", "zh": "电力变压器", "group": "Power Transformer"},
    "YEFN": {"en": "Earth Fault Neutralizer", "zh": "接地故障中性点装置", "group": "Power Transformer"},

    # 传感器 S系列
    "SARC": {"en": "Arc Protection", "zh": "电弧保护", "group": "Sensor"},
    "SIMG": {"en": "Image Sensor", "zh": "图像传感器", "group": "Sensor"},
    "SIML": {"en": "Light Sensor", "zh": "光照传感器", "group": "Sensor"},
    "STMP": {"en": "Temperature Sensor", "zh": "温度传感器", "group": "Sensor"},

    # 输入输出 I系列
    "IARC": {"en": "Arc Detector Input", "zh": "电弧检测输入", "group": "I/O"},
    "IHMI": {"en": "Human Machine Interface", "zh": "人机接口", "group": "I/O"},
    "ITCI": {"en": "Telecontrol Interface", "zh": "远方控制接口", "group": "I/O"},
    "ITMI": {"en": "Telemetry Interface", "zh": "远方监视接口", "group": "I/O"},

    # 通用功能 G系列
    "GGIO": {"en": "Generic GOOSE I/O", "zh": "通用GOOSE输入输出", "group": "Generic"},
    "GAPC": {"en": "Generic Automatic Process Control", "zh": "通用自动过程控制", "group": "Generic"},

    # 合并单元 M系列(MU)
    "MSVC": {"en": "Merging Unit", "zh": "合并单元", "group": "Merging Unit"},
}

# 功能约束详解
FC_DETAIL = {
    "MX": {"zh": "测量值", "desc": "模拟量测量值，如电流、电压、功率等"},
    "ST": {"zh": "状态信息", "desc": "状态类数据，如开关位置、保护动作状态等"},
    "CO": {"zh": "控制", "desc": "控制操作类数据，如控制命令、控制模式等"},
    "CF": {"zh": "配置", "desc": "配置参数，如设备名称、版本信息等"},
    "DC": {"zh": "描述", "desc": "描述性信息，如设备描述、铭牌信息等"},
    "EX": {"zh": "扩展定义", "desc": "厂商自定义扩展数据"},
    "LG": {"zh": "日志", "desc": "日志控制相关数据"},
    "BR": {"zh": "缓存报告", "desc": "缓存报告控制块相关数据"},
    "RP": {"zh": "非缓存报告", "desc": "非缓存报告控制块相关数据"},
    "SE": {"zh": "定值组可编辑", "desc": "定值组编辑控制"},
    "SG": {"zh": "定值组", "desc": "定值组数据"},
    "SP": {"zh": "设定点", "desc": "设定点控制"},
    "SV": {"zh": "采样值替代", "desc": "采样值替代服务"},
    "GS": {"zh": "GSSE控制", "desc": "通用变电站状态事件控制"},
    "GO": {"zh": "GOOSE控制", "desc": "通用面向变电站事件对象控制"},
    "US": {"zh": "单播采样值", "desc": "单播采样值控制"},
    "MS": {"zh": "多播采样值", "desc": "多播采样值控制"},
}