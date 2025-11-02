# 📝 录音文字校对助手

这是一个基于Streamlit的应用，用于课堂录音文字的智能校对和整理。

## ✨ 功能特点

- 🤖 **双角色LLM处理**：基础校对员 + 编辑整理员
- 📄 **多种输入方式**：支持文件上传或直接文本输入
- 🔧 **灵活配置**：可配置LLM模型、API密钥等参数
- 📊 **对比查看**：同时显示基础校对版本和编辑整理版本
- 💾 **结果导出**：支持Markdown格式下载

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Poetry（推荐）或 pip

### 安装依赖

#### 使用 Poetry（推荐）

```bash
# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

#### 使用 pip

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的API密钥：
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 启动应用

#### 方式一：使用启动脚本
```bash
python run.py
```

#### 方式二：直接使用Streamlit
```bash
streamlit run app.py
```

应用将在 http://localhost:8501 启动。

## 📖 使用方法

1. **配置LLM**：在侧边栏设置API Key、模型等参数
2. **输入文本**：上传录音文字文件或直接输入文本
3. **提供上下文**：
   - 领域知识：如"这是易经离卦的描述"
   - 关键字：如"离卦,坎卦,八卦"
4. **开始处理**：点击"开始校对"按钮
5. **查看结果**：在右侧查看基础校对版本和编辑整理版本

## 🔧 处理流程

### 基础校对员
- 去除录音中口语化的内容（如"嗯"、"啊"、"那个"等）
- 修正录音中的同音错别字或词语错误
- 使句子通顺、易读
- 保持原文的核心意思和结构

### 编辑整理员
- 合理进行段落拆分
- 为每个段落添加合适的标题
- 优化文本结构，使其更加清晰易读
- 输出Markdown格式

## 📁 项目结构

```
preproof/
├── app.py              # 主应用文件
├── llm_processor.py    # LLM处理器（双角色）
├── text_processor.py   # 文本分段处理器
├── pyproject.toml      # Poetry配置文件
├── requirements.txt    # pip依赖文件
├── run.py             # 启动脚本
├── .env.example       # 环境变量示例
├── .gitignore         # Git忽略文件
└── README.md          # 项目说明
```

## ⚙️ 技术特点

- **智能分段**：自动处理长文本，支持重叠分段避免信息丢失
- **错误处理**：完善的异常处理和用户提示
- **进度显示**：实时显示处理进度
- **响应式UI**：现代化的用户界面设计

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License