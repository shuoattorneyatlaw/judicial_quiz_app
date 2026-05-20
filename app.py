import streamlit as st
import json
import random

# 設定網頁標題與手機版面配置
st.set_page_config(page_title="國考一試刷題神器", page_icon="⚖️", layout="centered")

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

# 初始化狀態紀錄 (記住使用者的考試進度)
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = []
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'is_submitted' not in st.session_state:
    st.session_state.is_submitted = False

st.title("⚖️ 司法官/律師 一試刷題神器")
st.write(f"目前總題庫共 **{len(quiz_data)}** 題")

# 按鈕：抽取新題目
if st.button("🎲 隨機抽取 5 題", type="primary"):
    st.session_state.current_quiz = random.sample(quiz_data, min(5, len(quiz_data)))
    st.session_state.user_answers = {}
    st.session_state.is_submitted = False
    st.rerun()

st.divider()

# 如果目前有題目，就印出來
if st.session_state.current_quiz:
    for i, q in enumerate(st.session_state.current_quiz):
        st.subheader(f"第 {i+1} 題 ({q['year']}年 {q['subject']} - 原題號:{q['q_num']})")
        
        # 【修正功能 1】強制讓題目與 (A)(B)(C)(D) 選項換行，並把選項加粗，排版更漂亮
        raw_text = q['text']
        formatted_text = raw_text.replace("(A) ", "\n\n**(A)** ").replace("(B) ", "\n\n**(B)** ").replace("(C) ", "\n\n**(C)** ").replace("(D) ", "\n\n**(D)** ")
        
        st.markdown(formatted_text)
        st.write("") # 留一點微小的空白間隔
        
        # 讓使用者選擇答案 (A, B, C, D)
        options = ["(未作答)", "A", "B", "C", "D"]
        
        # 如果已經交卷，鎖定選項不給改
        user_choice = st.radio(
            "請選擇你的作答：", 
            options, 
            key=f"q_{i}",
            disabled=st.session_state.is_submitted
        )
        
        if user_choice != "(未作答)":
            st.session_state.user_answers[i] = user_choice
        
        # 如果已交卷，顯示解析與問 Gemini 功能
        if st.session_state.is_submitted:
            correct_ans = q['answer']
            if user_choice == correct_ans:
                st.success(f"✅ 答對了！正確答案是 {correct_ans}")
            else:
                st.error(f"❌ 答錯了！你的答案: {user_choice if user_choice != '(未作答)' else '未作答'}，正確答案是: {correct_ans}")
            
            # 【修正功能 2】加入問 Gemini 的智慧組裝發問功能
            # 自動建立完整的發問 Prompt（告訴 Gemini 正確答案，請它針對選項解析法條）
            gemini_prompt = f"請幫我詳細解析這道司法官/律師一試考古題：\n\n{formatted_text}\n\n官方標準答案是 ({correct_ans})。\n請說明為什麼這個答案是正確的，並解析其他三個選項錯在哪裡、涉及哪些法條或實務見解？"
            
            # 利用 Streamlit 的 text_area，其右上角會自動內建「一鍵複製」按鈕
            st.text_area("📋 點擊右上角按鈕複製題目與正確答案：", value=gemini_prompt, height=120, key=f"copy_{i}")
            st.link_button("💬 前往 Gemini 頁面發問", "https://gemini.google.com/")
            
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
        st.info(f"🏆 測驗結束！你答對了 **{score} / 5** 題！")
        st.balloons() # 放慶祝氣球特效！
else:
    st.info("請點擊上方的「隨機抽取 5 題」開始測驗！")
