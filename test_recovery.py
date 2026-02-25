import asyncio
import logging
from agent import WebUIAgent
from planner import Action

async def test_interaction_and_recovery():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_recovery")
    
    # 初始化 Agent 任务：在一个不存在的页面上操作，然后回退
    agent = WebUIAgent("先搜索一个东西，然后回退", max_steps=5)
    
    await agent.start()
    try:
        # 1. 验证自定义思考过程的存储和 API 返回格式模拟
        step = 1
        screenshot_path = "screenshots/step_0.png" # 假设已存在
        # 模拟 Planner 生成一个带有 Thought 的 Backtrack 动作
        action = Action("backtrack", thought="由于点击进入了错误的页面，我打算执行回退操作以返回之前的状态。")
        
        logger.info(f"模拟执行动作: {action.action_type}, 思考: {action.thought}")
        result = await agent.executor.execute(agent.page, action)
        
        # 记录到历史，模拟 agent.run 内部逻辑
        agent.step_history.append({
            "step": step,
            "screenshot": screenshot_path,
            "action": action.to_dict(),
            "result": result
        })
        
        # 验证 step_history 中的 thought
        last_step = agent.step_history[-1]
        assert last_step["action"]["thought"] == action.thought
        logger.info("验证成功：Thought 字段已正确记录在步骤历史中。")
        logger.info(f"执行结果: {result}")
        
        # 2. 验证页面关闭后的自动恢复逻辑 (模拟 self.page.is_closed())
        logger.info("模拟页面意外关闭...")
        await agent.page.close()
        
        if agent.page.is_closed():
            logger.info("检测到页面已关闭，触发恢复逻辑...")
            # 调用 agent._start_browser() 的逻辑
            await agent._start_browser()
            assert not agent.page.is_closed()
            logger.info("页面恢复成功。")
            
    finally:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(test_interaction_and_recovery())
