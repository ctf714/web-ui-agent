import asyncio
from typing import Dict, Any, List, Optional
import logging
logger = logging.getLogger(__name__)
from playwright.async_api import async_playwright, Browser, Page
from perception import Perception
from planner import Planner
from executor import Executor
from mcp_client import MCPClient
from config import HEADLESS, MAX_STEPS

class WebUIAgent:
    """Web UI Agent 核心类"""
    
    def __init__(self, task: str, max_steps: int = MAX_STEPS):
        """
        初始化 Agent
        
        Args:
            task: 用户任务
            max_steps: 最大步数
        """
        self.task = task
        self.max_steps = max_steps
        self.step_history: List[Dict[str, Any]] = []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.perception = Perception()
        self.mcp_client = MCPClient()
        self.planner = Planner(self.mcp_client)
        self.executor = Executor()
    
    async def run(self) -> str:
        """
        运行 Agent
        
        Returns:
            任务执行结果
        """
        try:
            # 主循环
            for step in range(1, self.max_steps + 1):
                logger.info(f"\n=== 步骤 {step}/{self.max_steps} ===")
                
                # 0. 容错改进：检查页面是否失效或关闭
                if not self.page or self.page.is_closed():
                    logger.warning("检测到浏览器页面已关闭或未初始化，尝试恢复...")
                    await self._start_browser()
                
                logger.info(f"当前任务: {self.task}")
                
                # 1. 感知：获取页面截图
                screenshot_path = await self.perception.capture_screenshot(self.page, step)
                
                # 2. 规划：生成动作规划
                action = self.planner.generate_plan(screenshot_path, self.task, self.step_history)
                
                # 交互增强：打印 Agent 的思考过程
                if action.thought:
                    logger.info(f"Agent 思考: {action.thought}")
                
                # 3. 执行：执行动作
                result = await self.executor.execute(self.page, action)
                
                # 记录步骤历史
                self.step_history.append({
                    "step": step,
                    "screenshot": screenshot_path,
                    "action": action.to_dict(),
                    "result": result
                })
                
                # 检查是否完成任务
                if action.action_type == "complete":
                    logger.info(f"\n=== 任务完成 ===")
                    logger.info(f"完成消息: {result}")
                    return result
                
            # 达到最大步数
            logger.info(f"\n=== 达到最大步数 ===")
            return f"任务未完成，已达到最大步数 {self.max_steps}"
            
        except Exception as e:
            logger.error(f"Agent 运行失败: {e}")
            return f"Agent 运行失败: {e}"
    
    async def start(self) -> None:
        """
        启动 Agent（初始化浏览器）
        """
        await self._start_browser()
    
    async def stop(self) -> None:
        """
        停止 Agent（关闭浏览器）
        """
        await self._close_browser()
    
    async def execute_task(self, task: str) -> str:
        """
        执行指定任务
        
        Args:
            task: 用户任务
            
        Returns:
            任务执行结果
        """
        self.task = task
        self.step_history = []  # 重置步骤历史
        return await self.run()
    
    async def _start_browser(self) -> None:
        """
        启动浏览器
        """
        try:
            logger.info(f"启动浏览器 (headless: {HEADLESS})")
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=HEADLESS,
                args=["--start-maximized"]
            )
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            self.page = await context.new_page()
            
            # 导航到默认页面
            await self.page.goto("https://www.baidu.com", wait_until="networkidle")
            logger.info("浏览器启动成功")
            
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            raise
    
    async def _close_browser(self) -> None:
        """
        关闭浏览器
        """
        try:
            if self.browser:
                logger.info("关闭浏览器")
                await self.browser.close()
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
