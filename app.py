import streamlit as st
from zhipuai import ZhipuAI
import os
from PyPDF2 import PdfReader
from docx import Document

# ================= 配置区域 =================
API_KEY = os.getenv("ZHIPU_API_KEY", "")
if not API_KEY:
    API_KEY = "27b59c17f1c841dab8dc19cb6684192f.ULMYHrhpUSYQ1ZM6"  # 仅本地测试用，不要上传到公开仓库
client = ZhipuAI(api_key=API_KEY)

# ================= 页面配置 =================
st.set_page_config(page_title="AI信息筛选助手", page_icon="🤖", layout="centered")

st.markdown(
    """
<style>
          .stApp { background-color: #FAF7F2; }
          .big-title { font-size: 2.4rem; font-weight: 800; color: #1A3A6B; text-align: center; margin-bottom: 0.2rem; }
          .sub-title { font-size: 1rem; color: #6B7A8F; text-align: center; margin-bottom: 1.8rem; }
          .stButton>button { width: 100%; border-radius: 12px; font-weight: 600; border: none; transition: all 0.25s ease; }
          .stButton>button[kind="primary"] { background: linear-gradient(135deg, #1A3A6B, #2E5A9C); color: #FFFFFF; }
          .stButton>button[kind="primary"]:hover { background: linear-gradient(135deg, #F5A623, #F7B84B); color: #1A3A6B; transform: translateY(-2px); box-shadow: 0 8px 18px rgba(245, 166, 35, 0.35); }
          .stButton>button[kind="secondary"] { background-color: #FFFFFF; color: #1A3A6B; border: 1.5px solid #D6E2F2; }
          .stButton>button[kind="secondary"]:hover { background-color: #FFF6E8; border-color: #F5A623; color: #C87A00; }
          .reminder-card { background-color: #FFF9EC; padding: 1rem 1.2rem; border-radius: 12px; border-left: 5px solid #F5A623; margin-bottom: 0.8rem; }

          /* 强制所有文本用深色，解决白字看不见的问题 */
          .stApp, .stApp p, .stApp span, .stApp div, .stApp h1, .stApp h2, .stApp h3 {
                    color: #1A3A6B !important;
          }
          .stExpander {
                    background-color: #FFFFFF !important;
                    border-radius: 12px !important;
          }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="big-title">🤖 AI信息筛选助手</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">告别信息过载，一键筛出与你有关的事</div>',
    unsafe_allow_html=True,
)

# ================= session_state 初始化 =================
if "page" not in st.session_state:
    st.session_state.page = "filter"
if "identity_text" not in st.session_state:
    st.session_state.identity_text = ""
if "filter_result" not in st.session_state:
    st.session_state.filter_result = ""
if "reminders" not in st.session_state:
    st.session_state.reminders = []

# ================= 导航栏 =================
nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("📋 信息筛选", use_container_width=True):
        st.session_state.page = "filter"
with nav2:
    if st.button("🔔 信息提醒", use_container_width=True):
        st.session_state.page = "remind"
with nav3:
    if st.button("📤 导出与分享", use_container_width=True):
        st.session_state.page = "export"

st.markdown("---")


# ================= 文件解析函数 =================
def read_upload_file(file):
    text = ""
    suffix = file.name.split(".")[-1].lower()
    if suffix == "txt":
        text = file.read().decode("utf-8", errors="ignore")
    elif suffix == "pdf":
        reader = PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    elif suffix == "docx":
        doc = Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text[:3000]


# ================= 页面1：信息筛选 =================
if st.session_state.page == "filter":
    st.markdown("### 📝 填写你的信息")

    st.markdown("**快捷标签（点一下添加到输入框）：**")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("大一"):
            st.session_state.identity_text += "大一，"
    with col2:
        if st.button("大二"):
            st.session_state.identity_text += "大二，"
    with col3:
        if st.button("计算机专业"):
            st.session_state.identity_text += "计算机专业，"
    with col4:
        if st.button("想参加竞赛"):
            st.session_state.identity_text += "想参加竞赛，"
    with col5:
        if st.button("关注奖学金"):
            st.session_state.identity_text += "关注奖学金，"
    with col6:
        if st.button("清空标签"):
            st.session_state.identity_text = ""

    identity = st.text_input(
        "1. 你的身份标签",
        value=st.session_state.identity_text,
        placeholder="例如：大一，计算机专业，对AI感兴趣",
    )

    content = st.text_area(
        "2. 粘贴通知/消息内容",
        height=150,
        placeholder="把学校群、班级群、公众号里的通知复制到这里...",
    )

    uploaded_files = st.file_uploader(
        "3. 或上传文件（支持 .txt / .pdf / .docx，可多选）",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
    )

    if st.button("🔍 开始筛选", use_container_width=True, type="primary"):
        final_content = content
        if uploaded_files:
            for f in uploaded_files:
                file_text = read_upload_file(f)
                final_content += f"\n\n【文件：{f.name}】\n{file_text}"

        if not identity or not final_content.strip():
            st.warning("⚠️ 请填写身份，并粘贴文字或上传文件！")
        else:
            with st.spinner("AI正在努力筛选中，请稍候..."):
                try:
                    prompt = f"""
你是一个专业的信息筛选助手。用户的身份是：{identity}。
以下是用户收到的通知内容：
---
{final_content}
---

请根据用户身份，筛选出所有与之相关、可以参与的通知，并过滤掉不相关的。

【匹配原则】
用户的身份标签可能包含多个（如：大一、计算机专业、想参加竞赛）。
只要某条通知满足以下条件之一，就应被筛选为“适合的通知”：
1. 通知的参与对象覆盖了用户身份标签中的任意一个；
2. 通知的内容与用户身份标签中的任意一个相关；
3. 通知面向“全校师生”或“全体学生”的，无论用户是大几、什么专业，都应该保留。
         （例如：图书馆开放通知、体测安排、消防演练、运动会报名、食堂菜单更新、校园交通管制、停水停电通知等）
4. 通知涉及学生的基本校园生活、安全、学业或公共设施使用的，也应保留。
         （例如：宿舍管理通知、选课通知、考试安排、校园卡办理、医疗报销、心理健康讲座等）
5. 通知涉及全校性集体活动、志愿服务、社团招新等，即使与专业无关，也建议保留。
6. 只有当通知**明确排除**用户身份，或**完全无关**时，才过滤掉。

【输出格式要求】
你必须严格按照以下格式输出，每条通知必须包含标题：

✅ 适合你的通知
1. 标题：xxx
         - 报名截止：xxx
         - 关键提醒：xxx

❌ 已被过滤
1. 标题：xxx
         - 过滤原因：xxx

注意：
1. 每一条通知都必须有一个明确的标题。如果原文没有标题，请根据内容帮你总结一个简短的标题。
2. 不要用“通知1、通知2”来代替标题，必须写出具体内容。
3. 如果没有任何相关通知，就写“未发现与您身份相关的通知”。
"""

                    response = client.chat.completions.create(
                        model="glm-4-flash",
                        messages=[{"role": "user", "content": prompt}],
                        timeout=30,
                    )
                    result = response.choices[0].message.content
                    st.session_state.filter_result = result

                    # 提取截止提醒
                    reminders = []
                    lines = result.split("\n")
                    current_title = ""
                    for line in lines:
                        line = line.strip()
                        if "标题：" in line:
                            current_title = line.split("标题：")[-1].strip()
                        if "截止" in line and current_title:
                            reminders.append(f"{current_title} — {line}")
                    st.session_state.reminders = reminders

                    st.success("✅ 筛选完成！")
                    st.markdown("---")
                    st.markdown("### 📋 筛选结果")

                    with st.expander("点击展开查看完整筛选结果", expanded=True):
                        st.markdown(result)

                except Exception as e:
                    st.error(f"调用AI时出错，请检查API Key和网络。错误信息：{e}")

# ================= 页面2：信息提醒 =================
elif st.session_state.page == "remind":
    st.markdown("### 🔔 信息提醒")
    if st.session_state.reminders:
        st.write("根据你筛选出的通知，以下截止时间需要重点关注：")
        for r in st.session_state.reminders:
            st.markdown(
                f'<div class="reminder-card">⏰ {r}</div>', unsafe_allow_html=True
            )
    else:
        st.info(
            "你还没有进行筛选，或者没有检测到明确的截止时间。请先去「信息筛选」页进行筛选。"
        )

# ================= 页面3：导出与分享 =================
elif st.session_state.page == "export":
    st.markdown("### 📤 导出与分享")
    if st.session_state.filter_result:
        st.write("你可以把筛选结果导出，或者复制分享给同学：")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📄 下载TXT（可复制到Word）",
                data=st.session_state.filter_result,
                file_name="筛选结果.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="📕 下载TXT（备用）",
                data=st.session_state.filter_result,
                file_name="筛选结果.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col3:
            st.button("🖼️ 生成分享图（截图即可）", use_container_width=True)

        st.markdown("---")
        st.text_area(
            "也可以直接复制下面的文字，发给微信好友：",
            value=st.session_state.filter_result,
            height=200,
        )
    else:
        st.info("你还没有进行筛选，请先去「信息筛选」页进行筛选。")
