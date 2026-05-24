"""
ICD文件批量提取器
"""

from pathlib import Path
from collections import defaultdict
import json
import csv

from icd_parse.parser import ICDParser
from icd_parse.abbr_resolver import AbbrResolver
from icd_parse.abbr_dict import ABBREVIATIONS, LN_CLASS_MAP, FC_DETAIL


class ICDExtractor:
    """ICD/CID/SCD文件批量提取器"""

    def __init__(self, input_dir, output_dir=None, enable_semantic=True):
        self.input_path = Path(input_dir)
        # 支持直接传入单个文件
        self.is_single_file = self.input_path.is_file()
        if self.is_single_file:
            self.input_dir = self.input_path.parent
        else:
            self.input_dir = self.input_path
        self.output_dir = Path(output_dir) if output_dir else self.input_dir.parent / 'output'
        self.enable_semantic = enable_semantic

    def find_icd_files(self):
        """查找所有ICD/CID/SCD文件"""
        if self.is_single_file:
            return [self.input_path]

        files = []
        for ext in ['*.icd', '*.ICD', '*.cid', '*.CID', '*.scd', '*.SCD']:
            files.extend(self.input_dir.glob(ext))
        for ext in ['**/*.icd', '**/*.ICD', '**/*.cid', '**/*.CID', '**/*.scd', '**/*.SCD']:
            files.extend(self.input_dir.glob(ext))
        return sorted(set(files))

    def extract_all_files(self):
        """提取所有文件的完整信息"""
        files = self.find_icd_files()
        print(f"找到 {len(files)} 个ICD/CID/SCD文件")

        results = []
        for i, file_path in enumerate(files, 1):
            print(f"处理 [{i}/{len(files)}]: {file_path.name}")
            parser = ICDParser(file_path, enable_semantic=self.enable_semantic)
            result = parser.extract_all()
            if result:
                results.append(result)

        return results

    def extract_and_save_separately(self):
        """提取并分别保存到同名JSON文件，保持输入目录结构"""
        files = self.find_icd_files()
        print(f"找到 {len(files)} 个ICD/CID/SCD文件")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        success_count = 0

        # 获取输入目录的最后一级目录名，用于保持输出目录结构
        input_dir_name = self.input_dir.name

        for i, file_path in enumerate(files, 1):
            print(f"处理 [{i}/{len(files)}]: {file_path.name}")
            parser = ICDParser(file_path, enable_semantic=self.enable_semantic)
            result = parser.extract_all()
            if result:
                # 计算相对于输入目录的相对路径
                try:
                    rel_path = file_path.relative_to(self.input_dir)
                    # 如果相对路径直接是文件名（没有子目录），使用输入目录名作为子目录
                    if rel_path.parent == Path('.'):
                        json_rel_path = Path(input_dir_name) / (file_path.stem + '.json')
                    else:
                        json_rel_path = rel_path.parent / (file_path.stem + '.json')
                except ValueError:
                    # 如果无法计算相对路径，直接使用输入目录名
                    json_rel_path = Path(input_dir_name) / (file_path.stem + '.json')

                json_path = self.output_dir / json_rel_path
                json_path.parent.mkdir(parents=True, exist_ok=True)

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  -> 已保存: {json_rel_path}")
                success_count += 1

        print(f"\n成功提取并保存 {success_count} 个文件")
        return success_count

    def extract_summary_all(self):
        """提取所有文件的摘要信息"""
        files = self.find_icd_files()
        print(f"找到 {len(files)} 个ICD/CID/SCD文件")

        summaries = []
        for i, file_path in enumerate(files, 1):
            print(f"处理 [{i}/{len(files)}]: {file_path.name}")
            parser = ICDParser(file_path, enable_semantic=self.enable_semantic)
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
        """保存摘要到CSV文件（每个IED一行）"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / file_name

        if not summaries:
            print("无数据可保存")
            return None

        rows = []
        for s in summaries:
            file_name_val = s.get('file_name', '')
            for ied in s.get('ieds', []):
                row = {
                    'file_name': file_name_val,
                    'ied_name': ied.get('ied_name', ''),
                    'ied_type': ied.get('ied_type', ''),
                    'manufacturer': ied.get('manufacturer', ''),
                    'ldevice_count': ied.get('ldevice_count', 0),
                    'ln_count': ied.get('ln_count', 0),
                    'dataset_count': ied.get('dataset_count', 0),
                    'report_ctrl_count': ied.get('report_ctrl_count', 0),
                    'gse_ctrl_count': ied.get('gse_ctrl_count', 0),
                    'ln_classes': ','.join(ied.get('ln_classes', []))
                }
                rows.append(row)

        if not rows:
            print("无数据可保存")
            return None

        fieldnames = list(rows[0].keys())
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"摘要已保存: {output_path}")
        return output_path

    def generate_statistics_report(self, summaries):
        """生成统计报告"""
        if not summaries:
            return {}

        manufacturers = defaultdict(int)
        ied_types = defaultdict(int)
        ln_class_stats = defaultdict(int)
        total_ldevices = 0
        total_lns = 0
        total_datasets = 0
        total_report_controls = 0
        total_gse_controls = 0

        for s in summaries:
            for ied in s.get('ieds', []):
                mfr = ied.get('manufacturer', 'Unknown')
                manufacturers[mfr] += 1
                ied_type = ied.get('ied_type', 'Unknown')
                ied_types[ied_type] += 1
                total_ldevices += ied.get('ldevice_count', 0)
                total_lns += ied.get('ln_count', 0)
                total_datasets += ied.get('dataset_count', 0)
                total_report_controls += ied.get('report_ctrl_count', 0)
                total_gse_controls += ied.get('gse_ctrl_count', 0)
                for ln_class in ied.get('ln_classes', []):
                    ln_class_stats[ln_class] += 1

        return {
            'total_files': len(summaries),
            'total_ieds': sum(s.get('ied_count', 0) for s in summaries),
            'manufacturer_distribution': dict(manufacturers),
            'ied_type_distribution': dict(ied_types),
            'ln_class_distribution': dict(ln_class_stats),
            'total_ldevices': total_ldevices,
            'total_lns': total_lns,
            'total_datasets': total_datasets,
            'total_report_controls': total_report_controls,
            'total_gse_controls': total_gse_controls
        }