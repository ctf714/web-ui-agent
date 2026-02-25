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
        self.subtasks = []
        self.current_subtask_index = 0
        self.task_decomposition_done = False
    
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
            # 更新当前任务
            self.current_task = task
            
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
    
    def _analyze_history(self, step_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析步骤历史，提取有用信息
        """
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
        
        # 统计动作类型出现次数
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

            # 检测用户干预：如果上一个动作是 ask_user 或 wait，且当前有了结果（非失败），说明用户可能操作了
            if action_type in ["ask_user", "wait"]:
                analysis['user_intervened'] = True
            
            # 统计动作类型出现次数
            analysis['action_counts'][action_type] = analysis['action_counts'].get(action_type, 0) + 1
        
        # 检测重复操作：如果最近3次操作中有2次以上相同类型的操作，则认为重复
        if len(action_types) >= 3:
            recent_actions = action_types[-3:]
            if recent_actions.count(recent_actions[0]) >= 2:
                analysis['repeated_actions'] = True
                analysis['suggested_improvements'].append(f"检测到重复的 {recent_actions[0]} 操作，请检查任务是否已完成")

        last_step = step_history[-1]
        last_action = last_step.get('action', {})
        analysis['last_action_type'] = last_action.get('action_type')
        analysis['last_thought'] = last_action.get('thought')
        
        return analysis
    
    def _build_prompt(self, task: str, step_history: List[Dict[str, Any]], dom_snapshot: List[Dict] = None) -> str:
        """
        构建分析提示词
        
        Args:
            task: 用户任务
            step_history: 步骤历史
            
        Returns:
            提示词字符串
        """
        logger.info(f"构建提示词 - DOM快照元素数量: {len(dom_snapshot) if dom_snapshot else 0}")
        
        # 分析历史操作
        history_analysis = self._analyze_history(step_history)
        
        # 构建步骤历史摘要
        history_summary = ""
        if step_history:
            history_summary = "步骤历史:\n"
            # 只显示最近5个步骤，避免提示词过长
            recent_steps = step_history[-5:]
            for i, step in enumerate(recent_steps, start=len(step_history)-len(recent_steps)+1):
                action_type = step.get('action', {}).get('action_type', 'unknown')
                result = step.get('result', 'unknown')
                history_summary += f"步骤 {i}: {action_type} - {result}\n"
            history_summary += "\n"
        
        analysis_summary = ""  # 默认为空，避免 step_history 为空时变量未定义
        if history_analysis['total_steps'] > 0:
            analysis_summary = "历史分析:\n"
            analysis_summary += f"已执行步数: {history_analysis['total_steps']}\n"
            
            if history_analysis['already_completed']:
                analysis_summary += "提示: 任务在之前的步骤中已被标记为完成。请分析当前页面是否符合完成后的预期。如果用户进行了手动操作，请指出并询问后续需求。\n"
            elif history_analysis['user_intervened']:
                analysis_summary += "提示: 用户最近可能手动操作了页面，请对比截图分析用户的意图并接手剩余工作。\n"
            
            if history_analysis['repeated_actions']:
                analysis_summary += "警告: 检测到重复操作，任务可能已经完成。请仔细检查当前页面状态，如果任务目标已经达成，请使用 complete 动作结束任务。\n"
            
            # 如果某种操作执行次数过多，也提示
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

        # 直接用 f-string 拼接，避免 format() 因新增变量名不同步导致 KeyError
        prompt = f"""你是一个专业的 Web UI Agent，精通网页交互和元素定位。你的任务是根据用户指令、当前页面截图和历史操作记录，分析页面结构，识别关键元素，并生成精确的下一步操作计划。

# 元素定位说明
页面元素信息由下方「页面可交互元素列表」表格提供，包含每个元素的坐标、类型、文本等信息。
请根据表格中的坐标 (x, y) 进行操作，坐标系为归一化坐标 (0-1000)。

# 用户任务
{task}

{dom_context}{history_summary}{analysis_summary}# 页面分析指南
1. **任务完成判断（最重要）**：
   - 在执行任何操作前，首先检查当前页面是否已经满足任务目标。
   - 如果搜索结果已经显示、目标内容已经出现、目标页面已经打开，请立即使用 `complete` 动作结束任务。
   - 不要重复执行相同的操作，如果发现重复操作，请检查任务是否已完成。

2. **人机协同策略**：
   - 如果上一历史步是 `ask_user` 或 `wait`，请对比截图与历史，分析用户是否已完成请求的操作。
   - 在 `thought` 中明确指出你观察到的页面状态变化。

3. **元素定位策略**：
   - **核心方法：使用 DOM 快照表格中的坐标**。表格提供了每个元素的归一化坐标 (x, y)，范围 0-1000。
   - **定位步骤**：
     1. 在表格中找到目标元素（通过文本、类型、名称等匹配）
     2. 使用该元素的坐标值作为 params.x 和 params.y
     3. 例如：表格显示"搜索按钮 | button | | 搜索 | | (750,200) | 80x30 | 可用 |"
     4. 则操作为：{{"action_type": "click", "params": {{"x": 750, "y": 200}}}}
   - **输入操作**：先定位输入框坐标，再添加 params.text 字段
     例如：{{"action_type": "type", "params": {{"x": 450, "y": 180, "text": "AI新闻"}}}}

4. **动作选择策略**：
   - **回退 (backtrack)**: 发现操作错误或页面状态异常时使用。
   - **任务完成 (complete)**: 必须在截图中见到明确成功证据才使用。
   - **请求协助 (ask_user)**: 遇到验证码、需要登录或操作存在风险时使用，`message` 字段写明需要用户做什么。

# 输出格式
严格按照 JSON 格式输出，必须包含 `thought` 字段（中文说明推理过程）：

动作类型：click(x,y) | type(text,x,y) | scroll(direction) | navigate(url) | wait(duration) | backtrack | ask_user(message) | complete(message)

示例：
- 点击操作：{{"action_type": "click", "thought": "点击搜索按钮", "params": {{"x": 750, "y": 200}}}}
- 输入操作：{{"action_type": "type", "thought": "在搜索框输入关键词", "params": {{"x": 450, "y": 180, "text": "AI新闻"}}}}
- 完成任务：{{"action_type": "complete", "thought": "搜索结果已显示，任务完成", "params": {{"message": "搜索完成"}}}}
- 请求协助：{{"action_type": "ask_user", "thought": "页面弹出了验证码", "params": {{"message": "请帮我输入验证码"}}}}

请确保你的输出只包含 JSON 格式的动作指令，不包含其他文字。"""

        return prompt
    
    def _decompose_task(self, task: str) -> List[str]:
        """
        分解复杂任务为子任务
        
        Args:
            task: 原始任务
            
        Returns:
            子任务列表
        """
        try:
            # 构建任务分解提示词
            decomposition_prompt = """
你是一个任务分解专家，擅长将复杂的Web操作任务分解为简单、可执行的子任务。

请将以下任务分解为具体的子任务，每个子任务应该是一个明确的、可执行的操作：

任务：{task}

分解要求：
1. 每个子任务应该具体明确，只包含一个操作
2. 子任务应该按执行顺序排列
3. 子任务数量应该合理，既不过多也不过少
4. 子任务应该覆盖整个任务的所有步骤

请以JSON格式输出子任务列表，例如：
{{
  "subtasks": [
    "打开百度首页",
    "在搜索框中输入关键词",
    "点击搜索按钮"
  ]
}}
            """.format(task=task)
            
            # 调用 Gemini API 进行任务分解
            # 构建一个空的图像路径（因为任务分解不需要图像）
            empty_image_path = ""
            # 使用 generate_content 方法，但不传入实际图像
            result = self.mcp_client.generate_content(empty_image_path, decomposition_prompt)
            
            # 解析返回结果
            import json
            import re
            
            # 从 analyze_image 的返回结果中提取 output
            output = result.get("output", "")
            logger.info(f"任务分解结果: {output[:200]}...")
            
            # 提取 JSON 部分
            cleaned_output = output.strip()
            
            # 尝试处理 Markdown 代码块
            if cleaned_output.startswith('```'):
                # 找到代码块结束标记
                end_code_block = cleaned_output.find('```', 3)
                if end_code_block != -1:
                    cleaned_output = cleaned_output[3:end_code_block].strip()
                    # 移除可能的语言标记（如 json）
                    if '\n' in cleaned_output:
                        first_line, rest = cleaned_output.split('\n', 1)
                        if not first_line.strip().startswith('{'):
                            cleaned_output = rest.strip()
                    elif not cleaned_output.startswith('{'):
                        # 如果第一行不是 JSON 开始，尝试找到 JSON 开始
                        json_start = cleaned_output.find('{')
                        if json_start != -1:
                            cleaned_output = cleaned_output[json_start:].strip()
            
            # 尝试找到 JSON 对象
            start_idx = cleaned_output.find('{')
            end_idx = cleaned_output.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = cleaned_output[start_idx:end_idx+1]
                try:
                    decomposition_result = json.loads(json_str)
                    subtasks = decomposition_result.get('subtasks', [])
                    logger.info(f"成功分解任务为 {len(subtasks)} 个子任务")
                    return subtasks
                except json.JSONDecodeError as e:
                    logger.error(f"解析任务分解结果失败: {e}")
            
            # 如果解析失败，返回默认子任务
            logger.warning("任务分解失败，使用默认子任务")
            return [task]
            
        except Exception as e:
            logger.error(f"任务分解失败: {e}")
            return [task]
    
    def _get_current_subtask(self) -> str:
        """
        获取当前正在执行的子任务
        
        Returns:
            当前子任务
        """
        if self.subtasks and self.current_subtask_index < len(self.subtasks):
            return self.subtasks[self.current_subtask_index]
        return self.current_task
    
    def _mark_subtask_completed(self) -> None:
        """
        标记当前子任务完成，移动到下一个子任务
        """
        if self.current_subtask_index < len(self.subtasks) - 1:
            self.current_subtask_index += 1
            logger.info(f"子任务完成，开始执行下一个子任务: {self._get_current_subtask()}")
        else:
            logger.info("所有子任务已完成")
    
    def _check_task_completion(self) -> bool:
        """
        检查整个任务是否完成
        
        Returns:
            是否完成
        """
        return not self.subtasks or self.current_subtask_index >= len(self.subtasks)
    
    def generate_plan(self, screenshot_path: str, task: str, step_history: List[Dict[str, Any]], dom_snapshot: List[Dict] = None) -> Action:
        """
        生成动作规划
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # 状态重置检查：如果任务描述变了，重置解析标志
                if self.current_task != task:
                    logger.info(f"检测到新任务，重置状态。旧任务: {self.current_task}, 新任务: {task}")
                    self.task_decomposition_done = False
                    self.subtasks = []
                    self.current_subtask_index = 0
                
                self.current_task = task
                
                # 如果是第一次执行，分解任务
                if not self.task_decomposition_done:
                    logger.info(f"开始分解任务: {task}")
                    try:
                        self.subtasks = self._decompose_task(task)
                        self.current_subtask_index = 0
                        self.task_decomposition_done = True
                        
                        if len(self.subtasks) > 1:
                            logger.info(f"任务分解完成，共 {len(self.subtasks)} 个子任务")
                            for i, subtask in enumerate(self.subtasks):
                                logger.info(f"子任务 {i+1}: {subtask}")
                    except Exception as decompose_error:
                        logger.error(f"任务分解失败: {decompose_error}")
                        self.subtasks = [task]
                        self.current_subtask_index = 0
                        self.task_decomposition_done = True
                
                # 获取当前子任务
                current_subtask = self._get_current_subtask()
                logger.info(f"当前执行子任务: {current_subtask}")
                
                # 构建分析提示词（传入 DOM 快照以提升定位精度）
                try:
                    prompt = self._build_prompt(current_subtask, step_history, dom_snapshot=dom_snapshot)
                except Exception as prompt_error:
                    logger.error(f"提示词构建失败: {prompt_error}")
                    return Action("wait", duration=2)
                
                # 调用内容生成工具
                try:
                    result = self.mcp_client.generate_content(screenshot_path, prompt)
                except Exception as api_error:
                    logger.error(f"API 调用失败: {api_error}")
                    if "401" in str(api_error) or "unauthorized" in str(api_error).lower():
                        return Action("complete", message="任务失败: API 认证错误")
                    elif "429" in str(api_error) or "quota" in str(api_error).lower():
                        return Action("complete", message="任务失败: API 配额用尽")
                    else:
                        retry_count += 1
                        if retry_count > max_retries:
                            return Action("wait", duration=3)
                        import time
                        time.sleep(2)
                        continue
                
                # 解析工具返回结果
                try:
                    action = self._parse_result(result)
                    
                    # 检查子任务层进逻辑
                    if action.action_type == "complete":
                        if len(self.subtasks) > 1:
                            self._mark_subtask_completed()
                            # 如果还有后续子任务，则转为 wait 以便下一步分析新的子任务
                            if not self._check_task_completion():
                                return Action("wait", duration=1)
                    
                    return action
                except Exception as parse_error:
                    logger.error(f"解析动作失败: {parse_error}")
                    return Action("wait", duration=2)
                
            except Exception as e:
                logger.error(f"生成动作规划异常: {e}")
                retry_count += 1
                if retry_count > max_retries:
                    return Action("wait", duration=2)
                import time
                time.sleep(1)
        
        return Action("wait", duration=1)
    
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
            
            if action_data and isinstance(action_data, dict):
                action_type = action_data.get("action_type", "wait")
                if action_type != "wait":
                    # 如果有有效的 action 字段且不是等待动作，使用它
                    params = action_data.get("params", {})
                    logger.info(f"从 action 字段提取动作: {action_type}")
                    return Action(action_type, **params)
            
            # 如果没有有效的 action 字段，尝试从工具返回的文本中解析
            tool_output = result.get("output", "")
            if tool_output:
                logger.info(f"尝试从 Gemini 响应中解析动作: {tool_output[:200]}...")
                
                # 尝试从文本中提取 JSON 格式的动作指令
                import json
                import re
                
                # 清理工具输出，移除可能的代码块标记
                cleaned_output = tool_output.strip()
                
                # 处理各种代码块标记格式
                code_block_patterns = [
                    ('```json', '```'),
                    ('```', '```')
                ]
                
                json_candidate = cleaned_output
                
                # 尝试移除代码块标记
                for start_marker, end_marker in code_block_patterns:
                    if cleaned_output.startswith(start_marker):
                        json_candidate = cleaned_output[len(start_marker):]
                        if json_candidate.endswith(end_marker):
                            json_candidate = json_candidate[:-len(end_marker)]
                        json_candidate = json_candidate.strip()
                        break
                
                # 尝试直接解析清理后的输出
                try:
                    action_data = json.loads(json_candidate)
                    if isinstance(action_data, dict):
                        action_type = action_data.get("action_type", "wait")
                        thought = action_data.get("thought", "")
                        params = action_data.get("params", {})
                        logger.info(f"成功解析 JSON 动作: {action_type}, 思考: {thought}")
                        return Action(action_type, thought=thought, **params)
                except json.JSONDecodeError as e:
                    logger.warning(f"直接解析 JSON 失败: {e}")
                
                # 如果直接解析失败，尝试查找 JSON 对象
                try:
                    # 使用更智能的方法查找 JSON 对象
                    # 找到所有可能的 JSON 开始和结束位置
                    json_pattern = re.compile(r'\{[\s\S]*?\}', re.MULTILINE)
                    json_matches = json_pattern.findall(cleaned_output)
                    
                    for json_str in json_matches:
                        try:
                            action_data = json.loads(json_str)
                            if isinstance(action_data, dict) and "action_type" in action_data:
                                action_type = action_data.get("action_type", "wait")
                                thought = action_data.get("thought", "")
                                params = action_data.get("params", {})
                                logger.info(f"成功从文本中提取 JSON 动作: {action_type}, 思考: {thought}")
                                return Action(action_type, thought=thought, **params)
                        except json.JSONDecodeError:
                            continue
                except Exception as e:
                    logger.warning(f"查找 JSON 失败: {e}")
                
                # 如果没有找到有效的 JSON 动作指令，尝试基于任务类型生成默认动作
                # 这里可以根据任务类型添加更智能的回退机制
                if "打开" in self.current_task:
                    if "百度" in self.current_task:
                        logger.info(f"任务包含百度，导航到百度首页")
                        return Action("navigate", url="https://www.baidu.com")
                    elif "GitHub" in self.current_task:
                        logger.info(f"任务包含 GitHub，导航到 GitHub 首页")
                        return Action("navigate", url="https://github.com")
                    elif "网页" in self.current_task:
                        # 尝试从任务中提取 URL
                        url_pattern = re.compile(r'(https?://[\w\-]+(\.[\w\-]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#]))')
                        url_match = url_pattern.search(self.current_task)
                        if url_match:
                            url = url_match.group(1)
                            logger.info(f"从任务中提取 URL: {url}")
                            return Action("navigate", url=url)
                
                # 如果是搜索任务，尝试生成搜索相关动作
                if "搜索" in self.current_task:
                    # 假设当前在百度首页，尝试点击搜索框
                    logger.info(f"任务包含搜索，尝试点击搜索框")
                    return Action("click", x=450, y=180)
                
                # 如果没有找到有效的动作指令，返回等待动作
                logger.warning("未找到有效的动作指令，返回等待动作")
                return Action("wait", duration=2)
            else:
                # 如果没有输出文本，返回等待动作
                logger.warning("没有输出文本，返回等待动作")
                return Action("wait", duration=1)
            
        except Exception as e:
            logger.error(f"解析动作结果失败: {e}")
            # 出错时根据任务类型返回适当的回退动作
            if "打开" in self.current_task and "百度" in self.current_task:
                return Action("navigate", url="https://www.baidu.com")
            return Action("wait", duration=1)
