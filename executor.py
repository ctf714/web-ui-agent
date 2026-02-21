import time
from typing import Dict, Any, Optional
from loguru import logger
from playwright.async_api import Page
from planner import Action

class Executor:
    """执行模块，负责执行动作"""
    
    def __init__(self):
        """初始化执行模块"""
        pass
    
    async def execute(self, page: Page, action: Action) -> str:
        """
        执行动作
        
        Args:
            page: Playwright 页面对象
            action: 动作对象
            
        Returns:
            执行结果
        """
        try:
            action_type = action.action_type
            params = action.params
            
            logger.info(f"执行动作: {action_type}, 参数: {params}")
            
            if action_type == "click":
                result = await self._execute_click(page, params)
            elif action_type == "type":
                result = await self._execute_type(page, params)
            elif action_type == "scroll":
                result = await self._execute_scroll(page, params)
            elif action_type == "navigate":
                result = await self._execute_navigate(page, params)
            elif action_type == "wait":
                result = await self._execute_wait(params)
            elif action_type == "complete":
                result = self._execute_complete(params)
            else:
                result = f"未知动作类型: {action_type}"
            
            logger.info(f"动作执行结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"执行动作失败: {e}")
            return f"执行失败: {e}"
    
    async def _execute_click(self, page: Page, params: Dict[str, Any]) -> str:
        """
        执行点击动作
        
        Args:
            page: Playwright 页面对象
            params: 动作参数，包含 x 和 y（归一化坐标 0-1000）
            
        Returns:
            执行结果
        """
        try:
            # 获取归一化坐标
            x_norm = params.get("x", 0)
            y_norm = params.get("y", 0)
            
            # 获取页面视口大小
            viewport_size = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
            width = viewport_size.get("width", 1920)
            height = viewport_size.get("height", 1080)
            
            # 转换为实际坐标
            x = int((x_norm / 1000) * width)
            y = int((y_norm / 1000) * height)
            
            logger.info(f"点击坐标: ({x}, {y}) (归一化坐标: ({x_norm}, {y_norm}))")
            
            try:
                # 第一种方式：使用 Playwright 鼠标点击
                await page.mouse.click(x, y)
                logger.info("使用 Playwright 鼠标点击成功")
            except Exception as e:
                # 第一种方式失败，尝试第二种方式
                logger.warning(f"Playwright 鼠标点击失败: {e}")
                logger.info("尝试使用 JavaScript 元素点击")
                # 第二种方式：使用 JavaScript 直接点击元素
                await page.evaluate(f"document.elementFromPoint({x}, {y})?.click()")
                logger.info("使用 JavaScript 元素点击完成")
            
            # 等待页面响应
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                # 如果 networkidle 超时，使用简短的固定等待
                await page.wait_for_timeout(1000)
            
            return f"点击坐标: ({x}, {y})"
            
        except Exception as e:
            logger.error(f"执行点击动作失败: {e}")
            return f"点击失败: {e}"
    
    async def _execute_type(self, page: Page, params: Dict[str, Any]) -> str:
        """
        执行输入动作
        
        Args:
            page: Playwright 页面对象
            params: 动作参数，包含 text（输入文本）和可选的 x、y（归一化坐标 0-1000）
            
        Returns:
            执行结果
        """
        try:
            text = params.get("text", "")
            
            # 如果提供了坐标，先点击该位置
            if "x" in params and "y" in params:
                click_params = {"x": params["x"], "y": params["y"]}
                await self._execute_click(page, click_params)
            
            # 执行输入
            await page.keyboard.type(text)
            
            # 等待页面响应
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            return f"输入文本: {text}"
            
        except Exception as e:
            logger.error(f"执行输入动作失败: {e}")
            return f"输入失败: {e}"
    
    async def _execute_scroll(self, page: Page, params: Dict[str, Any]) -> str:
        """
        执行滚动动作
        
        Args:
            page: Playwright 页面对象
            params: 动作参数，包含 direction（方向）和 distance（距离 0-1000）
            
        Returns:
            执行结果
        """
        try:
            direction = params.get("direction", "down")
            distance = params.get("distance", 500)
            
            # 转换距离为像素值
            pixel_distance = int((distance / 1000) * 1000)  # 最大滚动 1000 像素
            
            logger.info(f"滚动方向: {direction}, 距离: {pixel_distance} 像素")
            
            # 执行滚动
            if direction == "up":
                await page.mouse.wheel(0, -pixel_distance)
            elif direction == "down":
                await page.mouse.wheel(0, pixel_distance)
            elif direction == "left":
                await page.mouse.wheel(-pixel_distance, 0)
            elif direction == "right":
                await page.mouse.wheel(pixel_distance, 0)
            
            # 等待页面响应
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            return f"滚动 {direction} {pixel_distance} 像素"
            
        except Exception as e:
            logger.error(f"执行滚动动作失败: {e}")
            return f"滚动失败: {e}"
    
    async def _execute_navigate(self, page: Page, params: Dict[str, Any]) -> str:
        """
        执行导航动作
        
        Args:
            page: Playwright 页面对象
            params: 动作参数，包含 url（目标 URL）
            
        Returns:
            执行结果
        """
        try:
            url = params.get("url", "")
            
            logger.info(f"导航到: {url}")
            
            # 执行导航
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            return f"导航到: {url}"
            
        except Exception as e:
            logger.error(f"执行导航动作失败: {e}")
            return f"导航失败: {e}"
    
    async def _execute_wait(self, params: Dict[str, Any]) -> str:
        """
        执行等待动作
        
        Args:
            params: 动作参数，包含 duration（等待时间，秒）
            
        Returns:
            执行结果
        """
        try:
            duration = params.get("duration", 1)
            
            logger.info(f"等待 {duration} 秒")
            
            # 执行等待
            time.sleep(duration)
            
            return f"等待 {duration} 秒"
            
        except Exception as e:
            logger.error(f"执行等待动作失败: {e}")
            return f"等待失败: {e}"
    
    def _execute_complete(self, params: Dict[str, Any]) -> str:
        """
        执行完成动作
        
        Args:
            params: 动作参数，包含 message（完成消息）
            
        Returns:
            执行结果
        """
        try:
            message = params.get("message", "任务完成")
            
            logger.info(f"任务完成: {message}")
            
            return message
            
        except Exception as e:
            logger.error(f"执行完成动作失败: {e}")
            return f"完成失败: {e}"
