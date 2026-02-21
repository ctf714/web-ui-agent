from typing import Dict, Any, Optional, List
from loguru import logger
from mcp_client import MCPClient

class Action:
    """动作类"""
    
    def __init__(self, action_type: str, **kwargs):
        """
        初始化动作
        
        Args:
            action_type: 动作类型，包括：click、type、scroll、navigate、wait、complete
            **kwargs: 动作参数
        """
        self.action_type = action_type
        self.params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_type": self.action_type,
            "params": self.params
        }

class Planner:
    """规划模块，负责生成动作规划"""
    
    def __init__(self, mcp_client: MCPClient):
        """
        初始化规划模块
        
        Args:
            mcp_client: MCP 客户端实例
        """
        self.mcp_client = mcp_client
    
    def generate_plan(self, screenshot_path: str, task: str, step_history: List[Dict[str, Any]]) -> Action:
        """
        生成动作规划
        
        Args:
            screenshot_path: 截图文件路径
            task: 用户任务
            step_history: 步骤历史
            
        Returns:
            动作对象
        """
        try:
            # 构建分析提示词
            prompt = self._build_prompt(task, step_history)
            
            # 调用图像分析工具
            result = self.mcp_client.analyze_image(screenshot_path, prompt)
            
            # 解析工具返回结果，生成动作
            action = self._parse_result(result)
            
            logger.info(f"生成动作规划: {action.to_dict()}")
            return action
            
        except Exception as e:
            logger.error(f"生成动作规划失败: {e}")
            # 出错时返回等待动作
            return Action("wait", duration=1)
    
    def _build_prompt(self, task: str, step_history: List[Dict[str, Any]]) -> str:
        """
        构建分析提示词
        
        Args:
            task: 用户任务
            step_history: 步骤历史
            
        Returns:
            提示词字符串
        """
        prompt = f"""
        你是一个 Web UI Agent，需要根据用户任务和当前页面截图，决定下一步操作。
        
        用户任务: {task}
        
        步骤历史:
        """
        
        for i, step in enumerate(step_history):
            prompt += f"步骤 {i+1}: {step.get('action', {}).get('action_type', 'unknown')} - {step.get('result', 'unknown')}\n"
        
        prompt += """
        
        请分析当前页面截图，理解页面布局和元素，并根据用户任务生成下一步操作。
        
        请按照以下格式输出结构化动作指令：
        
        动作类型包括：
        1. click: 点击页面元素
           - 参数: x (归一化坐标 0-1000), y (归一化坐标 0-1000)
        2. type: 输入文本
           - 参数: text (输入文本), x (归一化坐标 0-1000), y (归一化坐标 0-1000)
        3. scroll: 滚动页面
           - 参数: direction (方向: up/down/left/right), distance (距离: 0-1000)
        4. navigate: 导航到 URL
           - 参数: url (目标 URL)
        5. wait: 等待
           - 参数: duration (等待时间，秒)
        6. complete: 任务完成
           - 参数: message (完成消息)
        
        请根据当前页面情况，选择最合适的动作类型，并提供相应的参数。
        坐标使用归一化格式 0-1000，其中 (0,0) 是页面左上角，(1000,1000) 是页面右下角。
        
        输出示例：
        {
            "action_type": "click",
            "params": {
                "x": 500,
                "y": 300
            }
        }
        """
        
        return prompt
    
    def _parse_result(self, result: Dict[str, Any]) -> Action:
        """
        解析工具返回结果
        
        Args:
            result: 工具返回结果
            
        Returns:
            动作对象
        """
        try:
            # 从结果中提取动作指令
            # 首先尝试从 action 字段中提取
            action_data = result.get("action", {})
            
            if action_data and action_data.get("action_type") != "wait":
                # 如果有有效的 action 字段且不是等待动作，使用它
                action_type = action_data.get("action_type", "wait")
                params = action_data.get("params", {})
                return Action(action_type, **params)
            else:
                # 如果没有有效的 action 字段，尝试从工具返回的文本中解析
                tool_output = result.get("output", "")
                if tool_output:
                    logger.info(f"尝试从 Gemini 响应中解析动作: {tool_output}")
                    
                    # 尝试从文本中提取 JSON 格式的动作指令
                    import json
                    import re
                    
                    # 清理工具输出，移除可能的代码块标记
                    cleaned_output = tool_output.strip()
                    if cleaned_output.startswith('```json'):
                        cleaned_output = cleaned_output[7:]
                    if cleaned_output.endswith('```'):
                        cleaned_output = cleaned_output[:-3]
                    cleaned_output = cleaned_output.strip()
                    
                    # 尝试直接解析清理后的输出
                    try:
                        action_data = json.loads(cleaned_output)
                        action_type = action_data.get("action_type", "wait")
                        params = action_data.get("params", {})
                        return Action(action_type, **params)
                    except json.JSONDecodeError as e:
                        logger.warning(f"直接解析 JSON 失败: {e}")
                    
                    # 如果直接解析失败，尝试查找 JSON 格式的动作指令
                    try:
                        # 使用更可靠的方法查找 JSON 对象
                        # 找到第一个 { 和最后一个 }
                        start_idx = cleaned_output.find('{')
                        end_idx = cleaned_output.rfind('}')
                        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                            action_json = cleaned_output[start_idx:end_idx+1]
                            action_data = json.loads(action_json)
                            action_type = action_data.get("action_type", "wait")
                            params = action_data.get("params", {})
                            return Action(action_type, **params)
                    except json.JSONDecodeError as e:
                        logger.warning(f"查找 JSON 失败: {e}")
                        if 'action_json' in locals():
                            logger.warning(f"JSON 内容: {action_json}")
                    
                    # 如果没有找到 JSON 格式的动作指令，根据文本内容生成动作
                    # 这里可以添加更复杂的文本解析逻辑
                    # 暂时返回等待动作
                    return Action("wait", duration=1)
                else:
                    # 如果没有输出文本，返回等待动作
                    return Action("wait", duration=1)
            
        except Exception as e:
            logger.error(f"解析动作结果失败: {e}")
            return Action("wait", duration=1)
