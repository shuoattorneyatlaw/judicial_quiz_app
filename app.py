import streamlit as st
import streamlit.components.v1 as components
import json
import random

# 設定網頁標題與手機版面配置
st.set_page_config(page_title="國考一試刷題神器", page_icon="⚖️", layout="centered")

# 讀取題庫
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
# 【新增】用來強制重置選項的計數器
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

# 抽題與重置邏輯
def draw_ten_questions():
    current_ids = [(q['year'], q['subject'], q['q_num']) for q in st.session_state.get('current_quiz', [])]
    available_pool = [q for q in quiz_data if (q['year'], q['subject'], q['q_num']) not in current_ids]
    
    if len(available_pool) < 10:
        available_pool = quiz_data
        
    st.session_state.current_quiz = random.sample(available_pool, min(10, len(available_pool)))
    st.session_state.user_answers = {}
    st.session_state.is_submitted = False
    
    # 【關鍵技巧】增加 counter，讓 Radio 按鈕的 key 變更，強制讓它重置
    st.session_state.reset_counter += 1

def submit_quiz():
    st.session_state.is_submitted = True

st.title("⚖️ 司法官/律師 一試刷題神器")
st.write(f"目前總題庫共 **{len(quiz_data)}** 題")

# 開頭的初始抽題按鈕
st.button("🎲 隨機抽取 10 題", type="primary", on_click=draw_ten_questions)

st.divider()

if st.session_state.current_quiz:
    for i, q in enumerate(st.session_state.current_quiz):
        st.subheader(f"第 {i+1} 題 ({q['year']}年 {q['subject']} - 原題號:{q['q_num']})")
        
        raw_text = q['text']
        formatted_text = raw_text.replace("(A) ", "\n\n**(A)** ").replace("(B) ", "\n\n**(B)** ").replace("(C) ", "\n\n**(C)** ").replace("(D) ", "\n\n**(D)** ")
        st.markdown(formatted_text)
        
        options = ["(未作答)", "A", "B", "C", "D"]
        
        # 【修正重點】key 加入 reset_counter，每次抽新題這裡的 key 就會變，按鈕會強制重置
        user_choice = st.radio(
            "請選擇你的作答：", 
            options, 
            key=f"q_{i}_{st.session_state.reset_counter}", 
            disabled=st.session_state.is_submitted
        )
        
        if user_choice != "(未作答)":
            st.session_state.user_answers[i] = user_choice
        
        if st.session_state.is_submitted:
            correct_ans = q['answer']
            if user_choice == correct_ans:
                st.success(f"✅ 答對了！正確答案是 {correct_ans}")
            else:
                st.error(f"❌ 答錯了！你的答案: {user_choice if user_choice != '(未作答)' else '未作答'}，正確答案是: {correct_ans}")
            
            gemini_prompt = f"請幫我詳細解析這道司法官/律師一試考古題：\n\n{formatted_text}\n\n官方標準答案是 ({correct_ans})。\n請說明為什麼這個答案是正確的，並解析其他三個選項錯在哪裡、涉及哪些法條或實務見解？"
            js_text = json.dumps(gemini_prompt)
            
            html_code = f"""
            <script>
            function copyAndOpen() {{
                const text = {js_text};
                navigator.clipboard.writeText(text).then(() => window.open('https://gemini.google.com/', '_blank'));
            }}
            </script>
            <button onclick='copyAndOpen()' style="padding: 0.5rem 1rem; border-radius: 0.5rem; border: 1px solid #ccc; cursor: pointer;">
                💬 一鍵複製並前往 Gemini 發問
            </button>
            """
            components.html(html_code, height=50)
            
        st.write("---")

    if not st.session_state.is_submitted:
        st.button("📝 提交答案", type="secondary", on_click=submit_quiz)
    else:
        score = sum(1 for i, q in enumerate(st.session_state.current_quiz) 
                    if st.session_state.user_answers.get(i) == q['answer'])
        st.info(f"🏆 測驗結束！你答對了 **{score} / 10** 題！")
        
        if st.button("🔄 重新隨機抽取下一輪 10 題 (不與此輪重複)", type="primary", on_click=draw_ten_questions):
            pass # 按鈕點擊已透過 on_click 觸發 draw_ten_questions
            
        st.balloons()
else:
    st.info("請點擊上方的「隨機抽取 10 題」開始測驗！")
