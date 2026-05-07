"""
IEC 61850 缩写语义解析器
基于 IEC 61850-2 标准
"""

import re
from icd_parse.abbr_dict import ABBREVIATIONS, LN_CLASS_MAP, FC_DETAIL


class AbbrResolver:
    """IEC 61850 缩写语义解析器"""

    def __init__(self):
        self.abbr_dict = ABBREVIATIONS
        self.ln_class_map = LN_CLASS_MAP
        self.fc_detail = FC_DETAIL

    def resolve_abbr(self, name):
        """
        解析缩写名称，返回语义解释
        支持部分匹配和组合缩写解析
        """
        if not name:
            return None

        # 直接匹配
        if name in self.abbr_dict:
            return {
                "abbr": name,
                "en": self.abbr_dict[name]["en"],
                "zh": self.abbr_dict[name]["zh"],
                "match_type": "exact"
            }

        # 尝试驼峰拆分匹配
        parts = self._split_camel_case(name)
        if len(parts) > 1:
            resolved_parts = []
            for part in parts:
                if part in self.abbr_dict:
                    resolved_parts.append({
                        "abbr": part,
                        "zh": self.abbr_dict[part]["zh"]
                    })
            if resolved_parts:
                combined_zh = "".join([p["zh"] for p in resolved_parts])
                return {
                    "abbr": name,
                    "en": name,
                    "zh": combined_zh,
                    "match_type": "combined",
                    "parts": resolved_parts
                }

        # 尝试前缀匹配
        for abbr in self.abbr_dict:
            if name.startswith(abbr) and len(abbr) >= 2:
                rest = name[len(abbr):]
                rest_resolved = self.resolve_abbr(rest)
                if rest_resolved:
                    return {
                        "abbr": name,
                        "zh": self.abbr_dict[abbr]["zh"] + rest_resolved["zh"],
                        "match_type": "prefix",
                        "parts": [abbr, rest]
                    }

        return None

    def resolve_ln_class(self, ln_class):
        """解析逻辑节点类名"""
        if not ln_class:
            return None

        if ln_class in self.ln_class_map:
            info = self.ln_class_map[ln_class]
            return {
                "lnClass": ln_class,
                "en": info["en"],
                "zh": info["zh"],
                "group": info["group"]
            }

        # 尝试前缀匹配
        prefix_map = {
            "P": {"zh": "保护功能", "group": "Protection"},
            "M": {"zh": "测量计量功能", "group": "Measuring"},
            "C": {"zh": "监控控制功能", "group": "Control"},
            "X": {"zh": "开关设备", "group": "Switchgear"},
            "T": {"zh": "互感器", "group": "Instrument Transformer"},
            "Y": {"zh": "电力变压器", "group": "Power Transformer"},
            "S": {"zh": "传感器", "group": "Sensor"},
            "I": {"zh": "输入输出接口", "group": "I/O"},
            "G": {"zh": "通用功能", "group": "Generic"},
            "R": {"zh": "保护相关功能", "group": "Protection"},
            "D": {"zh": "测量功能", "group": "Measuring"},
            "A": {"zh": "自动控制功能", "group": "Control"},
            "K": {"zh": "非电量测量", "group": "Sensor"},
            "F": {"zh": "熔断器", "group": "Switchgear"},
            "Q": {"zh": "电能质量", "group": "Measuring"},
            "L": {"zh": "系统逻辑节点", "group": "System"},
            "H": {"zh": "人机接口", "group": "I/O"},
            "N": {"zh": "网络通信", "group": "Communication"},
            "W": {"zh": "气象传感器", "group": "Sensor"},
            "Z": {"zh": "通信网关", "group": "Communication"},
        }

        for prefix, info in prefix_map.items():
            if ln_class.startswith(prefix):
                return {
                    "lnClass": ln_class,
                    "zh": f"{info['zh']}({ln_class})",
                    "group": info["group"],
                    "match_type": "prefix"
                }

        return {"lnClass": ln_class, "zh": ln_class, "match_type": "unknown"}

    def resolve_fc(self, fc):
        """解析功能约束"""
        if not fc:
            return None

        if fc in self.fc_detail:
            return {
                "fc": fc,
                "zh": self.fc_detail[fc]["zh"],
                "desc": self.fc_detail[fc]["desc"]
            }

        if fc in self.abbr_dict:
            return {
                "fc": fc,
                "zh": self.abbr_dict[fc]["zh"]
            }

        return {"fc": fc, "zh": fc}

    def resolve_data_name(self, name):
        """解析数据对象/数据属性名称"""
        if not name:
            return None

        if name in self.abbr_dict:
            return {
                "name": name,
                "zh": self.abbr_dict[name]["zh"],
                "match_type": "exact"
            }

        # 常见数据对象名称映射
        common_data_names = {
            "stVal": "状态值",
            "q": "品质",
            "t": "时间戳",
            "ctlVal": "控制值",
            "origin": "来源",
            "operTm": "操作时间",
            "ctlModel": "控制模式",
            "sbOpsRcv": "选择前操作接收",
            "sboTimeout": "SBO超时",
            "cancel": "取消",
            "pulseConfig": "脉冲配置",
            "pulseDur": "脉冲持续时间",
            "fbkNam": "反馈名称",
            "fbkEna": "反馈允许",
            "enbFail": "使能失败",
            "enabled": "已使能",
            "health": "健康状况",
            "mode": "模式",
            "beh": "行为",
            "eeClass": "错误事件类型",
            "eeNum": "错误事件编号",
            "eeCause": "错误事件原因",
            "eeDesc": "错误事件描述",
            "eeTime": "错误事件时间",
            "numSub": "订阅数",
            "cnt": "计数",
            "cntVal": "计数值",
            "prio": "优先级",
            "seqNum": "序列号",
            "timeStamp": "时间戳",
            "ndsCom": "needs Commissioning",
            "securityEnable": "安全使能",
            "goCbRef": "GOOSE控制块引用",
            "datSet": "数据集",
            "goID": "GOOSE标识",
            "confRev": "配置版本",
            "comms": "通信状态",
            "ndsSim": "模拟测试",
            "st": "状态",
            "test": "测试模式",
            "dst": "目标",
            "max": "最大",
            "min": "最小",
            "step": "步进",
            "incr": "增加",
            "decr": "减少",
            "first": "第一",
            "last": "最后",
            "next": "下一个",
            "prev": "上一个",
        }

        if name in common_data_names:
            return {
                "name": name,
                "zh": common_data_names[name],
                "match_type": "common"
            }

        result = self.resolve_abbr(name)
        if result:
            return {
                "name": name,
                "zh": result["zh"],
                "match_type": result["match_type"]
            }

        return {"name": name, "zh": name, "match_type": "unknown"}

    def _split_camel_case(self, name):
        """拆分驼峰命名的字符串"""
        pattern = r'([A-Z][a-z]*|[A-Z]+(?=[A-Z]|$))'
        parts = re.findall(pattern, name)
        return parts