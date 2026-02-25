import os
from playwright.async_api import Page
import logging
logger = logging.getLogger(__name__)
from config import SCREENSHOTS_DIR

class Perception:
    """感知模块，负责获取页面截图"""
    
    def __init__(self):
        """初始化感知模块"""
        pass
    
    async def capture_screenshot(self, page: Page, step: int) -> str:
        """
        获取当前页面截图并保存
        
        Args:
            page: Playwright 页面对象
            step: 当前步骤
            
        Returns:
            截图文件路径
        """
        try:
            screenshot_path = os.path.join(SCREENSHOTS_DIR, f"step_{step}.png")
            await page.screenshot(path=screenshot_path, full_page=False)
            logger.info(f"已保存截图到: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"获取截图失败: {e}")
            raise
