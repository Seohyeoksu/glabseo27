import os
import streamlit as st
from openai import OpenAI
import pandas as pd
import io

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = st.secrets['API_KEY']  # 또는 직접 입력: os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 페이지 설정
st.set_page_config(
    page_title="스토리텔링 문장제 문제 생성기",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="auto",
)

# 스타일 적용
st.markdown("""
    <style>
        .main {
            background-color: #F9FAFB;
            max-width: 800px;
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

# 페이지 헤더
st.markdown("<h1>스토리텔링 문장제 문제 생성기</h1>", unsafe_allow_html=True)

st.subheader("엑셀 파일로 수학 문제를 업로드하고 스토리텔링 문장제 문제로 변환")

# 사용자로부터 소설 또는 동화 제목 입력받기
story_title = st.text_input("소설 또는 동화 제목을 입력하세요", placeholder="예: '흥부와 놀부', '백설공주'")

# 엑셀 파일 업로드
uploaded_file = st.file_uploader("수학 문제가 포함된 엑셀 파일을 업로드하세요", type=['xlsx', 'xls'])

# 엑셀 템플릿 다운로드 버튼
def create_excel_template():
    """엑셀 템플릿 파일 생성"""
    df = pd.DataFrame({
        '문제': ['5 + 7', '12 x 3', '20 - 8']
    })
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='수학문제', index=False)
    return buffer

excel_template = create_excel_template()
st.download_button(
    label="엑셀 템플릿 다운로드",
    data=excel_template.getvalue(),
    file_name="수학문제_템플릿.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

if st.button("문장제 문제 생성"):
    if story_title.strip() == "":
        st.error("소설 또는 동화 제목을 입력해주세요!")
    elif uploaded_file is None:
        st.error("엑셀 파일을 업로드해주세요!")
    else:
        try:
            with st.spinner("문제 생성 중..."):
                # 엑셀 파일 읽기
                df = pd.read_excel(uploaded_file, engine='openpyxl')
                if '문제' not in df.columns:
                    st.error("엑셀 파일에 '문제' 열이 없습니다. 템플릿을 사용해주세요.")
                else:
                    generated_problems_list = []  # 수정된 부분: 리스트 초기화
                    for idx, row in df.iterrows():
                        math_problem = str(row['문제'])
                        if pd.isna(math_problem) or math_problem.strip() == "":
                            generated_problems_list.append("")  # 빈 값 처리
                            continue

                        # GPT-API 호출 프롬프트 생성
                        prompt = f"""
입력된 수학 문제와 소설 또는 동화 제목을 기반으로 스토리가 있는 문장제 수학 문제를 만들어주세요.

요구사항:
1. 이야기의 배경은 '{story_title}'입니다.
2. 원래 수학 문제의 계산 결과와 동일한 답을 가지도록 해주세요.
3. 이야기의 주요 인물과 설정을 활용해주세요.
4. 초등학생이 이해할 수 있는 수준으로 작성해주세요.
5. 문제와 함께 정답도 제공해주세요.

입력된 수학 문제: {math_problem}
"""
                        # GPT API 호출
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "당신은 창의적인 초등학교 수학 선생님입니다."},
                                {"role": "user", "content": prompt}
                            ],
                        )
                        generated_problem = response.choices[0].message.content

                        # 생성된 문제를 리스트에 추가
                        generated_problems_list.append(generated_problem)

                    # 생성된 모든 문제 표시
                    st.markdown("## 생성된 스토리텔링 문장제 문제")
                    for idx, problem in enumerate(generated_problems_list):
                        st.markdown(f"### 문제 {idx+1}")
                        st.markdown(problem)
                        st.markdown("---")

                    # 결과를 엑셀 파일로 저장
                    output_df = pd.DataFrame({
                        '문제': df['문제'],
                        '스토리텔링 문장제 문제': generated_problems_list
                    })
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        output_df.to_excel(writer, index=False, sheet_name='스토리텔링문제')
                    output.seek(0)

                    # 문제 다운로드 버튼 추가
                    st.download_button(
                        label="생성된 문제 엑셀 다운로드",
                        data=output,
                        file_name="스토리텔링_문장제_수학_문제.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error(f"문제 생성 중 오류가 발생했습니다: {e}")
