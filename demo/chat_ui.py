import streamlit as st
import time
from service import GraphBuilderService

# ================= 1. 页面与全局 CSS 配置 =================
st.set_page_config(page_title="AIOps 智能诊断助手", layout="wide", page_icon="🕸️")

st.markdown("""
<style>
    .sidebar-title { font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #1f2937; }
    .sidebar-label { color: #9ca3af; font-size: 12px; margin-top: 25px; margin-bottom: 10px; padding-left: 5px; font-weight: 600; text-transform: uppercase; }
    [data-testid="stForm"] { border-radius: 16px !important; border: 1px solid #e5e7eb !important; background-color: #f9fafb !important; padding: 10px 15px 5px 15px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    .stTextInput > div > div > input { background-color: transparent !important; border: none !important; box-shadow: none !important; padding-left: 0 !important; font-size: 15px; }
    [data-testid="baseButton-formSubmit"] { border-radius: 50% !important; height: 40px !important; width: 40px !important; padding: 0 !important; background-color: #111827 !important; color: white !important; border: none !important; margin-top: 5px; }
    [data-testid="baseButton-formSubmit"]:hover { background-color: #374151 !important; }
    .chat-spacer { height: 100px; }
    .model-meta { font-size: 0.75rem; color: #6b7280; margin-top: -10px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ================= 2. 后端服务与状态管理 =================
@st.cache_resource
def get_service():
    return GraphBuilderService()

service = get_service()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好，我是 AIOps 智能诊断助手。\n\n请在下方输入框中**直接上传架构文档**或**故障日志（带 TraceID）**，即可一键构建 HugeGraph 知识图谱并分析根因。"}
    ]

# 【修复核心 1】使用一个干净的状态专门存文件，不再用复杂的拦截器
if "process_files" not in st.session_state:
    st.session_state.process_files = []

# ================= 3. 左侧边栏 =================
with st.sidebar:
    st.markdown("<div class='sidebar-title'>🕸️ AIOps Graph 平台</div>", unsafe_allow_html=True)
    if st.button("➕ 新建诊断会话", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.process_files = []
        st.rerun()
        
    st.markdown("<div class='sidebar-label'>系统连接状态</div>", unsafe_allow_html=True)
    st.info("🟢 本地大模型: 就绪\n\n🟢 HugeGraph: 127.0.0.1:8080")


# ================= 4. 主聊天区域渲染 =================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # 渲染大模型的 JSON 数据面板
        if msg.get("json_data"):
            with st.expander("🤖 查看大模型提取的原始 JSON 数据", expanded=False):
                st.json(msg["json_data"])
                
        # 渲染数据库的执行日志面板
        if msg.get("exec_logs"):
            with st.expander("🧠 HugeGraph 写入执行日志", expanded=False):
                for log in msg["exec_logs"]:
                    st.code(log, language="text")
                    
        # 渲染耗时角标
        if "meta" in msg:
            st.markdown(f"<div class='model-meta'>{msg['meta']}</div>", unsafe_allow_html=True)


# ================= 5. 助手处理逻辑 (完美修复无限循环) =================
# 如果历史记录最后一条是 user，说明助手该干活了
if st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1]["content"]
    files = st.session_state.process_files
    
    with st.chat_message("assistant"):
        start_time = time.time()
        response_msg = ""
        parsed_data = None
        exec_logs = None
        
        # 加载动画
        with st.spinner("大模型正在深度思考并构建图谱中..."):
            if files:
                file_name = files[0]["name"]
                file_content = files[0]["content"]
                
                try:
                    service.initialize_system()
                    is_architecture = "架构" in last_msg or "md" in file_name or "yaml" in file_name
                    
                    if is_architecture:
                        parsed_data, exec_logs = service.build_ontology_graph(file_content)
                        response_msg = f"✅ 已成功解析架构文档 **{file_name}** 并写入图数据库！请前往 Hubble 查看系统微服务拓扑图。"
                    else:
                        parsed_data, exec_logs = service.build_mechanism_graph(file_content)
                        response_msg = f"✅ 已成功提取日志 **{file_name}** 中的异常传播链路，并完成本体图谱的动态融合挂载。"
                        
                except Exception as e:
                    st.error(f"图谱处理失败: {str(e)}")
                    response_msg = f"抱歉，在调用大模型或写入图数据库时遇到错误：{str(e)}"
            else:
                response_msg = f"收到：**{last_msg}**。请确保您在下方输入框中上传了需要分析的架构文档或日志文件。"
        
        # 打字机效果输出
        message_placeholder = st.empty()
        full_response = ""
        for chunk in response_msg.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        
        elapsed_time = round(time.time() - start_time, 1)
        meta_info = f"AIOps Local LLM | 耗时: {elapsed_time}s"
        
        # 将助手回复、JSON、执行日志一起存入记录
        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "meta": meta_info,
            "json_data": parsed_data,
            "exec_logs": exec_logs
        })
        
    # 【修复核心 2】处理完必须清空文件，并刷新页面让折叠面板渲染出来
    st.session_state.process_files = []
    st.rerun()


# ================= 6. 底部一体化输入区 =================
st.markdown("<div class='chat-spacer'></div>", unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    uploaded_files = st.file_uploader("📎 添加附件", accept_multiple_files=True, label_visibility="collapsed")
    cols = st.columns([15, 1])
    with cols[0]:
        user_input = st.text_input("Message", placeholder="输入分析需求，或直接上传文件点击发送...", label_visibility="collapsed")
    with cols[1]:
        submitted = st.form_submit_button("⬆️", use_container_width=True)
        
    if submitted and (user_input.strip() or uploaded_files):
        # 1. 收集文件数据
        file_data = [{"name": f.name, "content": f.getvalue().decode("utf-8", errors="replace")} for f in uploaded_files]
        
        # 2. 构造用户界面的显示文本
        display_text = user_input.strip()
        if file_data and not display_text:
            display_text = f"请帮我分析上传的文件：**{', '.join([f['name'] for f in file_data])}**"
        elif file_data and display_text:
            display_text = f"{display_text}\n\n*(📎 附件: {', '.join([f['name'] for f in file_data])})*"
            
        # 3. 把用户的话记下来，把文件存入待处理状态
        st.session_state.messages.append({"role": "user", "content": display_text})
        st.session_state.process_files = file_data
        
        # 4. 触发页面重绘（从上到下执行，到达 Step 5 时就会触发大模型工作）
        st.rerun()