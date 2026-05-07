"""
IEC 61850 ICD/CID 文件解析器
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from icd_parse.abbr_resolver import AbbrResolver


class ICDParser:
    """IEC 61850 ICD/CID 文件解析器"""

    NS = {'scl': 'http://www.iec.ch/61850/2003/SCL'}

    def __init__(self, file_path, enable_semantic=True):
        self.file_path = file_path
        self.tree = None
        self.root = None
        self.ns = self._detect_namespace()
        self.enable_semantic = enable_semantic
        self.abbr_resolver = AbbrResolver() if enable_semantic else None

    def _detect_namespace(self):
        """检测XML文件的命名空间"""
        try:
            for event, elem in ET.iterparse(self.file_path, events=('start',)):
                if elem.tag.startswith('{'):
                    ns = elem.tag.split('}')[0] + '}'
                    return {'scl': ns[1:-1]}
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
        """提取Header信息"""
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
        """提取通信配置信息"""
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

            for conn_ap in self._findall(sub_net, 'ConnectedAP'):
                ap_info = {
                    'iedName': self._get_attr(conn_ap, 'iedName'),
                    'apName': self._get_attr(conn_ap, 'apName')
                }

                address = self._find(conn_ap, 'Address')
                if address:
                    addr_info = {}
                    for p in self._findall(address, 'P'):
                        addr_info[self._get_attr(p, 'type')] = p.text if p.text else ''
                    ap_info['address'] = addr_info

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
        """提取IED基本信息"""
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

        for private in self._findall(ied, 'Private'):
            private_type = self._get_attr(private, 'type')
            if private_type:
                info.setdefault('private', []).append({
                    'type': private_type,
                    'content': private.text if private.text else ''
                })

        return info

    def extract_services_info(self):
        """提取IED支持的服务列表"""
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
            for attr, value in child.attrib.items():
                svc_info[attr] = value
            svc_list.append(svc_info)

        return {'services': svc_list}

    def extract_ldevice_info(self):
        """提取逻辑设备(LDevice)信息"""
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

                ln0 = self._find(ld, 'LN0')
                if ln0:
                    ld_info['ln0'] = self._extract_ln_info(ln0, is_ln0=True)

                lns = []
                for ln in self._findall(ld, 'LN'):
                    lns.append(self._extract_ln_info(ln))

                if lns:
                    ld_info['lns'] = lns

                ldevices.append(ld_info)

        return {'lDevices': ldevices}

    def _extract_ln_info(self, ln, is_ln0=False):
        """提取单个逻辑节点(LN)的详细信息"""
        info = {
            'lnClass': self._get_attr(ln, 'lnClass'),
            'lnType': self._get_attr(ln, 'lnType'),
            'inst': self._get_attr(ln, 'inst'),
            'prefix': self._get_attr(ln, 'prefix'),
            'desc': self._get_attr(ln, 'desc')
        }

        # 语义解析
        if self.abbr_resolver and info['lnClass']:
            info['lnClass_semantic'] = self.abbr_resolver.resolve_ln_class(info['lnClass'])

        # 提取数据集
        datasets = []
        for ds in self._findall(ln, 'DataSet'):
            ds_info = {
                'name': self._get_attr(ds, 'name'),
                'desc': self._get_attr(ds, 'desc')
            }
            if self.abbr_resolver and ds_info['name']:
                ds_info['name_semantic'] = self.abbr_resolver.resolve_data_name(ds_info['name'])

            fcdas = []
            for fcda in self._findall(ds, 'FCDA'):
                fcda_info = {
                    'ldInst': self._get_attr(fcda, 'ldInst'),
                    'lnClass': self._get_attr(fcda, 'lnClass'),
                    'lnInst': self._get_attr(fcda, 'lnInst'),
                    'prefix': self._get_attr(fcda, 'prefix'),
                    'doName': self._get_attr(fcda, 'doName'),
                    'daName': self._get_attr(fcda, 'daName'),
                    'fc': self._get_attr(fcda, 'fc')
                }
                if self.abbr_resolver:
                    if fcda_info['lnClass']:
                        fcda_info['lnClass_semantic'] = self.abbr_resolver.resolve_ln_class(fcda_info['lnClass'])
                    if fcda_info['doName']:
                        fcda_info['doName_semantic'] = self.abbr_resolver.resolve_data_name(fcda_info['doName'])
                    if fcda_info['daName']:
                        fcda_info['daName_semantic'] = self.abbr_resolver.resolve_data_name(fcda_info['daName'])
                    if fcda_info['fc']:
                        fcda_info['fc_semantic'] = self.abbr_resolver.resolve_fc(fcda_info['fc'])
                fcdas.append(fcda_info)

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
            trg_ops = self._find(rc, 'TrgOps')
            if trg_ops:
                rc_info['trgOps'] = {
                    'dchg': self._get_attr(trg_ops, 'dchg'),
                    'qchg': self._get_attr(trg_ops, 'qchg'),
                    'dupd': self._get_attr(trg_ops, 'dupd'),
                    'period': self._get_attr(trg_ops, 'period'),
                    'gi': self._get_attr(trg_ops, 'gi')
                }
            opt_fields = self._find(rc, 'OptFields')
            if opt_fields:
                rc_info['optFields'] = dict(opt_fields.attrib)
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

        # 提取DOI
        dois = []
        for doi in self._findall(ln, 'DOI'):
            doi_info = self._extract_doi_info(doi)
            dois.append(doi_info)

        if dois:
            info['dois'] = dois

        return info

    def _extract_doi_info(self, doi):
        """提取DOI信息"""
        info = {
            'name': self._get_attr(doi, 'name'),
            'desc': self._get_attr(doi, 'desc')
        }

        if self.abbr_resolver and info['name']:
            info['name_semantic'] = self.abbr_resolver.resolve_data_name(info['name'])

        for sdi in self._findall(doi, 'SDI'):
            sdi_name = self._get_attr(sdi, 'name')
            info.setdefault('sdis', []).append({
                'name': sdi_name,
                'desc': self._get_attr(sdi, 'desc')
            })
            nested_sdis = self._findall(sdi, 'SDI')
            if nested_sdis:
                self._extract_nested_sdi(sdi, info['sdis'][-1])

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
        """提取数据类型模板"""
        dtt = self._find(self.root, 'DataTypeTemplates')
        if dtt is None:
            return {}

        templates = {}

        # 提取LNodeType
        ln_types = []
        for lnt in self._findall(dtt, 'LNodeType'):
            lnt_info = {
                'id': self._get_attr(lnt, 'id'),
                'lnClass': self._get_attr(lnt, 'lnClass'),
                'desc': self._get_attr(lnt, 'desc')
            }
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

        # 提取DOType
        do_types = []
        for dot in self._findall(dtt, 'DOType'):
            dot_info = {
                'id': self._get_attr(dot, 'id'),
                'desc': self._get_attr(dot, 'desc'),
                'cdc': self._get_attr(dot, 'cdc')
            }
            das = []
            for da in self._findall(dot, 'DA'):
                da_info = {
                    'name': self._get_attr(da, 'name'),
                    'type': self._get_attr(da, 'type'),
                    'desc': self._get_attr(da, 'desc'),
                    'fc': self._get_attr(da, 'fc'),
                    'dchg': self._get_attr(da, 'dchg'),
                    'qchg': self._get_attr(da, 'qchg'),
                    'dupd': self._get_attr(da, 'dupd'),
                    'valKind': self._get_attr(da, 'valKind'),
                    'valImport': self._get_attr(da, 'valImport')
                }
                if self.abbr_resolver:
                    if da_info['name']:
                        da_info['name_semantic'] = self.abbr_resolver.resolve_data_name(da_info['name'])
                    if da_info['fc']:
                        da_info['fc_semantic'] = self.abbr_resolver.resolve_fc(da_info['fc'])
                val = self._find(da, 'Val')
                if val and val.text:
                    da_info['value'] = val.text
                das.append(da_info)
            if das:
                dot_info['das'] = das
            if self.abbr_resolver and dot_info['cdc']:
                dot_info['cdc_semantic'] = self.abbr_resolver.resolve_abbr(dot_info['cdc'])
            do_types.append(dot_info)
        templates['doTypes'] = do_types

        # 提取DAType
        da_types = []
        for dat in self._findall(dtt, 'DAType'):
            dat_info = {
                'id': self._get_attr(dat, 'id'),
                'desc': self._get_attr(dat, 'desc')
            }
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

        # 提取EnumType
        enum_types = []
        for enum in self._findall(dtt, 'EnumType'):
            enum_info = {
                'id': self._get_attr(enum, 'id'),
                'desc': self._get_attr(enum, 'desc')
            }
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
        """提取所有信息"""
        if not self.parse():
            return None

        return {
            'file_path': str(self.file_path),
            'file_name': Path(self.file_path).name,
            'header': self.extract_header_info(),
            'communication': self.extract_communication_info(),
            'ied': self.extract_ied_info(),
            'services': self.extract_services_info(),
            'lDevices': self.extract_ldevice_info(),
            'dataTypeTemplates': self.extract_datatype_templates()
        }

    def extract_summary(self):
        """提取摘要信息"""
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

        ied = self._find(self.root, 'IED')
        if ied:
            result['ied_name'] = self._get_attr(ied, 'name')
            result['ied_type'] = self._get_attr(ied, 'type')
            result['manufacturer'] = self._get_attr(ied, 'manufacturer')

        ln_classes_set = set()
        if ied:
            for ap in self._findall(ied, 'AccessPoint'):
                server = self._find(ap, 'Server')
                if server:
                    for ld in self._findall(server, 'LDevice'):
                        result['ldevice_count'] += 1
                        ln0 = self._find(ld, 'LN0')
                        if ln0:
                            result['ln_count'] += 1
                            ln_classes_set.add(self._get_attr(ln0, 'lnClass'))
                            result['dataset_count'] += len(self._findall(ln0, 'DataSet'))
                            result['report_ctrl_count'] += len(self._findall(ln0, 'ReportControl'))
                            result['gse_ctrl_count'] += len(self._findall(ln0, 'GSEControl'))
                        for ln in self._findall(ld, 'LN'):
                            result['ln_count'] += 1
                            ln_classes_set.add(self._get_attr(ln, 'lnClass'))

        result['ln_classes'] = sorted(list(ln_classes_set))
        return result