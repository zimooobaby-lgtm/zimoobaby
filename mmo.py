import os
import streamlit as st
from openai import OpenAI
# ==================================================
# 1. 页面配置
# ==================================================
st.set_page_config(
    page_title="AI 法律助手",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)
# ==================================================
# 2. 页面样式
# ==================================================
st.markdown("""
<style>
.stApp {
    background: #F4F6FA;
}
.block-container {
    max-width: 850px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
.main-title {
    text-align: center;
    font-size: 32px;
    font-weight: 800;
    color: #20385F;
    margin-top: 20px;
}
.sub-title {
    text-align: center;
    font-size: 15px;
    color: #7B8798;
    margin-bottom: 35px;
}
.stButton > button {
    width: 100%;
    min-height: 48px;
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.2s ease;
}
div.st-key-confirm_button button {
    background: #20385F;
    color: white;
    border: none;
}
div.st-key-skip_button button {
    background: #2878F0 !important;
    color: white !important;
    border: none !important;
}
div.st-key-start_consult button,
div.st-key-search_law button {
    background: #20385F;
    color: white;
    border: none;
}
div.st-key-back_button button {
    background: white;
    color: #20385F;
    border: 1px solid #D6DFEC;
}
div.stButton > button:hover {
    opacity: 0.9;
    border-color: #2878F0;
}
div[data-testid="stExpander"] {
    background: white;
    border-radius: 12px;
}
.stTextInput input,
.stTextArea textarea {
    border-radius: 10px;
}
.footer {
    text-align: center;
    color: #929CAB;
    font-size: 12px;
    margin-top: 30px;
}
.red-notice{
    color: #d62828;
    font-weight:bold;
    font-size:15px;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)
# ==================================================
# 3. 初始化会话状态【已填入你的密钥】
# ==================================================
defaults = {
    "page": "welcome",
    "identity": "",
    "legal_type": "",
    "api_key": "sk-c91cbd1c10374de392cb38032869aca7",
    "model_choice": "deepseek-chat",
    "history": []
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 工具函数：清理条款编号，兼容中文汉字、阿拉伯数字输入
def clean_article_text(raw_text: str) -> str:
    """去除“第、条”等多余汉字，返回干净的编号，兼容中文大写汉字编号"""
    t = raw_text.strip()
    t = t.replace("第", "").replace("条", "").strip()
    return t

# ==================================================
# 4. DeepSeek 客户端
# ==================================================
@st.cache_resource
def get_deepseek_client(api_key):
    """
    使用兼容 OpenAI SDK 的方式连接 DeepSeek API。
    实际请求发送到 DeepSeek，而不是 OpenAI。
    """
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
# ==================================================
# 5. 调用 DeepSeek
# ==================================================
def ask_ai(system_prompt, user_prompt):
    api_key = st.session_state.api_key.strip()
    model = st.session_state.model_choice
    if not api_key:
        st.error(
            "请先配置 DeepSeek API Key。"
        )
        return None
    try:
        client = get_deepseek_client(api_key)
        with st.spinner("AI正在分析，请稍候……"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.3
            )
        answer = response.choices[0].message.content
        if not answer:
            st.warning("AI没有返回文字，请稍后重试。")
            return None
        st.markdown(answer)
        st.session_state.history.append({
            "question": user_prompt,
            "answer": answer
        })
        return answer
    except Exception as e:
        error_message = str(e)
        error_lower = error_message.lower()
        if "401" in error_message or "authentication" in error_lower:
            st.error(
                "DeepSeek API Key 无效或认证失败。"
                "请检查密钥是否正确，以及是否复制完整。"
            )
        elif "402" in error_message:
            st.error(
                "DeepSeek API 账户余额不足或账户存在计费问题。"
                "请登录 DeepSeek 开放平台检查账户状态。"
            )
        elif "429" in error_message:
            st.error(
                "DeepSeek API 请求受到限制。"
                "可能是请求过于频繁、账户限制或服务配额问题，"
                "请查看 DeepSeek 平台的错误详情。"
            )
        elif "model" in error_lower:
            st.error(
                "模型调用失败。请检查模型名称是否正确，"
                "以及账户是否有权限使用该模型。"
            )
        elif (
            "connection" in error_lower
            or "timeout" in error_lower
        ):
            st.error(
                "暂时无法连接 DeepSeek 服务。"
                "请检查网络连接后重试。"
            )
        else:
            st.error(f"DeepSeek 调用失败：{error_message}")
        return None
# ==================================================
# 6. 欢迎页面
# ==================================================
def page_welcome():
    st.markdown(
        '<div class="main-title">⚖️ AI 法律助手</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-title">解决纠纷 · 法为民生</div>',
        unsafe_allow_html=True
    )
    st.markdown("### 开始之前")
    st.write("简单填写以下信息，帮助我们更好地了解您的需求。")
    identity = st.selectbox(
        "1. 请问您的身份是？",
        [
            "请选择",
            "个人用户",
            "企业用户",
            "律师",
            "法律工作者",
            "其他"
        ],
        key="welcome_identity"
    )
    legal_type = st.selectbox(
        "2. 您想咨询哪种类型的法律服务？",
        [
            "请选择",
            "民事纠纷",
            "刑事法律",
            "婚姻家庭",
            "劳动纠纷",
            "合同纠纷",
            "房产纠纷",
            "公司法律事务",
            "知识产权",
            "行政法律事务",
            "其他法律问题"
        ],
        key="welcome_legal_type"
    )
    st.write("")
    if st.button(
        "确认并继续",
        key="confirm_button",
        type="primary"
    ):
        if identity == "请选择" or legal_type == "请选择":
            st.warning("请选择您的身份和法律咨询类型。")
        else:
            st.session_state.identity = identity
            st.session_state.legal_type = legal_type
            st.session_state.page = "home"
            st.rerun()
    if st.button("跳过", key="skip_button"):
        st.session_state.identity = ""
        st.session_state.legal_type = ""
        st.session_state.page = "home"
        st.rerun()
    st.markdown(
        '<div class="footer">'
        '法律信息仅供一般普法参考，请以现行法律及专业法律意见为准。'
        '</div>',
        unsafe_allow_html=True
    )
# ==================================================
# 7. 主页面
# ==================================================
def page_home():
    st.markdown(
        '<div class="main-title">⚖️ AI 法律助手</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-title">解决纠纷 · 法为民生</div>',
        unsafe_allow_html=True
    )
    # --------------------------------------------------
    # 用户信息
    # --------------------------------------------------
    if st.session_state.identity:
        st.info(
            f"用户身份：{st.session_state.identity}　"
            f"咨询类型：{st.session_state.legal_type}"
        )
    # --------------------------------------------------
    # 功能导航
    # --------------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "💬 法律咨询",
        "📖 法条查询",
        "🗂️ 咨询记录"
    ])
    # ==================================================
    # 8. 法律咨询
    # ==================================================
    with tab1:
        st.markdown("### 描述你的法律问题")
        issue = st.text_area(
            "案情描述",
            height=180,
            placeholder=(
                "请尽量描述事情经过、发生时间、涉及金额、"
                "已有证据以及你希望解决的问题。"
            ),
            key="issue_input"
        )
        consult_type = st.radio(
            "希望获得什么帮助？",
            [
                "相关法律知识与法条",
                "纠纷解决方案",
                "法律知识与解决方案"
            ],
            index=2
        )
        if st.button(
            "开始 AI 法律咨询",
            key="start_consult",
            type="primary"
        ):
            issue = issue.strip()
            if not issue:
                st.warning("请先填写你的法律问题。")
            else:
                system_prompt = """
你是一名严谨的法律信息辅助助手。
请遵守以下原则：
1. 先识别用户涉及的国家或地区。
2. 如果用户没有说明司法管辖区，先提示其补充。
   可以提供一般性信息，但不要武断地认定适用哪国法律。
3. 对法律条文、法规名称、条文编号和生效状态保持谨慎。
4. 不确定的法律条文不得编造，应明确说明需要核实。
5. 根据用户的案情，区分已知事实、推测和待确认事项。
6. 提供清晰、可执行的下一步建议及相关证据清单。
7. 对诉讼时效、仲裁期限等风险给予提示，
   但不要随意猜测期限。
8. 不保证胜诉，不将一般性分析表述为律师正式意见。
9. 如果问题涉及紧急人身安全，应优先建议联系当地紧急服务。
回答应使用中文和清晰的 Markdown 格式。
在结尾说明：
本回答仅供一般法律信息参考，不构成律师正式法律意见。
具体案件应结合适用法律、证据和实际情况咨询执业律师。
"""
                user_prompt = (
                    f"用户身份：{st.session_state.identity or '未填写'}\n"
                    f"预选咨询类别：{st.session_state.legal_type or '未填写'}\n"
                    f"用户选择的帮助类型：{consult_type}\n"
                    "司法管辖区：请根据用户提供的信息判断；"
                    "如无法判断，请明确提示。\n"
                    f"案件描述：\n{issue}"
                )
                st.markdown("---")
                st.markdown("### AI 分析结果")
                ask_ai(system_prompt, user_prompt)
    # ==================================================
    # 9. 法条查询（优化：支持中文汉字条款编号）
    # ==================================================
    with tab2:
        st.markdown("### 📖 法律条文查询")
        jurisdiction = st.text_input(
            "国家或地区",
            placeholder="例如：中国大陆、美国加利福尼亚州"
        )
        law_name = st.text_input(
            "法律名称",
            placeholder="例如：中华人民共和国民法典"
        )
        article_num = st.text_input(
            "条款编号",
            placeholder="支持阿拉伯数字或中文汉字，例：1079 / 第一千零七十九条"
        )
        if st.button(
            "查询并解析",
            key="search_law",
            type="primary"
        ):
            if not jurisdiction.strip():
                st.warning("请填写适用的国家或地区。")
            elif not law_name.strip() or not article_num.strip():
                st.warning("请填写法律名称和条款编号。")
            else:
                clean_article = clean_article_text(article_num)
                sys_prompt = """
你是一名严谨的法律信息辅助助手。
用户要求查询特定法律条文时：
1. 说明法律名称、条款编号和所属司法管辖区。
2. 用户可能输入阿拉伯数字或者中文汉字大写编号（例如第一千零七十九条），两种都要识别处理。
3. 如果不能确认条文原文，不得伪造或声称已经核对官方数据库。
4. 将已确认内容与需要进一步核实的内容明确区分。
5. 可以提供通俗解释、可能适用的场景和相关问题。
6. 提醒用户核实官方现行文本及修订情况。
7. 使用中文 Markdown 格式回答。
8. 说明内容仅供普法参考，不构成律师正式法律意见。
"""
                user_prompt = (
                    f"司法管辖区：{jurisdiction}\n"
                    f"法律名称：{law_name}\n"
                    f"原始输入条款：{article_num}\n"
                    f"处理后编号：{clean_article}\n\n"
                    "请提供条文信息、通俗解释、适用场景及核实建议。"
                    "如果不能确认原文，请明确说明，不要编造。"
                )
                st.markdown("### 查询结果")
                ask_ai(sys_prompt, user_prompt)
    # ==================================================
    # 10. 咨询记录
    # ==================================================
    with tab3:
        st.markdown("### 🗂️ 当前会话咨询记录")
        if not st.session_state.history:
            st.info("当前会话还没有咨询记录。")
        else:
            for index, item in enumerate(
                reversed(st.session_state.history),
                start=1
            ):
                with st.expander(f"咨询记录 {index}"):
                    st.markdown("**问题**")
                    st.write(item["question"])
                    st.markdown("**回答**")
                    st.markdown(item["answer"])
            if st.button("清空当前会话记录"):
                st.session_state.history = []
                st.rerun()
    # --------------------------------------------------
    # 页脚红色重点免责 +12348
    # --------------------------------------------------
    st.markdown("---")
    st.markdown('<p class="red-notice">⚠️ 重要提示：AI生成内容仅为普法参考，不构成执业律师正式法律意见。如需专业法律帮助，请拨打全国公共法律服务热线：12348</p >', unsafe_allow_html=True)
    st.caption(
        "AI 法律助手 · 本工具提供一般法律信息，不替代执业律师的专业意见。"
    )
    if st.button("返回欢迎页", key="back_button"):
        st.session_state.page = "welcome"
        st.rerun()
# ==================================================
# 11. 页面入口
# ==================================================
if st.session_state.page == "welcome":
    page_welcome()
else:
    page_home()