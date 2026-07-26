"""
MatrixTest - 全局配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """应用配置"""

    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent

    # ADB / 设备
    ANDROID_HOME = os.getenv("ANDROID_HOME", "")
    ADB_PATH = os.getenv("ADB_PATH", "adb")
    DEVICE_SERIAL = os.getenv("DEVICE_SERIAL", "")

    # 目标应用
    TARGET_PACKAGE = os.getenv("TARGET_PACKAGE", "com.example.app")
    APP_ACTIVITY = os.getenv("APP_ACTIVITY", ".MainActivity")

    # AI / LLM
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # 性能监控
    PERF_SERVER_URL = os.getenv("PERF_SERVER_URL", "http://localhost:8000")
    PERF_ENABLED = os.getenv("PERF_ENABLED", "true").lower() == "true"

    # 报告
    REPORT_OUTPUT_DIR = Path(os.getenv("REPORT_OUTPUT_DIR", "./tests/results"))
    SCREENSHOT_ON_FAILURE = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"
    SCREENSHOT_ON_SUCCESS = os.getenv("SCREENSHOT_ON_SUCCESS", "false").lower() == "true"

    # CI/CD
    CI_MODE = os.getenv("CI_MODE", "false").lower() == "true"
    TEST_RUN_ID = os.getenv("TEST_RUN_ID", "local")

    @classmethod
    def ensure_dirs(cls):
        """确保必要目录存在"""
        dirs = [
            cls.REPORT_OUTPUT_DIR,
            cls.BASE_DIR / "tests" / "cases",
            cls.BASE_DIR / "tests" / "results",
            cls.BASE_DIR / "tests" / "screenshots",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# 初始化目录
Config.ensure_dirs()
