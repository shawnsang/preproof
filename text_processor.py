import re
from typing import List
from loguru import logger


class TextProcessor:
    """文本处理器，负责文本分割和结果合并"""
    
    def __init__(self, chunk_size: int = 1500, overlap_size: int = 100):
        """
        初始化文本处理器
        
        Args:
            chunk_size: 每个文本块的最大字符数
            overlap_size: 文本块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        logger.info(f"初始化文本处理器，分段大小: {chunk_size}, 重叠大小: {overlap_size}")

    def split_text(self, text: str) -> List[str]:
        """
        将文本分割成多个块，用于基础校对阶段
        
        Args:
            text: 要分割的文本
            
        Returns:
            分割后的文本块列表
        """
        if not text or len(text.strip()) == 0:
            logger.warning("输入文本为空")
            return []
        
        if len(text) <= self.chunk_size:
            logger.info(f"文本长度 {len(text)} 小于分段大小，无需分割")
            return [text]
        
        # 清理文本
        text = self._clean_text(text)
        
        # 按段落分割
        paragraphs = self._split_by_paragraphs(text)
        logger.info(f"文本包含 {len(paragraphs)} 个段落")
        
        # 组合段落成块
        chunks = self._combine_paragraphs_to_chunks(paragraphs)
        
        logger.info(f"文本分割完成，共 {len(chunks)} 个块")
        return chunks

    def merge_results(self, results: List[str]) -> str:
        """
        合并多个处理结果
        
        Args:
            results: 处理结果列表
            
        Returns:
            合并后的文本
        """
        if not results:
            logger.warning("没有结果需要合并")
            return ""
        
        if len(results) == 1:
            logger.info("只有一个结果，直接返回")
            return results[0]
        
        logger.info(f"开始合并 {len(results)} 个结果")
        
        # 合并结果，处理重叠部分
        merged_parts = []
        for i, result in enumerate(results):
            result = result.strip()
            
            if i == 0:
                # 第一块直接添加
                merged_parts.append(result)
            else:
                # 后续块需要处理重叠
                processed_result = self._process_overlap(result, merged_parts[-1])
                merged_parts.append(processed_result)
        
        # 用双换行连接各部分
        merged_text = '\n\n'.join(merged_parts)
        
        # 清理多余的空行
        merged_text = re.sub(r'\n{3,}', '\n\n', merged_text)
        
        logger.success(f"合并完成，最终文本长度: {len(merged_text)} 字符")
        return merged_text.strip()

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # 如果段落过长，进一步分割
        final_paragraphs = []
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                final_paragraphs.append(para)
            else:
                # 按句子分割长段落
                sentences = self._split_long_paragraph(para)
                final_paragraphs.extend(sentences)
        
        return final_paragraphs

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割过长的段落"""
        sentence_endings = ['。', '！', '？', '.', '!', '?']
        sentences = []
        current = ""
        
        for char in paragraph:
            current += char
            if char in sentence_endings and len(current) > 100:
                sentences.append(current.strip())
                current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        return sentences

    def _combine_paragraphs_to_chunks(self, paragraphs: List[str]) -> List[str]:
        """将段落组合成合适大小的块"""
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # 检查添加当前段落是否会超出大小限制
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 当前块已满，保存并开始新块
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 处理重叠
                if chunks and self.overlap_size > 0:
                    overlap_text = self._get_overlap_text(current_chunk, self.overlap_size)
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """获取文本末尾的重叠部分"""
        if len(text) <= overlap_size:
            return text
        
        # 尝试在句子边界获取重叠
        overlap_text = text[-overlap_size:]
        sentence_endings = ['。', '！', '？', '.', '!', '?']
        
        # 寻找最近的句子结束点
        for i, char in enumerate(overlap_text):
            if char in sentence_endings:
                return overlap_text[i+1:].strip()
        
        return overlap_text

    def _process_overlap(self, current_result: str, previous_result: str) -> str:
        """处理重叠部分，避免重复内容"""
        if not previous_result or not current_result:
            return current_result
        
        # 获取前一个结果的最后部分用于检测重复
        prev_tail = previous_result[-min(200, len(previous_result)):].lower()
        current_lines = current_result.split('\n')
        processed_lines = []
        
        # 检查前几行是否与前一个结果重复
        skip_count = 0
        for i, line in enumerate(current_lines[:5]):  # 只检查前5行
            line_stripped = line.strip()
            if line_stripped and line_stripped.lower() in prev_tail:
                skip_count = i + 1
            else:
                break
        
        # 跳过重复的行
        if skip_count > 0:
            processed_lines = current_lines[skip_count:]
            logger.debug(f"跳过了 {skip_count} 行重复内容")
        else:
            processed_lines = current_lines
        
        return '\n'.join(processed_lines).strip()

    def _clean_text(self, text: str) -> str:
        """清理文本，标准化空白字符"""
        # 标准化换行符
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        
        # 清理多余的空白，但保留段落分隔
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格/制表符 -> 单个空格
        text = re.sub(r'\n[ \t]+', '\n', text)  # 行首空白
        text = re.sub(r'[ \t]+\n', '\n', text)  # 行尾空白
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行 -> 双换行
        
        return text.strip()

