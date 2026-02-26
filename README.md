# Web UI Agent

基于 Gemini API 的智能网页自动化代理，能够根据自然语言指令自动操作浏览器完成任务。

## 功能特点

- 🤖 **智能视觉理解**：使用 Gemini 2.5 Flash 分析网页截图，理解页面布局和元素
- 🔄 **动态规划架构**：每一步都根据当前页面状态实时规划，灵活适应各种情况
- 🎯 **DOM 快照定位**：提取页面可交互元素信息，精准定位操作目标
- 🖱️ **坐标点击策略**：使用归一化坐标定位元素，操作更精准
- 💬 **Chrome 扩展集成**：通过浏览器扩展实现无侵入式网页操作
- 📝 **详细日志**：记录执行过程和结果，便于调试

## 技术栈

### 后端
- Python 3.10+
- Flask（Web API 服务）
- Google Generative AI SDK（Gemini API）
- Pillow（图像处理）
- Loguru（日志记录）

### 前端
- React 19
- Vite 7
- Chrome Extension Manifest V3

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/ctf714/web-ui-agent.git
cd web-ui-agent
```

### 2. 安装 Python 依赖

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

# MCP 服务器配置
MCP_SERVER_URL=http://localhost:8000

# 浏览器配置
HEADLESS=False

# Agent 配置
MAX_STEPS=10
```

### 4. 安装 Chrome 扩展

1. 打开 Chrome 浏览器，进入 `chrome://extensions/`
2. 开启「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 `ui/dist` 目录

### 5. 构建前端（可选）

如果需要修改前端代码：

```bash
cd ui
npm install
npm run build
```

## 使用方法

### 启动后端服务

```bash
python server.py
```

服务将在 `http://localhost:5000` 启动。

### 使用 Chrome 扩展

1. 点击浏览器工具栏中的扩展图标
2. 在弹出的界面中输入任务
3. 点击「开始」执行任务
4. 可随时点击「停止」终止任务

### 示例任务

- `打开百度首页`
- `帮我搜一下复旦大学校长是谁`
- `打开GitHub官网`
- `在京东搜索笔记本电脑`

## 项目结构

```
web-ui-agent/
├── server.py         # Flask API 服务
├── planner.py        # 动作规划模块（动态规划）
├── executor.py       # 动作执行模块
├── perception.py     # 页面感知模块（截图）
├── mcp_client.py     # Gemini API 客户端
├── config.py         # 配置文件
├── main.py           # 命令行入口
├── agent.py          # Agent 核心类
├── requirements.txt  # Python 依赖
├── .env.example      # 环境变量示例
├── ui/               # Chrome 扩展
│   ├── public/       # 扩展源码
│   │   ├── background.js  # 后台服务脚本
│   │   ├── bridge.js      # 内容脚本
│   │   └── manifest.json  # 扩展清单
│   ├── src/          # React UI
│   └── dist/         # 构建输出
└── screenshots/      # 截图目录
```

## 工作原理

### 架构流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Chrome 扩展     │────▶│  Flask 后端     │────▶│  Gemini API     │
│  (截图 + DOM)    │     │  (规划动作)      │     │  (视觉理解)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │                                               │
        ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│  执行动作        │◀──────────────────────────│  返回动作指令    │
│  (点击/输入等)   │                           │  (JSON 格式)    │
└─────────────────┘                           └─────────────────┘
```

### 动态规划策略

每一步都根据当前页面状态实时规划：

1. **观察**：分析截图和 DOM 元素列表，理解当前页面状态
2. **理解**：明确用户想要完成什么任务
3. **规划**：根据当前状态决定下一步最合适的操作
4. **检测**：如果任务目标已达成，立即结束任务

### DOM 快照

提取页面可交互元素信息：

| ID | 标签 | 类型/角色 | 文本/占位符 | 坐标(x,y) | 状态 |
|----|----|---------|------------|----------|------|
| 0 | button | | 搜索 | (750,200) | 可用 |
| 1 | input | text | 请输入关键词 | (450,180) | 可用 |

## 动作类型

| 动作 | 说明 | 参数 |
|------|------|------|
| `navigate` | 导航到 URL | `url` |
| `click` | 点击元素 | `x`, `y` (归一化坐标 0-1000) |
| `type` | 输入文本 | `x`, `y`, `text` |
| `scroll` | 滚动页面 | `direction` ("up"/"down") |
| `wait` | 等待 | `duration` (秒) |
| `backtrack` | 页面回退 | - |
| `ask_user` | 请求用户协助 | `message` |
| `complete` | 任务完成 | `message` |

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/plan` | POST | 规划下一步动作 |
| `/api/screenshot` | GET | 获取最新截图 |

### `/api/plan` 请求示例

```json
{
  "task": "打开百度首页",
  "image": "data:image/png;base64,...",
  "history": [],
  "dom_snapshot": [...]
}
```

### `/api/plan` 响应示例

```json
{
  "action": {
    "action_type": "navigate",
    "thought": "导航到百度首页",
    "params": {
      "url": "https://www.baidu.com"
    }
  }
}
```

## 注意事项

1. **API 配额**：使用 Gemini API 需要确保有足够的 API 配额
2. **网络连接**：执行任务需要稳定的网络连接
3. **页面加载**：部分页面可能需要较长时间加载，请耐心等待
4. **元素识别**：复杂页面可能会影响元素识别的准确性

## 故障排除

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| API 401 | Gemini API Key 无效 | 检查 `.env` 配置 |
| API 429 | API 配额用尽 | 等待或升级配额 |
| SSL 错误 | 网络连接问题 | 检查网络和代理设置 |
| 扩展无法连接 | 后端未启动 | 运行 `python server.py` |

### 日志查看

执行过程中的详细日志会输出到控制台，可用于调试和排查问题。

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v2.0.0
- 移除 SoM 视觉标记，改用纯坐标定位
- 移除任务分解，改为动态规划策略
- 添加 DOM 快照功能，增强元素定位
- 重构为 Chrome 扩展 + Flask 后端架构
- 优化提示词，提高任务完成准确率

### v1.0.0
- 初始化项目
- 实现基于 Gemini API 的视觉理解
- 支持交互式模式
