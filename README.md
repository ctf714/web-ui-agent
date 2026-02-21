# Web UI Agent

基于 Gemini API 的 Web UI Agent 项目，实现了一个单步循环的 GUI Agent，能够根据自然语言指令操作浏览器并完成任务。

## 功能特点

- 🤖 **智能视觉理解**：使用 Gemini API 分析网页截图，理解页面布局和元素
- 🔄 **单步循环架构**：感知 → 规划 → 执行的完整流程
- 🖱️ **双保险点击策略**：提高点击操作的成功率
- 💬 **交互式模式**：支持连续执行多个任务，无需每次重启
- 🌐 **浏览器自动化**：使用 Playwright 执行浏览器动作
- 📸 **页面截图**：自动捕获当前页面状态
- 📝 **详细日志**：记录执行过程和结果

## 技术栈

- Python 3.10+
- Google Generative AI SDK (`google-generativeai`)
- Playwright
- Pillow (PIL)
- Loguru
- python-dotenv

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/ctf714/web-ui-agent.git
cd web-ui-agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 文件为 `.env`，并填入你的 Gemini API Key：

```bash
cp .env.example .env
```

在 `.env` 文件中设置：

```env
# Gemini API 密钥
GEMINI_API_KEY=your_gemini_api_key_here

# 浏览器配置
HEADLESS=False

# Agent 配置
MAX_STEPS=10
```

### 4. 安装 Playwright 浏览器

```bash
playwright install
```

## 使用方法

### 交互式模式

运行以下命令启动交互式模式：

```bash
python main.py
```

在交互式模式下，输入任务内容即可开始执行，例如：

```
请输入任务: 打开百度首页并搜索：什么ai最好用
```

输入 `exit` 退出程序。

### 命令行模式

直接通过命令行参数指定任务：

```bash
python main.py --task "打开百度首页"
```

### 可选参数

- `--headless`：是否以无头模式运行浏览器（默认：False）
- `--max-steps`：最大执行步数（默认：10）

## 项目结构

```
web-ui-agent/
├── agent.py          # Web UI Agent 核心类
├── config.py         # 配置文件
├── executor.py       # 动作执行模块
├── main.py           # 主入口文件
├── mcp_client.py     # Gemini API 客户端
├── perception.py     # 页面感知模块
├── planner.py        # 动作规划模块
├── utils.py          # 工具函数
├── requirements.txt  # 依赖项配置
├── .env              # 环境变量
├── .env.example      # 环境变量示例
├── screenshots/      # 截图目录
└── README.md         # 项目文档
```

## 工作原理

1. **感知（Perception）**：使用 Playwright 捕获当前页面截图
2. **规划（Planning）**：使用 Gemini API 分析截图，生成下一步动作规划
3. **执行（Execution）**：使用 Playwright 执行浏览器动作
4. **循环**：重复上述步骤，直到任务完成或达到最大步数

## 动作类型

- `click`：点击页面元素
- `type`：输入文本
- `scroll`：滚动页面
- `navigate`：导航到 URL
- `wait`：等待
- `complete`：任务完成

## 示例任务

- `打开百度首页`
- `打开百度网页并搜索：什么ai最好用`
- `打开GitHub官网`
- `打开京东首页并点击搜索框`

## 注意事项

1. **API 配额**：使用 Gemini API 需要确保有足够的 API 配额
2. **网络连接**：执行任务需要稳定的网络连接
3. **页面加载**：部分页面可能需要较长时间加载，请耐心等待
4. **元素识别**：复杂页面可能会影响元素识别的准确性

## 故障排除

### 常见错误

- **API 401**：Gemini API Key 无效，请检查配置
- **API 429**：API 配额用尽，请等待或升级配额
- **浏览器启动失败**：请确保已正确安装 Playwright 浏览器
- **点击失败**：页面元素可能不可见或被遮挡，尝试调整任务描述

### 日志查看

执行过程中的详细日志会保存在 `agent.log` 文件中，可用于调试和排查问题。

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 初始化项目
- 实现基于 Gemini API 的视觉理解
- 添加双保险点击策略
- 支持交互式模式
- 完善错误处理和日志记录