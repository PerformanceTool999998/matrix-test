"""
MatrixTest - AI 测试用例生成器
支持 OpenAI / 通义千问 / Claude
"""

import os
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    import openai
except ImportError:
    openai = None

load_dotenv()


@dataclass
class TestStep:
    """单条测试步骤"""
    action: str           # click / input / swipe / assert / wait
    target: str           # 元素定位（text/resourceId/xpath）
    target_type: str      # text / resourceId / xpath / className
    value: Optional[str] = None   # input 时的输入值
    timeout: int = 10     # 等待超时（秒）
    description: str = "" # 步骤说明


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    priority: str         # P0 / P1 / P2
    preconditions: List[str]
    steps: List[TestStep]
    expected_result: str
    tags: List[str]


class AICaseGenerator:
    """AI 测试用例生成器"""

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai")
        self.api_key = os.getenv("AI_API_KEY")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("AI_MODEL", "gpt-4o")

        if openai and self.api_key:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = None

    def generate_from_prd(self, prd_text: str, app_package: str = "") -> List[TestCase]:
        """
        根据 PRD 文档生成测试用例

        Args:
            prd_text: 需求文档文本
            app_package: 目标应用包名

        Returns:
            测试用例列表
        """
        prompt = self._build_prompt(prd_text, app_package)

        if not self.client:
            print("⚠️ 未配置 AI API，使用默认示例用例")
            return self._get_default_cases()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的移动端测试工程师，擅长根据需求文档生成结构化的 UI 自动化测试用例。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            return self._parse_cases(content)

        except Exception as e:
            print(f"❌ AI 生成失败: {e}")
            return self._get_default_cases()

    def generate_from_api_doc(self, api_doc: str) -> List[TestCase]:
        """根据接口文档生成接口测试用例（可扩展）"""
        # TODO: 实现 API 测试用例生成
        return []

    def _build_prompt(self, prd_text: str, app_package: str) -> str:
        """构建 Prompt"""
        return f"""请根据以下需求文档，生成 Android UI 自动化测试用例。

目标应用包名: {app_package or "com.example.app"}

需求文档:
{prd_text}

要求:
1. 用 JSON 格式输出
2. 每条用例包含: id, name, description, priority, preconditions, steps, expected_result, tags
3. 每个 step 包含: action(click/input/swipe/assert/wait), target, target_type(text/resourceId/xpath), value(可选), timeout, description
4. 覆盖正常流程、异常流程、边界条件
5. 用例 ID 格式: TC_模块_序号

输出格式示例:
```json
{{
  "cases": [
    {{
      "id": "TC_LOGIN_001",
      "name": "正常登录",
      "description": "使用正确手机号和验证码登录",
      "priority": "P0",
      "preconditions": ["已安装应用", "网络正常"],
      "steps": [
        {{
          "action": "click",
          "target": "我的",
          "target_type": "text",
          "timeout": 5,
          "description": "点击底部'我的'Tab"
        }},
        {{
          "action": "input",
          "target": "com.example.app:id/et_phone",
          "target_type": "resourceId",
          "value": "13800138000",
          "timeout": 5,
          "description": "输入手机号"
        }}
      ],
      "expected_result": "登录成功，跳转到首页",
      "tags": ["登录", "冒烟"]
    }}
  ]
}}
```
"""

    def _parse_cases(self, content: str) -> List[TestCase]:
        """解析 AI 返回的 JSON"""
        # 提取 JSON 块
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        try:
            data = json.loads(content)
            cases = []
            for case_data in data.get("cases", []):
                steps = [
                    TestStep(**step) 
                    for step in case_data.get("steps", [])
                ]
                cases.append(TestCase(
                    id=case_data["id"],
                    name=case_data["name"],
                    description=case_data.get("description", ""),
                    priority=case_data.get("priority", "P1"),
                    preconditions=case_data.get("preconditions", []),
                    steps=steps,
                    expected_result=case_data.get("expected_result", ""),
                    tags=case_data.get("tags", [])
                ))
            return cases
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return self._get_default_cases()

    def _get_default_cases(self) -> List[TestCase]:
        """默认示例用例（AI 不可用时）"""
        return [
            TestCase(
                id="TC_LOGIN_001",
                name="正常登录流程",
                description="使用正确账号密码登录",
                priority="P0",
                preconditions=["应用已安装", "网络正常"],
                steps=[
                    TestStep("click", "我的", "text", timeout=5, description="点击我的Tab"),
                    TestStep("click", "登录/注册", "text", timeout=5, description="点击登录入口"),
                    TestStep("input", "com.example.app:id/et_phone", "resourceId", "13800138000", 5, "输入手机号"),
                    TestStep("input", "com.example.app:id/et_code", "resourceId", "123456", 5, "输入验证码"),
                    TestStep("click", "登录", "text", timeout=5, description="点击登录按钮"),
                    TestStep("assert", "首页", "text", timeout=10, description="断言进入首页")
                ],
                expected_result="登录成功，显示首页",
                tags=["登录", "冒烟"]
            )
        ]

    def export_to_yaml(self, cases: List[TestCase], filepath: str):
        """导出为 YAML 格式"""
        import yaml
        data = {
            "cases": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "priority": c.priority,
                    "preconditions": c.preconditions,
                    "steps": [
                        {
                            "action": s.action,
                            "target": s.target,
                            "target_type": s.target_type,
                            "value": s.value,
                            "timeout": s.timeout,
                            "description": s.description
                        }
                        for s in c.steps
                    ],
                    "expected_result": c.expected_result,
                    "tags": c.tags
                }
                for c in cases
            ]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"✅ 用例已导出: {filepath}")


if __name__ == "__main__":
    # 测试
    generator = AICaseGenerator()

    prd = """
    用户登录功能需求:
    1. 用户输入手机号，点击获取验证码
    2. 输入6位验证码，点击登录
    3. 登录成功后跳转到首页
    4. 验证码错误提示"验证码错误"
    5. 手机号格式错误提示"请输入正确的手机号"
    """

    cases = generator.generate_from_prd(prd, "com.example.app")
    print(f"生成了 {len(cases)} 条用例")
    for case in cases:
        print(f"  - {case.id}: {case.name}")
