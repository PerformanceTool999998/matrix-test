"""
MatrixTest - 报告生成器
支持 HTML / Markdown / Allure 格式
"""

import os
import json
from typing import List, Dict
from datetime import datetime
from pathlib import Path

from jinja2 import Template


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str = "./output/reports"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _format_time(self, time_str: str) -> str:
        """格式化时间字符串"""
        if not time_str:
            return "N/A"
        try:
            # 尝试解析 ISO 格式
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            # 如果已经是短格式，直接返回
            if len(time_str) == 8 and ':' in time_str:
                return time_str
            return time_str[:19] if len(time_str) > 19 else time_str

    def _format_duration(self, seconds: float) -> str:
        """格式化耗时"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"

    def generate_html(self, session) -> str:
        """生成 HTML 报告"""
        template = Template("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MatrixTest 测试报告 - {{ session.session_id }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header .meta { opacity: 0.9; margin-top: 8px; font-size: 0.95em; }
        .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; padding: 30px; max-width: 1200px; margin: -30px auto 0; }
        .card { background: white; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .card .number { font-size: 2.5em; font-weight: bold; }
        .card .label { color: #666; margin-top: 8px; }
        .passed { color: #10b981; }
        .failed { color: #ef4444; }
        .skipped { color: #f59e0b; }
        .total { color: #3b82f6; }
        .results { max-width: 1200px; margin: 30px auto; padding: 0 30px; }
        .results h2 { margin-bottom: 20px; color: #333; }
        .case { background: white; border-radius: 8px; margin-bottom: 16px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .case-header { padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; }
        .case-passed .case-header { background: #d1fae5; }
        .case-failed .case-header { background: #fee2e2; }
        .case-title { font-weight: 600; color: #333; }
        .case-status { padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; }
        .case-passed .case-status { background: #10b981; color: white; }
        .case-failed .case-status { background: #ef4444; color: white; }
        .case-body { padding: 20px; }
        .case-meta { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; color: #666; font-size: 0.9em; }
        .case-meta .icon { margin-right: 4px; }
        .steps { margin-top: 16px; }
        .steps h4 { margin-bottom: 12px; color: #333; }
        .step { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
        .step:last-child { border-bottom: none; }
        .step-icon { width: 24px; height: 24px; border-radius: 50%; margin-right: 12px; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }
        .step-success { background: #d1fae5; color: #10b981; }
        .step-fail { background: #fee2e2; color: #ef4444; }
        .step-info { flex: 1; }
        .step-desc { color: #333; }
        .step-detail { color: #999; font-size: 0.85em; margin-top: 2px; }
        .error-box { background: #fee2e2; border: 1px solid #fecaca; border-radius: 8px; padding: 12px 16px; margin-top: 12px; color: #991b1b; }
        .error-box strong { display: block; margin-bottom: 4px; }
        .perf-box { margin-top: 12px; padding: 12px 16px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #3b82f6; }
        .perf-box strong { color: #1e40af; }
        .footer { text-align: center; padding: 40px; color: #999; font-size: 0.9em; }
        @media (max-width: 768px) {
            .summary { grid-template-columns: repeat(2, 1fr); }
            .case-meta { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 MatrixTest 测试报告</h1>
        <div class="meta">会话 ID: {{ session.session_id }}</div>
        <div class="meta">{{ start_time }} ~ {{ end_time }}</div>
        <div class="meta">总耗时: {{ total_duration }}</div>
    </div>

    <div class="summary">
        <div class="card">
            <div class="number total">{{ session.total_cases }}</div>
            <div class="label">总用例</div>
        </div>
        <div class="card">
            <div class="number passed">{{ session.passed }}</div>
            <div class="label">通过</div>
        </div>
        <div class="card">
            <div class="number failed">{{ session.failed }}</div>
            <div class="label">失败</div>
        </div>
        <div class="card">
            <div class="number skipped">{{ session.skipped }}</div>
            <div class="label">跳过</div>
        </div>
    </div>

    <div class="results">
        <h2>详细结果</h2>
        {% for result in session.results %}
        <div class="case case-{{ result.status }}">
            <div class="case-header">
                <span class="case-title">{{ result.case_id }}: {{ result.case_name }}</span>
                <span class="case-status">{{ result.status.upper() }}</span>
            </div>
            <div class="case-body">
                <div class="case-meta">
                    <div><span class="icon">⏱️</span>耗时: {{ result.duration }}s</div>
                    <div><span class="icon">🕐</span>开始: {{ result.start_time_formatted }}</div>
                    <div><span class="icon">🕐</span>结束: {{ result.end_time_formatted }}</div>
                </div>

                {% if result.steps_result %}
                <div class="steps">
                    <h4>执行步骤</h4>
                    {% for step in result.steps_result %}
                    <div class="step">
                        <span class="step-icon {% if step.success %}step-success{% else %}step-fail{% endif %}">
                            {% if step.success %}✓{% else %}✗{% endif %}
                        </span>
                        <div class="step-info">
                            <div class="step-desc">{{ step.description }}</div>
                            {% if step.duration %}
                            <div class="step-detail">{{ step.action }} | {{ step.target_type }}: {{ step.target }} | {{ step.duration }}s</div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                {% if result.error_msg %}
                <div class="error-box">
                    <strong>❌ 错误信息</strong>
                    {{ result.error_msg }}
                </div>
                {% endif %}

                {% if result.perf_data %}
                <div class="perf-box">
                    <strong>📊 性能数据</strong><br>
                    CPU: {{ result.perf_data.cpu_avg }}% (avg) / {{ result.perf_data.cpu_max }}% (max) | 
                    内存: {{ result.perf_data.memory_avg }}MB (avg) / {{ result.perf_data.memory_max }}MB (max)
                </div>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="footer">
        <p>Generated by MatrixTest · {{ now }}</p>
    </div>
</body>
</html>
        """)

        # 计算总耗时
        total_duration = "N/A"
        if session.start_time and session.end_time:
            try:
                start = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
                end = datetime.fromisoformat(session.end_time.replace('Z', '+00:00'))
                duration = (end - start).total_seconds()
                total_duration = self._format_duration(duration)
            except:
                pass

        # 处理每个结果的时间
        for result in session.results:
            result.start_time_formatted = self._format_time(result.start_time)
            result.end_time_formatted = self._format_time(result.end_time)

        html = template.render(
            session=session,
            start_time=self._format_time(session.start_time),
            end_time=self._format_time(session.end_time),
            total_duration=total_duration,
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        filepath = f"{self.output_dir}/report_{session.session_id}.html"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"📄 HTML 报告已生成: {filepath}")
        return filepath

    def generate_markdown(self, session) -> str:
        """生成 Markdown 报告"""
        lines = [
            f"# 🧪 MatrixTest 测试报告",
            f"",
            f"**会话 ID:** {session.session_id}",
            f"**时间:** {self._format_time(session.start_time)} ~ {self._format_time(session.end_time)}",
            f"",
            f"## 📊 汇总",
            f"",
            f"| 指标 | 数量 |",
            f"|------|------|",
            f"| 总用例 | {session.total_cases} |",
            f"| ✅ 通过 | {session.passed} |",
            f"| ❌ 失败 | {session.failed} |",
            f"| ⏭️ 跳过 | {session.skipped} |",
            f"",
            f"## 📝 详细结果",
            f"",
        ]

        for result in session.results:
            icon = "✅" if result.status == "passed" else "❌"
            lines.extend([
                f"### {icon} {result.case_id}: {result.case_name}",
                f"",
                f"- **状态:** {result.status}",
                f"- **耗时:** {result.duration}s",
                f"- **时间:** {self._format_time(result.start_time)} ~ {self._format_time(result.end_time)}",
            ])

            if result.error_msg:
                lines.extend([
                    f"- **错误:** {result.error_msg}",
                ])

            if result.perf_data:
                lines.extend([
                    f"- **性能:** CPU {result.perf_data.get('cpu_avg', 'N/A')}% | 内存 {result.perf_data.get('memory_avg', 'N/A')}MB",
                ])

            lines.append("")

        md = "\n".join(lines)

        filepath = f"{self.output_dir}/report_{session.session_id}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"📄 Markdown 报告已生成: {filepath}")
        return filepath


if __name__ == "__main__":
    # 测试
    generator = ReportGenerator()
    print("报告生成器就绪")
