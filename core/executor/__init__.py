"""
MatrixTest - UI 执行器模块
"""

from .mock_executor import MockUIExecutor

try:
    from .ui_executor import UIExecutor
except ImportError:
    UIExecutor = None
