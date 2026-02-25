import asyncio
import threading
import uuid
from flask import Flask, request, jsonify, send_from_directory
import logging
import os
from agent import WebUIAgent
from config import MAX_STEPS, GEMINI_API_KEY, SCREENSHOTS_DIR
from planner import Planner
from mcp_client import MCPClient
import base64
import io
from PIL import Image

# 初始化全局规划器
mcp_client = MCPClient()
planner = Planner(mcp_client)

app = Flask(__name__)

# 手动处理 CORS，避免依赖 flask_cors
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 存储任务状态
tasks = {}

@app.route('/api', methods=['GET'])
def list_apis():
    """返回所有可用的 API 接口清单"""
    return jsonify({
        "apis": [
            {
                "path": "/api/execute",
                "method": "POST",
                "description": "提交一个新的 Agent 任务",
                "params": {"task": "string (任务描述)"}
            },
            {
                "path": "/api/status/<task_id>",
                "method": "GET",
                "description": "获取指定任务的执行状态、日志和结果"
            },
            {
                "path": "/api/screenshot",
                "method": "GET",
                "description": "获取 Agent 当前操作的实时载入截图"
            },
            {
                "path": "/api",
                "method": "GET",
                "description": "查看所有可用的接口列表"
            }
        ],
        "version": "1.0.0",
        "status": "online"
    })

def run_agent_in_thread(task_id, task_text):
    """在独立线程中运行异步 Agent"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    agent = WebUIAgent(task_text, MAX_STEPS)
    tasks[task_id]["agent"] = agent
    
    async def run():
        await agent.start()
        try:
            result = await agent.execute_task(task_text)
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = result
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)
        finally:
            await agent.stop()

    loop.run_until_complete(run())
    loop.close()

@app.route('/api/execute', methods=['POST', 'OPTIONS'])
def execute_task():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    
    # 彻底禁用旧版 Playwright 模式，强制用户刷新至“注入式”版本
    return jsonify({
        "error": "架构已升级：请在 chrome://extensions 页面点击‘刷新’按钮同步最新插件，并直接在当前网页操作即可，无需后台开启新窗口。",
        "status": "failed"
    }), 400

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
    
    task_info = tasks[task_id]
    # 提取日志（这里可以根据 WebUIAgent 的 step_history 提取更多详细信息）
    logs = []
    if task_info["agent"]:
        for step in task_info["agent"].step_history:
            thought = step['action'].get('thought', '无')
            logs.append(f"Step {step['step']}: [{step['action']['action_type']}] 思路: {thought} -> 结果: {step['result']}")

    return jsonify({
        "status": task_info["status"],
        "logs": logs,
        "last_action": task_info["agent"].step_history[-1]["action"] if task_info["agent"] and task_info["agent"].step_history else None,
        "result": task_info.get("result"),
        "error": task_info.get("error")
    })

@app.route('/api/plan', methods=['POST', 'OPTIONS'])
def plan_action():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    
    data = request.json
    task_text = data.get('task')
    image_base64 = data.get('image')
    history = data.get('history', [])
    dom_snapshot = data.get('dom_snapshot', [])  # 新增：DOM 快照
    
    logger.info(f"收到请求 - 任务: {task_text}, DOM快照元素数量: {len(dom_snapshot)}")
    
    if not task_text or not image_base64:
        return jsonify({"error": "Missing task or image"}), 400
    
    try:
        # 解码 Base64 图像
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # 保存临时截图（仅供规划器分析，完成后立即删除）
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"plan_{uuid.uuid4().hex[:8]}.png")
        image.save(screenshot_path)
        
        try:
            # 调用规划器生成动作（传入 DOM 快照以增强定位精度）
            action = planner.generate_plan(screenshot_path, task_text, history, dom_snapshot=dom_snapshot)
        finally:
            # 规划完成后立即清理截图，避免磁盘堆积
            # 注意：/api/screenshot/<filename> 接口不受影响，因为此文件原本就是临时的
            try:
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                    logger.info(f"已清理临时截图: {screenshot_path}")
            except Exception as cleanup_err:
                logger.warning(f"清理截图失败（不影响功能）: {cleanup_err}")
        
        return jsonify({
            "status": "success",
            "action": action.to_dict()
        })
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/screenshot/<filename>', methods=['GET'])
def get_specific_screenshot(filename):
    return send_from_directory(SCREENSHOTS_DIR, filename)

@app.route('/api/screenshot', methods=['GET'])
def get_screenshot():
    # 获取此目录下最新的截图
    screenshot_dir = os.path.join(os.getcwd(), "screenshots")
    if not os.path.exists(screenshot_dir):
        return jsonify({"error": "No screenshots found"}), 404
    
    files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
    if not files:
        return jsonify({"error": "No screenshots found"}), 404
    
    # 按修改时间排序
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(screenshot_dir, x)))
    return send_from_directory(screenshot_dir, latest_file)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("server.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("server")
    app.run(port=5000, debug=True, threaded=True)
