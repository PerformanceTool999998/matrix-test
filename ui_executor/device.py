"""
设备管理：连接、状态检查、截图等
"""
import subprocess
import time
from pathlib import Path
from typing import Optional, List
import adbutils
from adbutils import AdbDevice

from config.settings import Config


class DeviceManager:
    """Android 设备管理器"""

    def __init__(self, serial: Optional[str] = None):
        self.serial = serial or Config.DEVICE_SERIAL
        self.adb = adbutils.AdbClient(host="127.0.0.1", port=5037)
        self.device: Optional[AdbDevice] = None
        self._connect()

    def _connect(self):
        """连接设备"""
        devices = self.adb.device_list()

        if not devices:
            raise RuntimeError("未检测到 ADB 设备，请检查：
1. 手机是否开启 USB 调试
2. 数据线是否正常
3. adb devices 是否能识别")

        if self.serial:
            self.device = self.adb.device(self.serial)
        else:
            self.device = devices[0]
            self.serial = self.device.serial

        print(f"✅ 已连接设备: {self.serial}")

    def is_connected(self) -> bool:
        """检查设备是否在线"""
        try:
            self.device.shell("echo ping")
            return True
        except:
            return False

    def get_device_info(self) -> dict:
        """获取设备信息"""
        info = {}
        info["serial"] = self.serial
        info["model"] = self.device.prop.get("ro.product.model", "unknown")
        info["brand"] = self.device.prop.get("ro.product.brand", "unknown")
        info["android_version"] = self.device.prop.get("ro.build.version.release", "unknown")
        info["sdk"] = self.device.prop.get("ro.build.version.sdk", "unknown")
        return info

    def screenshot(self, filename: Optional[str] = None) -> str:
        """截图并保存"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"tests/screenshots/{timestamp}_{self.serial}.png"

        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        self.device.screenshot().save(filename)
        return filename

    def start_app(self, package: str = None, activity: str = None):
        """启动应用"""
        pkg = package or Config.TARGET_PACKAGE
        act = activity or Config.APP_ACTIVITY
        self.device.app_start(pkg)
        time.sleep(2)  # 等待启动

    def stop_app(self, package: str = None):
        """停止应用"""
        pkg = package or Config.TARGET_PACKAGE
        self.device.app_stop(pkg)

    def clear_app(self, package: str = None):
        """清除应用数据"""
        pkg = package or Config.TARGET_PACKAGE
        self.device.app_clear(pkg)

    def press_back(self):
        """返回键"""
        self.device.keyevent("BACK")

    def press_home(self):
        """Home 键"""
        self.device.keyevent("HOME")

    def get_current_package(self) -> str:
        """获取当前前台应用"""
        return self.device.app_current().package


def get_device(serial: Optional[str] = None) -> DeviceManager:
    """获取设备管理器实例"""
    return DeviceManager(serial)


if __name__ == "__main__":
    device = get_device()
    print(device.get_device_info())
    device.screenshot("tests/screenshots/test.png")
