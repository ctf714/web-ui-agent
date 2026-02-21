import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Gemini API 密钥
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAXC2sSa0DiEPhNdt9tUoJzNN9LRjDta8c")

# MCP 服务器配置
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000")

# 浏览器配置
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"

# Agent 配置
MAX_STEPS = int(os.getenv("MAX_STEPS", "10"))

# 截图配置
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

# 确保截图目录存在
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
