# 🧪 MatrixTest

**Android AI 自动化测试平台 — 从需求到报告的全链路测试**

[Python](https://python.org)
[FastAPI](https://fastapi.tiangolo.com)
[uiautomator2](https://github.com/openatx/uiautomator2)
[License](LICENSE)

[📖 文档](docs/) · [🤖 MatrixPerformance](https://github.com/PerformanceTool999998/matrix-performance-lite) · [💬 Issue](https://github.com/PerformanceTool999998/matrix-test/issues)



---

## 📋 目录

- [🧪 MatrixTest](#-matrixtest)
  - [📋 目录](#-目录)
  - [🎯 项目简介](#-项目简介)
    - [✨ 核心特性](#-核心特性)
  - [🏗️ 系统架构](#️-系统架构)
  - [🚀 快速开始](#-快速开始)
    - [环境要求](#环境要求)
    - [安装](#安装)
    - [1. AI 生成用例](#1-ai-生成用例)
    - [2. 执行测试](#2-执行测试)
    - [3. 查看报告](#3-查看报告)
  - [📡 API 接口](#-api-接口)
  - [🔧 配置说明](#-配置说明)
  - [📁 项目结构](#-项目结构)
  - [🔄 CI/CD 集成](#-cicd-集成)
    - [GitHub Actions](#github-actions)
    - [GitLab CI](#gitlab-ci)
  - [📊 与 MatrixPerformance 联动](#-与-matrixperformance-联动)
  - [🛠️ 技术栈](#️-技术栈)
  - [🤝 贡献指南](#-贡献指南)
  - [📄 许可证](#-许可证)

---

## 🎯 项目简介

MatrixTest 是一款面向 **Android 测试工程师** 的 AI 驱动自动化测试平台，覆盖**需求分析 → 用例生成 → UI 执行 → 性能监控 → 报告输出**的完整测试生命周期。

> 💡 **解决痛点**：写用例耗时、维护成本高、性能数据与功能测试割裂

### ✨ 核心特性

| 功能 | 说明 |
|------|------|
| 🤖 **AI 用例生成** | 输入 PRD/需求文本，LLM 自动生成结构化测试用例 |
| 📱 **UI 自动化执行** | 基于 uiautomator2，零侵入，支持真机/模拟器 |
| 📊 **性能联动监控** | 测试期间自动采集 CPU/内存/FPS，与 MatrixPerformance 打通 |
| 📄 **多格式报告** | HTML / Markdown / JSON，含性能数据关联 |
| 🔄 **CI/CD 集成** | GitHub Actions / GitLab CI / Jenkins 开箱即用 |
| 🏷️ **标签化管理** | 冒烟/回归/性能，按需执行不同套件 |

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                        MatrixTest 平台                        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐ │
│  │  AI 生成器   │   │  测试引擎    │   │    报告生成器        │ │
│  │ (LLM/NLP)   │→  │ (调度/生命周期)│→  │ (HTML/Markdown/JSON)│ │
│  └──────┬──────┘   └──────┬──────┘   └─────────────────────┘ │
│         │                 │                                   │
│         ↓                 ↓                                   │
│  ┌─────────────────────────────────┐   ┌──────────────────┐  │
│  │      UI 执行器 (uiautomator2)    │   │  性能监控器 (ADB) │  │
│  │  · click / input / swipe / assert│   │  · CPU / 内存 / FPS│  │
│  │  · 截图 / 元素定位 / 异常处理     │   │  · 上报 MatrixPerf │  │
│  └─────────────────────────────────┘   └──────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**测试生命周期：**

```
需求文档(PRD) → AI 解析 → 生成用例(YAML) → 设备连接 → 执行测试 → 采集性能 → 生成报告 → CI 通知
```

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Android 设备（开启 USB 调试）或模拟器
- ADB 工具
- （可选）OpenAI API Key（AI 生成用例时需要）

### 安装

```bash
git clone https://github.com/PerformanceTool999998/matrix-test.git
cd matrix-test
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env
# 编辑 .env 填入你的配置
```

### 1. AI 生成用例

```bash
# 方式一：从 PRD 文件生成
python main.py generate --prd docs/sample_prd.md --package com.example.app

# 方式二：直接输入需求文本
python main.py generate --text "用户登录功能：输入手机号获取验证码，输入验证码后登录成功跳转到首页" --package com.example.app

# 输出：tests/cases/generated_cases.yaml
```

### 2. 执行测试

```bash
# 连接设备并执行
python main.py run \
    --cases tests/cases/generated_cases.yaml \
    --package com.example.app \
    --perf \
    --report all

# 参数说明：
# --cases: 用例文件路径
# --package: 目标应用包名
# --device: 指定设备序列号（多设备时）
# --perf: 启用性能监控
# --report: 报告格式 (html/md/all)
```

### 3. 查看报告

```bash
# HTML 报告
open output/reports/report_*.html

# Markdown 报告
cat output/reports/report_*.md

# JSON 原始数据
cat output/result_*.json
```

---

## 📡 API 接口

### 用例生成

| 方法 | 命令 | 说明 |
|------|------|------|
| CLI | `python main.py generate --prd <file>` | 从 PRD 生成用例 |
| CLI | `python main.py generate --text <text>` | 从文本生成用例 |

### 测试执行

| 方法 | 命令 | 说明 |
|------|------|------|
| CLI | `python main.py run --cases <file>` | 执行指定用例 |
| CLI | `python main.py ci --suite <name>` | CI 模式执行套件 |

### 报告输出

| 格式 | 路径 | 说明 |
|------|------|------|
| HTML | `output/reports/report_*.html` | 可视化报告 |
| Markdown | `output/reports/report_*.md` | 文本报告 |
| JSON | `output/result_*.json` | 原始数据 |

---

## 🔧 配置说明

编辑 `.env` 文件：

```bash
# AI 配置
AI_PROVIDER=openai
AI_API_KEY=sk-your-key
AI_MODEL=gpt-4o

# 设备配置
ANDROID_DEVICE_SERIAL=  # 留空自动选择
TARGET_PACKAGE=com.example.app

# 性能监控联动
PERF_SERVER_URL=http://localhost:8000
PERF_DEVICE_ID=TEST_DEVICE_001

# 报告配置
REPORT_OUTPUT_DIR=./output/reports
```

---

## 📁 项目结构

```text
matrix-test/
├── ai_generator/              # AI 用例生成
│   ├── __init__.py
│   └── generator.py           # LLM 调用 + 解析
│
├── core/                      # 核心引擎
│   ├── engine/
│   │   └── test_engine.py     # 测试生命周期管理
│   ├── executor/
│   │   └── ui_executor.py     # uiautomator2 封装
│   ├── perf_monitor/
│   │   └── perf_monitor.py    # 性能监控 + 上报
│   └── reporter/
│       └── report_generator.py # 报告生成
│
├── tests/                     # 测试用例
│   ├── fixtures/
│   │   └── smoke.yaml         # 示例用例
│   └── cases/                 # 生成的用例存放
│
├── docs/                      # 文档
│   └── sample_prd.md          # 示例 PRD
│
├── ci/                        # CI/CD 配置
│   ├── .github/workflows/     # GitHub Actions
│   └── .gitlab-ci.yml         # GitLab CI
│
├── main.py                    # 入口文件
├── requirements.txt           # 依赖
├── .env.example               # 环境变量模板
└── README.md                  # 本文档
```

---

## 🔄 CI/CD 集成

### GitHub Actions

`.github/workflows/matrixtest.yml` 已配置：

- **Push/PR 触发**：自动执行冒烟测试
- **定时任务**：每天凌晨 2 点执行回归测试
- **失败通知**：自动发送钉钉/飞书告警
- **产物上传**：测试报告自动归档

### GitLab CI

`.gitlab-ci.yml` 已配置：

```yaml
stages:
  - generate    # AI 生成用例
  - test        # 执行测试
  - report      # 生成报告
```

---

## 📊 与 MatrixPerformance 联动

MatrixTest 在执行 UI 测试时，会自动将性能数据上报到 MatrixPerformance Server：

```
MatrixTest (UI 测试)  →  触发性能采集  →  上报 MatrixPerformance  →  统一看板展示
```

**联动效果：**
- 每个测试用例关联性能曲线
- 失败用例自动标记性能异常点
- 历史版本性能对比

---

## 🛠️ 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| AI 生成 | OpenAI / 通义千问 / Claude | 用例生成 |
| UI 执行 | uiautomator2 | Android 自动化 |
| 性能采集 | ADB + psutil | CPU/内存/FPS |
| 数据上报 | requests | HTTP API |
| 报告生成 | Jinja2 | HTML 模板 |
| 配置管理 | python-dotenv | 环境变量 |

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'feat: xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 提交 Pull Request

---

## 📄 许可证

MIT License - 可自由学习、修改、商用。

---



如果这个项目对你有帮助，请给个 ⭐ **Star**！

你的支持是我持续开源的动力 ❤️
