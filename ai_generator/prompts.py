"""
AI 生成测试用例的 Prompt 模板
"""

# 基础用例生成 Prompt
CASE_GENERATOR_PROMPT = """你是一位资深移动端测试工程师，精通 Android UI 自动化测试。

请根据以下需求描述，生成结构化的测试用例，输出为 JSON 格式。

## 需求描述
{requirement}

## 输出要求
1. 用例必须包含：用例名称、前置条件、测试步骤、预期结果
2. 每个步骤必须包含：action（操作类型）、target（元素定位）、value（输入值，可选）
3. 支持的操作类型：click, input, swipe, assert, wait, back, launch
4. 元素定位支持：resourceId, text, content-desc, xpath, className
5. 必须包含至少一个 assert 步骤作为断言

## 输出格式示例
```json
{
  "case_name": "用户登录成功",
  "priority": "P0",
  "preconditions": ["已安装APP", "网络正常"],
  "steps": [
    {"step": 1, "action": "launch", "target": "", "value": "", "desc": "启动应用"},
    {"step": 2, "action": "click", "target": {"type": "text", "value": "我的"}, "desc": "点击我的Tab"},
    {"step": 3, "action": "click", "target": {"type": "text", "value": "登录/注册"}, "desc": "点击登录按钮"},
    {"step": 4, "action": "input", "target": {"type": "resourceId", "value": "com.example.app:id/et_phone"}, "value": "13800138000", "desc": "输入手机号"},
    {"step": 5, "action": "click", "target": {"type": "text", "value": "获取验证码"}, "desc": "点击获取验证码"},
    {"step": 6, "action": "input", "target": {"type": "resourceId", "value": "com.example.app:id/et_code"}, "value": "123456", "desc": "输入验证码"},
    {"step": 7, "action": "click", "target": {"type": "text", "value": "登录"}, "desc": "点击登录"},
    {"step": 8, "action": "assert", "target": {"type": "text", "value": "个人中心"}, "value": "", "desc": "断言进入个人中心"}
  ],
  "expected_result": "登录成功，跳转到个人中心页面"
}
```

请直接输出 JSON，不要包含其他解释文字。
"""

# 批量生成 Prompt
BATCH_CASE_PROMPT = """请根据以下功能模块，生成 {count} 条核心测试用例：

功能模块：{module}
应用包名：{package}

要求：
1. 覆盖正向流程和异常流程
2. 包含边界值测试
3. 输出 JSON 数组格式
4. 每条用例包含 case_name, priority, steps, expected_result
"""

# 元素定位优化 Prompt
LOCATOR_OPTIMIZE_PROMPT = """你是一位 UI 自动化专家。请为以下界面元素提供最优的定位策略：

元素信息：
{element_info}

要求：
1. 优先使用 resourceId（最稳定）
2. 其次使用 content-desc
3. 最后使用 xpath（包含文本匹配）
4. 避免使用纯坐标定位
5. 输出 JSON 格式：{"type": "resourceId", "value": "xxx", "backup": [...]}
"""
