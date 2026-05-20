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
        # 顯示題目
        st.markdown(f"**{q['text']}**")
        
        # 讓使用者選擇答案 (A, B, C, D)
        options = ["(未作答)", "A", "B", "C", "D"]
        
        # 如果已經交卷，鎖定選項不給改
        user_choice = st.radio(
            "請選擇答案：", 
            options, 
            key=f"q_{i}",
            disabled=st.session_state.is_submitted
        )
        
        if user_choice != "(未作答)":
            st.session_state.user_answers[i] = user_choice
        
        # 如果已交卷，顯示解析
        if st.session_state.is_submitted:
            correct_ans = q['answer']
            if user_choice == correct_ans:
                st.success(f"✅ 答對了！正確答案是 {correct_ans}")
            else:
                st.error(f"❌ 答錯了！你的答案: {user_choice if user_choice != '(未作答)' else '未作答'}，正確答案是: {correct_ans}")
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
