import argparse
import asyncio
import logging
logger = logging.getLogger(__name__)
from agent import WebUIAgent
from config import MAX_STEPS

def parse_args():
    """
    解析命令行参数
    
    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(description="Web UI Agent")
    parser.add_argument("--headless", type=bool, default=False, help="是否以无头模式运行浏览器")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS, help="最大步数")
    parser.add_argument("--task", type=str, default=None, help="任务内容")
    return parser.parse_args()

async def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    logger.info(f"启动 Web UI Agent")
    logger.info(f"最大步数: {args.max_steps}")
    
    # 创建 Agent 实例
    agent = WebUIAgent("初始化", args.max_steps)
    
    # 启动 Agent（初始化浏览器）
    await agent.start()
    
    try:
        # 如果指定了任务参数，直接执行任务并退出
        if args.task:
            task = args.task
            logger.info(f"命令行指定任务: {task}")
            print(f"\n正在执行任务: {task}")
            
            result = await agent.execute_task(task)
            
            logger.info(f"任务执行结果: {result}")
            print(f"\n任务执行结果: {result}")
        else:
            # 进入交互式模式
            print("=== Web UI Agent 交互式模式 ===")
            print("输入任务内容，或输入 'exit' 退出程序")
            print("\n示例任务:")
            print("  打开百度首页")
            print("  打开百度网页并搜索：什么ai最好用")
            print("  打开GitHub官网")
            
            while True:
                # 读取用户输入
                task = input("\n请输入任务: ").strip()
                
                # 检查是否退出
                if task.lower() == "exit":
                    print("正在退出...")
                    break
                
                # 检查任务是否为空
                if not task:
                    print("任务不能为空，请重新输入")
                    continue
                
                # 执行任务
                logger.info(f"用户输入任务: {task}")
                print(f"\n正在执行任务: {task}")
                
                result = await agent.execute_task(task)
                
                logger.info(f"任务执行结果: {result}")
                print(f"\n任务执行结果: {result}")
                print("\n===================================")
                print("输入新的任务，或输入 'exit' 退出程序")
            
    finally:
        # 停止 Agent（关闭浏览器）
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
