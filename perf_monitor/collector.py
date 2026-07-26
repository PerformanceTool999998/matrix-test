"""
性能监控采集器
与 MatrixPerformance Agent 联动，在 UI 测试执行时同步采集性能
"""
import json
import time
import threading
import requests
from datetime import datetime
from typing import Optional, Dict, List
import subprocess

from config.settings import Config


class PerfCollector:
    """性能采集器"""

    def __init__(self, package: Optional[str] = None, server_url: Optional[str] = None):
        self.package = package or Config.TARGET_PACKAGE
        self.server_url = server_url or Config.PERF_SERVER_URL
        self.enabled = Config.PERF_ENABLED

        self.collecting = False
        self.thread: Optional[threading.Thread] = None
        self.data_buffer: List[Dict] = []
        self.start_time: Optional[float] = None

    def start(self):
        """开始采集"""
        if not self.enabled:
            print("⚠️ 性能监控已禁用")
            return

        self.collecting = True
        self.start_time = time.time()
        self.data_buffer = []

        # 启动后台采集线程
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()

        print(f"📊 性能采集已启动 | 目标应用: {self.package}")

    def stop(self) -> Dict:
        """停止采集并返回报告"""
        if not self.collecting:
            return {}

        self.collecting = False
        if self.thread:
            self.thread.join(timeout=5)

        duration = time.time() - (self.start_time or time.time())

        report = self._generate_report(duration)
        print(f"📊 性能采集已停止 | 时长: {duration:.1f}s | 数据点: {len(self.data_buffer)}")

        return report

    def _collect_loop(self):
        """采集循环"""
        while self.collecting:
            try:
                data = self._collect_once()
                if data:
                    self.data_buffer.append(data)
                    # 实时上报到 Server
                    self._upload_to_server(data)
                time.sleep(1)  # 每秒采集一次
            except Exception as e:
                print(f"采集异常: {e}")
                time.sleep(1)

    def _collect_once(self) -> Optional[Dict]:
        """单次采集"""
        try:
            # CPU
            cpu = self._get_cpu()
            # 内存
            mem = self._get_memory()
            # FPS (需要 dumpsys gfxinfo)
            fps_data = self._get_fps()
            # 温度
            temp = self._get_temperature()

            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "device_id": Config.TEST_RUN_ID,
                "cpu_percent": cpu,
                "pss_kb": mem.get("pss", 0),
                "uss_kb": mem.get("uss", 0),
                "heap_size_kb": mem.get("heap", 0),
                "fps": fps_data.get("fps", 0),
                "jank_count": fps_data.get("jank", 0),
                "battery_temp": temp
            }
        except Exception as e:
            print(f"采集失败: {e}")
            return None

    def _get_cpu(self) -> float:
        """获取 CPU 使用率"""
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "cpuinfo"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n"):
                if self.package in line:
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if match:
                        return float(match.group(1))
            return 0.0
        except:
            return 0.0

    def _get_memory(self) -> Dict[str, int]:
        """获取内存数据"""
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "meminfo", self.package],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout

            pss = uss = heap = 0
            for line in output.split("\n"):
                line = line.strip()
                if "TOTAL PSS:" in line:
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        pss = int(match.group(1))
                elif "TOTAL PRIVATE DIRTY:" in line:
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        uss = int(match.group(1))
                elif "Dalvik Heap" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        heap = int(parts[2])

            return {"pss": pss, "uss": uss, "heap": heap}
        except:
            return {"pss": 0, "uss": 0, "heap": 0}

    def _get_fps(self) -> Dict[str, float]:
        """获取 FPS 数据"""
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "gfxinfo", self.package],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout

            frame_times = []
            in_section = False

            for line in output.split("\n"):
                if "---PROFILEDATA---" in line:
                    in_section = not in_section
                    continue
                if in_section:
                    try:
                        frame_times.append(float(line.strip()))
                    except:
                        pass

            if frame_times:
                avg_ms = sum(frame_times) / len(frame_times)
                fps = 1000.0 / avg_ms if avg_ms > 0 else 0
                jank = sum(1 for t in frame_times if t > 16.67)
                return {"fps": round(fps, 2), "jank": jank}

            return {"fps": 0, "jank": 0}
        except:
            return {"fps": 0, "jank": 0}

    def _get_temperature(self) -> float:
        """获取电池温度"""
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "battery"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n"):
                if "temperature:" in line:
                    import re
                    match = re.search(r'temperature:\s*(\d+)', line)
                    if match:
                        return int(match.group(1)) / 10.0
            return 0.0
        except:
            return 0.0

    def _upload_to_server(self, data: Dict):
        """上报到 MatrixPerformance Server"""
        try:
            url = f"{self.server_url}/performance/upload"
            response = requests.post(url, json=data, timeout=5)
            if response.status_code != 200:
                print(f"上报失败: {response.status_code}")
        except Exception as e:
            print(f"上报异常: {e}")

    def _generate_report(self, duration: float) -> Dict:
        """生成性能报告"""
        if not self.data_buffer:
            return {}

        cpus = [d["cpu_percent"] for d in self.data_buffer]
        fps_list = [d["fps"] for d in self.data_buffer]
        temps = [d["battery_temp"] for d in self.data_buffer]
        pss_list = [d["pss_kb"] for d in self.data_buffer]
        janks = [d["jank_count"] for d in self.data_buffer]

        return {
            "duration": round(duration, 1),
            "data_points": len(self.data_buffer),
            "cpu": {
                "avg": round(sum(cpus) / len(cpus), 1),
                "max": round(max(cpus), 1),
                "min": round(min(cpus), 1)
            },
            "fps": {
                "avg": round(sum(fps_list) / len(fps_list), 1),
                "max": round(max(fps_list), 1),
                "min": round(min(fps_list), 1)
            },
            "temperature": {
                "avg": round(sum(temps) / len(temps), 1),
                "max": round(max(temps), 1)
            },
            "memory": {
                "avg_pss_kb": round(sum(pss_list) / len(pss_list), 0),
                "max_pss_kb": max(pss_list)
            },
            "jank": {
                "total": sum(janks),
                "avg_per_sec": round(sum(janks) / duration, 2) if duration > 0 else 0
            },
            "raw_data": self.data_buffer
        }


class PerfContext:
    """性能采集上下文管理器 (with 语句)"""

    def __init__(self, package: Optional[str] = None):
        self.collector = PerfCollector(package)
        self.report: Optional[Dict] = None

    def __enter__(self):
        self.collector.start()
        return self.collector

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.report = self.collector.stop()
        return False


if __name__ == "__main__":
    # 测试
    with PerfContext() as perf:
        time.sleep(5)

    print(json.dumps(perf.report, ensure_ascii=False, indent=2))
