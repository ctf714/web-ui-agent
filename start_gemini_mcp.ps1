# 设置 Gemini API 密钥环境变量
$env:GEMINI_API_KEY = "AIzaSyAXC2sSa0DiEPhNdt9tUoJzNN9LRjDta8c"

# 验证环境变量是否设置成功
Write-Host "GEMINI_API_KEY 已设置: $env:GEMINI_API_KEY"

# 启动 Gemini MCP 服务器
Write-Host "正在启动 Gemini MCP 服务器..."
gemini-mcp