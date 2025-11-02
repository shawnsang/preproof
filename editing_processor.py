import openai
from typing import List, Dict, Tuple
from loguru import logger


class EditingProcessor:
    """编辑整理处理器，负责分块编辑逻辑"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        """
        初始化编辑处理器
        
        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL
            model: 使用的模型名称
        """
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        logger.info(f"初始化编辑处理器，使用模型: {model}")

    def edit_chunk(self, chunk_info: Dict, domain_knowledge: str = "", keywords: str = "") -> Dict:
        """
        编辑单个文本块
        
        Args:
            chunk_info: 包含文本块信息的字典
            domain_knowledge: 领域知识
            keywords: 关键字
            
        Returns:
            编辑结果字典，包含编辑后的内容和元数据
        """
        content = chunk_info['content']
        index = chunk_info['index']
        total = chunk_info['total']
        context = chunk_info['context']
        
        logger.info(f"开始编辑第 {index}/{total} 个文本块")
        
        # 构建提示词
        prompt = self._build_editing_prompt(content, index, total, context, domain_knowledge, keywords)
        
        logger.info(f"编辑提示词:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # 解析编辑结果
            parsed_result = self._parse_editing_result(result, index, total)
            
            logger.success(f"第 {index}/{total} 块编辑完成，输出长度: {len(result)} 字符")
            
            return {
                'content': parsed_result['content'],
                'titles': parsed_result['titles'],
                'golden_quotes': parsed_result['golden_quotes'],
                'index': index,
                'total': total,
                'raw_result': result
            }
            
        except Exception as e:
            error_msg = f"第 {index}/{total} 块编辑失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _build_editing_prompt(self, content: str, index: int, total: int, context: Dict, 
                            domain_knowledge: str, keywords: str) -> str:
        """构建编辑提示词"""
        
        # 基础提示
        base_prompt = f"""请对以下已校对的文字进行编辑整理，这是第 {index}/{total} 个文本块。

编辑要求：
1. 合理分段，每段内容相对独立
2. 为每个段落添加合适的小标题（使用 ## 格式）
3. 优化文字结构和逻辑顺序
4. 使用Markdown格式输出
5. 保持内容的完整性和准确性"""

        # 添加上下文信息
        context_info = ""
        if not context.get('is_single', False):
            if context.get('is_first'):
                context_info += "\n\n**注意：这是第一个文本块，请设置合适的开头结构。**"
            elif context.get('is_last'):
                context_info += "\n\n**注意：这是最后一个文本块，请在文档最后添加\"💎 精彩金句\"部分。**"
            else:
                context_info += f"\n\n**注意：这是中间文本块（第{index}/{total}块），请保持与前后内容的连贯性。**"
            
            if context.get('previous_summary'):
                context_info += f"\n前一块内容摘要：{context['previous_summary']}"
            
            if context.get('next_preview'):
                context_info += f"\n下一块内容预览：{context['next_preview']}"

        # 添加领域知识和关键字
        domain_info = ""
        if domain_knowledge:
            domain_info += f"\n\n领域知识：{domain_knowledge}"
        if keywords:
            domain_info += f"\n关键字：{keywords}"

        # 输出格式要求
        format_requirements = """

输出格式要求：
- 使用 ## 作为主要段落标题
- 使用 ### 作为子段落标题（如需要）
- 保持Markdown格式的规范性"""

        # 特殊处理最后一块
        if context.get('is_last') or context.get('is_single', False):
            format_requirements += """
- 在文档最后添加：
  ## 💎 精彩金句
  - 金句1
  - 金句2
  - ..."""

        # 组合完整提示词
        full_prompt = base_prompt + context_info + domain_info + format_requirements + f"""

待编辑文字：
{content}

请直接输出整理后的Markdown格式文字，不要添加任何说明："""

        return full_prompt

    def _parse_editing_result(self, result: str, index: int, total: int) -> Dict:
        """解析编辑结果，提取标题和金句"""
        import re
        
        # 提取标题
        titles = []
        title_pattern = r'^(#{1,3})\s+(.+)$'
        for line in result.split('\n'):
            match = re.match(title_pattern, line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                titles.append({'level': level, 'title': title})
        
        # 提取金句（如果是最后一块或单独一块）
        golden_quotes = []
        if index == total or total == 1:
            # 查找金句部分
            golden_section_pattern = r'##\s*💎\s*精彩金句\s*\n(.*?)(?=\n##|\Z)'
            match = re.search(golden_section_pattern, result, re.DOTALL)
            if match:
                quotes_text = match.group(1)
                # 提取列表项
                quote_pattern = r'^\s*[-*]\s+(.+)$'
                for line in quotes_text.split('\n'):
                    quote_match = re.match(quote_pattern, line.strip())
                    if quote_match:
                        golden_quotes.append(quote_match.group(1).strip())
        
        return {
            'content': result,
            'titles': titles,
            'golden_quotes': golden_quotes
        }

    def edit_chunks_batch(self, chunk_info_list: List[Dict], domain_knowledge: str = "", 
                         keywords: str = "") -> List[Dict]:
        """
        批量编辑文本块
        
        Args:
            chunk_info_list: 文本块信息列表
            domain_knowledge: 领域知识
            keywords: 关键字
            
        Returns:
            编辑结果列表
        """
        results = []
        
        for chunk_info in chunk_info_list:
            try:
                result = self.edit_chunk(chunk_info, domain_knowledge, keywords)
                results.append(result)
            except Exception as e:
                logger.error(f"批量编辑中断，已完成 {len(results)} 个块")
                raise e
        
        logger.success(f"批量编辑完成，共处理 {len(results)} 个文本块")
        return results

    def extract_golden_quotes_from_text(self, text: str, domain_knowledge: str = "", 
                                      keywords: str = "") -> List[str]:
        """
        从文本中提取金句（独立功能）
        
        Args:
            text: 输入文本
            domain_knowledge: 领域知识
            keywords: 关键字
            
        Returns:
            金句列表
        """
        prompt = f"""请从以下文字中提取有深度、有启发性、有哲理或特别有意义的句子作为精彩金句。

要求：
1. 选择最有价值和启发性的句子
2. 每个金句应该相对独立，有完整的意思
3. 优先选择有哲理性、指导性或深刻见解的内容
4. 数量控制在3-8句之间
5. 按重要性排序

{f"领域知识：{domain_knowledge}" if domain_knowledge else ""}
{f"关键字：{keywords}" if keywords else ""}

文字内容：
{text}

请直接输出金句列表，每行一个，使用 "- " 开头："""

        logger.info("开始提取精彩金句")
        logger.info(f"金句提取提示词:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            result = response.choices[0].message.content.strip()
            
            # 解析金句
            quotes = []
            for line in result.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    quote = line[2:].strip()
                    if quote:
                        quotes.append(quote)
            
            logger.success(f"金句提取完成，共提取 {len(quotes)} 个金句")
            return quotes
            
        except Exception as e:
            error_msg = f"金句提取失败: {str(e)}"
            logger.error(error_msg)
            return []