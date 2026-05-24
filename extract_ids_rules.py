"""
IEC 61850 入侵检测规则提取器

从解析后的 SCD/ICD JSON 文件中提取网络白名单规则，用于工控网络入侵检测。
生成的规则涵盖：GOOSE/SMV 白名单、MMS 通信白名单、配置变更检测规则。
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict


def load_parsed_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_goose_rules(data):
    """提取 GOOSE 白名单规则：合法的 GOOSE 发布者、MAC、APPID、数据集"""
    rules = []
    comm = data.get('communication', {})

    # 建立 IED → AccessPoint 映射
    ied_ap_map = {}
    for ied in data.get('ieds', []):
        ied_name = ied.get('name', '')
        ied_ap_map[ied_name] = ied

    for sn in comm.get('subNetworks', []):
        sn_name = sn.get('name', '')
        sn_type = sn.get('type', '')
        for ap in sn.get('connectedAPs', []):
            ied_name = ap.get('iedName', '')
            for gse in ap.get('gse', []):
                gse_addr = gse.get('address', {})
                rule = {
                    'rule_type': 'GOOSE_WHITELIST',
                    'publisher_ied': ied_name,
                    'subnetwork': sn_name,
                    'network_type': sn_type,
                    'control_block': gse.get('cbName', ''),
                    'ld_inst': gse.get('ldInst', ''),
                    'mac_address': gse_addr.get('MAC-Address', ''),
                    'vlan_id': gse_addr.get('VLAN-ID', ''),
                    'vlan_priority': gse_addr.get('VLAN-PRIORITY', ''),
                    'appid': gse_addr.get('APPID', ''),
                }

                # 从 IED 配置中补充数据集信息
                ied = ied_ap_map.get(ied_name)
                if ied:
                    for ld in ied.get('lDevices', []):
                        if ld.get('inst') == rule['ld_inst']:
                            ln0 = ld.get('ln0', {})
                            for gc in ln0.get('gseControls', []):
                                if gc.get('name') == rule['control_block']:
                                    rule['dataset'] = gc.get('datSet', '')
                                    rule['appID_config'] = gc.get('appID', '')
                                    # 补充 FCDA 数量
                                    for ds in ln0.get('datasets', []):
                                        if ds['name'] == rule['dataset']:
                                            rule['fcda_count'] = ds.get('fcda_count', len(ds.get('fcdas', [])))
                                            break
                                    break

                rules.append(rule)

    return rules


def extract_smv_rules(data):
    """提取 SMV 采样值白名单规则"""
    rules = []
    comm = data.get('communication', {})

    for sn in comm.get('subNetworks', []):
        sn_name = sn.get('name', '')
        for ap in sn.get('connectedAPs', []):
            ied_name = ap.get('iedName', '')
            for smv in ap.get('smv', []):
                smv_addr = smv.get('address', {})
                rule = {
                    'rule_type': 'SMV_WHITELIST',
                    'publisher_ied': ied_name,
                    'subnetwork': sn_name,
                    'control_block': smv.get('cbName', ''),
                    'ld_inst': smv.get('ldInst', ''),
                    'mac_address': smv_addr.get('MAC-Address', ''),
                    'vlan_id': smv_addr.get('VLAN-ID', ''),
                    'vlan_priority': smv_addr.get('VLAN-PRIORITY', ''),
                    'appid': smv_addr.get('APPID', ''),
                }
                rules.append(rule)

    return rules


def extract_mms_rules(data):
    """提取 MMS 通信白名单规则：合法的 IED IP 地址和报告订阅关系"""
    rules = []
    comm = data.get('communication', {})

    for sn in comm.get('subNetworks', []):
        sn_name = sn.get('name', '')
        sn_type = sn.get('type', '')
        if 'MMS' not in sn_type:
            continue

        subnet_info = {
            'rule_type': 'MMS_SUBNET',
            'subnetwork': sn_name,
            'connected_ieds': [],
        }

        for ap in sn.get('connectedAPs', []):
            ied_name = ap.get('iedName', '')
            addr = ap.get('address', {})
            ip = addr.get('IP', '')
            subnet = addr.get('IP-SUBNET', '')
            gateway = addr.get('IP-GATEWAY', '')

            ied_info = {
                'ied_name': ied_name,
                'ip': ip,
                'subnet_mask': subnet,
                'gateway': gateway,
            }

            # 补充该 IED 提供的报告服务
            for ied in data.get('ieds', []):
                if ied.get('name') == ied_name:
                    reports = []
                    for ld in ied.get('lDevices', []):
                        ln0 = ld.get('ln0', {})
                        for rc in ln0.get('reportControls', []):
                            reports.append({
                                'name': rc.get('name', ''),
                                'dataset': rc.get('datSet', ''),
                                'buffered': rc.get('buffered', ''),
                                'ld_inst': ld.get('inst', ''),
                            })
                    ied_info['report_services'] = reports
                    break

            subnet_info['connected_ieds'].append(ied_info)

        rules.append(subnet_info)

    return rules


def extract_config_integrity_rules(data):
    """提取配置完整性检测规则：IED 配置版本、数据集成员数、控制块数量"""
    rules = []

    for ied in data.get('ieds', []):
        ied_name = ied.get('name', '')

        # 配置基线规则
        baseline = {
            'rule_type': 'CONFIG_BASELINE',
            'ied_name': ied_name,
            'ied_type': ied.get('type', ''),
            'manufacturer': ied.get('manufacturer', ''),
            'config_version': ied.get('configVersion', ''),
            'ldevice_count': len(ied.get('lDevices', [])),
        }

        # 统计控制块和数据集数量
        gse_count = 0
        report_count = 0
        dataset_count = 0
        dataset_signatures = []

        for ld in ied.get('lDevices', []):
            ln0 = ld.get('ln0', {})
            gse_ctrls = ln0.get('gseControls', [])
            report_ctrls = ln0.get('reportControls', [])
            datasets = ln0.get('datasets', [])

            gse_count += len(gse_ctrls)
            report_count += len(report_ctrls)
            dataset_count += len(datasets)

            for ds in datasets:
                fcda_count = ds.get('fcda_count', len(ds.get('fcdas', [])))
                dataset_signatures.append({
                    'ld_inst': ld.get('inst', ''),
                    'dataset_name': ds.get('name', ''),
                    'fcda_count': fcda_count,
                })

        baseline['gse_control_count'] = gse_count
        baseline['report_control_count'] = report_count
        baseline['dataset_count'] = dataset_count
        baseline['dataset_signatures'] = dataset_signatures

        rules.append(baseline)

    return rules


def extract_goose_subscription_rules(data):
    """提取 GOOSE 订阅关系规则：哪些 IED 应该接收哪些 GOOSE"""
    rules = []

    # 先收集所有 GOOSE 发布者
    publishers = {}
    for ied in data.get('ieds', []):
        ied_name = ied.get('name', '')
        for ld in ied.get('lDevices', []):
            ln0 = ld.get('ln0', {})
            for gc in ln0.get('gseControls', []):
                key = f"{ied_name}/{ld.get('inst', '')}/{gc.get('name', '')}"
                publishers[key] = {
                    'publisher_ied': ied_name,
                    'ld_inst': ld.get('inst', ''),
                    'control_block': gc.get('name', ''),
                    'dataset': gc.get('datSet', ''),
                    'appID': gc.get('appID', ''),
                }

    # 通过 FCDA 中的 ldInst/lnClass 推断订阅关系
    # 如果一个 IED 的数据集引用了另一个 IED 的数据，说明它可能订阅了那个 IED 的 GOOSE
    # 更直接的方式：通过 LN 中的 DOI 输入引用识别
    for ied in data.get('ieds', []):
        ied_name = ied.get('name', '')
        subscriptions = []

        for ld in ied.get('lDevices', []):
            ln0 = ld.get('ln0', {})
            for ds in ln0.get('datasets', []):
                for fcda in ds.get('fcdas', []):
                    fcda_ld = fcda.get('ldInst', '')
                    # 如果 FCDA 引用的 ldInst 不属于当前 IED 的任何 LDevice，说明是外部输入
                    if fcda_ld and fcda_ld not in [l.get('inst', '') for l in ied.get('lDevices', [])]:
                        # 这是外部引用，记录订阅关系
                        sub = {
                            'source_ld_inst': fcda_ld,
                            'source_ln_class': fcda.get('lnClass', ''),
                            'source_do_name': fcda.get('doName', ''),
                            'fc': fcda.get('fc', ''),
                        }
                        if sub not in subscriptions:
                            subscriptions.append(sub)

        if subscriptions:
            rules.append({
                'rule_type': 'GOOSE_SUBSCRIPTION',
                'subscriber_ied': ied_name,
                'external_inputs': subscriptions,
            })

    return rules


def extract_network_segmentation_rules(data):
    """提取网络分区规则：过程层 vs 站控层的 IED 分组"""
    rules = []
    comm = data.get('communication', {})

    segments = defaultdict(lambda: {'ieds': [], 'macs': [], 'appids': []})

    for sn in comm.get('subNetworks', []):
        sn_name = sn.get('name', '')
        sn_type = sn.get('type', '')
        ied_names = set()

        for ap in sn.get('connectedAPs', []):
            ied_name = ap.get('iedName', '')
            ied_names.add(ied_name)

            for gse in ap.get('gse', []):
                addr = gse.get('address', {})
                mac = addr.get('MAC-Address', '')
                appid = addr.get('APPID', '')
                if mac:
                    segments[sn_name]['macs'].append(mac)
                if appid:
                    segments[sn_name]['appids'].append(appid)

            for smv in ap.get('smv', []):
                addr = smv.get('address', {})
                mac = addr.get('MAC-Address', '')
                appid = addr.get('APPID', '')
                if mac:
                    segments[sn_name]['macs'].append(mac)
                if appid:
                    segments[sn_name]['appids'].append(appid)

        segments[sn_name]['ieds'] = sorted(list(ied_names))

    for sn_name, info in segments.items():
        rules.append({
            'rule_type': 'NETWORK_SEGMENT',
            'subnetwork': sn_name,
            'allowed_ieds': info['ieds'],
            'allowed_macs': sorted(list(set(info['macs']))),
            'allowed_appids': sorted(list(set(info['appids']))),
        })

    return rules


def generate_ids_rules(json_path, output_path=None):
    """主函数：从解析后的 JSON 文件生成入侵检测规则"""
    data = load_parsed_data(json_path)

    all_rules = {
        'source_file': data.get('file_name', ''),
        'description': '基于 SCD 配置自动提取的 IEC 61850 入侵检测规则',
        'rule_categories': {
            'goose_whitelist': extract_goose_rules(data),
            'smv_whitelist': extract_smv_rules(data),
            'mms_whitelist': extract_mms_rules(data),
            'goose_subscription': extract_goose_subscription_rules(data),
            'network_segmentation': extract_network_segmentation_rules(data),
            'config_integrity': extract_config_integrity_rules(data),
        },
        'rule_summary': {},
    }

    # 统计
    for cat, rules in all_rules['rule_categories'].items():
        all_rules['rule_summary'][cat] = len(rules)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_rules, f, ensure_ascii=False, indent=2)
        print(f"检测规则已保存: {output_path}")

    return all_rules


def print_rules_summary(rules):
    """打印规则摘要"""
    print("\n" + "=" * 70)
    print("IEC 61850 入侵检测规则摘要")
    print("=" * 70)
    print(f"源文件: {rules['source_file']}")

    summary = rules['rule_summary']
    print(f"\n规则统计:")
    print(f"  GOOSE 白名单规则: {summary.get('goose_whitelist', 0)} 条")
    print(f"  SMV 白名单规则:   {summary.get('smv_whitelist', 0)} 条")
    print(f"  MMS 通信白名单:   {summary.get('mms_whitelist', 0)} 条")
    print(f"  GOOSE 订阅关系:   {summary.get('goose_subscription', 0)} 条")
    print(f"  网络分区规则:     {summary.get('network_segmentation', 0)} 条")
    print(f"  配置基线规则:     {summary.get('config_integrity', 0)} 条")

    # GOOSE 白名单详情
    goose_rules = rules['rule_categories']['goose_whitelist']
    if goose_rules:
        print(f"\n{'─' * 70}")
        print("GOOSE 白名单（合法的 GOOSE 发布者）:")
        print(f"{'─' * 70}")
        print(f"{'IED':<10} {'CB':<10} {'LD':<10} {'MAC':<22} {'APPID':<8} {'FCDA数':<6}")
        print(f"{'─' * 70}")
        for r in goose_rules:
            print(f"{r['publisher_ied']:<10} {r['control_block']:<10} {r['ld_inst']:<10} "
                  f"{r['mac_address']:<22} {r['appid']:<8} {r.get('fcda_count', '?'):<6}")

    # SMV 白名单
    smv_rules = rules['rule_categories']['smv_whitelist']
    if smv_rules:
        print(f"\n{'─' * 70}")
        print("SMV 采样值白名单:")
        print(f"{'─' * 70}")
        print(f"{'IED':<10} {'CB':<12} {'LD':<10} {'MAC':<22} {'APPID':<8}")
        print(f"{'─' * 70}")
        for r in smv_rules:
            print(f"{r['publisher_ied']:<10} {r['control_block']:<12} {r['ld_inst']:<10} "
                  f"{r['mac_address']:<22} {r['appid']:<8}")

    # 网络分区
    seg_rules = rules['rule_categories']['network_segmentation']
    if seg_rules:
        print(f"\n{'─' * 70}")
        print("网络分区规则:")
        print(f"{'─' * 70}")
        for r in seg_rules:
            print(f"  子网: {r['subnetwork']}")
            print(f"    合法 IED: {', '.join(r['allowed_ieds'])}")
            print(f"    合法 MAC: {len(r['allowed_macs'])} 个")
            print(f"    合法 APPID: {', '.join(r['allowed_appids'])}")

    # 配置基线
    config_rules = rules['rule_categories']['config_integrity']
    if config_rules:
        print(f"\n{'─' * 70}")
        print("配置基线（用于检测未授权配置变更）:")
        print(f"{'─' * 70}")
        print(f"{'IED':<10} {'类型':<20} {'LD数':<6} {'GOOSE':<7} {'报告':<7} {'数据集':<7} {'版本':<15}")
        print(f"{'─' * 70}")
        for r in config_rules:
            print(f"{r['ied_name']:<10} {r['ied_type']:<20} {r['ldevice_count']:<6} "
                  f"{r['gse_control_count']:<7} {r['report_control_count']:<7} "
                  f"{r['dataset_count']:<7} {r['config_version']:<15}")


def main():
    parser = argparse.ArgumentParser(
        description='IEC 61850 入侵检测规则提取器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python extract_ids_rules.py output/input/中科院.json
  python extract_ids_rules.py output/input/中科院.json -o output/ids_rules.json
        """
    )
    parser.add_argument('json_path', help='解析后的 SCD/ICD JSON 文件路径')
    parser.add_argument('-o', '--output', help='输出规则文件路径')

    args = parser.parse_args()

    rules = generate_ids_rules(args.json_path, args.output)
    print_rules_summary(rules)


if __name__ == '__main__':
    main()
