"""
测试报告生成器
支持 HTML / Markdown / JSON 格式
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Template

from config.settings import Config


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>MatrixTest 测试报告 - {{ run_id }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #e0e0e0; }
        .header h1 { color: #333; font-size: 28px; }
        .header .subtitle { color: #666; margin-top: 8px; }
        .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
        .summary-card { padding: 20px; border-radius: 8px; text-align: center; }
        .summary-card.passed { background: #e8f5e9; color: #2e7d32; }
        .summary-card.failed { background: #ffebee; color: #c62828; }
        .summary-card.total { background: #e3f2fd; color: #1565c0; }
        .summary-card.time { background: #fff3e0; color: #e65100; }
        .summary-card .number { font-size: 36px; font-weight: bold; }
        .summary-card .label { font-size: 14px; margin-top: 5px; }
        .case-list { margin-top: 20px; }
        .case-item { border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden; }
        .case-header { padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
        .case-header.passed { background: #e8f5e9; }
        .case-header.failed { background: #ffebee; }
        .case-header.error { background: #fff3e0; }
        .case-name { font-weight: 600; font-size: 16px; }
        .case-status { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .case-status.passed { background: #4caf50; color: white; }
        .case-status.failed { background: #f44336; color: white; }
        .case-status.error { background: #ff9800; color: white; }
        .case-body { padding: 20px; background: #fafafa; }
        .step-table { width: 100%; border-collapse: collapse; }
        .step-table th { background: #f0f0f0; padding: 10px; text-align: left; font-size: 13px; }
        .step-table td { padding: 10px; border-bottom: 1px solid #eee; font-size: 13px; }
        .step-table .status-pass { color: #4caf50; }
        .step-table .status-fail { color: #f44336; }
        .perf-section { margin-top: 15px; padding: 15px; background: white; border-radius: 6px; }
        .perf-section h4 { margin-bottom: 10px; color: #333; }
        .perf-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .perf-item { padding: 10px; background: #f5f5f5; border-radius: 4px; }
        .perf-item .label { font-size: 12px; color: #666; }
        .perf-item .value { font-size: 18px; font-weight: bold; color: #333; margin-top: 4px; }
        .screenshot { max-width: 300px; border-radius: 4px; margin-top: 10px; }
        .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #999; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 MatrixTest 测试报告</h1>
            <div class="subtitle">
                运行ID: {{ run_id }} | 时间: {{ start_time }} ~ {{ end_time }} | 总耗时: {{ total_duration }}s
            </div>
        </div>

        <div class="summary">
            <div class="summary-card total">
                <div class="number">{{ total_cases }}</div>
                <div class="label">总用例</div>
            </div>
            <div class="summary-card passed">
                <div class="number">{{ passed_cases }}</div>
                <div class="label">通过</div>
            </div>
            <div class="summary-card failed">
                <div class="number">{{ failed_cases }}</div>
                <div class="label">失败</div>
            </div>
            <div class="summary-card time">
                <div class="number">{{ total_duration }}s</div>
                <div class="label">总耗时</div>
            </div>
        </div>

        <div class="case-list">
            {% for case in cases %}
            <div class="case-item">
                <div class="case-header {{ case.status }}">
                    <span class="case-name">{{ case.case_name }}</span>
                    <span class="case-status {{ case.status }}">{{ case.status.upper() }}</span>
                </div>
                <div class="case-body">
                    <p><strong>用例ID:</strong> {{ case.case_id }} | <strong>耗时:</strong> {{ case.duration }}s</p>
                    {% if case.error %}
                    <p style="color: #c62828; margin-top: 8px;"><strong>错误:</strong> {{ case.error }}</p>
                    {% endif %}

                    <table class="step-table" style="margin-top: 15px;">
                        <tr>
                            <th>步骤</th>
                            <th>操作</th>
                            <th>描述</th>
                            <th>状态</th>
                            <th>耗时</th>
                        </tr>
                        {% for step in case.steps %}
                        <tr>
                            <td>{{ step.step }}</td>
                            <td>{{ step.action }}</td>
                            <td>{{ step.desc }}</td>
                            <td class="status-{{ 'pass' if step.status == 'passed' else 'fail' }}">{{ step.status }}</td>
                            <td>{{ step.elapsed }}s</td>
                        </tr>
                        {% endfor %}
                    </table>

                    {% if case.perf_report %}
                    <div class="perf-section">
                        <h4>📊 性能数据</h4>
                        <div class="perf-grid">
                            <div class="perf-item">
                                <div class="label">平均 CPU</div>
                                <div class="value">{{ case.perf_report.cpu.avg }}%</div>
                            </div>
                            <div class="perf-item">
                                <div class="label">平均 FPS</div>
                                <div class="value">{{ case.perf_report.fps.avg }}</div>
                            </div>
                            <div class="perf-item">
                                <div class="label">最高温度</div>
                                <div class="value">{{ case.perf_report.temperature.max }}°C</div>
                            </div>
                            <div class="perf-item">
                                <div class="label">总 Jank</div>
                                <div class="value">{{ case.perf_report.jank.total }}</div>
                            </div>
                            <div class="perf-item">
                                <div class="label">平均 PSS</div>
                                <div class="value">{{ case.perf_report.memory.avg_pss_kb // 1024 }}MB</div>
                            </div>
                            <div class="perf-item">
                                <div class="label">采集时长</div>
                                <div class="value">{{ case.perf_report.duration }}s</div>
                            </div>
                        </div>
                    </div>
                    {% endif %}

                    {% for screenshot in case.screenshots %}
                    <img src="{{ screenshot }}" class="screenshot" alt="截图">
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            Generated by MatrixTest | {{ timestamp }}
        </div>
    </div>
</body>
</html>
"""


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or Config.REPORT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html(self, results: List[Dict], run_id: Optional[str] = None) -> str:
        """生成 HTML 报告"""
        run_id = run_id or Config.TEST_RUN_ID

        # 统计
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = sum(1 for r in results if r["status"] == "failed")
        total_duration = sum(r["duration"] for r in results)

        template = Template(HTML_TEMPLATE)
        html = template.render(
            run_id=run_id,
            start_time=results[0]["start_time"] if results else "",
            end_time=results[-1]["end_time"] if results else "",
            total_duration=round(total_duration, 1),
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            cases=results,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        filepath = self.output_dir / f"report_{run_id}_{time.strftime('%Y%m%d_%H%M%S')}.html"
        filepath.write_text(html, encoding="utf-8")

        print(f"📄 HTML 报告已生成: {filepath}")
        return str(filepath)

    def generate_json(self, results: List[Dict], run_id: Optional[str] = None) -> str:
        """生成 JSON 报告"""
        run_id = run_id or Config.TEST_RUN_ID

        report = {
            "run_id": run_id,
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r["status"] == "passed"),
                "failed": sum(1 for r in results if r["status"] == "failed"),
                "duration": sum(r["duration"] for r in results)
            },
            "cases": results,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        filepath = self.output_dir / f"report_{run_id}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        filepath.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"📄 JSON 报告已生成: {filepath}")
        return str(filepath)

    def generate_markdown(self, results: List[Dict], run_id: Optional[str] = None) -> str:
        """生成 Markdown 报告"""
        run_id = run_id or Config.TEST_RUN_ID

        lines = [
            f"# 🧪 MatrixTest 测试报告",
            f"",
            f"**运行ID:** {run_id}",
            f"**时间:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 📊 汇总",
            f"",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总用例 | {len(results)} |",
            f"| 通过 | {sum(1 for r in results if r['status'] == 'passed')} |",
            f"| 失败 | {sum(1 for r in results if r['status'] == 'failed')} |",
            f"| 总耗时 | {sum(r['duration'] for r in results):.1f}s |",
            f"",
            f"## 📋 用例详情",
            f"",
        ]

        for case in results:
            status_emoji = "✅" if case["status"] == "passed" else "❌"
            lines.append(f"### {status_emoji} {case['case_name']}")
            lines.append(f"")
            lines.append(f"- **状态:** {case['status']}")
            lines.append(f"- **耗时:** {case['duration']}s")
            if case.get("error"):
                lines.append(f"- **错误:** {case['error']}")
            lines.append(f"")
            lines.append(f"| 步骤 | 操作 | 描述 | 状态 |")
            lines.append(f"|------|------|------|------|")
            for step in case.get("steps", []):
                lines.append(f"| {step['step']} | {step['action']} | {step['desc']} | {step['status']} |")
            lines.append(f"")

        content = "\n".join(lines)
        filepath = self.output_dir / f"report_{run_id}_{time.strftime('%Y%m%d_%H%M%S')}.md"
        filepath.write_text(content, encoding="utf-8")

        print(f"📄 Markdown 报告已生成: {filepath}")
        return str(filepath)


if __name__ == "__main__":
    # 测试
    sample_results = [
        {
            "case_name": "登录测试",
            "case_id": "LOGIN_001",
            "status": "passed",
            "duration": 5.2,
            "steps": [
                {"step": 1, "action": "click", "desc": "点击登录", "status": "passed", "elapsed": 1.0}
            ]
        }
    ]

    gen = ReportGenerator()
    gen.generate_html(sample_results)
    gen.generate_json(sample_results)
    gen.generate_markdown(sample_results)
