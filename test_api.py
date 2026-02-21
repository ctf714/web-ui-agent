import os
import google.generativeai as genai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取 API 密钥
api_key = os.getenv("GEMINI_API_KEY", "")

print(f"API 密钥: {api_key}")
print(f"API 密钥长度: {len(api_key)}")

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

# 创建模型实例
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("模型创建成功")
except Exception as e:
    print(f"模型创建失败: {e}")
    exit(1)

# 测试简单的文本生成
try:
    response = model.generate_content("Hello, world!")
    print(f"文本生成成功: {response.text}")
except Exception as e:
    print(f"文本生成失败: {e}")
    exit(1)

print("API 测试成功！")
