import os
import google.generativeai as genai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取 API 密钥
api_key = os.getenv("GEMINI_API_KEY", "")

if not api_key:
    print("错误: API 密钥未设置")
    exit(1)

# 配置 Gemini API
try:
    genai.configure(api_key=api_key)
    print("Gemini API 配置成功")
except Exception as e:
    print(f"Gemini API 配置失败: {e}")
    exit(1)

# 列出所有可用的模型
try:
    models = genai.list_models()
    print("\n可用的模型:")
    for model in models:
        print(f"- {model.name}")
        print(f"  支持的方法: {model.supported_generation_methods}")
        print()
except Exception as e:
    print(f"列出模型失败: {e}")
    exit(1)
