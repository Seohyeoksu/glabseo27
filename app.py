import os
from openai import OpenAI
import streamlit as st

os.environ["OPENAI_API_KEY"] = st.secrets['API_KEY']
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

st.set_page_config(
    page_title="행사 시나리오 생성기",
    page_icon="🎭",
    layout="centered",
    initial_sidebar_state="auto",
)

st.markdown("""
    <style>
        .main {
            background-color: #F9FAFB;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #1E3A8A;
            text-align: center;
            font-family: 'Arial', sans-serif;
            margin-bottom: 30px;
        }
        .section {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 25px;
            border-left: 5px solid #2563EB;
        }
        .stButton>button {
            background-color: #2563EB;
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 12px 20px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            width: 100%;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #1D4ED8;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>행사 시나리오 생성기</h1>", unsafe_allow_html=True)

event_type = st.radio(
    "행사 유형 선택",
    ["학교 행사", "교육청 행사"],
    horizontal=True
)

if event_type == "학교 행사":
    event_templates = {
        "입학식": ["개식사", "국민의례", "학교장 환영사", "신입생 선서", "교가 제창", "폐식사"],
        "졸업식": ["개식사", "국민의례", "졸업장 수여", "학교장 식사", "축사", "졸업생 대표 답사", "교가 제창", "폐식사"],
        "체육대회": ["개회식", "준비운동", "트랙경기", "단체경기", "학년별 경기", "폐회식"],
        "직접 입력": []
    }
else:
    event_templates = {
        "교육감 이취임식": ["개식사", "국민의례", "이임사", "이임패 증정", "취임사", "축사", "폐식사"],
        "교육청 학술대회": ["개회식", "기조강연", "세션발표", "토론회", "시상식", "폐회식"],
        "교육청 연수": ["등록", "개회식", "특강", "분임토의", "사례발표", "폐회식"],
        "직접 입력": []
    }

selected_template = st.selectbox("행사 템플릿 선택", options=list(event_templates.keys()))

with st.container():
    event_name = st.text_input("행사명", 
                              value="" if selected_template == "직접 입력" else selected_template,
                              placeholder="행사명을 입력하세요")
    event_date = st.date_input("행사 날짜")
    event_location = st.text_input("행사 장소", placeholder="행사 장소를 입력하세요")
    
    mc_count = st.radio("사회자 수", [1, 2], horizontal=True)
    if mc_count == 2:
        st.info("2인 사회의 경우, 남녀 사회자가 번갈아가며 진행하는 형식으로 작성됩니다.")

    if event_type == "교육청 행사":
        vip_attendees = st.text_area("주요 참석자", placeholder="예: 교육감, 부교육감, 국장 등\n각 줄에 한 명씩 입력해주세요")
    else:
        vip_attendees = ""

    if 'event_items' not in st.session_state or selected_template != st.session_state.get('last_template'):
        st.session_state.event_items = [{"item": item, "time": 5, "detail": ""} for item in event_templates[selected_template]]
        st.session_state.last_template = selected_template
    
    st.subheader("행사 순서")

    new_item = st.text_input("순서 추가", placeholder="행사 순서를 입력하세요")
    new_time = st.number_input("소요 시간(분)", min_value=1, value=5)
    new_detail = st.text_area("세부사항", placeholder="세부사항을 입력하세요")
    
    if st.button("순서 추가"):
        if new_item:
            st.session_state.event_items.append({
                "item": new_item,
                "time": new_time,
                "detail": new_detail
            })
    
    if st.session_state.event_items:
        for idx, item in enumerate(st.session_state.event_items):
            col1, col2, col3, col4 = st.columns([3, 2, 4, 1])
            with col1:
                item['item'] = st.text_input("순서", value=item['item'], key=f"item_{idx}")
            with col2:
                item['time'] = st.number_input("시간(분)", min_value=1, value=item['time'], key=f"time_{idx}")
            with col3:
                item['detail'] = st.text_input("세부사항", value=item['detail'], key=f"detail_{idx}")
            with col4:
                if st.button("삭제", key=f"delete_{idx}"):
                    st.session_state.event_items.pop(idx)
                    st.experimental_rerun()
    
    if st.button("시나리오 생성하기", disabled=len(st.session_state.event_items) == 0):
        if not event_name:
            st.error("행사명을 입력해주세요.")
        else:
            with st.spinner('시나리오를 생성중입니다...'):
                # 행사 순서 문자열 생성
                event_items_str = "\n".join([
                    f"{idx+1}. {item['item']} ({item['time']}분) - {item['detail']}" 
                    for idx, item in enumerate(st.session_state.event_items)
                ])

                vip_info = ""
                if event_type == "교육청 행사" and vip_attendees:
                    vip_info = f"주요 참석자:\n{vip_attendees}\n"

                scenario_instructions = [
                    "1. 각 순서별 정확한 사회자 멘트",
                    "2. 시간 배분",
                    "3. 특이사항 및 주의사항",
                    "4. 청중 동작 안내 (기립, 착석 등)"
                ]
                
                if event_type == "교육청 행사":
                    scenario_instructions.append("5. VIP 참석자 소개 및 예우 사항")

                mc_instruction = "사회자 2명이 번갈아가며 진행하는 형식으로 작성해주세요." if mc_count == 2 else ""

                prompt = f"""행사 유형: {event_type}
행사명: {event_name}
일시: {event_date.strftime("%Y년 %m월 %d일")}
장소: {event_location}
사회자 수: {mc_count}명
{vip_info}

행사 순서:
{event_items_str}

위 정보를 바탕으로 {event_type}에 적합한 시나리오를 작성해주세요. 다음 사항을 반드시 포함해주세요:
{chr(10).join(scenario_instructions)}

{mc_instruction}"""

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": f"당신은 전문적인 {event_type} 시나리오 작성자입니다. 행사의 특성과 분위기를 고려하여 자연스럽고 품격 있는 시나리오를 작성해주세요."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                )
                
                st.markdown("### 생성된 시나리오")
                st.markdown(response.choices[0].message.content)
                st.download_button(
                    label="시나리오 다운로드",
                    data=response.choices[0].message.content,
                    file_name=f"{event_name}_시나리오.txt",
                    mime="text/plain"
                )
