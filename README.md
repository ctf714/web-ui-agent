# Web UI Agent

基于智谱视觉理解 MCP 的 Web UI Agent 项目，实现一个单步循环的 GUI Agent，能够根据自然语言指令和当前网页截图，调用智谱视觉 MCP 工具决定下一步操作，并通过 Playwright 执行浏览器动作。

## 项目架构

- `main.py`: 入口脚本，解析命令行参数，启动 Agent
- `agent.py`: Agent 核心类，实现主循环
- `perception.py`: 负责获取页面截图和管理截图文件
- `planner.py`: 与智谱视觉 MCP 交互，调用合适的工具获取动作规划
- `executor.py`: 执行具体动作（点击、输入等）
- `mcp_client.py`: MCP 客户端封装，负责连接和管理智谱视觉 MCP 服务器
- `config.py`: 加载配置（如 MCP 服务器路径、最大步数等）
- `utils.py`: 工具函数（如截图保存、日志设置）
- `requirements.txt`: 列出所有依赖
- `.env.example`: 环境变量模板

## 安装步骤

### 1. 安装 Node.js 和智谱视觉 MCP 服务器

1. 下载并安装 Node.js (v18.0.0+): https://nodejs.org/en/download/
2. 安装智谱视觉 MCP 服务器:
   ```bash
   npm install -g @z_ai/mcp-server@latest
   ```
3. 启动 MCP 服务器:
   ```bash
   # 设置 API 密钥
   export Z_AI_API_KEY=dba23fe8284e4aa592a7faf6151f0e1a.zdwNqnENJOeOtnv6
   
   # 启动服务器
   mcp-server
   ```

### 2. 配置 Python 环境

1. 创建并激活虚拟环境:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # 或 source venv/bin/activate  # Linux/Mac
   ```

2. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量:
   ```bash
   # 复制环境变量模板
   copy .env.example .env  # Windows
   # 或 cp .env.example .env  # Linux/Mac
   
   # 编辑 .env 文件，配置 API 密钥
   ```

4. 安装 Playwright 浏览器:
   ```bash
   playwright install
   ```

## 运行示例

```bash
# 在百度搜索人工智能
python main.py --task "在百度搜索人工智能"

# 无头模式运行
python main.py --task "在百度搜索人工智能" --headless true

# 设置最大步数
python main.py --task "在百度搜索人工智能" --max-steps 15
```

## 工作原理

1. **感知**: 使用 Playwright 获取当前页面截图
2. **规划**: 调用智谱视觉 MCP 的 `image_analysis` 工具分析截图，生成动作规划
3. **执行**: 根据动作规划，使用 Playwright 执行浏览器动作
4. **循环**: 重复上述步骤，直到任务完成或达到最大步数

## 动作类型

- `click`: 点击页面元素
- `type`: 输入文本
- `scroll`: 滚动页面
- `navigate`: 导航到 URL
- `wait`: 等待
- `complete`: 任务完成

## 注意事项

1. 确保智谱视觉 MCP 服务器已启动并运行在 `http://localhost:8000`
2. 确保 `.env` 文件中的 `Z_AI_API_KEY` 已正确配置
3. 首次运行时，Playwright 会自动下载所需的浏览器
4. 任务执行过程中，会在 `./screenshots/` 目录下保存每一步的截图
5. 详细日志会记录在 `agent.log` 文件中
