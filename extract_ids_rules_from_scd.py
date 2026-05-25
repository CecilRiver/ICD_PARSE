"""
IEC 61850 入侵检测规则提取器（直接从 SCD 文件提取，输出规范化规则）

每条规则为扁平结构，包含：
- rule_id: 全局唯一标识
- severity: critical / high / medium / low / info
- category: 规则类别
- protocol: GOOSE / SMV / MMS
- description: 人类可读的规则描述
- condition: 匹配条件（字段→期望值）
- action: 告警动作（alert / block / log）
- reference: 相关标准
"""

import xml.etree.ElementTree as ET
import json
import argparse
from pathlib import Path
from collections import defaultdict


class SCDDirectExtractor:
    def __init__(self, scd_path):
        self.scd_path = Path(scd_path)
        self.tree = ET.parse(scd_path)
        self.root = self.tree.getroot()
        self.ns = self._detect_namespace()

    def _detect_namespace(self):
        if self.root.tag.startswith('{'):
            ns = self.root.tag.split('}')[0] + '}'
            return ns
        return ''

    def _find(self, elem, tag):
        return elem.find(f'{self.ns}{tag}')

    def _findall(self, elem, tag):
        return elem.findall(f'{self.ns}{tag}')

    def _attr(self, elem, name, default=''):
        return elem.get(name, default) if elem is not None else default

    # ── 原始数据提取（内部方法）──

    def _extract_goose_raw(self):
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return []

        results = []
        for sn in self._findall(comm, 'SubNetwork'):
            sn_name = self._attr(sn, 'name')
            sn_type = self._attr(sn, 'type')
            for ap in self._findall(sn, 'ConnectedAP'):
                ied_name = self._attr(ap, 'iedName')
                for gse in self._findall(ap, 'GSE'):
                    addr = self._find(gse, 'Address')
                    addr_info = {}
                    if addr:
                        for p in self._findall(addr, 'P'):
                            addr_info[self._attr(p, 'type')] = p.text or ''

                    min_time = self._find(gse, 'MinTime')
                    max_time = self._find(gse, 'MaxTime')

                    raw = {
                        'publisher_ied': ied_name,
                        'subnetwork': sn_name,
                        'network_type': sn_type,
                        'control_block': self._attr(gse, 'cbName'),
                        'ld_inst': self._attr(gse, 'ldInst'),
                        'mac_address': addr_info.get('MAC-Address', ''),
                        'vlan_id': addr_info.get('VLAN-ID', ''),
                        'vlan_priority': addr_info.get('VLAN-PRIORITY', ''),
                        'appid': addr_info.get('APPID', ''),
                        'min_time_ms': self._parse_time(min_time),
                        'max_time_ms': self._parse_time(max_time),
                    }

                    # 补充 IED 配置中的数据集信息
                    ied = self._find_ied_by_name(ied_name)
                    if ied:
                        ld = self._find_ld_by_inst(ied, raw['ld_inst'])
                        if ld:
                            ln0 = self._find(ld, 'LN0')
                            if ln0:
                                for gc in self._findall(ln0, 'GSEControl'):
                                    if self._attr(gc, 'name') == raw['control_block']:
                                        raw['dataset'] = self._attr(gc, 'datSet')
                                        raw['appID_config'] = self._attr(gc, 'appID')
                                        raw['conf_rev'] = self._attr(gc, 'confRev')
                                        raw['gse_type'] = self._attr(gc, 'type')
                                for ds in self._findall(ln0, 'DataSet'):
                                    if self._attr(ds, 'name') == raw.get('dataset', ''):
                                        raw['fcda_count'] = len(self._findall(ds, 'FCDA'))

                    results.append(raw)
        return results

    def _extract_smv_raw(self):
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return []

        results = []
        for sn in self._findall(comm, 'SubNetwork'):
            sn_name = self._attr(sn, 'name')
            for ap in self._findall(sn, 'ConnectedAP'):
                ied_name = self._attr(ap, 'iedName')
                for smv in self._findall(ap, 'SMV'):
                    addr = self._find(smv, 'Address')
                    addr_info = {}
                    if addr:
                        for p in self._findall(addr, 'P'):
                            addr_info[self._attr(p, 'type')] = p.text or ''

                    raw = {
                        'publisher_ied': ied_name,
                        'subnetwork': sn_name,
                        'control_block': self._attr(smv, 'cbName'),
                        'ld_inst': self._attr(smv, 'ldInst'),
                        'mac_address': addr_info.get('MAC-Address', ''),
                        'vlan_id': addr_info.get('VLAN-ID', ''),
                        'vlan_priority': addr_info.get('VLAN-PRIORITY', ''),
                        'appid': addr_info.get('APPID', ''),
                    }

                    ied = self._find_ied_by_name(ied_name)
                    if ied:
                        ld = self._find_ld_by_inst(ied, raw['ld_inst'])
                        if ld:
                            ln0 = self._find(ld, 'LN0')
                            if ln0:
                                for sc in self._findall(ln0, 'SampledValueControl'):
                                    if self._attr(sc, 'name') == raw['control_block']:
                                        raw['dataset'] = self._attr(sc, 'datSet')
                                        raw['smp_rate'] = self._attr(sc, 'smpRate')
                                        raw['nof_asdu'] = self._attr(sc, 'nofASDU')
                                        raw['smv_id'] = self._attr(sc, 'smvID')
                                for ds in self._findall(ln0, 'DataSet'):
                                    if self._attr(ds, 'name') == raw.get('dataset', ''):
                                        raw['fcda_count'] = len(self._findall(ds, 'FCDA'))

                    results.append(raw)
        return results

    def _extract_mms_raw(self):
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return []

        results = []
        for sn in self._findall(comm, 'SubNetwork'):
            sn_type = self._attr(sn, 'type')
            if 'MMS' not in sn_type:
                continue

            subnet = {
                'subnetwork': self._attr(sn, 'name'),
                'ieds': [],
            }

            for ap in self._findall(sn, 'ConnectedAP'):
                ied_name = self._attr(ap, 'iedName')
                addr = self._find(ap, 'Address')
                addr_info = {}
                if addr:
                    for p in self._findall(addr, 'P'):
                        addr_info[self._attr(p, 'type')] = p.text or ''

                ied_info = {
                    'ied_name': ied_name,
                    'ip': addr_info.get('IP', ''),
                    'subnet_mask': addr_info.get('IP-SUBNET', ''),
                    'gateway': addr_info.get('IP-GATEWAY', ''),
                }

                phys_conns = []
                for pc in self._findall(ap, 'PhysConn'):
                    pc_info = {'type': self._attr(pc, 'type')}
                    for p in self._findall(pc, 'P'):
                        pc_info[self._attr(p, 'type')] = p.text or ''
                    phys_conns.append(pc_info)
                if phys_conns:
                    ied_info['phys_connections'] = phys_conns

                ied = self._find_ied_by_name(ied_name)
                if ied:
                    reports = []
                    for ld in self._findall_ied_lds(ied):
                        ln0 = self._find(ld, 'LN0')
                        if ln0:
                            for rc in self._findall(ln0, 'ReportControl'):
                                reports.append({
                                    'name': self._attr(rc, 'name'),
                                    'dataset': self._attr(rc, 'datSet'),
                                    'buffered': self._attr(rc, 'buffered'),
                                    'ld_inst': self._attr(ld, 'inst'),
                                    'conf_rev': self._attr(rc, 'confRev'),
                                    'max_instances': self._attr(
                                        self._find(rc, 'RptEnabled'), 'max', ''),
                                })
                    ied_info['report_services'] = reports

                subnet['ieds'].append(ied_info)
            results.append(subnet)
        return results

    def _extract_extref_raw(self):
        results = []
        for ied in self._findall(self.root, 'IED'):
            ied_name = self._attr(ied, 'name')
            for ld in self._findall_ied_lds(ied):
                ld_inst = self._attr(ld, 'inst')
                for ln in [self._find(ld, 'LN0')] + self._findall(ld, 'LN'):
                    if ln is None:
                        continue
                    inputs = self._find(ln, 'Inputs')
                    if inputs is None:
                        continue
                    for ext_ref in self._findall(inputs, 'ExtRef'):
                        src_ied = self._attr(ext_ref, 'iedName')
                        if not src_ied:
                            continue
                        results.append({
                            'subscriber_ied': ied_name,
                            'subscriber_ld_inst': ld_inst,
                            'src_ied': src_ied,
                            'src_ld_inst': self._attr(ext_ref, 'ldInst'),
                            'src_ln_class': self._attr(ext_ref, 'lnClass'),
                            'src_ln_inst': self._attr(ext_ref, 'lnInst'),
                            'src_prefix': self._attr(ext_ref, 'prefix'),
                            'src_do_name': self._attr(ext_ref, 'doName'),
                            'src_da_name': self._attr(ext_ref, 'daName'),
                            'src_service_type': self._attr(ext_ref, 'serviceType'),
                            'int_addr': self._attr(ext_ref, 'intAddr'),
                        })
        return results

    def _extract_network_seg_raw(self):
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return []

        results = []
        for sn in self._findall(comm, 'SubNetwork'):
            sn_name = self._attr(sn, 'name')
            sn_type = self._attr(sn, 'type')
            ieds = set()
            macs = set()
            appids = set()

            for ap in self._findall(sn, 'ConnectedAP'):
                ieds.add(self._attr(ap, 'iedName'))
                for gse in self._findall(ap, 'GSE'):
                    addr = self._find(gse, 'Address')
                    if addr:
                        for p in self._findall(addr, 'P'):
                            t = self._attr(p, 'type')
                            if t == 'MAC-Address' and p.text:
                                macs.add(p.text)
                            elif t == 'APPID' and p.text:
                                appids.add(p.text)
                for smv in self._findall(ap, 'SMV'):
                    addr = self._find(smv, 'Address')
                    if addr:
                        for p in self._findall(addr, 'P'):
                            t = self._attr(p, 'type')
                            if t == 'MAC-Address' and p.text:
                                macs.add(p.text)
                            elif t == 'APPID' and p.text:
                                appids.add(p.text)

            results.append({
                'subnetwork': sn_name,
                'network_type': sn_type,
                'allowed_ieds': sorted(ieds),
                'allowed_macs': sorted(macs),
                'allowed_appids': sorted(appids),
            })
        return results

    def _extract_config_raw(self):
        results = []
        for ied in self._findall(self.root, 'IED'):
            ied_name = self._attr(ied, 'name')
            auth = self._find(ied, 'Authentication')

            raw = {
                'ied_name': ied_name,
                'ied_type': self._attr(ied, 'type'),
                'manufacturer': self._attr(ied, 'manufacturer'),
                'config_version': self._attr(ied, 'configVersion'),
                'original_scl_revision': self._attr(ied, 'originalSclRevision'),
                'original_scl_version': self._attr(ied, 'originalSclVersion'),
                'authentication': {
                    'none': self._attr(auth, 'none') if auth is not None else '',
                    'certificate': self._attr(auth, 'certificate') if auth is not None else '',
                    'strong': self._attr(auth, 'strong') if auth is not None else '',
                    'weak': self._attr(auth, 'weak') if auth is not None else '',
                    'password': self._attr(auth, 'password') if auth is not None else '',
                },
            }

            gse_count = 0
            report_count = 0
            dataset_count = 0
            dataset_signatures = []
            control_models = []

            for ld in self._findall_ied_lds(ied):
                ld_inst = self._attr(ld, 'inst')
                ln0 = self._find(ld, 'LN0')
                if ln0:
                    gse_count += len(self._findall(ln0, 'GSEControl'))
                    report_count += len(self._findall(ln0, 'ReportControl'))
                    dataset_count += len(self._findall(ln0, 'DataSet'))
                    for ds in self._findall(ln0, 'DataSet'):
                        dataset_signatures.append({
                            'ld_inst': ld_inst,
                            'name': self._attr(ds, 'name'),
                            'fcda_count': len(self._findall(ds, 'FCDA')),
                        })

                for ln in [ln0] + self._findall(ld, 'LN'):
                    if ln is None:
                        continue
                    for doi in self._findall(ln, 'DOI'):
                        for dai in self._findall(doi, 'DAI'):
                            if self._attr(dai, 'name') == 'ctlModel':
                                val = self._find(dai, 'Val')
                                if val is not None and val.text:
                                    control_models.append({
                                        'ld_inst': ld_inst,
                                        'ln_class': self._attr(ln, 'lnClass'),
                                        'ln_inst': self._attr(ln, 'inst'),
                                        'doi_name': self._attr(doi, 'name'),
                                        'ctl_model': val.text,
                                    })

            raw['ldevice_count'] = len(list(self._findall_ied_lds(ied)))
            raw['gse_control_count'] = gse_count
            raw['report_control_count'] = report_count
            raw['dataset_count'] = dataset_count
            raw['dataset_signatures'] = dataset_signatures
            raw['control_models'] = control_models
            results.append(raw)
        return results

    # ── 规范化：原始数据 → 扁平规则 ──

    def _normalize_goose(self, raw_list):
        rules = []
        # 去重：同一个 GOOSE 控制块在 A/B 网重复出现
        seen = set()
        for raw in raw_list:
            key = f"{raw['publisher_ied']}/{raw['ld_inst']}/{raw['control_block']}"
            if key in seen:
                continue
            seen.add(key)

            ied = raw['publisher_ied']
            cb = raw['control_block']
            ld = raw['ld_inst']

            # GOOSE MAC 白名单
            if raw.get('mac_address'):
                rules.append({
                    'rule_id': f"GOOSE-MAC-{raw['mac_address']}",
                    'severity': 'critical',
                    'category': 'goose_whitelist',
                    'protocol': 'GOOSE',
                    'description': f"GOOSE合法发布者: IED={ied}, LD={ld}, CB={cb}, MAC={raw['mac_address']}",
                    'condition': {
                        'eth.src': raw['mac_address'],
                        'goose.appid': raw.get('appid', ''),
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-8-1 GOOSE',
                    'meta': {'ied': ied, 'ld_inst': ld, 'control_block': cb,
                             'subnetwork': raw.get('subnetwork', '')},
                })

            # GOOSE 时间参数
            if raw.get('min_time_ms') is not None or raw.get('max_time_ms') is not None:
                rules.append({
                    'rule_id': f"GOOSE-TIME-{ied}-{ld}-{cb}",
                    'severity': 'medium',
                    'category': 'goose_timing',
                    'protocol': 'GOOSE',
                    'description': f"GOOSE时间参数: IED={ied}, LD={ld}, CB={cb}, "
                                   f"MinTime={raw.get('min_time_ms')}ms, MaxTime={raw.get('max_time_ms')}ms",
                    'condition': {
                        'goose.appid': raw.get('appid', ''),
                        'goose.min_time_ms': raw.get('min_time_ms'),
                        'goose.max_time_ms': raw.get('max_time_ms'),
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-8-1 GOOSE',
                    'meta': {'ied': ied, 'ld_inst': ld, 'control_block': cb},
                })

            # GOOSE 数据集完整性
            if raw.get('dataset') and raw.get('fcda_count') is not None:
                rules.append({
                    'rule_id': f"GOOSE-DS-{ied}-{ld}-{raw['dataset']}",
                    'severity': 'high',
                    'category': 'goose_dataset_integrity',
                    'protocol': 'GOOSE',
                    'description': f"GOOSE数据集完整性: IED={ied}, LD={ld}, "
                                   f"DataSet={raw['dataset']}, FCDA数={raw['fcda_count']}",
                    'condition': {
                        'goose.appid': raw.get('appid', ''),
                        'goose.datset': raw['dataset'],
                        'goose.fcda_count': raw['fcda_count'],
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-8-1 GOOSE',
                    'meta': {'ied': ied, 'ld_inst': ld, 'control_block': cb,
                             'dataset': raw['dataset'], 'conf_rev': raw.get('conf_rev', '')},
                })

        return rules

    def _normalize_smv(self, raw_list):
        rules = []
        for raw in raw_list:
            ied = raw['publisher_ied']
            cb = raw['control_block']
            ld = raw['ld_inst']

            # SMV MAC 白名单
            if raw.get('mac_address'):
                rules.append({
                    'rule_id': f"SMV-MAC-{raw['mac_address']}",
                    'severity': 'critical',
                    'category': 'smv_whitelist',
                    'protocol': 'SMV',
                    'description': f"SMV合法发布者: IED={ied}, LD={ld}, CB={cb}, MAC={raw['mac_address']}",
                    'condition': {
                        'eth.src': raw['mac_address'],
                        'sv.appid': raw.get('appid', ''),
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-9-2 SV',
                    'meta': {'ied': ied, 'ld_inst': ld, 'control_block': cb,
                             'subnetwork': raw.get('subnetwork', '')},
                })

            # SMV 采样参数
            if raw.get('smp_rate'):
                rules.append({
                    'rule_id': f"SMV-SMP-{ied}-{ld}-{cb}",
                    'severity': 'high',
                    'category': 'smv_sampling',
                    'protocol': 'SMV',
                    'description': f"SMV采样参数: IED={ied}, LD={ld}, CB={cb}, "
                                   f"smpRate={raw['smp_rate']}, nofASDU={raw.get('nof_asdu','')}, "
                                   f"smvID={raw.get('smv_id','')}",
                    'condition': {
                        'sv.appid': raw.get('appid', ''),
                        'sv.smp_rate': raw['smp_rate'],
                        'sv.nof_asdu': raw.get('nof_asdu', ''),
                        'sv.smv_id': raw.get('smv_id', ''),
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-9-2 SV',
                    'meta': {'ied': ied, 'ld_inst': ld, 'control_block': cb,
                             'dataset': raw.get('dataset', '')},
                })

            # SMV 数据集完整性
            if raw.get('dataset') and raw.get('fcda_count') is not None:
                rules.append({
                    'rule_id': f"SMV-DS-{ied}-{ld}-{raw['dataset']}",
                    'severity': 'high',
                    'category': 'smv_dataset_integrity',
                    'protocol': 'SMV',
                    'description': f"SMV数据集完整性: IED={ied}, LD={ld}, "
                                   f"DataSet={raw['dataset']}, FCDA数={raw['fcda_count']}",
                    'condition': {
                        'sv.appid': raw.get('appid', ''),
                        'sv.datset': raw['dataset'],
                        'sv.fcda_count': raw['fcda_count'],
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-9-2 SV',
                    'meta': {'ied': ied, 'ld_inst': ld, 'control_block': cb,
                             'dataset': raw['dataset']},
                })

        return rules

    def _normalize_mms(self, raw_list):
        rules = []
        for subnet in raw_list:
            sn = subnet['subnetwork']

            for ied_info in subnet['ieds']:
                ied = ied_info['ied_name']

                # MMS IP 白名单
                if ied_info.get('ip'):
                    rules.append({
                        'rule_id': f"MMS-IP-{ied_info['ip']}",
                        'severity': 'high',
                        'category': 'mms_whitelist',
                        'protocol': 'MMS',
                        'description': f"MMS合法IED: {ied}, IP={ied_info['ip']}, "
                                       f"子网={sn}",
                        'condition': {
                            'ip.src': ied_info['ip'],
                            'mms.ied_name': ied,
                        },
                        'action': 'alert',
                        'reference': 'IEC 61850-8-1 MMS',
                        'meta': {'ied': ied, 'subnetwork': sn,
                                 'subnet_mask': ied_info.get('subnet_mask', ''),
                                 'gateway': ied_info.get('gateway', '')},
                    })

                # 报告服务白名单
                for rpt in ied_info.get('report_services', []):
                    rules.append({
                        'rule_id': f"MMS-RPT-{ied}-{rpt['ld_inst']}-{rpt['name']}",
                        'severity': 'medium',
                        'category': 'mms_report',
                        'protocol': 'MMS',
                        'description': f"MMS报告服务: IED={ied}, LD={rpt['ld_inst']}, "
                                       f"Report={rpt['name']}, DataSet={rpt['dataset']}, "
                                       f"buffered={rpt.get('buffered','')}",
                        'condition': {
                            'mms.ied_name': ied,
                            'mms.report_name': rpt['name'],
                            'mms.dataset': rpt['dataset'],
                            'mms.ld_inst': rpt['ld_inst'],
                        },
                        'action': 'log',
                        'reference': 'IEC 61850-8-1 MMS',
                        'meta': {'ied': ied, 'ld_inst': rpt['ld_inst'],
                                 'buffered': rpt.get('buffered', ''),
                                 'conf_rev': rpt.get('conf_rev', ''),
                                 'max_instances': rpt.get('max_instances', '')},
                    })

        return rules

    def _normalize_subscription(self, extref_list):
        rules = []

        # 按 (subscriber, src_ied) 聚合
        subs_by_pair = defaultdict(list)
        for ref in extref_list:
            key = (ref['subscriber_ied'], ref['src_ied'])
            subs_by_pair[key].append(ref)

        # IED 间订阅白名单
        for (sub_ied, src_ied), refs in subs_by_pair.items():
            rules.append({
                'rule_id': f"SUB-PAIR-{sub_ied}-{src_ied}",
                'severity': 'high',
                'category': 'subscription_whitelist',
                'protocol': 'GOOSE_SMV',
                'description': f"订阅白名单: {sub_ied} 可接收来自 {src_ied} 的GOOSE/SMV数据 ({len(refs)}个ExtRef)",
                'condition': {
                    'subscriber.ied': sub_ied,
                    'source.ied': src_ied,
                },
                'action': 'alert',
                'reference': 'IEC 61850-6 SCL ExtRef',
                'meta': {'ext_ref_count': len(refs)},
            })

        # 每个 ExtRef 一条精确规则
        for ref in extref_list:
            ref_desc = (f"{ref['src_ied']}/{ref['src_ld_inst']}/"
                        f"{ref['src_ln_class']}{ref['src_ln_inst']}/"
                        f"{ref['src_do_name']}")
            if ref.get('src_da_name'):
                ref_desc += f".{ref['src_da_name']}"

            rules.append({
                'rule_id': f"SUB-REF-{ref['subscriber_ied']}-{ref['int_addr']}",
                'severity': 'medium',
                'category': 'subscription_extref',
                'protocol': 'GOOSE_SMV',
                'description': f"ExtRef订阅: {ref['subscriber_ied']}/{ref['subscriber_ld_inst']} "
                               f"← {ref_desc}",
                'condition': {
                    'subscriber.ied': ref['subscriber_ied'],
                    'subscriber.ld_inst': ref['subscriber_ld_inst'],
                    'source.ied': ref['src_ied'],
                    'source.ld_inst': ref['src_ld_inst'],
                    'source.ln_class': ref['src_ln_class'],
                    'source.do_name': ref['src_do_name'],
                },
                'action': 'log',
                'reference': 'IEC 61850-6 SCL ExtRef',
                'meta': {'src_da_name': ref.get('src_da_name', ''),
                         'src_prefix': ref.get('src_prefix', ''),
                         'service_type': ref.get('src_service_type', ''),
                         'int_addr': ref.get('int_addr', '')},
            })

        return rules

    def _normalize_topology(self, goose_raw, extref_list):
        rules = []

        # 构建 GOOSE 发布者表（去重）
        publishers = {}
        for raw in goose_raw:
            key = f"{raw['publisher_ied']}/{raw['ld_inst']}/{raw['control_block']}"
            if key not in publishers:
                publishers[key] = {
                    'publisher_ied': raw['publisher_ied'],
                    'ld_inst': raw['ld_inst'],
                    'control_block': raw['control_block'],
                    'mac': raw.get('mac_address', ''),
                    'appid': raw.get('appid', ''),
                }

        # 构建订阅者映射
        subscriber_map = defaultdict(set)
        for ref in extref_list:
            if ref['src_ied'] and ref['src_ld_inst']:
                subscriber_map[(ref['src_ied'], ref['src_ld_inst'])].add(
                    (ref['subscriber_ied'], ref['subscriber_ld_inst']))

        for key, pub in publishers.items():
            subs = subscriber_map.get((pub['publisher_ied'], pub['ld_inst']), set())
            sub_list = [{'ied': s[0], 'ld_inst': s[1]} for s in sorted(subs)]

            rules.append({
                'rule_id': f"TOPO-{pub['publisher_ied']}-{pub['ld_inst']}-{pub['control_block']}",
                'severity': 'high',
                'category': 'goose_topology',
                'protocol': 'GOOSE',
                'description': (f"GOOSE拓扑: {pub['publisher_ied']}/{pub['ld_inst']}/"
                                f"{pub['control_block']} → "
                                f"{', '.join(s['ied']+'/'+s['ld_inst'] for s in sub_list) if sub_list else '无订阅者'}"),
                'condition': {
                    'publisher.ied': pub['publisher_ied'],
                    'publisher.ld_inst': pub['ld_inst'],
                    'publisher.control_block': pub['control_block'],
                    'goose.appid': pub['appid'],
                },
                'action': 'alert',
                'reference': 'IEC 61850-8-1 GOOSE',
                'meta': {'mac': pub['mac'],
                         'allowed_subscribers': sub_list},
            })

        return rules

    def _normalize_network_seg(self, raw_list):
        rules = []
        for seg in raw_list:
            sn = seg['subnetwork']
            sn_type = seg.get('network_type', '')

            # 子网 IED 白名单
            if seg['allowed_ieds']:
                rules.append({
                    'rule_id': f"SEG-IED-{sn}",
                    'severity': 'high',
                    'category': 'network_segment_ied',
                    'protocol': 'MULTI',
                    'description': f"子网IED白名单: {sn} 允许的IED: {', '.join(seg['allowed_ieds'])}",
                    'condition': {
                        'network.subnetwork': sn,
                        'network.type': sn_type,
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-6 SCL Communication',
                    'meta': {'allowed_ieds': seg['allowed_ieds']},
                })

            # 子网 MAC 白名单
            if seg['allowed_macs']:
                rules.append({
                    'rule_id': f"SEG-MAC-{sn}",
                    'severity': 'critical',
                    'category': 'network_segment_mac',
                    'protocol': 'MULTI',
                    'description': f"子网MAC白名单: {sn}, {len(seg['allowed_macs'])}个合法MAC",
                    'condition': {
                        'network.subnetwork': sn,
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-6 SCL Communication',
                    'meta': {'allowed_macs': seg['allowed_macs']},
                })

            # 子网 APPID 白名单
            if seg['allowed_appids']:
                rules.append({
                    'rule_id': f"SEG-APPID-{sn}",
                    'severity': 'critical',
                    'category': 'network_segment_appid',
                    'protocol': 'MULTI',
                    'description': f"子网APPID白名单: {sn}, {len(seg['allowed_appids'])}个合法APPID",
                    'condition': {
                        'network.subnetwork': sn,
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-6 SCL Communication',
                    'meta': {'allowed_appids': seg['allowed_appids']},
                })

        return rules

    def _normalize_config(self, raw_list):
        rules = []

        for raw in raw_list:
            ied = raw['ied_name']

            # IED 身份基线
            rules.append({
                'rule_id': f"CFG-IDENTITY-{ied}",
                'severity': 'high',
                'category': 'config_identity',
                'protocol': 'MMS',
                'description': f"IED身份基线: {ied}, 类型={raw['ied_type']}, "
                               f"厂商={raw['manufacturer']}, 版本={raw['config_version']}",
                'condition': {
                    'mms.ied_name': ied,
                },
                'action': 'alert',
                'reference': 'IEC 61850-6 SCL IED',
                'meta': {'ied_type': raw['ied_type'],
                         'manufacturer': raw['manufacturer'],
                         'config_version': raw['config_version'],
                         'original_scl_revision': raw.get('original_scl_revision', ''),
                         'original_scl_version': raw.get('original_scl_version', '')},
            })

            # 配置数量基线
            rules.append({
                'rule_id': f"CFG-COUNT-{ied}",
                'severity': 'medium',
                'category': 'config_count',
                'protocol': 'MMS',
                'description': f"IED配置数量基线: {ied}, LDevice={raw['ldevice_count']}, "
                               f"GOOSE={raw['gse_control_count']}, Report={raw['report_control_count']}, "
                               f"DataSet={raw['dataset_count']}",
                'condition': {
                    'mms.ied_name': ied,
                },
                'action': 'alert',
                'reference': 'IEC 61850-6 SCL IED',
                'meta': {
                    'ldevice_count': raw['ldevice_count'],
                    'gse_control_count': raw['gse_control_count'],
                    'report_control_count': raw['report_control_count'],
                    'dataset_count': raw['dataset_count'],
                },
            })

            # 数据集指纹
            for ds in raw.get('dataset_signatures', []):
                rules.append({
                    'rule_id': f"CFG-DS-{ied}-{ds['ld_inst']}-{ds['name']}",
                    'severity': 'high',
                    'category': 'config_dataset_fingerprint',
                    'protocol': 'MMS',
                    'description': f"数据集指纹: {ied}/{ds['ld_inst']}/{ds['name']}, "
                                   f"FCDA数={ds['fcda_count']}",
                    'condition': {
                        'mms.ied_name': ied,
                        'mms.ld_inst': ds['ld_inst'],
                        'mms.dataset_name': ds['name'],
                    },
                    'action': 'alert',
                    'reference': 'IEC 61850-7-2 DataSet',
                    'meta': {'fcda_count': ds['fcda_count']},
                })

            # 控制模型基线
            for cm in raw.get('control_models', []):
                CTL_MEANING = {'0': 'StatusOnly', '1': 'Direct-Normal',
                               '2': 'SBO-Normal', '3': 'Direct-Enhanced',
                               '4': 'SBO-Enhanced'}
                meaning = CTL_MEANING.get(cm['ctl_model'], f"Unknown({cm['ctl_model']})")
                rules.append({
                    'rule_id': f"CFG-CTL-{ied}-{cm['ld_inst']}-{cm['ln_class']}{cm['ln_inst']}-{cm['doi_name']}",
                    'severity': 'low',
                    'category': 'config_control_model',
                    'protocol': 'MMS',
                    'description': f"控制模型: {ied}/{cm['ld_inst']}/{cm['ln_class']}{cm['ln_inst']}/"
                                   f"{cm['doi_name']}={meaning}",
                    'condition': {
                        'mms.ied_name': ied,
                        'mms.ld_inst': cm['ld_inst'],
                        'mms.ln_class': cm['ln_class'],
                        'mms.ln_inst': cm['ln_inst'],
                        'mms.doi_name': cm['doi_name'],
                    },
                    'action': 'log',
                    'reference': 'IEC 61850-7-2 ControlModel',
                    'meta': {'ctl_model': cm['ctl_model'],
                             'ctl_meaning': meaning},
                })

            # 认证状态
            auth = raw.get('authentication', {})
            auth_none = auth.get('none', '')
            rules.append({
                'rule_id': f"CFG-AUTH-{ied}",
                'severity': 'critical' if auth_none == 'true' else 'info',
                'category': 'config_authentication',
                'protocol': 'MMS',
                'description': f"IED认证状态: {ied}, "
                               f"{'无认证(安全隐患)' if auth_none == 'true' else '有认证'}",
                'condition': {
                    'mms.ied_name': ied,
                },
                'action': 'alert',
                'reference': 'IEC 61850-8-1 Authentication',
                'meta': {'none': auth_none,
                         'certificate': auth.get('certificate', ''),
                         'strong': auth.get('strong', ''),
                         'weak': auth.get('weak', ''),
                         'password': auth.get('password', '')},
            })

        return rules

    # ── 工具方法 ──

    def _find_ied_by_name(self, name):
        for ied in self._findall(self.root, 'IED'):
            if self._attr(ied, 'name') == name:
                return ied
        return None

    def _find_ld_by_inst(self, ied, inst):
        for ap in self._findall(ied, 'AccessPoint'):
            server = self._find(ap, 'Server')
            if server:
                for ld in self._findall(server, 'LDevice'):
                    if self._attr(ld, 'inst') == inst:
                        return ld
        return None

    def _findall_ied_lds(self, ied):
        lds = []
        for ap in self._findall(ied, 'AccessPoint'):
            server = self._find(ap, 'Server')
            if server:
                lds.extend(self._findall(server, 'LDevice'))
        return lds

    def _parse_time(self, elem):
        if elem is None:
            return None
        val = elem.text
        multiplier = self._attr(elem, 'multiplier')
        unit = self._attr(elem, 'unit')
        if not val:
            return None
        try:
            v = float(val)
            if unit == 's':
                if multiplier == 'm':
                    v *= 0.001
            return v * 1000
        except ValueError:
            return None

    # ── 主提取方法 ──

    def extract_all_rules(self):
        # 原始数据提取
        goose_raw = self._extract_goose_raw()
        smv_raw = self._extract_smv_raw()
        mms_raw = self._extract_mms_raw()
        extref_raw = self._extract_extref_raw()
        seg_raw = self._extract_network_seg_raw()
        config_raw = self._extract_config_raw()

        # 规范化为扁平规则
        rules = []
        rules.extend(self._normalize_goose(goose_raw))
        rules.extend(self._normalize_smv(smv_raw))
        rules.extend(self._normalize_mms(mms_raw))
        rules.extend(self._normalize_subscription(extref_raw))
        rules.extend(self._normalize_topology(goose_raw, extref_raw))
        rules.extend(self._normalize_network_seg(seg_raw))
        rules.extend(self._normalize_config(config_raw))

        # 按 category 统计
        category_stats = defaultdict(int)
        severity_stats = defaultdict(int)
        protocol_stats = defaultdict(int)
        for r in rules:
            category_stats[r['category']] += 1
            severity_stats[r['severity']] += 1
            protocol_stats[r['protocol']] += 1

        return {
            'source_file': self.scd_path.name,
            'description': '基于 SCD 配置自动提取的 IEC 61850 入侵检测规则（规范化格式）',
            'total_rules': len(rules),
            'statistics': {
                'by_category': dict(category_stats),
                'by_severity': dict(severity_stats),
                'by_protocol': dict(protocol_stats),
            },
            'rules': rules,
        }


def print_rules_summary(result):
    print("\n" + "=" * 70)
    print("IEC 61850 入侵检测规则摘要")
    print("=" * 70)
    print(f"源文件: {result['source_file']}")
    print(f"规则总数: {result['total_rules']}")

    stats = result['statistics']
    print(f"\n按严重等级:")
    for sev in ['critical', 'high', 'medium', 'low', 'info']:
        if sev in stats['by_severity']:
            print(f"  {sev:<10} {stats['by_severity'][sev]} 条")

    print(f"\n按协议:")
    for proto, count in sorted(stats['by_protocol'].items()):
        print(f"  {proto:<12} {count} 条")

    print(f"\n按类别:")
    for cat, count in sorted(stats['by_category'].items()):
        print(f"  {cat:<30} {count} 条")

    # 每个 severity 的典型规则示例
    rules = result['rules']
    print(f"\n{'─' * 70}")
    print("规则示例（每类 severity 一条）:")
    print(f"{'─' * 70}")
    shown = set()
    for r in rules:
        if r['severity'] not in shown:
            shown.add(r['severity'])
            print(f"\n  [{r['severity'].upper()}] {r['rule_id']}")
            print(f"    {r['description']}")
            print(f"    condition: {json.dumps(r['condition'], ensure_ascii=False)}")
            print(f"    action: {r['action']}")


def main():
    parser = argparse.ArgumentParser(
        description='IEC 61850 入侵检测规则提取器（规范化输出）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python extract_ids_rules_from_scd.py input/中科院.scd
  python extract_ids_rules_from_scd.py input/中科院.scd -o output/ids_rules_direct.json
        """
    )
    parser.add_argument('scd_path', help='SCD/ICD/CID 文件路径')
    parser.add_argument('-o', '--output', help='输出规则文件路径')

    args = parser.parse_args()

    extractor = SCDDirectExtractor(args.scd_path)
    result = extractor.extract_all_rules()

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"检测规则已保存: {args.output}")

    print_rules_summary(result)


if __name__ == '__main__':
    main()
