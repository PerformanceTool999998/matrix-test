"""
MatrixTest - Mock UI 执行器
无设备时模拟测试执行
"""

import random
import time
from typing import List, Dict
from pathlib import Path


class MockUIExecutor:
    """Mock UI 执行器 - 无需真实设备"""
    
    def __init__(self, device_serial: str = "", target_package: str = "", fail_rate: float = 0.1):
        self.device_serial = device_serial or "MOCK_DEVICE_001"
        self.target_package = target_package or "com.example.app"
        self.fail_rate = fail_rate
        self.screenshot_dir = "./output/screenshots"
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
        self._step_count = 0
    
    def connect(self) -> bool:
        print(f"✅ [Mock] 设备已连接: {self.device_serial}")
        print(f"   📱 型号: Mock Pixel 6 Pro")
        print(f"   🤖 Android: 14")
        print(f"   📦 目标应用: {self.target_package}")
        return True
    
    def start_app(self, package: str = "", activity: str = "") -> bool:
        pkg = package or self.target_package
        print(f"✅ [Mock] 应用已启动: {pkg}")
        time.sleep(0.3)
        return True
    
    def stop_app(self, package: str = ""):
        pkg = package or self.target_package
        print(f"🛑 [Mock] 应用已停止: {pkg}")
    
    def execute(self, case) -> List[Dict]:
        steps_result = []
        self._step_count = 0
        
        print(f"\n📝 执行用例: {case.id} - {case.name}")
        print(f"   优先级: {case.priority} | 标签: {', '.join(case.tags)}")
        
        for i, step in enumerate(case.steps, 1):
            self._step_count += 1
            result = self._execute_step(step, i)
            steps_result.append(result)
            
            if not result["success"]:
                self._take_screenshot(f"{case.id}_step{i}_fail")
                break
            
            time.sleep(0.2)
        
        return steps_result
    
    def _execute_step(self, step, index: int) -> Dict:
        result = {
            "step": index,
            "action": step.action,
            "target": step.target,
            "target_type": step.target_type,
            "value": step.value,
            "description": step.description,
            "success": True,
            "error": None,
            "duration": 0.0
        }
        
        start = time.time()
        base_delay = random.uniform(0.1, 0.5)
        
        print(f"   步骤 {index}: {step.description}")
        print(f"      → 查找元素 [{step.target_type}]: {step.target}")
        time.sleep(random.uniform(0.05, 0.2))
        
        if random.random() < self.fail_rate:
            result["success"] = False
            result["error"] = random.choice([
                "元素未找到: 超时",
                "元素不可点击",
                "页面加载超时",
                "元素被遮挡"
            ])
            print(f"      ❌ 失败: {result['error']}")
        else:
            if step.action == "click":
                print(f"      ✓ 点击元素")
            elif step.action == "input":
                masked = step.value[:3] + "***" if step.value else ""
                print(f"      ✓ 输入: {masked}")
            elif step.action == "swipe":
                print(f"      ✓ 滑动操作")
            elif step.action == "assert":
                print(f"      ✓ 断言通过: {step.target}")
            elif step.action == "wait":
                wait_time = float(step.value or 1)
                print(f"      ⏱️ 等待 {wait_time}s")
                time.sleep(wait_time * 0.1)
            
            print(f"      ✅ 成功 ({base_delay:.2f}s)")
        
        result["duration"] = round(time.time() - start, 3)
        return result
    
    def _take_screenshot(self, name: str) -> str:
        filename = f"{self.screenshot_dir}/{name}_{int(time.time())}.png"
        Path(filename).touch()
        print(f"      📸 截图已保存: {filename}")
        return filename
    
    def get_device_info(self) -> Dict:
        return {
            "serial": self.device_serial,
            "model": "Mock Pixel 6 Pro",
            "android_version": "14",
            "sdk_version": 34,
            "resolution": "1440x3120",
            "dpi": 512
        }
    
    def press_back(self):
        print("[Mock] 按下返回键")
    
    def press_home(self):
        print("[Mock] 按下Home键")