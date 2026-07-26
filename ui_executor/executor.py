"""
UI 自动化执行引擎
解析 JSON 用例 → 执行 uiautomator2 操作
"""
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional
import uiautomator2 as u2

from config.settings import Config
from ui_executor.device import DeviceManager


class CaseExecutor:
    """测试用例执行器"""

    def __init__(self, device_manager: Optional[DeviceManager] = None):
        self.dm = device_manager or DeviceManager()
        self.d: u2.Device = u2.connect(self.dm.serial)
        self.results = []
        self.current_case = None

    def execute_case(self, case: Dict) -> Dict:
        """
        执行单条测试用例

        Args:
            case: 用例字典，包含 steps

        Returns:
            执行结果
        """
        self.current_case = case
        case_name = case.get("case_name", "unnamed")
        steps = case.get("steps", [])

        print(f"\n{'='*60}")
        print(f"🚀 开始执行: {case_name}")
        print(f"{'='*60}")

        result = {
            "case_name": case_name,
            "case_id": case.get("case_id", "unknown"),
            "status": "passed",
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": None,
            "duration": 0,
            "steps": [],
            "screenshots": [],
            "error": None
        }

        start = time.time()

        try:
            # 执行前置条件
            self._run_preconditions(case.get("preconditions", []))

            # 执行步骤
            for step in steps:
                step_result = self._execute_step(step)
                result["steps"].append(step_result)

                if step_result["status"] == "failed":
                    result["status"] = "failed"
                    break

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            traceback.print_exc()

        finally:
            result["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            result["duration"] = round(time.time() - start, 2)

            # 失败截图
            if result["status"] != "passed" and Config.SCREENSHOT_ON_FAILURE:
                screenshot = self._take_screenshot(f"fail_{case_name}")
                result["screenshots"].append(screenshot)

        print(f"\n📊 结果: {result['status'].upper()} | 耗时: {result['duration']}s")
        self.results.append(result)
        return result

    def _execute_step(self, step: Dict) -> Dict:
        """执行单个步骤"""
        action = step.get("action", "").lower()
        target = step.get("target", {})
        value = step.get("value", "")
        desc = step.get("desc", "")

        step_result = {
            "step": step.get("step", 0),
            "action": action,
            "desc": desc,
            "status": "passed",
            "elapsed": 0,
            "error": None
        }

        start = time.time()

        try:
            print(f"  Step {step['step']}: [{action}] {desc}")

            if action == "launch":
                self.dm.start_app()

            elif action == "click":
                element = self._find_element(target)
                element.click()

            elif action == "input":
                element = self._find_element(target)
                element.clear_text()
                element.send_keys(value)

            elif action == "swipe":
                # value: "up/down/left/right"
                direction = value or "up"
                self.d.swipe_ext(direction)

            elif action == "assert":
                element = self._find_element(target, wait=False)
                assert element.exists, f"断言失败: 未找到元素 {target}"

            elif action == "wait":
                wait_time = float(value) if value else 1.0
                time.sleep(wait_time)

            elif action == "back":
                self.dm.press_back()

            elif action == "screenshot":
                screenshot = self._take_screenshot(desc)
                step_result["screenshot"] = screenshot

            else:
                raise ValueError(f"未知的操作类型: {action}")

        except Exception as e:
            step_result["status"] = "failed"
            step_result["error"] = str(e)
            print(f"    ❌ 失败: {e}")

        step_result["elapsed"] = round(time.time() - start, 2)
        return step_result

    def _find_element(self, target: Dict, wait: bool = True) -> u2.UiObject:
        """查找元素"""
        if not target:
            raise ValueError("target 为空")

        elem_type = target.get("type", "text")
        elem_value = target.get("value", "")

        if elem_type == "resourceId":
            selector = self.d(resourceId=elem_value)
        elif elem_type == "text":
            selector = self.d(text=elem_value)
        elif elem_type == "content-desc":
            selector = self.d(description=elem_value)
        elif elem_type == "xpath":
            selector = self.d.xpath(elem_value)
        elif elem_type == "className":
            selector = self.d(className=elem_value)
        else:
            raise ValueError(f"不支持的元素定位类型: {elem_type}")

        if wait:
            selector.wait(timeout=10.0)

        return selector

    def _run_preconditions(self, preconditions: List[str]):
        """执行前置条件"""
        for cond in preconditions:
            if "启动" in cond or "launch" in cond.lower():
                self.dm.start_app()
            elif "清除数据" in cond:
                self.dm.clear_app()
            time.sleep(1)

    def _take_screenshot(self, name: str) -> str:
        """截图"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"tests/screenshots/{timestamp}_{name.replace(' ', '_')}.png"
        return self.dm.screenshot(filename)

    def execute_cases(self, cases: List[Dict]) -> List[Dict]:
        """批量执行用例"""
        results = []
        for case in cases:
            result = self.execute_case(case)
            results.append(result)
        return results

    def execute_file(self, filepath: str) -> Dict:
        """从 JSON 文件执行用例"""
        with open(filepath, "r", encoding="utf-8") as f:
            case = json.load(f)
        return self.execute_case(case)


if __name__ == "__main__":
    # 测试执行
    executor = CaseExecutor()

    # 示例用例
    test_case = {
        "case_name": "测试截图",
        "steps": [
            {"step": 1, "action": "launch", "desc": "启动应用"},
            {"step": 2, "action": "wait", "value": "3", "desc": "等待3秒"},
            {"step": 3, "action": "screenshot", "desc": "首页截图"}
        ]
    }

    result = executor.execute_case(test_case)
    print(json.dumps(result, ensure_ascii=False, indent=2))
