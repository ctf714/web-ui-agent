import os
import base64
from typing import Optional


def save_screenshot(screenshot_bytes: bytes, path: str) -> str:
    """
    保存截图
    
    Args:
        screenshot_bytes: 截图字节数据
        path: 保存路径
        
    Returns:
        保存路径
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # 保存文件
    with open(path, "wb") as f:
        f.write(screenshot_bytes)
    
    return path


def image_to_base64(image_path: str) -> str:
    """
    将图像转换为 base64 编码
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        base64 编码字符串
    """
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    return base64_str


def get_absolute_path(relative_path: str) -> str:
    """
    获取绝对路径
    
    Args:
        relative_path: 相对路径
        
    Returns:
        绝对路径
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))
