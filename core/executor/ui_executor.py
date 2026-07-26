"""
MatrixTest - UI 执行器
基于 uiautomator2 的 Android UI 自动化执行
"""

import os
import time
from typing import List, Dict, Optional
from pathlib import Path

import uiautomator2 as u2
from colorama import Fore, Style


class UIExecutor:
    """UI 自动化执行器"""

    def __init__(self, device_serial: str = "", target_package: str = ""):
        self.device_serial = device_serial or os.getenv("ANDROID_DEVICE_SERIAL", "")
        self.target_package = target_package or os.getenv("TARGET_PACKAGE", "")
        self.d: Optional[u2.Device] = None
        self.screenshot_dir = "./output/screenshots"
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)

    def connect(self) -> bool:
        """连接设备"""
        try:
            if self.device_serial:
                self.d = u2.connect(self.device_serial)
            else:
                self.d = u2.connect()

            print(f"✅ 设备已连接: {self.d.device_info['serial']}")
            return True
        except Exception as e:
            print(f"❌ 设备连接失败: {e}")
            return False

    def start_app(self, package: str = "", activity: str = "") -> bool:
        """启动应用"""
        pkg = package or self.target_package
        if not pkg:
            print("❌ 未指定应用包名")
            return False

        try:
            if activity:
                self.d.app_start(pkg, activity)
            else:
                self.d.app_start(pkg)
            time.sleep(2)  # 等待启动
            print(f"✅ 应用已启动: {pkg}")
            return True
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False

    def stop_app(self, package: str = ""):
        """停止应用"""
        pkg = package or self.target_package
        if pkg:
            self.d.app_stop(pkg)

    def execute(self, case) -> List[Dict]:
        """执行单条用例"""
        steps_result = []

        for i, step in enumerate(case.steps, 1):
            result = self._execute_step(step, i)
            steps_result.append(result)

            if not result["success"]:
                # 失败时截图
                self._take_screenshot(f"{case.id}_step{i}_fail")
                break

        return steps_result

    def _execute_step(self, step, index: int) -> Dict:
        """执行单步操作"""
        result = {
            "step": index,
            "action": step.action,
            "target": step.target,
            "description": step.description,
            "success": True,
            "error": None
        }

        try:
            print(f"   步骤 {index}: {step.description}")

            # 查找元素
            element = self._find_element(step.target, step.target_type, step.timeout)

            if step.action == "click":
                element.click()

            elif step.action == "input":
                element.set_text(step.value or "")

            elif step.action == "swipe":
                # 简单滑动实现
                self.d.swipe(0.5, 0.8, 0.5, 0.2)

            elif step.action == "assert":
                assert element.exists, f"元素不存在: {step.target}"

            elif step.action == "wait":
                time.sleep(int(step.value or 1))

            time.sleep(0.5)  # 操作间隔

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            print(f"   {Fore.RED}失败: {e}{Style.RESET_ALL}")

        return result

    def _find_element(self, target: str, target_type: str, timeout: int = 10):
        """查找元素"""
        if target_type == "text":
            return self.d(text=target)
        elif target_type == "resourceId":
            return self.d(resourceId=target)
        elif target_type == "xpath":
            return self.d.xpath(target)
        elif target_type == "className":
            return self.d(className=target)
        else:
            return self.d(text=target)

    def _take_screenshot(self, name: str) -> str:
        """截图"""
        filename = f"{self.screenshot_dir}/{name}_{int(time.time())}.png"
        self.d.screenshot(filename)
        print(f"   📸 截图已保存: {filename}")
        return filename

    def get_device_info(self) -> Dict:
        """获取设备信息"""
        if not self.d:
            return {}
        return self.d.device_info

    def press_back(self):
        """返回键"""
        self.d.press("back")

    def press_home(self):
        """Home 键"""
        self.d.press("home")


if __name__ == "__main__":
    # 测试
    executor = UIExecutor()
    if executor.connect():
        print(executor.get_device_info())
