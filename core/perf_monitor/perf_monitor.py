"""
MatrixTest - 性能监控模块
与 MatrixPerformance Agent 联动，在 UI 测试期间采集性能数据
"""

import os
import time
import json
import threading
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

import requests
import psutil


@dataclass
class PerfSnapshot:
    """性能快照"""
    timestamp: str
    cpu_percent: float
    memory_mb: float
    fps: Optional[float] = None
    battery_temp: Optional[float] = None


class PerfMonitor:
    """性能监控器"""

    def __init__(self, server_url: str = "", device_id: str = ""):
        self.server_url = server_url or os.getenv("PERF_SERVER_URL", "http://localhost:8000")
        self.device_id = device_id or os.getenv("PERF_DEVICE_ID", "TEST_DEVICE")
        self.target_package = os.getenv("TARGET_PACKAGE", "")

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._snapshots: List[PerfSnapshot] = []
        self._interval = 1.0  # 采样间隔（秒）

    def start(self):
        """启动监控"""
        self._running = True
        self._snapshots = []
        self._thread = threading.Thread(target=self._collect_loop)
        self._thread.start()
        print("📊 性能监控已启动")

    def stop(self) -> Dict:
        """停止监控并返回数据"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

        # 计算统计值
        if not self._snapshots:
            return {}

        cpu_values = [s.cpu_percent for s in self._snapshots]
        mem_values = [s.memory_mb for s in self._snapshots]

        result = {
            "sample_count": len(self._snapshots),
            "duration": len(self._snapshots) * self._interval,
            "cpu_avg": round(sum(cpu_values) / len(cpu_values), 2),
            "cpu_max": round(max(cpu_values), 2),
            "memory_avg": round(sum(mem_values) / len(mem_values), 2),
            "memory_max": round(max(mem_values), 2),
            "snapshots": [
                {
                    "timestamp": s.timestamp,
                    "cpu": s.cpu_percent,
                    "memory": s.memory_mb
                }
                for s in self._snapshots
            ]
        }

        print(f"📊 性能监控已停止，共采集 {len(self._snapshots)} 个样本")
        return result

    def _collect_loop(self):
        """采集循环"""
        while self._running:
            try:
                snapshot = self._collect_once()
                self._snapshots.append(snapshot)

                # 上报到 MatrixPerformance Server
                self._upload_to_server(snapshot)

            except Exception as e:
                print(f"采集异常: {e}")

            time.sleep(self._interval)

    def _collect_once(self) -> PerfSnapshot:
        """单次采集"""
        # 本机 CPU/内存（PC 端）
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.Process().memory_info().rss / 1024 / 1024

        return PerfSnapshot(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu,
            memory_mb=round(mem, 2)
        )

    def _upload_to_server(self, snapshot: PerfSnapshot):
        """上报到性能监控 Server"""
        try:
            data = {
                "device_id": self.device_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cpu_percent": snapshot.cpu_percent,
                "pss_kb": int(snapshot.memory_mb * 1024),
                "uss_kb": 0,
                "heap_size_kb": 0,
                "fps": 0,
                "jank_count": 0,
                "battery_temp": 0
            }

            response = requests.post(
                f"{self.server_url}/performance/upload",
                json=data,
                timeout=5
            )

        except Exception:
            pass  # 上报失败不影响测试


class ADBPerfMonitor(PerfMonitor):
    """基于 ADB 的设备端性能监控（更精准）"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._adb_available = self._check_adb()

    def _check_adb(self) -> bool:
        """检查 ADB 是否可用"""
        import subprocess
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
            return "device" in result.stdout
        except:
            return False

    def _collect_once(self) -> PerfSnapshot:
        """通过 ADB 采集设备性能"""
        if not self._adb_available or not self.target_package:
            return super()._collect_once()

        import subprocess

        # 采集 CPU
        cpu = 0
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "cpuinfo"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n"):
                if self.target_package in line:
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if match:
                        cpu = float(match.group(1))
                        break
        except:
            pass

        # 采集内存
        mem = 0
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "meminfo", self.target_package],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n"):
                if "TOTAL PSS:" in line:
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        mem = int(match.group(1)) / 1024  # KB -> MB
                        break
        except:
            pass

        return PerfSnapshot(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu,
            memory_mb=round(mem, 2)
        )


if __name__ == "__main__":
    # 测试
    monitor = PerfMonitor()
    monitor.start()
    time.sleep(3)
    result = monitor.stop()
    print(json.dumps(result, indent=2))
