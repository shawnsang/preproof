import re
from typing import List, Dict, Tuple
from loguru import logger


class MergingProcessor:
    """智能合并处理器，负责合并编辑后的文本块"""
    
    def __init__(self):
        """初始化合并处理器"""
        logger.info("初始化智能合并处理器")

    def merge_edited_chunks(self, edited_results: List[Dict]) -> Dict:
        """
        合并编辑后的文本块
        
        Args:
            edited_results: 编辑结果列表，每个元素包含content、titles、golden_quotes等
            
        Returns:
            合并结果字典，包含最终内容、标题结构、金句等
        """
        if not edited_results:
            logger.warning("没有编辑结果需要合并")
            return {'content': '', 'titles': [], 'golden_quotes': []}
        
        if len(edited_results) == 1:
            logger.info("只有一个文本块，直接返回")
            return {
                'content': edited_results[0]['content'],
                'titles': edited_results[0]['titles'],
                'golden_quotes': edited_results[0]['golden_quotes']
            }
        
        logger.info(f"开始合并 {len(edited_results)} 个编辑结果")
        
        # 合并内容
        merged_content = self._merge_content(edited_results)
        
        # 合并标题结构
        merged_titles = self._merge_titles(edited_results)
        
        # 合并金句
        merged_golden_quotes = self._merge_golden_quotes(edited_results)
        
        # 优化合并后的内容
        optimized_content = self._optimize_merged_content(merged_content, merged_golden_quotes)
        
        result = {
            'content': optimized_content,
            'titles': merged_titles,
            'golden_quotes': merged_golden_quotes
        }
        
        logger.success(f"合并完成，最终内容长度: {len(optimized_content)} 字符")
        return result

    def _merge_content(self, edited_results: List[Dict]) -> str:
        """合并文本内容"""
        merged_parts = []
        
        for i, result in enumerate(edited_results):
            content = result['content'].strip()
            
            if i == 0:
                # 第一块直接添加
                merged_parts.append(content)
            else:
                # 后续块需要处理重复标题和连接
                processed_content = self._process_subsequent_chunk(content, merged_parts[-1])
                merged_parts.append(processed_content)
        
        # 用双换行连接各部分
        merged_content = '\n\n'.join(merged_parts)
        
        # 清理多余的空行
        merged_content = re.sub(r'\n{3,}', '\n\n', merged_content)
        
        return merged_content.strip()

    def _process_subsequent_chunk(self, content: str, previous_content: str) -> str:
        """处理后续文本块，避免重复标题"""
        lines = content.split('\n')
        processed_lines = []
        
        # 获取前一块的最后几行，用于检测重复
        prev_lines = previous_content.split('\n')[-3:]
        prev_text = '\n'.join(prev_lines).lower()
        
        skip_lines = 0
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 跳过开头的空行
            if not line_stripped and not processed_lines:
                continue
            
            # 检测是否是重复的标题或内容
            if i < 3 and line_stripped:  # 只检查前3行
                if self._is_duplicate_line(line_stripped, prev_text):
                    skip_lines = i + 1
                    continue
            
            # 如果已经确定要跳过的行数，继续跳过
            if i < skip_lines:
                continue
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines).strip()

    def _is_duplicate_line(self, line: str, previous_text: str) -> bool:
        """检测是否是重复的行"""
        line_lower = line.lower().strip()
        
        # 忽略标题标记
        line_clean = re.sub(r'^#+\s*', '', line_lower)
        
        # 如果行太短，不认为是重复
        if len(line_clean) < 5:
            return False
        
        # 检查是否在前面的内容中出现过
        return line_clean in previous_text

    def _merge_titles(self, edited_results: List[Dict]) -> List[Dict]:
        """合并标题结构"""
        all_titles = []
        
        for result in edited_results:
            titles = result.get('titles', [])
            all_titles.extend(titles)
        
        # 去重相似标题
        unique_titles = self._deduplicate_titles(all_titles)
        
        logger.info(f"标题合并完成，共 {len(unique_titles)} 个标题")
        return unique_titles

    def _deduplicate_titles(self, titles: List[Dict]) -> List[Dict]:
        """去重相似标题"""
        if not titles:
            return []
        
        unique_titles = []
        seen_titles = set()
        
        for title_info in titles:
            title = title_info['title'].strip()
            title_clean = re.sub(r'[^\w\u4e00-\u9fff]', '', title.lower())
            
            # 检查是否已经存在相似标题
            is_duplicate = False
            for seen in seen_titles:
                if self._titles_similar(title_clean, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_titles.append(title_info)
                seen_titles.add(title_clean)
        
        return unique_titles

    def _titles_similar(self, title1: str, title2: str) -> bool:
        """判断两个标题是否相似"""
        if not title1 or not title2:
            return False
        
        # 完全相同
        if title1 == title2:
            return True
        
        # 一个包含另一个，且长度差不大
        if len(title1) > 0 and len(title2) > 0:
            longer = title1 if len(title1) > len(title2) else title2
            shorter = title2 if len(title1) > len(title2) else title1
            
            if shorter in longer and len(longer) - len(shorter) <= 3:
                return True
        
        return False

    def _merge_golden_quotes(self, edited_results: List[Dict]) -> List[str]:
        """合并金句"""
        all_quotes = []
        
        for result in edited_results:
            quotes = result.get('golden_quotes', [])
            all_quotes.extend(quotes)
        
        # 去重相似金句
        unique_quotes = self._deduplicate_quotes(all_quotes)
        
        logger.info(f"金句合并完成，共 {len(unique_quotes)} 个金句")
        return unique_quotes

    def _deduplicate_quotes(self, quotes: List[str]) -> List[str]:
        """去重相似金句"""
        if not quotes:
            return []
        
        unique_quotes = []
        
        for quote in quotes:
            quote = quote.strip()
            if not quote:
                continue
            
            # 检查是否已经存在相似金句
            is_duplicate = False
            for existing in unique_quotes:
                if self._quotes_similar(quote, existing):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_quotes.append(quote)
        
        return unique_quotes

    def _quotes_similar(self, quote1: str, quote2: str) -> bool:
        """判断两个金句是否相似"""
        if not quote1 or not quote2:
            return False
        
        # 去除标点符号进行比较
        clean1 = re.sub(r'[^\w\u4e00-\u9fff]', '', quote1)
        clean2 = re.sub(r'[^\w\u4e00-\u9fff]', '', quote2)
        
        # 完全相同
        if clean1 == clean2:
            return True
        
        # 一个包含另一个，且长度差不大
        if len(clean1) > 10 and len(clean2) > 10:
            longer = clean1 if len(clean1) > len(clean2) else clean2
            shorter = clean2 if len(clean1) > len(clean2) else clean1
            
            if shorter in longer and len(longer) - len(shorter) <= 5:
                return True
        
        return False

    def _optimize_merged_content(self, content: str, golden_quotes: List[str]) -> str:
        """优化合并后的内容"""
        # 确保金句部分在最后
        if golden_quotes:
            # 移除现有的金句部分
            content = re.sub(r'##\s*💎\s*精彩金句.*?(?=\n##|\Z)', '', content, flags=re.DOTALL)
            
            # 在最后添加金句部分
            quotes_section = "\n\n## 💎 精彩金句\n"
            for quote in golden_quotes:
                quotes_section += f"- {quote}\n"
            
            content = content.rstrip() + quotes_section
        
        # 清理多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 确保标题前后有适当的空行
        content = re.sub(r'\n(#{1,3}\s)', r'\n\n\1', content)
        content = re.sub(r'(#{1,3}\s[^\n]+)\n([^\n#])', r'\1\n\n\2', content)
        
        return content.strip()

    def create_content_summary(self, merged_result: Dict) -> str:
        """创建内容摘要"""
        content = merged_result['content']
        titles = merged_result['titles']
        golden_quotes = merged_result['golden_quotes']
        
        summary_parts = []
        
        # 统计信息
        word_count = len(content)
        title_count = len(titles)
        quote_count = len(golden_quotes)
        
        summary_parts.append(f"📊 内容统计：{word_count} 字符，{title_count} 个标题，{quote_count} 个金句")
        
        # 标题结构
        if titles:
            summary_parts.append("\n📋 内容结构：")
            for title_info in titles[:10]:  # 最多显示10个标题
                level = title_info['level']
                title = title_info['title']
                indent = "  " * (level - 1)
                summary_parts.append(f"{indent}- {title}")
            
            if len(titles) > 10:
                summary_parts.append(f"  ... 还有 {len(titles) - 10} 个标题")
        
        # 精彩金句预览
        if golden_quotes:
            summary_parts.append("\n💎 精彩金句预览：")
            for quote in golden_quotes[:3]:  # 最多显示3个金句
                summary_parts.append(f"- {quote}")
            
            if len(golden_quotes) > 3:
                summary_parts.append(f"- ... 还有 {len(golden_quotes) - 3} 个金句")
        
        return '\n'.join(summary_parts)