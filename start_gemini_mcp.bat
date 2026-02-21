@echo off

:: 设置 API 密钥环境变量
set GEMINI_API_KEY=AIzaSyAXC2sSa0DiEPhNdt9tUoJzNN9LRjDta8c

:: 验证环境变量是否设置成功
echo API 密钥已设置

:: 启动 MCP 服务器
echo 正在启动 Gemini MCP 服务器...
npx @houtini/gemini-mcp@latest