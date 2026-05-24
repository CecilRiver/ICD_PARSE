"""
IEC 61850 入侵检测规则提取器（直接从 SCD 文件提取）

直接解析 SCD 原始 XML，提取完整的 IDS 规则，包括中间 JSON 方式会遗漏的：
- ExtRef: GOOSE/SMV 订阅关系
- MinTime/MaxTime: GOOSE 时间参数
- PhysConn: 物理连接信息
- Authentication: 认证配置
- ctlModel: 控制模型
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

    # ── GOOSE 白名单 ──

    def extract_goose_whitelist(self):
        """提取 GOOSE 白名单：发布者 IED、MAC、APPID、数据集、时间参数"""
        rules = []
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return rules

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

                    rule = {
                        'rule_type': 'GOOSE_WHITELIST',
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
                    rules.append(rule)

        # 补充数据集 FCDA 数量（从 IED 配置中查）
        for rule in rules:
            ied = self._find_ied_by_name(rule['publisher_ied'])
            if ied:
                ld = self._find_ld_by_inst(ied, rule['ld_inst'])
                if ld:
                    ln0 = self._find(ld, 'LN0')
                    if ln0:
                        for gc in self._findall(ln0, 'GSEControl'):
                            if self._attr(gc, 'name') == rule['control_block']:
                                rule['dataset'] = self._attr(gc, 'datSet')
                                rule['appID_config'] = self._attr(gc, 'appID')
                                rule['conf_rev'] = self._attr(gc, 'confRev')
                                rule['type'] = self._attr(gc, 'type')
                        for ds in self._findall(ln0, 'DataSet'):
                            if self._attr(ds, 'name') == rule.get('dataset', ''):
                                rule['fcda_count'] = len(self._findall(ds, 'FCDA'))

        return rules

    # ── SMV 白名单 ──

    def extract_smv_whitelist(self):
        """提取 SMV 采样值白名单"""
        rules = []
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return rules

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

                    rule = {
                        'rule_type': 'SMV_WHITELIST',
                        'publisher_ied': ied_name,
                        'subnetwork': sn_name,
                        'control_block': self._attr(smv, 'cbName'),
                        'ld_inst': self._attr(smv, 'ldInst'),
                        'mac_address': addr_info.get('MAC-Address', ''),
                        'vlan_id': addr_info.get('VLAN-ID', ''),
                        'vlan_priority': addr_info.get('VLAN-PRIORITY', ''),
                        'appid': addr_info.get('APPID', ''),
                    }
                    rules.append(rule)

        # 补充 SMV 数据集 FCDA 数量
        for rule in rules:
            ied = self._find_ied_by_name(rule['publisher_ied'])
            if ied:
                ld = self._find_ld_by_inst(ied, rule['ld_inst'])
                if ld:
                    ln0 = self._find(ld, 'LN0')
                    if ln0:
                        for ds in self._findall(ln0, 'DataSet'):
                            if self._attr(ds, 'name') == rule.get('dataset', ''):
                                rule['fcda_count'] = len(self._findall(ds, 'FCDA'))
                        for sc in self._findall(ln0, 'SampledValueControl'):
                            if self._attr(sc, 'name') == rule['control_block']:
                                rule['dataset'] = self._attr(sc, 'datSet')
                                rule['smp_rate'] = self._attr(sc, 'smpRate')
                                rule['nof_asdu'] = self._attr(sc, 'nofASDU')
                                rule['smv_id'] = self._attr(sc, 'smvID')

        return rules

    # ── MMS 通信白名单 ──

    def extract_mms_whitelist(self):
        """提取 MMS 站控层通信白名单"""
        rules = []
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return rules

        for sn in self._findall(comm, 'SubNetwork'):
            sn_type = self._attr(sn, 'type')
            if 'MMS' not in sn_type:
                continue

            subnet = {
                'rule_type': 'MMS_WHITELIST',
                'subnetwork': self._attr(sn, 'name'),
                'connected_ieds': [],
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

                # 物理连接
                phys_conns = []
                for pc in self._findall(ap, 'PhysConn'):
                    pc_info = {'type': self._attr(pc, 'type')}
                    for p in self._findall(pc, 'P'):
                        pc_info[self._attr(p, 'type')] = p.text or ''
                    phys_conns.append(pc_info)
                if phys_conns:
                    ied_info['phys_connections'] = phys_conns

                # 报告服务
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

                subnet['connected_ieds'].append(ied_info)

            rules.append(subnet)

        return rules

    # ── GOOSE/SMV 订阅关系（ExtRef）──

    def extract_subscription_rules(self):
        """从 ExtRef 提取 GOOSE/SMV 订阅关系"""
        rules = []

        for ied in self._findall(self.root, 'IED'):
            ied_name = self._attr(ied, 'name')
            subscriptions = defaultdict(list)

            for ld in self._findall_ied_lds(ied):
                ld_inst = self._attr(ld, 'inst')
                # ExtRef 在 LN0 和 LN 的 Inputs 下
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
                        sub = {
                            'src_ied': src_ied,
                            'src_ld_inst': self._attr(ext_ref, 'ldInst'),
                            'src_ln_class': self._attr(ext_ref, 'lnClass'),
                            'src_ln_inst': self._attr(ext_ref, 'lnInst'),
                            'src_prefix': self._attr(ext_ref, 'prefix'),
                            'src_do_name': self._attr(ext_ref, 'doName'),
                            'src_da_name': self._attr(ext_ref, 'daName'),
                            'src_service_type': self._attr(ext_ref, 'serviceType'),
                            'int_addr': self._attr(ext_ref, 'intAddr'),
                        }
                        subscriptions[src_ied].append(sub)

            if subscriptions:
                rules.append({
                    'rule_type': 'SUBSCRIPTION_WHITELIST',
                    'subscriber_ied': ied_name,
                    'subscriptions': {k: v for k, v in subscriptions.items()},
                    'subscribed_ieds': sorted(subscriptions.keys()),
                    'ext_ref_count': sum(len(v) for v in subscriptions.values()),
                })

        return rules

    # ── 网络分区规则 ──

    def extract_network_segmentation(self):
        """提取网络分区规则：哪些 IED/MAC/APPID 应出现在哪个子网"""
        rules = []
        comm = self._find(self.root, 'Communication')
        if comm is None:
            return rules

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

            rules.append({
                'rule_type': 'NETWORK_SEGMENT',
                'subnetwork': sn_name,
                'network_type': sn_type,
                'allowed_ieds': sorted(ieds),
                'allowed_macs': sorted(macs),
                'allowed_appids': sorted(appids),
            })

        return rules

    # ── 配置基线 ──

    def extract_config_baseline(self):
        """提取 IED 配置基线，用于检测未授权变更"""
        rules = []

        for ied in self._findall(self.root, 'IED'):
            ied_name = self._attr(ied, 'name')
            auth = self._find(ied, 'Authentication')

            baseline = {
                'rule_type': 'CONFIG_BASELINE',
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

                # 所有 LN（含 LN0）的 ctlModel
                for ln in [ln0] + self._findall(ld, 'LN'):
                    if ln is None:
                        continue
                    for doi in self._findall(ln, 'DOI'):
                        for dai in self._findall(doi, 'DAI'):
                            if self._attr(dai, 'name') == 'ctlModel':
                                val = self._find(dai, 'Val')
                                if val is not None and val.text:
                                    ln_class = self._attr(ln, 'lnClass')
                                    ln_inst = self._attr(ln, 'inst')
                                    control_models.append({
                                        'ld_inst': ld_inst,
                                        'ln_class': ln_class,
                                        'ln_inst': ln_inst,
                                        'doi_name': self._attr(doi, 'name'),
                                        'ctl_model': val.text,
                                    })

            baseline['ldevice_count'] = len(list(self._findall_ied_lds(ied)))
            baseline['gse_control_count'] = gse_count
            baseline['report_control_count'] = report_count
            baseline['dataset_count'] = dataset_count
            baseline['dataset_signatures'] = dataset_signatures
            baseline['control_models'] = control_models

            rules.append(baseline)

        return rules

    # ── GOOSE 发布-订阅拓扑 ──

    def extract_goose_topology(self):
        """提取完整的 GOOSE 发布-订阅拓扑关系"""
        # 发布者：从 Communication > SubNetwork > ConnectedAP > GSE 获取
        publishers = {}
        comm = self._find(self.root, 'Communication')
        if comm:
            for sn in self._findall(comm, 'SubNetwork'):
                sn_name = self._attr(sn, 'name')
                sn_type = self._attr(sn, 'type')
                for ap in self._findall(sn, 'ConnectedAP'):
                    ied_name = self._attr(ap, 'iedName')
                    for gse in self._findall(ap, 'GSE'):
                        addr = self._find(gse, 'Address')
                        mac = ''
                        appid = ''
                        if addr:
                            for p in self._findall(addr, 'P'):
                                if self._attr(p, 'type') == 'MAC-Address':
                                    mac = p.text or ''
                                elif self._attr(p, 'type') == 'APPID':
                                    appid = p.text or ''
                        key = f"{ied_name}/{self._attr(gse, 'ldInst')}/{self._attr(gse, 'cbName')}"
                        publishers[key] = {
                            'publisher_ied': ied_name,
                            'ld_inst': self._attr(gse, 'ldInst'),
                            'control_block': self._attr(gse, 'cbName'),
                            'subnetwork': sn_name,
                            'network_type': sn_type,
                            'mac': mac,
                            'appid': appid,
                        }

        # 订阅者：从 ExtRef 获取
        subscriber_map = defaultdict(list)
        for ied in self._findall(self.root, 'IED'):
            ied_name = self._attr(ied, 'name')
            for ld in self._findall_ied_lds(ied):
                for ln in [self._find(ld, 'LN0')] + self._findall(ld, 'LN'):
                    if ln is None:
                        continue
                    inputs = self._find(ln, 'Inputs')
                    if inputs is None:
                        continue
                    for ext_ref in self._findall(inputs, 'ExtRef'):
                        src_ied = self._attr(ext_ref, 'iedName')
                        src_ld = self._attr(ext_ref, 'ldInst')
                        src_service = self._attr(ext_ref, 'serviceType')
                        if src_ied:
                            subscriber_map[src_ied].append({
                                'subscriber_ied': ied_name,
                                'subscriber_ld_inst': self._attr(ld, 'inst'),
                                'src_ld_inst': src_ld,
                                'service_type': src_service,
                                'src_ln_class': self._attr(ext_ref, 'lnClass'),
                                'src_do_name': self._attr(ext_ref, 'doName'),
                                'src_da_name': self._attr(ext_ref, 'daName'),
                            })

        # 组合拓扑
        topology = []
        for key, pub in publishers.items():
            pub_ied = pub['publisher_ied']
            subscribers = subscriber_map.get(pub_ied, [])
            # 过滤：只保留 src_ld_inst 匹配的订阅者
            matching_subs = [s for s in subscribers
                             if not pub['ld_inst'] or s['src_ld_inst'] == pub['ld_inst']]

            # 按 (ied, ld_inst) 去重
            seen = set()
            unique_subs = []
            for s in matching_subs:
                skey = (s['subscriber_ied'], s['subscriber_ld_inst'])
                if skey not in seen:
                    seen.add(skey)
                    unique_subs.append({'ied': s['subscriber_ied'], 'ld_inst': s['subscriber_ld_inst']})

            topology.append({
                'rule_type': 'GOOSE_TOPOLOGY',
                **pub,
                'subscriber_count': len(unique_subs),
                'subscribers': unique_subs,
            })

        return topology

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
            return v * 1000  # 统一转毫秒
        except ValueError:
            return None

    # ── 主提取方法 ──

    def extract_all_rules(self):
        return {
            'source_file': self.scd_path.name,
            'description': '基于 SCD 配置自动提取的 IEC 61850 入侵检测规则',
            'rule_categories': {
                'goose_whitelist': self.extract_goose_whitelist(),
                'smv_whitelist': self.extract_smv_whitelist(),
                'mms_whitelist': self.extract_mms_whitelist(),
                'subscription': self.extract_subscription_rules(),
                'goose_topology': self.extract_goose_topology(),
                'network_segmentation': self.extract_network_segmentation(),
                'config_baseline': self.extract_config_baseline(),
            },
            'rule_summary': {},
        }


def print_rules_summary(rules):
    print("\n" + "=" * 70)
    print("IEC 61850 入侵检测规则摘要")
    print("=" * 70)
    print(f"源文件: {rules['source_file']}")

    cats = rules['rule_categories']
    summary = {k: len(v) for k, v in cats.items()}
    rules['rule_summary'] = summary

    print(f"\n规则统计:")
    print(f"  GOOSE 白名单:       {summary.get('goose_whitelist', 0)} 条")
    print(f"  SMV 白名单:         {summary.get('smv_whitelist', 0)} 条")
    print(f"  MMS 通信白名单:     {summary.get('mms_whitelist', 0)} 条")
    print(f"  GOOSE/SMV 订阅关系: {summary.get('subscription', 0)} 条")
    print(f"  GOOSE 拓扑:         {summary.get('goose_topology', 0)} 条")
    print(f"  网络分区规则:       {summary.get('network_segmentation', 0)} 条")
    print(f"  配置基线规则:       {summary.get('config_baseline', 0)} 条")

    # GOOSE 白名单
    goose = cats.get('goose_whitelist', [])
    if goose:
        print(f"\n{'─' * 70}")
        print("GOOSE 白名单（合法发布者）:")
        print(f"{'─' * 70}")
        print(f"{'IED':<10} {'CB':<10} {'LD':<10} {'MAC':<22} {'APPID':<8} "
              f"{'FCDA':<5} {'Min(ms)':<8} {'Max(ms)':<8}")
        print(f"{'─' * 70}")
        for r in goose:
            print(f"{r['publisher_ied']:<10} {r['control_block']:<10} {r['ld_inst']:<10} "
                  f"{r['mac_address']:<22} {r['appid']:<8} "
                  f"{r.get('fcda_count', '?'):<5} "
                  f"{r.get('min_time_ms', '-') or '-':<8} "
                  f"{r.get('max_time_ms', '-') or '-':<8}")

    # SMV 白名单
    smv = cats.get('smv_whitelist', [])
    if smv:
        print(f"\n{'─' * 70}")
        print("SMV 采样值白名单:")
        print(f"{'─' * 70}")
        print(f"{'IED':<10} {'CB':<12} {'LD':<10} {'MAC':<22} {'APPID':<8} {'SmpRate':<8} {'ASDU':<6}")
        print(f"{'─' * 70}")
        for r in smv:
            print(f"{r['publisher_ied']:<10} {r['control_block']:<12} {r['ld_inst']:<10} "
                  f"{r['mac_address']:<22} {r['appid']:<8} "
                  f"{r.get('smp_rate', '-'):<8} {r.get('nof_asdu', '-'):<6}")

    # 订阅关系
    subs = cats.get('subscription', [])
    if subs:
        print(f"\n{'─' * 70}")
        print("GOOSE/SMV 订阅关系:")
        print(f"{'─' * 70}")
        for s in subs:
            print(f"  订阅者: {s['subscriber_ied']} ← {', '.join(s['subscribed_ieds'])} "
                  f"(ExtRef: {s['ext_ref_count']} 条)")

    # GOOSE 拓扑
    topo = cats.get('goose_topology', [])
    if topo:
        print(f"\n{'─' * 70}")
        print("GOOSE 发布-订阅拓扑:")
        print(f"{'─' * 70}")
        for t in topo:
            sub_names = [s['ied'] for s in t['subscribers']]
            print(f"  {t['publisher_ied']}/{t['ld_inst']}/{t['control_block']} → "
                  f"{', '.join(sub_names) if sub_names else '(无订阅者)'}")

    # 网络分区
    segs = cats.get('network_segmentation', [])
    if segs:
        print(f"\n{'─' * 70}")
        print("网络分区:")
        print(f"{'─' * 70}")
        for s in segs:
            print(f"  {s['subnetwork']} (type={s['network_type']})")
            print(f"    IED: {', '.join(s['allowed_ieds'])}")
            print(f"    MAC: {len(s['allowed_macs'])} 个, APPID: {len(s['allowed_appids'])} 个")

    # 配置基线
    cfgs = cats.get('config_baseline', [])
    if cfgs:
        print(f"\n{'─' * 70}")
        print("配置基线:")
        print(f"{'─' * 70}")
        print(f"{'IED':<10} {'类型':<20} {'LD':<4} {'GOOSE':<6} {'报告':<6} {'数据集':<6} "
              f"{'ctlModel':<8} {'认证':<6} {'版本':<15}")
        print(f"{'─' * 70}")
        for c in cfgs:
            auth_none = c['authentication'].get('none', '')
            auth_str = 'none' if auth_none == 'true' else '有认证'
            print(f"{c['ied_name']:<10} {c['ied_type']:<20} {c['ldevice_count']:<4} "
                  f"{c['gse_control_count']:<6} {c['report_control_count']:<6} "
                  f"{c['dataset_count']:<6} {len(c['control_models']):<8} "
                  f"{auth_str:<6} {c['config_version']:<15}")


def main():
    parser = argparse.ArgumentParser(
        description='IEC 61850 入侵检测规则提取器（直接从 SCD 文件提取）',
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
    rules = extractor.extract_all_rules()

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        print(f"检测规则已保存: {args.output}")

    print_rules_summary(rules)


if __name__ == '__main__':
    main()
