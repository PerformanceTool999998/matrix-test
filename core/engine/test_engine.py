"""
MatrixTest - 测试执行引擎
协调 AI 生成、UI 执行、性能监控、报告输出
"""

import os
import time
import json
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class TestResult:
    """单条用例执行结果"""
    case_id: str
    case_name: str
    status: str          # passed / failed / skipped / error
    duration: float      # 执行耗时（秒）
    start_time: str
    end_time: str
    steps_result: List[Dict]
    screenshot: Optional[str] = None
    error_msg: Optional[str] = None
    perf_data: Optional[Dict] = None


@dataclass
class TestSession:
    """测试会话"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    results: List[TestResult] = None

    def __post_init__(self):
        if self.results is None:
            self.results = []


class TestEngine:
    """测试执行引擎"""

    def __init__(self):
        self.session: Optional[TestSession] = None
        self.device = None
        self.perf_monitor = None
        self.reporter = None
        self.hooks: Dict[str, List[Callable]] = {
            "before_session": [],
            "before_case": [],
            "after_case": [],
            "after_session": []
        }

    def register_hook(self, event: str, callback: Callable):
        """注册生命周期钩子"""
        if event in self.hooks:
            self.hooks[event].append(callback)

    def _trigger_hooks(self, event: str, **kwargs):
        """触发钩子"""
        for callback in self.hooks.get(event, []):
            try:
                callback(**kwargs)
            except Exception as e:
                print(f"Hook {event} 执行失败: {e}")

    def start_session(self, session_name: str = "") -> TestSession:
        """启动测试会话"""
        self.session = TestSession(
            session_id=f"TS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_time=datetime.now().isoformat()
        )

        print(f"🚀 测试会话启动: {self.session.session_id}")
        self._trigger_hooks("before_session", session=self.session)
        return self.session

    def end_session(self):
        """结束测试会话"""
        if not self.session:
            return

        self.session.end_time = datetime.now().isoformat()

        # 统计结果
        for result in self.session.results:
            self.session.total_cases += 1
            if result.status == "passed":
                self.session.passed += 1
            elif result.status == "failed":
                self.session.failed += 1
            else:
                self.session.skipped += 1

        self._trigger_hooks("after_session", session=self.session)

        print(f"📊 测试完成:")
        print(f"   总计: {self.session.total_cases}")
        print(f"   ✅ 通过: {self.session.passed}")
        print(f"   ❌ 失败: {self.session.failed}")
        print(f"   ⏭️ 跳过: {self.session.skipped}")

    def run_case(self, case, executor, perf_monitor=None) -> TestResult:
        """执行单条用例"""
        if not self.session:
            raise RuntimeError("请先调用 start_session()")

        self._trigger_hooks("before_case", case=case)

        start_time = time.time()
        start_iso = datetime.now().isoformat()

        try:
            # 启动性能监控
            if perf_monitor:
                perf_monitor.start()

            # 执行用例
            steps_result = executor.execute(case)

            # 停止性能监控
            perf_data = None
            if perf_monitor:
                perf_data = perf_monitor.stop()

            status = "passed"
            error_msg = None

            # 检查步骤结果
            for step in steps_result:
                if not step.get("success", True):
                    status = "failed"
                    error_msg = step.get("error", "未知错误")
                    break

        except Exception as e:
            status = "error"
            error_msg = str(e)
            steps_result = []
            perf_data = None

        end_time = time.time()
        end_iso = datetime.now().isoformat()

        result = TestResult(
            case_id=case.id,
            case_name=case.name,
            status=status,
            duration=round(end_time - start_time, 2),
            start_time=start_iso,
            end_time=end_iso,
            steps_result=steps_result,
            perf_data=perf_data,
            error_msg=error_msg
        )

        self.session.results.append(result)
        self._trigger_hooks("after_case", case=case, result=result)

        icon = "✅" if status == "passed" else "❌"
        print(f"{icon} {case.id}: {case.name} ({result.duration}s)")
        if error_msg:
            print(f"   错误: {error_msg}")

        return result

    def run_cases(self, cases: List, executor, perf_monitor=None):
        """批量执行用例"""
        for case in cases:
            self.run_case(case, executor, perf_monitor)

    def export_results(self, output_dir: str = "./output"):
        """导出测试结果"""
        if not self.session:
            return

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # JSON 格式
        json_path = f"{output_dir}/result_{self.session.session_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self.session.session_id,
                "start_time": self.session.start_time,
                "end_time": self.session.end_time,
                "summary": {
                    "total": self.session.total_cases,
                    "passed": self.session.passed,
                    "failed": self.session.failed,
                    "skipped": self.session.skipped
                },
                "results": [asdict(r) for r in self.session.results]
            }, f, ensure_ascii=False, indent=2)

        print(f"📁 结果已导出: {json_path}")
        return json_path


if __name__ == "__main__":
    # 测试
    engine = TestEngine()
    session = engine.start_session("冒烟测试")

    # 模拟执行
    class MockCase:
        id = "TC_001"
        name = "测试用例1"

    class MockExecutor:
        def execute(self, case):
            return [{"step": 1, "success": True}]

    engine.run_case(MockCase(), MockExecutor())
    engine.end_session()
    engine.export_results()
