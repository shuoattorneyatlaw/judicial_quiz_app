import streamlit as st
import streamlit.components.v1 as components
import json
import random

# 設定網頁標題與手機版面配置
st.set_page_config(page_title="國考一試刷題神器", page_icon="⚖️", layout="centered")

# 讀取題庫 (使用 cache 讓網頁瞬間載入)
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

# 【新增核心功能】抽取 10 題且排除上一輪題目的邏輯
def draw_ten_questions():
    # 取得當前題目的識別特徵 (年度, 科目, 原題號)
    current_ids = [(q['year'], q['subject'], q['q_num']) for q in st.session_state.get('current_quiz', [])]
    
    # 從總題庫中排除剛才出現過的題目
    available_pool = [q for q in quiz_data if (q['year'], q['subject'], q['q_num']) not in current_ids]
    
    # 防呆機制：如果剩餘題庫不足 10 題，就用回完整題庫
    if len(available_pool) < 10:
        available_pool = quiz_data
        
    # 隨機抽取 10 題
    st.session_state.current_quiz = random.sample(available_pool, min(10, len(available_pool)))
    st.session_state.user_answers = {}
    st.session_state.is_submitted = False
    
    # 【核心功能】將所有單選鈕作答位置強制歸位回到未作答
    for i in range(10):
        if f"q_{i}" in st.session_state:
            st.session_state[f"q_{i}"] = "(未作答)"

st.title("⚖️ 司法官/律師 一試刷題神器")
st.write(f"目前總題庫共 **{len(quiz_data)}** 題")

# 開頭的初始抽題按鈕
if st.button("🎲 隨機抽取 10 題", type="primary"):
    draw_ten_questions()
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
        
        # 單選按鈕
        user_choice = st.radio(
            "請選擇你的作答：", 
            options, 
            key=f"q_{i}",
            disabled=st.session_state.is_submitted
        )
        
        if user_choice != "(未作答)":
            st.session_state.user_answers[i] = user_choice
        
        # 交卷後的解析與一鍵跳轉
        if st.session_state.is_submitted:
            correct_ans = q['answer']
            if user_choice == correct_ans:
                st.success(f"✅ 答對了！正確答案是 {correct_ans}")
            else:
                st.error(f"❌ 答錯了！你的答案: {user_choice if user_choice != '(未作答)' else '未作答'}，正確答案是: {correct_ans}")
            
            gemini_prompt = f"請幫我詳細解析這道司法官/律師一試考古題：\n\n{formatted_text}\n\n官方標準答案是 ({correct_ans})。\n請說明為什麼這個答案是正確的，並解析其他三個選項錯在哪裡、涉及哪些法條或實務見解？"
            js_text = json.dumps(gemini_prompt)
            
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
            components.html(html_code, height=60)
            
        st.write("---")

    # 底部控制按鈕區
    if not st.session_state.is_submitted:
        if st.button("📝 提交答案", type="secondary"):
            st.session_state.is_submitted = True
            st.rerun()
    else:
        # 計算總分 (滿分改為 10 題)
        score = sum(1 for i, q in enumerate(st.session_state.current_quiz) 
                    if st.session_state.user_answers.get(i) == q['answer'])
        st.info(f"🏆 測驗結束！你答對了 **{score} / 10** 題！")
        
        # 【新增功能】位於計分結果正下方的「再抽 10 題不重複」按鈕
        if st.button("🔄 重新隨機抽取下一輪 10 題 (不與此輪重複)", type="primary"):
            draw_ten_questions()
            st.rerun()
            
        st.balloons()
else:
    st.info("請點擊上方的「隨機抽取 10 題」開始測驗！")
