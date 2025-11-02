import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from llm_processor import LLMProcessor
from text_processor import TextProcessor

# 配置日志
logger.remove()  # 移除默认处理器
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)
# 添加控制台日志输出
logger.add(
    lambda msg: print(msg, end=""),
    format="{time:HH:mm:ss} | {level} | {message}",
    level="INFO",
    colorize=True
)

# 加载环境变量
load_dotenv()

# 配置缓存文件路径
CONFIG_CACHE_FILE = "config_cache.json"

def load_cached_config():
    """加载缓存的配置"""
    try:
        if os.path.exists(CONFIG_CACHE_FILE):
            with open(CONFIG_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"加载配置缓存失败: {e}")
    return {}

def save_config_cache(api_key, base_url, model):
    """保存配置到缓存"""
    try:
        config = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "last_updated": datetime.now().isoformat()
        }
        with open(CONFIG_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info("配置已保存到缓存")
    except Exception as e:
        logger.error(f"保存配置缓存失败: {e}")

def main():
    st.set_page_config(
        page_title="录音文字校对助手",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 录音文字校对助手")
    st.markdown("---")
    
    # 加载缓存的配置
    cached_config = load_cached_config()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ LLM配置")
        
        # 简化的LLM配置 - 只保留三个必要参数
        api_key = st.text_input(
            "API Key", 
            type="password", 
            value=cached_config.get("api_key", os.getenv("OPENAI_API_KEY", "")),
            help="输入你的LLM服务API密钥"
        )
        
        base_url = st.text_input(
            "Base URL", 
            value=cached_config.get("base_url", os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")),
            help="LLM服务的API基础URL"
        )
        
        model = st.text_input(
            "模型名称", 
            value=cached_config.get("model", "qwen-turbo"),
            placeholder="例如：qwen-turbo, gpt-3.5-turbo",
            help="输入要使用的模型名称"
        )
        
        # 保存配置按钮
        if st.button("💾 保存配置", help="保存当前配置以便下次使用"):
            if api_key and base_url and model:
                save_config_cache(api_key, base_url, model)
                st.success("配置已保存！")
            else:
                st.error("请填写完整的配置信息")
        
        # 显示上次保存时间
        if cached_config.get("last_updated"):
            st.caption(f"上次保存: {cached_config['last_updated'][:19].replace('T', ' ')}")
        
        st.markdown("---")
        
        # 处理参数
        st.subheader("处理参数")
        chunk_size = st.slider("分段大小（字符数）", 500, 3000, 1500)
        overlap_size = st.slider("重叠大小（字符数）", 50, 300, 100)
        

    
    # 输入区域（上半部分）
    st.header("📄 输入内容")
    
    # 添加处理模式选择
    st.subheader("🔧 处理模式")
    processing_mode = st.radio(
        "选择处理模式",
        ["完整校对模式", "直接编辑模式"],
        help="完整校对模式：先进行基础校对，再进行编辑整理\n直接编辑模式：跳过基础校对，直接对已校对文稿进行编辑整理"
    )
    
    # 根据模式显示不同的文件上传提示
    if processing_mode == "完整校对模式":
        st.info("📝 完整校对模式：适用于录音转文字的原始文稿，将进行基础校对和编辑整理两个步骤")
        uploaded_file = st.file_uploader("上传录音文字文件（原始文稿）", type=['txt'])
    else:
        st.info("✏️ 直接编辑模式：适用于已经完成基础校对的文稿，将直接进行编辑整理")
        uploaded_file = st.file_uploader("上传已校对文稿", type=['txt', 'md'])
    
    # 或者直接输入
    if processing_mode == "完整校对模式":
        text_input = st.text_area("或直接输入录音文字（原始文稿）", height=200)
    else:
        text_input = st.text_area("或直接输入已校对文稿", height=200)
    
    # 领域知识和关键字
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        domain_knowledge = st.text_area("领域知识", placeholder="例如：这是易经离卦的描述", height=100)
        if st.button("🔍 扩展领域知识", help="使用AI扩展和优化领域知识"):
            if domain_knowledge.strip() and api_key:
                with st.spinner("正在扩展领域知识..."):
                    try:
                        processor = LLMProcessor(api_key, base_url, model)
                        expanded_domain = processor.expand_domain_knowledge(domain_knowledge)
                        st.session_state.expanded_domain_knowledge = expanded_domain
                        st.success("领域知识扩展完成！")
                    except Exception as e:
                        st.error(f"扩展失败: {str(e)}")
            elif not domain_knowledge.strip():
                st.warning("请先输入领域知识")
            else:
                st.error("请先配置API Key")
        
        # 显示扩展后的领域知识
        if 'expanded_domain_knowledge' in st.session_state:
            st.text_area("扩展后的领域知识", value=st.session_state.expanded_domain_knowledge, height=150, disabled=True)
    
    with col_input2:
        keywords = st.text_area("关键字", placeholder="例如：离卦,坎卦,八卦", height=100)
        if st.button("🔍 扩展关键字", help="使用AI扩展和补全关键字"):
            if keywords.strip() and api_key:
                with st.spinner("正在扩展关键字..."):
                    try:
                        processor = LLMProcessor(api_key, base_url, model)
                        # 使用扩展后的领域知识（如果有的话）
                        reference_domain = st.session_state.get('expanded_domain_knowledge', domain_knowledge)
                        expanded_keywords = processor.expand_keywords(keywords, reference_domain)
                        st.session_state.expanded_keywords = expanded_keywords
                        st.success("关键字扩展完成！")
                    except Exception as e:
                        st.error(f"扩展失败: {str(e)}")
            elif not keywords.strip():
                st.warning("请先输入关键字")
            else:
                st.error("请先配置API Key")
        
        # 显示扩展后的关键字
        if 'expanded_keywords' in st.session_state:
            st.text_area("扩展后的关键字", value=st.session_state.expanded_keywords, height=150, disabled=True)
    
    # 处理按钮
    button_text = "开始校对" if processing_mode == "完整校对模式" else "开始编辑"
    if st.button(button_text, type="primary"):
        # 获取输入文本
        input_text = ""
        if uploaded_file is not None:
            input_text = uploaded_file.read().decode('utf-8')
            logger.info(f"上传文件，文本长度: {len(input_text)} 字符")
        elif text_input:
            input_text = text_input
            logger.info(f"直接输入文本，长度: {len(input_text)} 字符")
        
        if input_text and api_key:
            # 获取扩展后的领域知识和关键字（如果有的话）
            final_domain_knowledge = st.session_state.get('expanded_domain_knowledge', domain_knowledge)
            final_keywords = st.session_state.get('expanded_keywords', keywords)
            
            # 根据处理模式调用不同的函数
            if processing_mode == "完整校对模式":
                process_text(input_text, final_domain_knowledge, final_keywords, api_key, base_url, model, chunk_size, overlap_size)
            else:
                process_direct_edit(input_text, final_domain_knowledge, final_keywords, api_key, base_url, model)
        else:
            error_msg = "请提供文本内容和API Key" if processing_mode == "完整校对模式" else "请提供已校对文稿和API Key"
            st.error(error_msg)
            logger.error("缺少必要参数：文本内容或API Key")
    
    st.markdown("---")
    
    # 结果区域（下半部分）
    st.header("📋 处理结果")
    
    # 显示处理结果的标签页
    if 'basic_result' in st.session_state or 'edited_result' in st.session_state:
        tab1, tab2, tab3 = st.tabs(["基础校对版本", "编辑整理版本", "对比查看"])
        
        with tab1:
            if 'basic_result' in st.session_state:
                # 使用容器确保完整显示
                with st.container():
                    st.markdown("### 基础校对结果")
                    # 使用expander来处理长文本
                    with st.expander("查看完整内容", expanded=True):
                        st.markdown(st.session_state.basic_result, unsafe_allow_html=True)
                    
                    # 显示文本统计信息
                    st.info(f"文本长度: {len(st.session_state.basic_result)} 字符")
                    
                    st.download_button(
                        "下载基础校对版本",
                        st.session_state.basic_result,
                        "basic_proofread.md",
                        "text/markdown"
                    )
        
        with tab2:
            if 'edited_result' in st.session_state:
                # 使用容器确保完整显示
                with st.container():
                    st.markdown("### 编辑整理结果")
                    # 使用expander来处理长文本
                    with st.expander("查看完整内容", expanded=True):
                        st.markdown(st.session_state.edited_result, unsafe_allow_html=True)
                    
                    # 显示文本统计信息
                    st.info(f"文本长度: {len(st.session_state.edited_result)} 字符")
                    
                    st.download_button(
                        "下载编辑整理版本",
                        st.session_state.edited_result,
                        "edited_version.md",
                        "text/markdown"
                    )
        
        with tab3:
            if 'basic_result' in st.session_state and 'edited_result' in st.session_state:
                st.markdown("### 对比查看")
                col_basic, col_edited = st.columns(2)
                
                with col_basic:
                    st.subheader("基础校对版本")
                    with st.container():
                        # 限制高度并添加滚动
                        st.markdown(
                            f'<div style="height: 600px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 5px;">'
                            f'{st.session_state.basic_result}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        st.info(f"长度: {len(st.session_state.basic_result)} 字符")
                
                with col_edited:
                    st.subheader("编辑整理版本")
                    with st.container():
                        # 限制高度并添加滚动
                        st.markdown(
                            f'<div style="height: 600px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 5px;">'
                            f'{st.session_state.edited_result}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        st.info(f"长度: {len(st.session_state.edited_result)} 字符")
    else:
        st.info("请在上方输入录音文字并点击\"开始校对\"按钮")

def process_text(input_text, domain_knowledge, keywords, api_key, base_url, model, chunk_size, overlap_size):
    """处理文本的主要函数"""
    try:
        logger.info(f"开始处理文本，使用模型: {model}")
        logger.info(f"领域知识: {domain_knowledge}")
        logger.info(f"关键字: {keywords}")
        
        # 初始化处理器
        llm_processor = LLMProcessor(api_key, base_url, model)
        text_processor = TextProcessor(chunk_size, overlap_size)
        
        # 显示进度
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            progress_text = st.empty()
        
        # 第一步：基础校对
        status_text.text("正在进行基础校对...")
        logger.info("开始基础校对阶段")
        
        # 分段处理
        chunks = text_processor.split_text(input_text)
        total_chunks = len(chunks)
        logger.info(f"文本分为 {total_chunks} 个段落")
        
        basic_results = []
        
        for i, chunk in enumerate(chunks):
            current_progress = 25 + (i * 50 // total_chunks)
            progress_bar.progress(current_progress)
            progress_text.text(f"基础校对进度: {i+1}/{total_chunks}")
            
            logger.info(f"处理第 {i+1}/{total_chunks} 个段落")
            chunk_result = llm_processor.basic_proofread(chunk, domain_knowledge, keywords)
            basic_results.append(chunk_result)
        
        # 合并基础校对结果
        basic_result = text_processor.merge_results(basic_results)
        st.session_state.basic_result = basic_result
        
        # 保存基础校对结果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"logs/basic_proofread_{timestamp}.md", "w", encoding="utf-8") as f:
            f.write(basic_result)
        logger.info(f"基础校对结果已保存到: logs/basic_proofread_{timestamp}.md")
        
        # 第二步：编辑整理
        status_text.text("正在进行编辑整理...")
        progress_text.text("编辑整理进度: 1/1")
        progress_bar.progress(75)
        logger.info("开始编辑整理阶段")
        
        edited_result = llm_processor.edit_and_organize(basic_result, domain_knowledge, keywords)
        st.session_state.edited_result = edited_result
        
        # 保存编辑整理结果到文件
        with open(f"logs/edited_version_{timestamp}.md", "w", encoding="utf-8") as f:
            f.write(edited_result)
        logger.info(f"编辑整理结果已保存到: logs/edited_version_{timestamp}.md")
        
        progress_bar.progress(100)
        status_text.text("处理完成！")
        progress_text.text("所有任务已完成")
        
        st.success("文字校对完成！请查看下方结果。")
        logger.success("文字校对处理完成")
        
    except Exception as e:
        error_msg = f"处理过程中出现错误：{str(e)}"
        st.error(error_msg)
        logger.error(error_msg)

def process_direct_edit(input_text, domain_knowledge, keywords, api_key, base_url, model):
    """直接编辑处理函数，跳过基础校对步骤"""
    try:
        logger.info(f"开始直接编辑处理，使用模型: {model}")
        logger.info(f"领域知识: {domain_knowledge}")
        logger.info(f"关键字: {keywords}")
        
        # 初始化处理器
        llm_processor = LLMProcessor(api_key, base_url, model)
        
        # 显示进度
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            progress_text = st.empty()
        
        # 直接进行编辑整理
        status_text.text("正在进行编辑整理...")
        progress_text.text("编辑整理进度: 1/1")
        progress_bar.progress(50)
        logger.info("开始编辑整理阶段（直接编辑模式）")
        
        # 将输入文本作为基础校对结果保存（用于对比查看）
        st.session_state.basic_result = input_text
        
        # 直接调用编辑整理功能
        edited_result = llm_processor.edit_and_organize(input_text, domain_knowledge, keywords)
        st.session_state.edited_result = edited_result
        
        # 保存结果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"logs/direct_edit_{timestamp}.md", "w", encoding="utf-8") as f:
            f.write(edited_result)
        logger.info(f"直接编辑结果已保存到: logs/direct_edit_{timestamp}.md")
        
        progress_bar.progress(100)
        status_text.text("编辑完成！")
        progress_text.text("所有任务已完成")
        
        st.success("文稿编辑完成！请查看下方结果。")
        logger.success("直接编辑处理完成")
        
    except Exception as e:
        error_msg = f"编辑过程中出现错误：{str(e)}"
        st.error(error_msg)
        logger.error(error_msg)

if __name__ == "__main__":
    # 确保logs目录存在
    os.makedirs("logs", exist_ok=True)
    main()