import openai
from loguru import logger
from chunking_processor import ChunkingProcessor
from editing_processor import EditingProcessor
from merging_processor import MergingProcessor

class LLMProcessor:
    def __init__(self, api_key, base_url, model):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        logger.info(f"初始化LLM处理器，模型: {model}, Base URL: {base_url}")
        
        # 初始化分块编辑相关处理器
        self.chunking_processor = ChunkingProcessor()
        self.editing_processor = EditingProcessor(api_key, base_url, model)
        self.merging_processor = MergingProcessor()
    
    def basic_proofread(self, text, domain_knowledge="", keywords=""):
        """基础校对：去除口语化表达，纠正错别字，提高可读性"""
        
        prompt = f"""请对以下录音转文字的内容进行基础校对，要求：
1. 去除口语化表达（如"那个"、"这个"、"嗯"、"啊"等）
2. 纠正错别字和语法错误
3. 保持原意不变，提高文字的可读性
4. 保持原有的段落结构

{f"领域知识：{domain_knowledge}" if domain_knowledge else ""}
{f"关键字：{keywords}" if keywords else ""}

原文：
{text}

请直接输出校对后的文字，不要添加任何说明："""

        logger.info("发送基础校对请求到LLM")
        logger.info(f"完整提示词:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            logger.success(f"基础校对完成，输出长度: {len(result)} 字符")
            logger.debug(f"基础校对结果预览: {result[:100]}...")
            
            return result
            
        except Exception as e:
            error_msg = f"基础校对请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def edit_and_organize(self, text, domain_knowledge="", keywords=""):
        """编辑整理：使用分块策略处理长文本"""
        
        logger.info(f"开始编辑整理，文本长度: {len(text)} 字符")
        
        # 检查是否需要分块处理
        if not self.chunking_processor.should_use_chunking(text):
            logger.info("文本较短，使用单块处理")
            # 直接使用编辑处理器处理单个块
            chunk_info = {
                'content': text,
                'index': 1,
                'total': 1,
                'context': {'is_single': True}
            }
            
            result = self.editing_processor.edit_chunk(chunk_info, domain_knowledge, keywords)
            return result['content']
        
        logger.info("文本较长，使用分块处理")
        
        # 分块处理
        chunks_info = self.chunking_processor.split_for_editing(text)
        logger.info(f"文本分为 {len(chunks_info)} 个块进行处理")
        
        # 批量编辑各个块
        edited_results = self.editing_processor.edit_chunks_batch(
            chunks_info, domain_knowledge, keywords
        )
        
        # 合并编辑结果
        merged_result = self.merging_processor.merge_edited_chunks(edited_results)
        
        # 创建处理摘要
        summary = self.merging_processor.create_content_summary(merged_result)
        logger.info(f"编辑整理完成\n{summary}")
        
        return merged_result['content']
    
    def expand_domain_knowledge(self, domain_knowledge):
        """扩展和优化领域知识"""
        if not domain_knowledge.strip():
            return ""
            
        prompt = f"""请对以下领域知识进行简洁扩展，要求：
1. 补充2-3个核心专业术语
2. 用一句话概括背景信息
3. 总共不超过三句话

原始领域知识：
{domain_knowledge}

请输出扩展后的领域知识（不超过三句话）："""

        logger.info("发送领域知识扩展请求到LLM")
        logger.info(f"完整提示词:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            result = response.choices[0].message.content.strip()
            logger.success(f"领域知识扩展完成，输出长度: {len(result)} 字符")
            logger.debug(f"扩展后的领域知识预览: {result[:100]}...")
            
            return result
            
        except Exception as e:
            error_msg = f"领域知识扩展请求失败: {str(e)}"
            logger.error(error_msg)
            return domain_knowledge  # 失败时返回原始内容
    
    def expand_keywords(self, keywords, domain_knowledge=""):
        """扩展和补全关键字"""
        if not keywords.strip():
            return ""
            
        prompt = f"""请对以下关键字进行横向扩展，基于领域知识补充相关的准确关键字，要求：
1. 根据领域知识，补充相关的专业术语和概念
2. 扩展同类别、同层次的关键字
3. 只输出准确、清楚的关键字，便于后续校对参考
4. 用逗号分隔，按类别分组
5. 不要包含错别字或近音字

{f"参考领域知识：{domain_knowledge}" if domain_knowledge else ""}

原始关键字：
{keywords}

请输出扩展后的准确关键字（只要关键字，不要解释）："""

        logger.info("发送关键字扩展请求到LLM")
        logger.info(f"完整提示词:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            result = response.choices[0].message.content.strip()
            logger.success(f"关键字扩展完成，输出长度: {len(result)} 字符")
            logger.debug(f"扩展后的关键字预览: {result[:100]}...")
            
            return result
            
        except Exception as e:
            error_msg = f"关键字扩展请求失败: {str(e)}"
            logger.error(error_msg)
            return keywords  # 失败时返回原始内容

    def extract_golden_quotes(self, text, domain_knowledge="", keywords=""):
        """单独提取金句功能：支持长文分块提取并汇总去重"""

        logger.info(f"开始提取金句，文本长度: {len(text)} 字符")

        try:
            # 如果文本较短，直接提取
            if not self.chunking_processor.should_use_chunking(text):
                quotes = self.editing_processor.extract_golden_quotes_from_text(
                    text, domain_knowledge, keywords
                )
                logger.success(f"金句提取完成（单块），共 {len(quotes)} 条")
                return "\n".join([f"- {q}" for q in quotes])

            # 文本较长，按编辑分块策略拆分并逐块提取
            logger.info("文本较长，采用分块提取金句并汇总")
            chunk_info_list = self.chunking_processor.split_for_editing(text)
            all_quotes = []

            for chunk in chunk_info_list:
                idx = chunk.get('index')
                total = chunk.get('total')
                logger.info(f"提取第 {idx}/{total} 块的金句")
                quotes = self.editing_processor.extract_golden_quotes_from_text(
                    chunk['content'], domain_knowledge, keywords
                )
                logger.info(f"第 {idx}/{total} 块提取 {len(quotes)} 条金句")
                all_quotes.extend(quotes)

            # 去重与整理
            unique_quotes = self.merging_processor._deduplicate_quotes(all_quotes)
            logger.success(f"分块金句汇总完成，共 {len(unique_quotes)} 条（去重后）")

            return "\n".join([f"- {q}" for q in unique_quotes])

        except Exception as e:
            error_msg = f"金句提取请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def process_full_text(self, text, domain_knowledge="", keywords=""):
        """完整处理流程：基础校对 + 编辑整理（包含金句提取）"""
        logger.info("开始完整文本处理流程")
        
        # 第一步：基础校对
        basic_result = self.basic_proofread(text, domain_knowledge, keywords)
        
        # 第二步：编辑整理（已包含金句提取）
        final_result = self.edit_and_organize(basic_result, domain_knowledge, keywords)
        
        logger.success("完整文本处理流程完成")
        return basic_result, final_result