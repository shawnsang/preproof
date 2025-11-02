import re
from typing import List, Dict, Tuple
from loguru import logger


class ChunkingProcessor:
    """编辑阶段的智能分块处理器"""
    
    def __init__(self, chunk_size: int = 2000, overlap_size: int = 200):
        """
        初始化分块处理器
        
        Args:
            chunk_size: 每个文本块的最大字符数（编辑阶段使用更大的块）
            overlap_size: 文本块之间的重叠字符数（编辑阶段使用更大的重叠）
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        logger.info(f"初始化编辑分块处理器，分段大小: {chunk_size}, 重叠大小: {overlap_size}")

    def split_for_editing(self, text: str) -> List[Dict]:
        """
        为编辑整理阶段分割文本，保持段落完整性
        
        Args:
            text: 要分割的已校对文本
            
        Returns:
            分割后的文本块信息列表，每个元素包含：
            - content: 文本内容
            - index: 块索引
            - total: 总块数
            - context: 上下文信息
        """
        if len(text) <= self.chunk_size:
            logger.info(f"文本长度 {len(text)} 小于分段大小，无需分割")
            return [{
                'content': text,
                'index': 1,
                'total': 1,
                'context': {'is_single': True}
            }]
        
        # 首先按段落分割
        paragraphs = self._split_by_paragraphs(text)
        logger.info(f"文本包含 {len(paragraphs)} 个段落")
        
        # 组合段落成块
        chunks = self._combine_paragraphs_to_chunks(paragraphs)
        
        # 添加上下文信息
        chunk_info_list = []
        for i, chunk in enumerate(chunks):
            chunk_info = {
                'content': chunk,
                'index': i + 1,
                'total': len(chunks),
                'context': self._generate_context(chunks, i)
            }
            chunk_info_list.append(chunk_info)
        
        logger.info(f"编辑分块完成，共 {len(chunks)} 个块")
        return chunk_info_list

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 清理文本
        text = self._clean_text(text)
        
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # 如果段落过长，进一步分割
        final_paragraphs = []
        for para in paragraphs:
            if len(para) <= self.chunk_size // 2:
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

    def _generate_context(self, chunks: List[str], current_index: int) -> Dict:
        """为当前块生成上下文信息"""
        context = {
            'is_first': current_index == 0,
            'is_last': current_index == len(chunks) - 1,
            'previous_summary': None,
            'next_preview': None
        }
        
        # 添加前一块的摘要
        if current_index > 0:
            prev_chunk = chunks[current_index - 1]
            context['previous_summary'] = self._extract_summary(prev_chunk)
        
        # 添加下一块的预览
        if current_index < len(chunks) - 1:
            next_chunk = chunks[current_index + 1]
            context['next_preview'] = self._extract_preview(next_chunk)
        
        return context

    def _extract_summary(self, text: str) -> str:
        """提取文本的简要摘要（最后几句话）"""
        sentences = re.split(r'[。！？.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 2:
            return text[:100] + "..." if len(text) > 100 else text
        
        # 返回最后两句话
        return "...".join(sentences[-2:]) + "。"

    def _extract_preview(self, text: str) -> str:
        """提取文本的预览（前几句话）"""
        sentences = re.split(r'[。！？.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 2:
            return text[:100] + "..." if len(text) > 100 else text
        
        # 返回前两句话
        return "。".join(sentences[:2]) + "。"

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

    def should_use_chunking(self, text: str, threshold: int = 3000) -> bool:
        """
        判断是否需要使用分块处理
        
        Args:
            text: 输入文本
            threshold: 长度阈值
            
        Returns:
            是否需要分块处理
        """
        return len(text) > threshold