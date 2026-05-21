import streamlit as st
import streamlit.components.v1 as components
import json
import random

# 設定網頁標題與手機版面配置
st.set_page_config(page_title="司律一試刷題", page_icon="⚖️", layout="centered")

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

# 【全新架構】初始化多輪狀態紀錄
# rounds 裡面會存放多個字典，每個字典代表一輪 10 題的狀態
if 'rounds' not in st.session_state:
    st.session_state.rounds = []

# 抽題邏輯 (現在是新增一輪，而不是覆蓋舊的)
def draw_ten_questions():
    # 搜集之前「所有輪次」出現過的題目 ID，確保絕對不重複
    current_ids = [(q['year'], q['subject'], q['q_num']) 
                   for r in st.session_state.rounds 
                   for q in r['questions']]
                   
    available_pool = [q for q in quiz_data if (q['year'], q['subject'], q['q_num']) not in current_ids]
    
    # 防呆：如果題庫快抽完了，就重新重置題庫池
    if len(available_pool) < 10:
        available_pool = quiz_data
        
    new_quiz = random.sample(available_pool, min(10, len(available_pool)))
    
    # 將新抽出的 10 題作為一個「新輪次」加入紀錄中
    st.session_state.rounds.append({
        "questions": new_quiz,
        "answers": {},
        "submitted": False
    })

st.title("⚖️ 司律 一試 刷題 ")
st.write(f"目前總題庫共 **{len(quiz_data)}** 題")

# 當完全沒有題目時，顯示初始的開始按鈕
if len(st.session_state.rounds) == 0:
    if st.button("🎲 開始隨機抽取第一輪 10 題", type="primary"):
        draw_ten_questions()
        st.rerun()

# 逐一渲染每一個輪次的題目
for r_idx, current_round in enumerate(st.session_state.rounds):
    
    st.markdown(f"## 🏁 第 {r_idx + 1} 輪測驗")
    st.divider()
    
    for i, q in enumerate(current_round['questions']):
        # 計算累積的總題號 (例如第二輪第一題就是第 11 題)
        global_q_num = r_idx * 10 + i + 1
        
        st.subheader(f"第 {global_q_num} 題 ({q['year']}年 {q['subject']} - 原題號:{q['q_num']})")
        
        raw_text = q['text']
        formatted_text = raw_text.replace("(A) ", "\n\n**(A)** ").replace("(B) ", "\n\n**(B)** ").replace("(C) ", "\n\n**(C)** ").replace("(D) ", "\n\n**(D)** ")
        st.markdown(formatted_text)
        
        options = ["(未作答)", "A", "B", "C", "D"]
        
        # 【修正】給每個選項獨一無二的 key (輪次 + 題號)，避免互相干擾
        user_choice = st.radio(
            "請選擇你的作答：", 
            options, 
            key=f"r_{r_idx}_q_{i}", 
            disabled=current_round['submitted']
        )
        
        if user_choice != "(未作答)":
            current_round['answers'][i] = user_choice
        
        # 如果該輪已經交卷，顯示解析與 Gemini 按鈕
        if current_round['submitted']:
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
            <button onclick='copyAndOpen()' style="padding: 0.5rem 1rem; border-radius: 0.5rem; border: 1px solid #ccc; cursor: pointer; background: white; color: #333;">
                💬 一鍵複製並前往 Gemini 發問
            </button>
            """
            components.html(html_code, height=50)
            
        st.write("---")

    # 每輪底部的結算與操作區
    if not current_round['submitted']:
        # 該輪未交卷時，顯示交卷按鈕
        if st.button(f"📝 提交第 {r_idx + 1} 輪答案", type="secondary", key=f"submit_{r_idx}"):
            current_round['submitted'] = True
            st.rerun()
    else:
        # 該輪已交卷時，顯示該輪分數
        score = sum(1 for i, q in enumerate(current_round['questions']) 
                    if current_round['answers'].get(i) == q['answer'])
        st.info(f"🏆 第 {r_idx + 1} 輪結束！本輪答對了 **{score} / 10** 題！")
        
        # 【核心功能】如果這是「最後一輪」，才在最底下顯示抽取下一輪的按鈕
        if r_idx == len(st.session_state.rounds) - 1:
            st.write("") # 留一點空間
            if st.button("⬇️ 往下延伸：抽取下一輪 10 題 (不重複)", type="primary", key=f"next_{r_idx}"):
                draw_ten_questions()
                st.rerun()
