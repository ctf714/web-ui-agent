import time
import base64
import io
from typing import Dict, Any, Optional, List
import logging
logger = logging.getLogger(__name__)
from config import GEMINI_API_KEY
from google import genai
from PIL import Image

class MCPError(Exception):
    """MCP 客户端错误"""
    pass

class MCPToolError(MCPError):
    """MCP 工具调用错误"""
    pass

class MCPConnectionError(MCPError):
    """MCP 连接错误"""
    pass

class MCPResponseError(MCPError):
    """MCP 响应错误"""
    pass

class MCPClient:
    """MCP 客户端封装"""
    
    def __init__(self):
        try:
            self.api_key = GEMINI_API_KEY
            self.tools = {
                "ask_gemini": {"name": "ask_gemini"}
            }
            
            # 初始化 Gemini Client
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = "gemini-2.5-flash"  # 按照用户要求，使用 2.5 flash
            
            logger.info(f"MCP 客户端初始化成功，使用新版 google-genai SDK")
        except Exception as e:
            logger.error(f"MCP 客户端初始化失败: {e}")
            raise MCPConnectionError(f"无法初始化 Gemini API: {e}")
    
    def _image_to_base64(self, image_path: str) -> str:
        """
        将图像转换为 base64 编码
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            base64 编码字符串
        """
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return base64.b64encode(image_bytes).decode("utf-8")
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any], max_retries: int = 3, retry_delay: int = 1) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            
        Returns:
            工具返回结果
            
        Raises:
            MCPToolError: 工具调用失败
        """
        if tool_name not in self.tools:
            raise MCPToolError(f"工具 {tool_name} 不存在")
        
        retries = 0
        while retries <= max_retries:
            try:
                logger.info(f"调用 MCP 工具: {tool_name}, 参数: {parameters}")
                
                # 处理 ask_gemini 工具
                if tool_name == "ask_gemini":
                    prompt = parameters.get("prompt")
                    images = parameters.get("images", [])
                    
                    if not prompt:
                        raise MCPToolError("ask_gemini 工具需要 prompt 参数")
                    
                    # 构建内容列表
                    contents = [prompt]
                    
                    # 添加图像数据
                    for image in images:
                        if image.startswith("data:image/"):
                            # 从 base64 URL 中提取 base64 编码
                            image_data = image.split(",")[1]
                            # 将 base64 编码转换回字节
                            image_bytes = base64.b64decode(image_data)
                            # 将字节转换为 PIL Image
                            pil_image = Image.open(io.BytesIO(image_bytes))
                            # 将图像添加到内容中
                            contents.append(pil_image)
                    
                    # 调用 Gemini API
                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=contents,
                        config={
                            "temperature": 0.6,
                            "max_output_tokens": 2048
                        }
                    )
                    
                    # 解析响应
                    output = response.text
                    
                    # 构建结果
                    result = {
                        "output": output,
                        "action": {
                            "action_type": "wait",
                            "params": {
                                "duration": 1
                            }
                        }
                    }
                    
                    logger.info(f"工具 {tool_name} 调用成功，结果: {result}")
                    return result
                
                # 其他工具的处理可以在这里添加
                else:
                    logger.warning(f"工具 {tool_name} 暂未实现")
                    return {
                        "output": "工具暂未实现",
                        "action": {
                            "action_type": "wait",
                            "params": {
                                "duration": 1
                            }
                        }
                    }
                    
            except Exception as e:
                retries += 1
                if retries > max_retries:
                    logger.error(f"工具 {tool_name} 调用失败，已达到最大重试次数: {e}")
                    raise MCPToolError(f"工具调用失败: {e}")
                logger.warning(f"工具 {tool_name} 调用失败，正在重试 ({retries}/{max_retries}): {e}")
                time.sleep(retry_delay)
    
    def generate_content(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        生成内容（支持图像分析或纯文本处理）
        
        Args:
            image_path: 图像文件路径（可选，为空时只处理文本）
            prompt: 提示词
            
        Returns:
            生成结果
        """
        try:
            # 构建内容列表
            contents = [prompt]
            
            # 如果提供了图像路径且不为空，添加图像
            if image_path:
                # 读取图像文件并转换为 PIL Image 对象
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                
                # 将字节转换为 PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                contents.append(image)
                logger.info(f"开始分析图像: {image_path}")
            else:
                logger.info("无图像分析，仅处理文本提示")
            
            logger.info(f"分析提示词: {prompt[:100]}...")  # 只显示提示词的前100个字符
            
            # 调用 Gemini API
            result = self.client.models.generate_content(
                model=self.model_id,
                contents=contents,
                config={
                    "temperature": 0.6,
                    "max_output_tokens": 2048
                }
            )
            
            # 构建结果
            output = result.text
            logger.info(f"Gemini API 响应: {output[:200]}...")  # 只显示响应的前200个字符
            
            return {
                "output": output,
                "action": {
                    "action_type": "wait",
                    "params": {
                        "duration": 1
                    }
                }
            }
        except Exception as e:
            logger.error(f"分析图像失败: {e}")
            return {
                "output": f"分析图像失败: {e}",
                "action": {
                    "action_type": "wait",
                    "params": {
                        "duration": 1
                    }
                }
            }
