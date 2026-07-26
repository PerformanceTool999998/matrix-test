#!/usr/bin/env python3
"""
MatrixTest - Android AI 自动化测试平台
入口文件
"""

import os
import sys
import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_generator import AICaseGenerator
from core.engine.test_engine import TestEngine
from core.reporter.report_generator import ReportGenerator
from core.executor.mock_executor import MockUIExecutor

try:
    from core.executor.ui_executor import UIExecutor
    HAS_UIAUTOMATOR = True
except ImportError:
    HAS_UIAUTOMATOR = False
    print("⚠️ uiautomator2 未安装，真实设备模式不可用")

from core.perf_monitor.perf_monitor import PerfMonitor


def cmd_generate(args):
    """生成测试用例"""
    print("🤖 AI 用例生成模式")
    
    generator = AICaseGenerator()
    
    prd_text = ""
    if args.prd:
        with open(args.prd, "r", encoding="utf-8") as f:
            prd_text = f.read()
    else:
        prd_text = args.text or ""
    
    if not prd_text:
        print("❌ 请提供 PRD 文件 (--prd) 或文本 (--text)")
        return
    
    cases = generator.generate_from_prd(prd_text, args.package)
    
    output_dir = Path(args.output or "tests/cases")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator.export_to_yaml(cases, f"{output_dir}/generated_cases.yaml")
    
    print(f"✅ 已生成 {len(cases)} 条用例")
    for case in cases:
        print(f"   - {case.id}: {case.name} [{case.priority}]")


def cmd_run(args):
    """执行测试"""
    print("🚀 测试执行模式")
    
    if args.mock or not HAS_UIAUTOMATOR:
        print("📱 使用 Mock 执行器（无真实设备）")
        executor = MockUIExecutor(
            device_serial=args.device,
            target_package=args.package,
            fail_rate=args.mock_fail_rate if args.mock_fail_rate is not None else 0.1
        )
        perf_monitor = PerfMonitor() if args.perf else None
    else:
        print("📱 使用真实设备执行器")
        executor = UIExecutor(device_serial=args.device, target_package=args.package)
        perf_monitor = PerfMonitor() if args.perf else None
    
    if not executor.connect():
        print("❌ 设备连接失败，退出")
        return
    
    if args.package:
        executor.start_app(args.package, args.activity)
    
    engine = TestEngine()
    session = engine.start_session(args.suite or "default")
    
    import yaml
    cases = []
    
    if args.cases:
        case_file = Path(args.cases)
        if case_file.exists():
            with open(case_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                from ai_generator import TestCase, TestStep
                for case_data in data.get("cases", []):
                    steps = [TestStep(**s) for s in case_data.get("steps", [])]
                    cases.append(TestCase(
                        id=case_data["id"],
                        name=case_data["name"],
                        description=case_data.get("description", ""),
                        priority=case_data.get("priority", "P1"),
                        preconditions=case_data.get("preconditions", []),
                        steps=steps,
                        expected_result=case_data.get("expected_result", ""),
                        tags=case_data.get("tags", [])
                    ))
    
    if not cases:
        print("⚠️ 没有找到用例，使用默认示例")
        generator = AICaseGenerator()
        cases = generator._get_default_cases()
    
    print(f"📋 共加载 {len(cases)} 条用例")
    
    engine.run_cases(cases, executor, perf_monitor)
    engine.end_session()
    
    if args.report:
        reporter = ReportGenerator()
        if args.report == "html":
            reporter.generate_html(session)
        elif args.report == "md":
            reporter.generate_markdown(session)
        elif args.report == "all":
            reporter.generate_html(session)
            reporter.generate_markdown(session)
    
    engine.export_results()
    executor.stop_app()
    
    print(f"\n✅ 测试完成！查看报告: output/reports/")


def cmd_ci(args):
    """CI/CD 模式"""
    print("🔧 CI/CD 模式")
    
    suite = args.suite or os.getenv("TEST_SUITE", "smoke")
    print(f"执行测试套件: {suite}")
    
    args.cases = f"tests/fixtures/{suite}.yaml"
    args.perf = False
    args.report = "all"
    args.mock = args.mock or not HAS_UIAUTOMATOR
    cmd_run(args)


def main():
    parser = argparse.ArgumentParser(
        description="MatrixTest - Android AI 自动化测试平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # AI 生成用例
  python main.py generate --prd docs/prd.md --package com.example.app

  # 真实设备执行测试
  python main.py run --cases tests/cases/login.yaml --package com.example.app --perf --report html

  # Mock 模式（无设备，快速验证）
  python main.py run --cases tests/fixtures/smoke.yaml --mock --report html

  # CI 模式
  python main.py ci --suite smoke
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    gen_parser = subparsers.add_parser("generate", help="生成测试用例")
    gen_parser.add_argument("--prd", help="PRD 文件路径")
    gen_parser.add_argument("--text", help="需求文本")
    gen_parser.add_argument("--package", default="", help="目标应用包名")
    gen_parser.add_argument("--output", default="tests/cases", help="输出目录")
    gen_parser.set_defaults(func=cmd_generate)
    
    run_parser = subparsers.add_parser("run", help="执行测试")
    run_parser.add_argument("--cases", help="用例文件路径")
    run_parser.add_argument("--device", default="", help="设备序列号")
    run_parser.add_argument("--package", default="", help="目标应用包名")
    run_parser.add_argument("--activity", default="", help="启动 Activity")
    run_parser.add_argument("--perf", action="store_true", help="启用性能监控")
    run_parser.add_argument("--mock", action="store_true", help="Mock 模式（无设备）")
    run_parser.add_argument("--mock-fail-rate", type=float, default=0.1, help="Mock 失败率 (0-1)")
    run_parser.add_argument("--report", choices=["html", "md", "all"], help="报告格式")
    run_parser.add_argument("--suite", default="", help="测试套件名称")
    run_parser.set_defaults(func=cmd_run)
    
    ci_parser = subparsers.add_parser("ci", help="CI/CD 模式")
    ci_parser.add_argument("--suite", default="smoke", help="测试套件")
    ci_parser.add_argument("--device", default="", help="设备序列号")
    ci_parser.add_argument("--package", default="", help="目标应用包名")
    ci_parser.add_argument("--mock", action="store_true", help="Mock 模式")
    ci_parser.set_defaults(func=cmd_ci)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
