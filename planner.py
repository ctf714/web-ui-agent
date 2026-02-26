import os
from typing import Dict, Any, Optional, List
import logging
logger = logging.getLogger(__name__)
from mcp_client import MCPClient

class Action:
    """动作类"""
    
    def __init__(self, action_type: str, thought: str = "", **kwargs):
        """
        初始化动作
        
        Args:
            action_type: 动作类型，包括：click、type、scroll、navigate、wait、complete、backtrack、ask_user
            thought: 对该动作的自然语言解释
            **kwargs: 动作参数
        """
        self.action_type = action_type
        self.thought = thought
        self.params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_type": self.action_type,
            "thought": self.thought,
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
        self.current_task = ""
    
    def _analyze_history(self, step_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析步骤历史，提取有用信息"""
        analysis = {
            "total_steps": len(step_history),
            "successful_actions": 0,
            "failed_actions": 0,
            "last_action_type": None,
            "last_thought": None,
            "user_intervened": False,
            "already_completed": False,
            "suggested_improvements": [],
            "repeated_actions": False,
            "action_counts": {}
        }
        
        if not step_history:
            return analysis
        
        action_types = []
        for step in step_history:
            action = step.get('action', {})
            action_type = action.get('action_type', 'unknown')
            action_types.append(action_type)
            result = step.get('result', 'unknown')
            
            if "失败" in result or "error" in str(result).lower():
                analysis['failed_actions'] += 1
            else:
                analysis['successful_actions'] += 1
            
            if action_type == "complete":
                analysis['already_completed'] = True

            if action_type in ["ask_user", "wait"]:
                analysis['user_intervened'] = True
            
            analysis['action_counts'][action_type] = analysis['action_counts'].get(action_type, 0) + 1
        
        if len(action_types) >= 3:
            recent_actions = action_types[-3:]
            if recent_actions.count(recent_actions[0]) >= 2:
                analysis['repeated_actions'] = True
                analysis['suggested_improvements'].append(f"检测到重复的 {recent_actions[0]} 操作，请检查任务是否已完成")

        if step_history:
            last_step = step_history[-1]
            last_action = last_step.get('action', {})
            analysis['last_action_type'] = last_action.get('action_type')
            analysis['last_thought'] = last_action.get('thought')
        
        return analysis
    
    def _build_prompt(self, task: str, step_history: List[Dict[str, Any]], dom_snapshot: List[Dict] = None) -> str:
        """构建分析提示词"""
        logger.info(f"构建提示词 - DOM快照元素数量: {len(dom_snapshot) if dom_snapshot else 0}")
        
        history_analysis = self._analyze_history(step_history)
        
        history_summary = ""
        if step_history:
            history_summary = "步骤历史:\n"
            recent_steps = step_history[-5:]
            for i, step in enumerate(recent_steps, start=len(step_history)-len(recent_steps)+1):
                action_type = step.get('action', {}).get('action_type', 'unknown')
                result = step.get('result', 'unknown')
                history_summary += f"步骤 {i}: {action_type} - {result}\n"
            history_summary += "\n"
        
        analysis_summary = ""
        if history_analysis['total_steps'] > 0:
            analysis_summary = "历史分析:\n"
            analysis_summary += f"已执行步数: {history_analysis['total_steps']}\n"
            
            if history_analysis['already_completed']:
                analysis_summary += "提示: 任务在之前的步骤中已被标记为完成。请分析当前页面是否符合完成后的预期。\n"
            elif history_analysis['user_intervened']:
                analysis_summary += "提示: 用户最近可能手动操作了页面，请对比截图分析用户的意图并接手剩余工作。\n"
            
            if history_analysis['repeated_actions']:
                analysis_summary += "警告: 检测到重复操作，任务可能已经完成。请仔细检查当前页面状态，如果任务目标已经达成，请使用 complete 动作结束任务。\n"
            
            for action_type, count in history_analysis.get('action_counts', {}).items():
                if count >= 5 and action_type != 'complete':
                    analysis_summary += f"警告: {action_type} 操作已执行 {count} 次，可能陷入循环。请检查任务是否已完成或需要改变策略。\n"
            
            if history_analysis['suggested_improvements']:
                for improvement in history_analysis['suggested_improvements']:
                    analysis_summary += f"- {improvement}\n"
            analysis_summary += "\n"
        
        dom_context = ""
        if dom_snapshot:
            lines = ["# 页面可交互元素列表"]
            lines.append("以下是当前页面所有可交互元素的详细信息。请根据元素描述和坐标定位目标元素。")
            lines.append("")
            lines.append("| ID | 标签 | 类型/角色 | 文本/占位符 | 名称/ID | 坐标(x,y) | 尺寸 | 状态 |")
            lines.append("|----|----|---------|------------|--------|----------|------|------|")
            
            visible_elements = [el for el in dom_snapshot if el.get('visible', True)]
            for el in visible_elements[:80]:
                tag = el.get('tag', '')
                el_type = el.get('type') or el.get('role') or ''
                text = (el.get('text') or el.get('placeholder') or el.get('ariaLabel') or '')[:25]
                name = (el.get('name') or '')[:15]
                coords = f"({el['x']},{el['y']})"
                size = f"{el.get('width', 0)}x{el.get('height', 0)}"
                status = "禁用" if el.get('disabled') else "可用"
                
                lines.append(f"| {el['id']} | {tag} | {el_type} | {text} | {name} | {coords} | {size} | {status} |")
            
            dom_context = "\n".join(lines) + "\n\n"
            dom_context += "**重要提示**：\n"
            dom_context += "1. 坐标系为归一化坐标(0-1000)，x=0表示最左边，x=1000表示最右边\n"
            dom_context += "2. 点击时使用 params.x 和 params.y 字段传入坐标\n"
            dom_context += "3. 输入时先定位输入框坐标，再使用 params.text 传入文本\n"
            dom_context += "4. 优先选择「可用」状态的元素\n\n"

        prompt = f"""你是一个专业的 Web UI Agent，精通网页交互和元素定位。

你的工作方式：
1. **观察当前页面**：分析截图和 DOM 元素列表，理解当前页面状态
2. **理解用户任务**：明确用户想要完成什么
3. **动态规划下一步**：根据当前页面状态，决定下一步最合适的操作
4. **检测任务完成**：如果任务目标已达成，立即结束任务

# 当前用户任务
{task}

{dom_context}{history_summary}{analysis_summary}# 决策指南

## 1. 任务完成判断（最重要）
在执行任何操作前，首先检查当前页面是否已经满足任务目标：

**判断标准**：
- 打开网站任务：URL 显示目标网站域名，页面内容已加载
- 搜索任务：搜索结果页面已显示，包含相关搜索结果
- 点击任务：目标元素已被点击，页面状态已变化
- 输入任务：文本已成功输入到目标输入框

**如果任务已完成**，立即返回 complete 动作，message 中说明完成的具体内容。

## 2. 动态规划策略
根据当前页面状态选择最合适的操作：

- **navigate**: 需要打开新网站时使用，params.url 传入目标地址
- **click**: 需要点击页面元素时使用，params.x 和 params.y 传入坐标
- **type**: 需要输入文本时使用，params.x 和 params.y 定位输入框，params.text 传入文本
- **scroll**: 需要查看更多内容时使用，params.direction 传入 "down" 或 "up"
- **backtrack**: 发现操作错误需要回退时使用
- **ask_user**: 遇到验证码、登录等需要用户协助时使用
- **wait**: 页面正在加载时使用，params.duration 传入等待秒数

## 3. 元素定位方法
使用 DOM 快照表格中的坐标定位元素：
- 在表格中找到目标元素（通过文本、类型、名称匹配）
- 使用元素的坐标值作为 params.x 和 params.y
- 例如：表格显示 "| 5 | button | | 搜索 | | (750,200) | 80x30 | 可用 |"
- 则点击操作为：{{"action_type": "click", "params": {{"x": 750, "y": 200}}}}

# 输出格式
严格按照 JSON 格式输出，必须包含 thought 字段（中文说明推理过程）：

{{"action_type": "click", "thought": "你的推理过程", "params": {{"x": 750, "y": 200}}}}

示例：
- 点击操作：{{"action_type": "click", "thought": "点击搜索按钮开始搜索", "params": {{"x": 750, "y": 200}}}}
- 输入操作：{{"action_type": "type", "thought": "在搜索框输入关键词", "params": {{"x": 450, "y": 180, "text": "复旦大学校长"}}}}
- 导航操作：{{"action_type": "navigate", "thought": "导航到复旦大学官网", "params": {{"url": "https://www.fudan.edu.cn"}}}}
- 完成任务：{{"action_type": "complete", "thought": "任务已完成", "params": {{"message": "已成功找到复旦大学校长信息：XXX"}}}}
- 请求协助：{{"action_type": "ask_user", "thought": "需要用户协助", "params": {{"message": "请帮我输入验证码"}}}}

请确保你的输出只包含 JSON 格式的动作指令，不包含其他文字。"""

        return prompt
    
    def generate_plan(self, screenshot_path: str, task: str, step_history: List[Dict[str, Any]], dom_snapshot: List[Dict] = None) -> Action:
        """生成动作规划 - 每一步都根据当前页面状态动态规划"""
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if self.current_task != task:
                    logger.info(f"检测到新任务，重置状态。旧任务: {self.current_task}, 新任务: {task}")
                    self.current_task = task
                
                logger.info(f"动态规划下一步操作，任务: {task}")
                
                prompt = self._build_prompt(task, step_history, dom_snapshot=dom_snapshot)
                
                result = self.mcp_client.generate_content(screenshot_path, prompt)
                
                action = self._parse_result(result)
                logger.info(f"生成动作: {action.action_type}, 思考: {action.thought}")
                
                return action
                
            except Exception as e:
                logger.error(f"生成动作规划异常: {e}")
                retry_count += 1
                if retry_count > max_retries:
                    return Action("wait", thought="规划失败，等待后重试", duration=2)
                import time
                time.sleep(1)
        
        return Action("wait", thought="规划失败", duration=1)
    
    def _parse_result(self, result: Dict[str, Any]) -> Action:
        """解析工具返回结果"""
        try:
            import json
            import re
            
            tool_output = result.get("output", "")
            if not tool_output:
                logger.warning("没有输出文本，返回等待动作")
                return Action("wait", thought="无输出", duration=1)
            
            logger.info(f"解析 Gemini 响应: {tool_output[:200]}...")
            
            cleaned_output = tool_output.strip()
            
            if cleaned_output.startswith('```'):
                end_code_block = cleaned_output.find('```', 3)
                if end_code_block != -1:
                    cleaned_output = cleaned_output[3:end_code_block].strip()
                    if '\n' in cleaned_output:
                        first_line, rest = cleaned_output.split('\n', 1)
                        if not first_line.strip().startswith('{'):
                            cleaned_output = rest.strip()
            
            start_idx = cleaned_output.find('{')
            end_idx = cleaned_output.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = cleaned_output[start_idx:end_idx+1]
                try:
                    action_data = json.loads(json_str)
                    if isinstance(action_data, dict) and "action_type" in action_data:
                        action_type = action_data.get("action_type", "wait")
                        thought = action_data.get("thought", "")
                        params = action_data.get("params", {})
                        logger.info(f"成功解析动作: {action_type}")
                        return Action(action_type, thought=thought, **params)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析失败: {e}")
            
            logger.warning("未找到有效的动作指令，返回等待动作")
            return Action("wait", thought="解析失败", duration=2)
            
        except Exception as e:
            logger.error(f"解析动作结果失败: {e}")
            return Action("wait", thought="解析异常", duration=1)
