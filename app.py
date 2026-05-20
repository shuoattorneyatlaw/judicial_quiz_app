import streamlit as st
import streamlit.components.v1 as components
import json
import random

# 設定網頁標題與手機版面配置
st.set_page_config(page_title="司律一試刷題工具", page_icon="⚖️", layout="centered")

# 讀取剛剛做好的題庫 (使用 cache 讓網頁瞬間載入)
@st.cache_data
def load_data():
    with open('quiz_database.json', 'r', encoding='utf-8') as f:
        return json.load(f)

try:
    quiz_data = load_data()
except FileNotFoundError:
    st.error("找不到題庫檔案 quiz_database.json！")
    st.stop()

# 初始化狀態紀錄
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = []
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'is_submitted' not in st.session_state:
    st.session_state.is_submitted = False

st.title("⚖️ 司律 一試刷題工具")
st.write(f"目前總題庫共 **{len(quiz_data)}** 題")

# 按鈕：抽取新題目
if st.button("🎲 隨機抽取 10 題", type="primary"):
    st.session_state.current_quiz = random.sample(quiz_data, min(10, len(quiz_data)))
    st.session_state.user_answers = {}
    st.session_state.is_submitted = False
    st.rerun()

st.divider()

# 如果目前有題目，就印出來
if st.session_state.current_quiz:
    for i, q in enumerate(st.session_state.current_quiz):
        st.subheader(f"第 {i+1} 題 ({q['year']}年 {q['subject']} - 原題號:{q['q_num']})")
        
        # 題目與選項排版
        raw_text = q['text']
        formatted_text = raw_text.replace("(A) ", "\n\n**(A)** ").replace("(B) ", "\n\n**(B)** ").replace("(C) ", "\n\n**(C)** ").replace("(D) ", "\n\n**(D)** ")
        
        st.markdown(formatted_text)
        st.write("") 
        
        options = ["(未作答)", "A", "B", "C", "D"]
        
        user_choice = st.radio(
            "請選擇你的作答：", 
            options, 
            key=f"q_{i}",
            disabled=st.session_state.is_submitted
        )
        
        if user_choice != "(未作答)":
            st.session_state.user_answers[i] = user_choice
        
        # === 交卷後的解析與一鍵跳轉功能 ===
        if st.session_state.is_submitted:
            correct_ans = q['answer']
            if user_choice == correct_ans:
                st.success(f"✅ 答對了！正確答案是 {correct_ans}")
            else:
                st.error(f"❌ 答錯了！你的答案: {user_choice if user_choice != '(未作答)' else '未作答'}，正確答案是: {correct_ans}")
            
            # 自動組裝給 Gemini 的發問詞
            gemini_prompt = f"請幫我詳細解析這道司法官/律師一試考古題：\n\n{formatted_text}\n\n官方標準答案是 ({correct_ans})。\n請說明為什麼這個答案是正確的，並解析其他三個選項錯在哪裡、涉及哪些法條或實務見解？"
            
            # 將 Python 字串轉為安全的 JavaScript 字串
            js_text = json.dumps(gemini_prompt)
            
            # 建立帶有複製並跳轉功能的特製 HTML 按鈕
            html_code = f"""
            <div style="font-family: 'Source Sans Pro', sans-serif;">
                <button onclick='copyAndOpen()' style="
                    background-color: white;
                    color: #31333F;
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    padding: 0.5rem 1rem;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: 400;
                    display: inline-flex;
                    align-items: center;
                    transition: all 0.2s ease;
                " onmouseover="this.style.borderColor='#FF4B4B'; this.style.color='#FF4B4B';" onmouseout="this.style.borderColor='rgba(49, 51, 63, 0.2)'; this.style.color='#31333F';">
                    💬 一鍵複製並前往 Gemini 發問
                </button>
            </div>
            <script>
            function copyAndOpen() {{
                const text = {js_text};
                navigator.clipboard.writeText(text).then(function() {{
                    window.open('https://gemini.google.com/', '_blank');
                }}).catch(function(err) {{
                    // 備用複製方案 (針對部分手機瀏覽器限制)
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    textArea.style.position = "fixed"; 
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    try {{
                        document.execCommand('copy');
                    }} catch (err) {{
                        console.error('複製失敗', err);
                    }}
                    document.body.removeChild(textArea);
                    window.open('https://gemini.google.com/', '_blank');
                }});
            }}
            </script>
            """
            # 渲染這個特製按鈕
            components.html(html_code, height=60)
            
        st.write("---")

    # 交卷按鈕
    if not st.session_state.is_submitted:
        if st.button("📝 提交答案", type="secondary"):
            st.session_state.is_submitted = True
            st.rerun()
    else:
        # 計算總分
        score = sum(1 for i, q in enumerate(st.session_state.current_quiz) 
                    if st.session_state.user_answers.get(i) == q['answer'])
        st.info(f"🏆 測驗結束！你答對了 **{score} / 10** 題！")
        st.balloons()
else:
    st.info("請點擊上方的「隨機抽取 10 題」開始測驗！")
