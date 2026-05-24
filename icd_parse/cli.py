"""
命令行入口
"""

import argparse
import json

from icd_parse.extractor import ICDExtractor
from icd_parse.abbr_resolver import AbbrResolver
from icd_parse.abbr_dict import ABBREVIATIONS, LN_CLASS_MAP, FC_DETAIL
from icd_parse.utils import (
    print_extraction_info,
    print_semantic_reference,
    generate_semantic_report,
    print_ln_semantic_table
)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='IEC 61850 ICD/CID/SCD文件信息提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python cli.py input/61850ICD                  # 摘要模式
  python cli.py input/中科院.scd                # 解析单个SCD文件
  python cli.py input/61850ICD -m full          # 完整提取
  python cli.py input/61850ICD -m semantic      # 语义解析模式
  python cli.py --show-reference                # 显示缩写参考表
        """
    )
    parser.add_argument('input_path', nargs='?', default='input',
                        help='输入目录或文件路径 (默认: input)')
    parser.add_argument('-o', '--output', help='输出目录路径', default=None)
    parser.add_argument('-m', '--mode',
                        choices=['full', 'summary', 'stats', 'semantic'],
                        default='summary',
                        help='提取模式：full(完整)/summary(摘要)/stats(统计)/semantic(语义解析)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='显示详细信息')
    parser.add_argument('--no-semantic', action='store_true',
                        help='禁用语义解析')
    parser.add_argument('--show-reference', action='store_true',
                        help='显示缩写参考表')

    args = parser.parse_args()

    if args.verbose:
        print_extraction_info()

    if args.show_reference:
        print_semantic_reference()
        return

    enable_semantic = not args.no_semantic
    extractor = ICDExtractor(args.input_path, args.output, enable_semantic=enable_semantic)

    if args.mode == 'full':
        extractor.extract_and_save_separately()

    elif args.mode == 'summary':
        summaries = extractor.extract_summary_all()
        extractor.save_to_json(summaries, 'icd_summary.json')
        extractor.save_summary_to_csv(summaries)

        stats = extractor.generate_statistics_report(summaries)
        extractor.save_to_json(stats, 'icd_statistics.json')

        print("\n" + "=" * 60)
        print("统计摘要")
        print("=" * 60)
        print(f"文件总数: {stats.get('total_files', 0)}")
        print(f"IED总数: {stats.get('total_ieds', 0)}")
        print(f"逻辑设备总数: {stats.get('total_ldevices', 0)}")
        print(f"逻辑节点总数: {stats.get('total_lns', 0)}")
        print(f"数据集总数: {stats.get('total_datasets', 0)}")
        print(f"报告控制块总数: {stats.get('total_report_controls', 0)}")
        print(f"GOOSE控制块总数: {stats.get('total_gse_controls', 0)}")

        if enable_semantic and stats.get('ln_class_distribution'):
            print_ln_semantic_table(stats['ln_class_distribution'])

    elif args.mode == 'stats':
        summaries = extractor.extract_summary_all()
        stats = extractor.generate_statistics_report(summaries)
        extractor.save_to_json(stats, 'icd_statistics.json')
        print(json.dumps(stats, ensure_ascii=False, indent=2))

    elif args.mode == 'semantic':
        # 语义解析模式：完整提取 + 语义标注，每个文件单独保存
        extractor.extract_and_save_separately()

        # 生成语义解析报告
        results = extractor.extract_all_files()
        semantic_report = generate_semantic_report(results)
        extractor.save_to_json(semantic_report, 'icd_semantic_report.json')

        print("\n" + "=" * 60)
        print("语义解析报告")
        print("=" * 60)
        print(f"文件总数: {semantic_report.get('total_files', 0)}")
        print(f"缩写字典词条: {len(ABBREVIATIONS)}")
        print(f"逻辑节点类型定义: {len(LN_CLASS_MAP)}")
        print(f"功能约束类型: {len(FC_DETAIL)}")

        ln_semantics = semantic_report.get('ln_class_semantics', {})
        if ln_semantics:
            sorted_items = sorted(ln_semantics.items(),
                                  key=lambda x: x[1].get('count', 0), reverse=True)[:15]
            print("\n逻辑节点语义对照表:")
            print("-" * 60)
            for ln_class, info in sorted_items:
                semantic = info.get('semantic', {})
                zh = semantic.get('zh', ln_class) if semantic else ln_class
                group = semantic.get('group', 'Unknown') if semantic else 'Unknown'
                print(f"  {ln_class:8s} | {zh:20s} | {group:15s} | 出现次数: {info['count']}")


if __name__ == '__main__':
    main()