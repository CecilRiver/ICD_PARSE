"""
IEC 61850 ICD/CID 文件信息提取脚本

本脚本参考论文中PICS/EDE文件解析方法，从IEC 61850配置文件(ICD/CID)中提取结构化信息。

ICD (IED Configuration Description) - IED能力描述文件，描述设备支持的功能
CID (Configured IED Description) - IED配置描述文件，包含具体工程配置

提取的信息类型：
┌─────────────────────┬───────────────────────────────┐
│      信息类型       │             用途              │
├─────────────────────┼───────────────────────────────┤
│ IED基本信息         │ 设备身份识别（厂商、型号）    │
│ 通信配置            │ 网络参数（IP地址、子网）      │
│ 支持的服务          │ 定义允许的操作类型            │
│ 逻辑设备(LDevice)   │ 设备功能分区                  │
│ 逻辑节点(LN)        │ 具体功能模块（保护、测量等）  │
│ 数据集(DataSet)     │ 数据分组（用于报告/GOOSE）   │
│ 控制块              │ 报告/GOOSE发送配置            │
│ 数据对象(DOI)       │ 具体数据点及描述              │
│ 数据类型模板        │ 数据结构定义                  │
└─────────────────────┴───────────────────────────────┘
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import json
import csv
from datetime import datetime


class ICDParser:
    """IEC 61850 ICD/CID 文件解析器"""

    # IEC 61850 标准命名空间
    NS = {'scl': 'http://www.iec.ch/61850/2003/SCL'}

    def __init__(self, file_path):
        self.file_path = file_path
        self.tree = None
        self.root = None
        self.ns = self._detect_namespace()

    def _detect_namespace(self):
        """检测XML文件的命名空间"""
        try:
            # 先尝试解析一小部分来检测命名空间
            for event, elem in ET.iterparse(self.file_path, events=('start',)):
                if elem.tag.startswith('{'):
                    ns = elem.tag.split('}')[0] + '}'
                    return {'scl': ns[1:-1]}  # 去掉花括号
                break
        except:
            pass
        return self.NS

    def _find(self, elem, tag):
        """带命名空间查找元素"""
        return elem.find(f"{{{self.ns['scl']}}}{tag}")

    def _findall(self, elem, tag):
        """带命名空间查找所有元素"""
        return elem.findall(f"{{{self.ns['scl']}}}{tag}")

    def _get_attr(self, elem, attr, default=''):
        """安全获取属性值"""
        return elem.get(attr, default) if elem is not None else default

    def parse(self):
        """解析ICD文件"""
        try:
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
            return True
        except ET.ParseError as e:
            print(f"解析错误: {e}")
            return False

    def extract_header_info(self):
        """
        提取Header信息
        从文档顶部提取元数据信息
        """
        header = self._find(self.root, 'Header')
        if header is None:
            return {}

        info = {
            'id': self._get_attr(header, 'id'),
            'version': self._get_attr(header, 'version'),
            'revision': self._get_attr(header, 'revision'),
            'toolID': self._get_attr(header, 'toolID'),
            'nameStructure': self._get_attr(header, 'nameStructure')
        }

        # 提取历史记录
        history = self._find(header, 'History')
        if history:
            hitems = []
            for hitem in self._findall(history, 'Hitem'):
                hitems.append({
                    'version': self._get_attr(hitem, 'version'),
                    'revision': self._get_attr(hitem, 'revision'),
                    'when': self._get_attr(hitem, 'when'),
                    'who': self._get_attr(hitem, 'who'),
                    'what': self._get_attr(hitem, 'what')
                })
            info['history'] = hitems

        return info

    def extract_communication_info(self):
        """
        提取通信配置信息
        解析SubNetwork和ConnectedAP
        """
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return {}

        subnetworks = []
        for sub_net in self._findall(comm, 'SubNetwork'):
            sn_info = {
                'name': self._get_attr(sub_net, 'name'),
                'type': self._get_attr(sub_net, 'type'),
                'desc': self._get_attr(sub_net, 'desc')
            }

            # 提取连接点
            for conn_ap in self._findall(sub_net, 'ConnectedAP'):
                ap_info = {
                    'iedName': self._get_attr(conn_ap, 'iedName'),
                    'apName': self._get_attr(conn_ap, 'apName')
                }

                # 提取地址信息
                address = self._find(conn_ap, 'Address')
                if address:
                    addr_info = {}
                    for p in self._findall(address, 'P'):
                        addr_info[self._get_attr(p, 'type')] = p.text if p.text else ''
                    ap_info['address'] = addr_info

                # 提取GSE配置（GOOSE）
                for gse in self._findall(conn_ap, 'GSE'):
                    gse_info = {
                        'ldInst': self._get_attr(gse, 'ldInst'),
                        'cbName': self._get_attr(gse, 'cbName'),
                        'desc': self._get_attr(gse, 'desc')
                    }
                    gse_addr = self._find(gse, 'Address')
                    if gse_addr:
                        gse_addr_info = {}
                        for p in self._findall(gse_addr, 'P'):
                            gse_addr_info[self._get_attr(p, 'type')] = p.text if p.text else ''
                        gse_info['address'] = gse_addr_info
                    ap_info.setdefault('gse', []).append(gse_info)

                # 提取SMV配置（采样值）
                for smv in self._findall(conn_ap, 'SMV'):
                    smv_info = {
                        'ldInst': self._get_attr(smv, 'ldInst'),
                        'cbName': self._get_attr(smv, 'cbName'),
                        'desc': self._get_attr(smv, 'desc')
                    }
                    smv_addr = self._find(smv, 'Address')
                    if smv_addr:
                        smv_addr_info = {}
                        for p in self._findall(smv_addr, 'P'):
                            smv_addr_info[self._get_attr(p, 'type')] = p.text if p.text else ''
                        smv_info['address'] = smv_addr_info
                    ap_info.setdefault('smv', []).append(smv_info)

                sn_info.setdefault('connectedAPs', []).append(ap_info)

            subnetworks.append(sn_info)

        return {'subNetworks': subnetworks}

    def extract_ied_info(self):
        """
        提取IED基本信息
        从IED元素提取设备描述、厂商、型号等
        """
        ied = self._find(self.root, 'IED')
        if ied is None:
            return {}

        info = {
            'name': self._get_attr(ied, 'name'),
            'desc': self._get_attr(ied, 'desc'),
            'type': self._get_attr(ied, 'type'),
            'manufacturer': self._get_attr(ied, 'manufacturer'),
            'configVersion': self._get_attr(ied, 'configVersion'),
            'originalSclRevision': self._get_attr(ied, 'originalSclRevision'),
            'originalSclVersion': self._get_attr(ied, 'originalSclVersion')
        }

        # 提取Private信息（厂商扩展信息）
        for private in self._findall(ied, 'Private'):
            private_type = self._get_attr(private, 'type')
            if private_type:
                info.setdefault('private', []).append({
                    'type': private_type,
                    'content': private.text if private.text else ''
                })

        return info

    def extract_services_info(self):
        """
        提取IED支持的服务列表
        类似PICS中提取支持的BIBBs
        """
        ied = self._find(self.root, 'IED')
        if ied is None:
            return {}

        services = self._find(ied, 'Services')
        if services is None:
            return {}

        svc_list = []
        for child in services:
            tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            svc_info = {'name': tag_name}
            # 提取属性
            for attr, value in child.attrib.items():
                svc_info[attr] = value
            svc_list.append(svc_info)

        return {'services': svc_list}

    def extract_ldevice_info(self):
        """
        提取逻辑设备(LDevice)信息
        """
        ied = self._find(self.root, 'IED')
        if ied is None:
            return {}

        ldevices = []
        for ap in self._findall(ied, 'AccessPoint'):
            server = self._find(ap, 'Server')
            if server is None:
                continue

            for ld in self._findall(server, 'LDevice'):
                ld_info = {
                    'inst': self._get_attr(ld, 'inst'),
                    'desc': self._get_attr(ld, 'desc'),
                    'lnClass': self._get_attr(ld, 'lnClass'),
                    'lnInst': self._get_attr(ld, 'lnInst')
                }

                # 提取LN0（逻辑节点零）
                ln0 = self._find(ld, 'LN0')
                if ln0:
                    ld_info['ln0'] = self._extract_ln_info(ln0, is_ln0=True)

                # 提取所有LN
                lns = []
                for ln in self._findall(ld, 'LN'):
                    lns.append(self._extract_ln_info(ln))

                if lns:
                    ld_info['lns'] = lns

                ldevices.append(ld_info)

        return {'lDevices': ldevices}

    def _extract_ln_info(self, ln, is_ln0=False):
        """
        提取单个逻辑节点(LN)的详细信息
        """
        info = {
            'lnClass': self._get_attr(ln, 'lnClass'),
            'lnType': self._get_attr(ln, 'lnType'),
            'inst': self._get_attr(ln, 'inst'),
            'prefix': self._get_attr(ln, 'prefix'),
            'desc': self._get_attr(ln, 'desc')
        }

        # 提取数据集
        datasets = []
        for ds in self._findall(ln, 'DataSet'):
            ds_info = {
                'name': self._get_attr(ds, 'name'),
                'desc': self._get_attr(ds, 'desc')
            }
            fcdas = []
            for fcda in self._findall(ds, 'FCDA'):
                fcdas.append({
                    'ldInst': self._get_attr(fcda, 'ldInst'),
                    'lnClass': self._get_attr(fcda, 'lnClass'),
                    'lnInst': self._get_attr(fcda, 'lnInst'),
                    'prefix': self._get_attr(fcda, 'prefix'),
                    'doName': self._get_attr(fcda, 'doName'),
                    'daName': self._get_attr(fcda, 'daName'),
                    'fc': self._get_attr(fcda, 'fc')
                })
            if fcdas:
                ds_info['fcdas'] = fcdas
                ds_info['fcda_count'] = len(fcdas)
            datasets.append(ds_info)

        if datasets:
            info['datasets'] = datasets

        # 提取报告控制块
        report_ctrls = []
        for rc in self._findall(ln, 'ReportControl'):
            rc_info = {
                'name': self._get_attr(rc, 'name'),
                'rptID': self._get_attr(rc, 'rptID'),
                'datSet': self._get_attr(rc, 'datSet'),
                'confRev': self._get_attr(rc, 'confRev'),
                'bufTime': self._get_attr(rc, 'bufTime'),
                'buffered': self._get_attr(rc, 'buffered'),
                'desc': self._get_attr(rc, 'desc')
            }
            # 提取触发选项
            trg_ops = self._find(rc, 'TrgOps')
            if trg_ops:
                rc_info['trgOps'] = {
                    'dchg': self._get_attr(trg_ops, 'dchg'),
                    'qchg': self._get_attr(trg_ops, 'qchg'),
                    'dupd': self._get_attr(trg_ops, 'dupd'),
                    'period': self._get_attr(trg_ops, 'period'),
                    'gi': self._get_attr(trg_ops, 'gi')
                }
            # 提取可选字段
            opt_fields = self._find(rc, 'OptFields')
            if opt_fields:
                rc_info['optFields'] = dict(opt_fields.attrib)
            # 提取RptEnabled
            rpt_enabled = self._find(rc, 'RptEnabled')
            if rpt_enabled:
                rc_info['rptEnabled'] = {'max': self._get_attr(rpt_enabled, 'max')}
            report_ctrls.append(rc_info)

        if report_ctrls:
            info['reportControls'] = report_ctrls

        # 提取GOOSE控制块
        gse_ctrls = []
        for gc in self._findall(ln, 'GSEControl'):
            gc_info = {
                'name': self._get_attr(gc, 'name'),
                'datSet': self._get_attr(gc, 'datSet'),
                'appID': self._get_attr(gc, 'appID'),
                'desc': self._get_attr(gc, 'desc')
            }
            gse_ctrls.append(gc_info)

        if gse_ctrls:
            info['gseControls'] = gse_ctrls

        # 提取DOI（数据对象实例）
        dois = []
        for doi in self._findall(ln, 'DOI'):
            doi_info = self._extract_doi_info(doi)
            dois.append(doi_info)

        if dois:
            info['dois'] = dois

        return info

    def _extract_doi_info(self, doi):
        """
        提取DOI（数据对象实例）信息
        """
        info = {
            'name': self._get_attr(doi, 'name'),
            'desc': self._get_attr(doi, 'desc')
        }

        # 提取SDI（子数据实例）
        for sdi in self._findall(doi, 'SDI'):
            sdi_name = self._get_attr(sdi, 'name')
            info.setdefault('sdis', []).append({
                'name': sdi_name,
                'desc': self._get_attr(sdi, 'desc')
            })
            # 递归提取嵌套SDI
            nested_sdis = self._findall(sdi, 'SDI')
            if nested_sdis:
                self._extract_nested_sdi(sdi, info['sdis'][-1])

        # 提取DAI（数据属性实例）
        for dai in self._findall(doi, 'DAI'):
            dai_info = {
                'name': self._get_attr(dai, 'name'),
                'valKind': self._get_attr(dai, 'valKind'),
                'sAddr': self._get_attr(dai, 'sAddr')
            }
            val = self._find(dai, 'Val')
            if val and val.text:
                dai_info['value'] = val.text
            info.setdefault('dais', []).append(dai_info)

        return info

    def _extract_nested_sdi(self, parent, parent_info):
        """递归提取嵌套的SDI"""
        for sdi in self._findall(parent, 'SDI'):
            sdi_info = {
                'name': self._get_attr(sdi, 'name'),
                'desc': self._get_attr(sdi, 'desc')
            }
            parent_info.setdefault('nested_sdis', []).append(sdi_info)
            self._extract_nested_sdi(sdi, sdi_info)

        for dai in self._findall(parent, 'DAI'):
            dai_info = {
                'name': self._get_attr(dai, 'name'),
                'valKind': self._get_attr(dai, 'valKind'),
                'sAddr': self._get_attr(dai, 'sAddr')
            }
            val = self._find(dai, 'Val')
            if val and val.text:
                dai_info['value'] = val.text
            parent_info.setdefault('dais', []).append(dai_info)

    def extract_datatype_templates(self):
        """
        提取数据类型模板(DataTypeTemplates)
        定义数据结构和类型
        """
        dtt = self._find(self.root, 'DataTypeTemplates')
        if dtt is None:
            return {}

        templates = {}

        # 提取LNodeType（逻辑节点类型）
        ln_types = []
        for lnt in self._findall(dtt, 'LNodeType'):
            lnt_info = {
                'id': self._get_attr(lnt, 'id'),
                'lnClass': self._get_attr(lnt, 'lnClass'),
                'desc': self._get_attr(lnt, 'desc')
            }
            # 提取DO（数据对象）
            dos = []
            for do in self._findall(lnt, 'DO'):
                dos.append({
                    'name': self._get_attr(do, 'name'),
                    'type': self._get_attr(do, 'type'),
                    'desc': self._get_attr(do, 'desc'),
                    'accessControl': self._get_attr(do, 'accessControl'),
                    'transient': self._get_attr(do, 'transient')
                })
            if dos:
                lnt_info['dos'] = dos
            ln_types.append(lnt_info)

        templates['lnTypes'] = ln_types

        # 提取DOType（数据对象类型）
        do_types = []
        for dot in self._findall(dtt, 'DOType'):
            dot_info = {
                'id': self._get_attr(dot, 'id'),
                'desc': self._get_attr(dot, 'desc'),
                'cdc': self._get_attr(dot, 'cdc')  # Common Data Class
            }
            # 提取DA（数据属性）
            das = []
            for da in self._findall(dot, 'DA'):
                da_info = {
                    'name': self._get_attr(da, 'name'),
                    'type': self._get_attr(da, 'type'),
                    'desc': self._get_attr(da, 'desc'),
                    'fc': self._get_attr(da, 'fc'),  # Functional Constraint
                    'dchg': self._get_attr(da, 'dchg'),
                    'qchg': self._get_attr(da, 'qchg'),
                    'dupd': self._get_attr(da, 'dupd'),
                    'valKind': self._get_attr(da, 'valKind'),
                    'valImport': self._get_attr(da, 'valImport')
                }
                val = self._find(da, 'Val')
                if val and val.text:
                    da_info['value'] = val.text
                das.append(da_info)
            if das:
                dot_info['das'] = das
            do_types.append(dot_info)

        templates['doTypes'] = do_types

        # 提取DAType（数据属性类型）
        da_types = []
        for dat in self._findall(dtt, 'DAType'):
            dat_info = {
                'id': self._get_attr(dat, 'id'),
                'desc': self._get_attr(dat, 'desc')
            }
            # 提取BDA（基本数据属性）
            bdas = []
            for bda in self._findall(dat, 'BDA'):
                bda_info = {
                    'name': self._get_attr(bda, 'name'),
                    'type': self._get_attr(bda, 'type'),
                    'desc': self._get_attr(bda, 'desc'),
                    'sAddr': self._get_attr(bda, 'sAddr'),
                    'valKind': self._get_attr(bda, 'valKind'),
                    'valImport': self._get_attr(bda, 'valImport')
                }
                val = self._find(bda, 'Val')
                if val and val.text:
                    bda_info['value'] = val.text
                bdas.append(bda_info)
            if bdas:
                dat_info['bdas'] = bdas
            da_types.append(dat_info)

        templates['daTypes'] = da_types

        # 提取EnumType（枚举类型）
        enum_types = []
        for enum in self._findall(dtt, 'EnumType'):
            enum_info = {
                'id': self._get_attr(enum, 'id'),
                'desc': self._get_attr(enum, 'desc')
            }
            # 提取EnumVal
            enum_vals = []
            for ev in self._findall(enum, 'EnumVal'):
                enum_vals.append({
                    'ord': self._get_attr(ev, 'ord'),
                    'value': ev.text if ev.text else ''
                })
            if enum_vals:
                enum_info['values'] = enum_vals
            enum_types.append(enum_info)

        templates['enumTypes'] = enum_types

        return templates

    def extract_all(self):
        """
        提取所有信息
        类似论文中的完整解析流程
        """
        if not self.parse():
            return None

        result = {
            'file_path': str(self.file_path),
            'file_name': Path(self.file_path).name,
            'header': self.extract_header_info(),
            'communication': self.extract_communication_info(),
            'ied': self.extract_ied_info(),
            'services': self.extract_services_info(),
            'lDevices': self.extract_ldevice_info(),
            'dataTypeTemplates': self.extract_datatype_templates()
        }

        return result

    def extract_summary(self):
        """
        提取摘要信息（用于快速统计）
        """
        if not self.parse():
            return None

        result = {
            'file_name': Path(self.file_path).name,
            'ied_name': '',
            'ied_type': '',
            'manufacturer': '',
            'ldevice_count': 0,
            'ln_count': 0,
            'dataset_count': 0,
            'report_ctrl_count': 0,
            'gse_ctrl_count': 0,
            'ln_classes': []
        }

        # IED信息
        ied = self._find(self.root, 'IED')
        if ied:
            result['ied_name'] = self._get_attr(ied, 'name')
            result['ied_type'] = self._get_attr(ied, 'type')
            result['manufacturer'] = self._get_attr(ied, 'manufacturer')

        # 统计逻辑设备和逻辑节点
        ln_classes_set = set()
        if ied:
            for ap in self._findall(ied, 'AccessPoint'):
                server = self._find(ap, 'Server')
                if server:
                    for ld in self._findall(server, 'LDevice'):
                        result['ldevice_count'] += 1
                        # LN0
                        ln0 = self._find(ld, 'LN0')
                        if ln0:
                            result['ln_count'] += 1
                            ln_classes_set.add(self._get_attr(ln0, 'lnClass'))
                            # 统计数据集和控制块
                            result['dataset_count'] += len(self._findall(ln0, 'DataSet'))
                            result['report_ctrl_count'] += len(self._findall(ln0, 'ReportControl'))
                            result['gse_ctrl_count'] += len(self._findall(ln0, 'GSEControl'))
                        # 其他LN
                        for ln in self._findall(ld, 'LN'):
                            result['ln_count'] += 1
                            ln_classes_set.add(self._get_attr(ln, 'lnClass'))

        result['ln_classes'] = sorted(list(ln_classes_set))

        return result


class ICDExtractor:
    """
    ICD文件批量提取器
    处理目录中的所有ICD/CID文件
    """

    def __init__(self, input_dir, output_dir=None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir) if output_dir else self.input_dir.parent / 'output'

    def find_icd_files(self):
        """查找所有ICD/CID文件"""
        files = []
        for ext in ['*.icd', '*.ICD', '*.cid', '*.CID']:
            files.extend(self.input_dir.glob(ext))
        # 检查子目录
        for ext in ['**/*.icd', '**/*.ICD', '**/*.cid', '**/*.CID']:
            files.extend(self.input_dir.glob(ext))
        return sorted(set(files))

    def extract_all_files(self):
        """
        提取所有文件的完整信息（合并到一个列表）
        """
        files = self.find_icd_files()
        print(f"找到 {len(files)} 个ICD/CID文件")

        results = []
        for i, file_path in enumerate(files, 1):
            print(f"处理 [{i}/{len(files)}]: {file_path.name}")
            parser = ICDParser(file_path)
            result = parser.extract_all()
            if result:
                results.append(result)

        return results

    def extract_and_save_separately(self):
        """
        提取所有文件的完整信息，并分别保存到同名JSON文件
        保持输入目录的子目录结构
        例如：input/61850ICD/xxx.icd -> output/61850ICD/xxx.json
        """
        files = self.find_icd_files()
        print(f"找到 {len(files)} 个ICD/CID文件")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        success_count = 0

        for i, file_path in enumerate(files, 1):
            print(f"处理 [{i}/{len(files)}]: {file_path.name}")
            parser = ICDParser(file_path)
            result = parser.extract_all()
            if result:
                # 计算相对于输入目录的相对路径，保持子目录结构
                rel_path = file_path.relative_to(self.input_dir)
                # 生成同名JSON文件路径
                json_rel_path = rel_path.parent / (file_path.stem + '.json')
                json_path = self.output_dir / json_rel_path

                # 创建子目录
                json_path.parent.mkdir(parents=True, exist_ok=True)

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  -> 已保存: {json_rel_path}")
                success_count += 1

        print(f"\n成功提取并保存 {success_count} 个文件")
        return success_count

    def extract_summary_all(self):
        """
        提取所有文件的摘要信息
        生成统计报告
        """
        files = self.find_icd_files()
        print(f"找到 {len(files)} 个ICD/CID文件")

        summaries = []
        for i, file_path in enumerate(files, 1):
            print(f"处理 [{i}/{len(files)}]: {file_path.name}")
            parser = ICDParser(file_path)
            summary = parser.extract_summary()
            if summary:
                summaries.append(summary)

        return summaries

    def save_to_json(self, data, file_name):
        """保存结果到JSON文件"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / file_name
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"结果已保存: {output_path}")
        return output_path

    def save_summary_to_csv(self, summaries, file_name='icd_summary.csv'):
        """保存摘要到CSV文件"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / file_name

        if not summaries:
            print("无数据可保存")
            return None

        fieldnames = list(summaries[0].keys())

        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in summaries:
                # 将列表字段转为字符串
                row = {}
                for k, v in s.items():
                    if isinstance(v, list):
                        row[k] = ','.join(v)
                    else:
                        row[k] = v
                writer.writerow(row)

        print(f"摘要已保存: {output_path}")
        return output_path

    def generate_statistics_report(self, summaries):
        """
        生成统计报告
        类似论文中的PICS解析结果格式
        """
        if not summaries:
            return {}

        # 厂商统计
        manufacturers = defaultdict(int)
        for s in summaries:
            mfr = s.get('manufacturer', 'Unknown')
            manufacturers[mfr] += 1

        # LN类型统计
        ln_class_stats = defaultdict(int)
        for s in summaries:
            for ln_class in s.get('ln_classes', []):
                ln_class_stats[ln_class] += 1

        # 设备类型统计
        ied_types = defaultdict(int)
        for s in summaries:
            ied_type = s.get('ied_type', 'Unknown')
            ied_types[ied_type] += 1

        report = {
            'total_files': len(summaries),
            'manufacturer_distribution': dict(manufacturers),
            'ied_type_distribution': dict(ied_types),
            'ln_class_distribution': dict(ln_class_stats),
            'total_ldevices': sum(s.get('ldevice_count', 0) for s in summaries),
            'total_lns': sum(s.get('ln_count', 0) for s in summaries),
            'total_datasets': sum(s.get('dataset_count', 0) for s in summaries),
            'total_report_controls': sum(s.get('report_ctrl_count', 0) for s in summaries),
            'total_gse_controls': sum(s.get('gse_ctrl_count', 0) for s in summaries)
        }

        return report


def print_extraction_info():
    """
    显示提取信息说明
    类似论文Figure 8的解析流程说明
    """
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


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='IEC 61850 ICD/CID文件信息提取工具')
    parser.add_argument('input_dir', nargs='?', default='input', help='输入目录路径 (默认: input)')
    parser.add_argument('-o', '--output', help='输出目录路径', default=None)
    parser.add_argument('-m', '--mode', choices=['full', 'summary', 'stats'],
                        default='summary', help='提取模式：full(完整)/summary(摘要)/stats(统计)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    if args.verbose:
        print_extraction_info()

    extractor = ICDExtractor(args.input_dir, args.output)

    if args.mode == 'full':
        # 完整提取，每个文件单独保存
        extractor.extract_and_save_separately()

    elif args.mode == 'summary':
        # 摘要提取
        summaries = extractor.extract_summary_all()
        extractor.save_to_json(summaries, 'icd_summary.json')
        extractor.save_summary_to_csv(summaries)

        # 生成统计报告
        stats = extractor.generate_statistics_report(summaries)
        extractor.save_to_json(stats, 'icd_statistics.json')

        # 打印统计摘要
        print("\n" + "="*60)
        print("统计摘要")
        print("="*60)
        print(f"文件总数: {stats.get('total_files', 0)}")
        print(f"逻辑设备总数: {stats.get('total_ldevices', 0)}")
        print(f"逻辑节点总数: {stats.get('total_lns', 0)}")
        print(f"数据集总数: {stats.get('total_datasets', 0)}")
        print(f"报告控制块总数: {stats.get('total_report_controls', 0)}")
        print(f"GOOSE控制块总数: {stats.get('total_gse_controls', 0)}")
        print("\n厂商分布:")
        for mfr, count in stats.get('manufacturer_distribution', {}).items():
            print(f"  {mfr}: {count}")
        print("\nLN类型分布（前10）:")
        ln_stats = stats.get('ln_class_distribution', {})
        sorted_lns = sorted(ln_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for ln_class, count in sorted_lns:
            print(f"  {ln_class}: {count}")

    elif args.mode == 'stats':
        # 仅统计
        summaries = extractor.extract_summary_all()
        stats = extractor.generate_statistics_report(summaries)
        extractor.save_to_json(stats, 'icd_statistics.json')
        print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()