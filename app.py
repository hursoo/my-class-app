import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime # <-- 이 부분이 추가되었습니다.


# --------------------
# 페이지 기본 설정
# --------------------
st.set_page_config(
    page_title="[과목명] 강의 웹페이지",
    page_icon="🎓",
    layout="wide",
)

# --------------------
# 강의 정보 (사용자님 내용 그대로 유지)
# --------------------
COURSE_TITLE = "역사학 논문쓰기 1(25-2)"
COURSE_CODE = "M3533.001500. 강좌001"
PROFESSOR_NAME = "허 수 교수"
PROFESSOR_EMAIL = "crctaper@snu.ac.kr"
DAY_TIME = "화, 10:00~12:50"
CLASSROOM = "14-203"


# --------------------
# 주차별 강의 계획 데이터 (사용자님 내용 그대로 유지)
# --------------------
schedule_data = {
    '단계': [
        '[1부]<br>연구계획서 작성', '', '',
        '[2부]<br>연구사 정리', '', '',
        '[3부]<br>사료 읽기', '', '',
        '[4부]<br>초고 쓰기', '', '',
        '[5부]<br>논문 완성', '', ''
    ],
    '주차': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    '내용': ['강의 소개', '역사논문 작성법', '연구계획서 발표', '학술논문 2편 요약', '연구사 노트', '연구사 노트', '1차 사료 소개', '사료 노트', '사료 노트', '초고 작성 개요', '초고 작성', '초고 작성', '완고 발표', '완고 발표', '완고 발표'],
    '일자': [
        '09.02', '09.09', '09.16', '09.23', '09.30', '10.07', '10.14',
        '10.21', '10.28', '11.04', '11.11', '11.18', '11.25', '12.02', '12.09'
    ],
    '목표': [
        '강의의 목표, 과정, 참여 방법', '역사논문 작성법 발제<br>작성법에 관한 의견 교환', '졸업논문의 설계도 작성 (개인별)<br>교수자 및 수강자 동료의 피드백', '효과적인 연구사 노트 방법',
        '주제와 밀접한 연구사 정리 (1/2)', '주제와 밀접한 연구사 정리 (2/2)', '효과적인 사료 노트 방법', '주제와 밀접한 1차 사료 (1/2)', '주제와 밀접한 1차 사료 (2/2)',
        '논문 초고의 개요 작성', '논문 초고 작성 (1/2)', '논문 초고 작성 (2/2)', '완고 발표 & 피드백 (1/3)', '완고 발표 & 피드백 (2/3)', '완고 발표 & 피드백 (3/3)'
    ],
    '과제 제출<br>(일자정, etc)': ['-', '제출(일부)', '<font color="blue">제출(전원)</font>', '<font color="blue">제출(전원)</font>', '제출(1/2)', '제출(2/2)', '<font color="blue">제출(전원)</font>', '제출(1/2)', '제출(2/2)', '<font color="blue">제출(전원)</font>', '제출(1/2)', '제출(2/2)', '제출(1/3)', '제출(2/3)', '제출(3/3)'],
    '수업 발표': ['강의', '발표(일부)', '<font color="blue">발표(전원)</font>', '<font color="blue">발표(전원)</font>', '발표(일부)', '발표(일부)', '<font color="blue">발표(전원)</font>', '발표(일부)', '발표(일부)', '<font color="blue">발표(전원)</font>', '발표(일부)', '발표(일부)', '발표(일부)', '발표(일부)', '발표(일부)'],
    '기타 과제<br>(확인서, etc)': ['-', '-', '-', '-', '-', '-', '<font color="blue">교수 면담(1)</font>', '-', '<font color="blue">글쓰기 지도(1)</font>', '-', '<font color="blue">교수 면담(2)</font>', '-', '<font color="blue">글쓰기 지도(2)</font>', '-', '-']
}
df_schedule = pd.DataFrame(schedule_data)
row_spans = df_schedule['단계'].ne('').cumsum()
df_schedule['rowspan'] = row_spans.map(row_spans.value_counts())


# --- 구글 시트 데이터 로드 함수 ---
@st.cache_data(ttl=15)
def load_schedule_data(sheet_url):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_url(sheet_url)
        worksheet = spreadsheet.worksheet("발표일정") # 시트 이름
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.iloc[1:].reset_index(drop=True)
            if '순번' in df.columns:
                df['순번'] = pd.to_numeric(df['순번'], errors='coerce').astype('Int64')
        return df
    except Exception as e:
        return str(e)


# 'Q&A' 시트 로드 전용 함수
@st.cache_data(ttl=15)
def load_qna_data(sheet_url):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_url(sheet_url)
        worksheet = spreadsheet.worksheet("Questions")

        data = worksheet.get_all_records()
        # 데이터가 없을 경우, 올바른 헤더를 가진 빈 DataFrame 반환
        if not data:
            return pd.DataFrame(columns=["Timestamp", "Name", "Question", "Answer"])

        df = pd.DataFrame(data)
        # 만약을 위해 필수 컬럼이 모두 있는지 확인
        required_cols = ["Timestamp", "Name", "Question", "Answer"]
        if not all(col in df.columns for col in required_cols):
             return pd.DataFrame(columns=required_cols) # 헤더가 잘못된 경우
        return df
    except Exception as e:
        return str(e)


def save_question_to_gsheet(sheet_url, name, question):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_url(sheet_url)
        worksheet = spreadsheet.worksheet("Questions")

        # 시트의 첫 행을 읽어 헤더가 올바른지 확인
        header = worksheet.row_values(1) if worksheet.row_count > 0 else []
        if header != ["Timestamp", "Name", "Question", "Answer"]:
            # 헤더가 없거나 다를 경우, 시트가 비어있을 때만 헤더를 추가
            if not worksheet.get_all_values():
                worksheet.append_row(["Timestamp", "Name", "Question", "Answer"])

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, name, question, ""])
        return True
    except Exception as e:
        st.error(f"질문 저장 실패: {e}")
        return False


# --- 스타일이 적용된 HTML 테이블 생성 함수 (사용자님 내용 그대로 유지) ---
def generate_styled_html_table(df):
    table_css = """
    <style>
        .styled-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .styled-table th, .styled-table td { 
            border: 1px solid #ccc; padding: 10px; text-align: center; vertical-align: middle;
            word-break: keep-all; 
        }
        .styled-table th { font-weight: bold; }
        .header-row-1 th { height: 2.5em; padding: 5px; }
        .student-info-col { }
        .task-col { width: 4.5%; }
        .bg-blue { background-color: #dbe5f1 !important; }
        .bg-green { background-color: #e2efda !important; }
        .bg-pink { background-color: #f8cbad !important; }
        .bg-purple { background-color: #e8dff5 !important; }
    </style>
    """
    
    html = table_css + "<table class='styled-table'>"
    html += "<thead>"
    html += '<tr class="header-row-1">'
    html += '<th class="bg-blue student-info-col" rowspan="2">순번</th>'
    html += '<th class="bg-blue student-info-col" rowspan="2">학과</th>'
    html += '<th class="bg-blue student-info-col" rowspan="2">학번</th>'
    html += '<th class="bg-blue student-info-col" rowspan="2">성명</th>'
    html += '<th class="bg-green task-col">1</th><th class="bg-green task-col">2</th>'
    html += '<th class="bg-purple task-col">3</th>'
    html += '<th class="bg-purple task-col">4</th>'
    html += '<th class="bg-green task-col">5</th><th class="bg-green task-col">6</th>'
    html += '<th class="bg-purple task-col">7</th>'
    html += '<th class="bg-pink task-col bg-purple" rowspan="2">교수1</th>'
    html += '<th class="bg-green task-col">8</th><th class="bg-green task-col">9</th>'
    html += '<th class="bg-pink task-col bg-purple" rowspan="2">글쓰기1</th>'
    html += '<th class="bg-purple task-col">10</th>'
    html += '<th class="bg-green task-col">11</th>'
    html += '<th class="bg-pink task-col bg-purple" rowspan="2">교수2</th>'
    html += '<th class="bg-green task-col">12</th><th class="bg-green task-col">13</th>'
    html += '<th class="bg-pink task-col bg-purple" rowspan="2">글쓰기2</th>'
    html += '<th class="bg-green task-col">14</th><th class="bg-green task-col">15</th>'
    html += "</tr>"
    html += "<tr>"
    headers_row2 = { "강의 소개": "강의<br>소개", "논문 작성": "논문<br>작성", "연구 계획서": "연구<br>계획서", "논문 요약": "논문<br>요약", "연구사": "연구사", "1차 사료": "1차<br>사료", "사료 노트": "사료<br>노트", "초고 개요": "초고<br>개요", "초고 작성": "초고<br>작성", "완고 발표": "완고<br>발표" }
    html += f'<th class="bg-green task-col">{headers_row2["강의 소개"]}</th><th class="bg-green task-col">{headers_row2["논문 작성"]}</th>'
    html += f'<th class="bg-purple task-col">{headers_row2["연구 계획서"]}</th>'
    html += f'<th class="bg-purple task-col">{headers_row2["논문 요약"]}</th>'
    html += f'<th class="bg-green task-col">{headers_row2["연구사"]}</th><th class="bg-green task-col">{headers_row2["연구사"]}</th>'
    html += f'<th class="bg-purple task-col">{headers_row2["1차 사료"]}</th>'
    html += f'<th class="bg-green task-col">{headers_row2["사료 노트"]}</th><th class="bg-green task-col">{headers_row2["사료 노트"]}</th>'
    html += f'<th class="bg-purple task-col">{headers_row2["초고 개요"]}</th>'
    html += f'<th class="bg-green task-col">{headers_row2["초고 작성"]}</th><th class="bg-green task-col">{headers_row2["초고 작성"]}</th>'
    html += f'<th class="bg-green task-col">{headers_row2["완고 발표"]}</th><th class="bg-green task-col">{headers_row2["완고 발표"]}</th>'
    html += f'<th class="bg-green task-col">{headers_row2["완고 발표"]}</th>'
    html += "</tr></thead>"
    purple_cols_indices = [6, 7, 10, 11, 14, 15, 17, 20] 
    html += "<tbody>"
    for _, row in df.iterrows():
        html += "<tr>"
        seq_num = str(row.get('순번', '')) if pd.notna(row.get('순번')) else ''
        html += f'<td class="bg-blue student-info-col">{seq_num}</td>'
        html += f'<td class="bg-blue student-info-col">{row.get("학과", "")}</td>'
        html += f'<td class="bg-blue student-info-col">{row.get("학번", "")}</td>'
        html += f'<td class="bg-blue student-info-col">{row.get("성명", "")}</td>'
        for i, col_name in enumerate(df.columns[4:], 4):
            cell_class = "bg-purple" if i in purple_cols_indices else ""
            html += f"<td class='task-col {cell_class}'>{row.get(col_name, '')}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


# --------------------
# 웹앱 UI 구성 (사용자님 내용 그대로 유지)
# --------------------
st.title(f"🎓 {COURSE_TITLE}")
st.markdown("---")

tab1, tab2, tab5, tab3, tab4 = st.tabs([ "**강의 소개**", "**주차별 강의**", "**📢 실시간 발표 일정**", "**자료실**", "**Q&A**" ])

with tab1:
    st.header("📋 강의 소개")
    st.markdown(f"""
    - **과목명:** {COURSE_TITLE} ({COURSE_CODE})
    - **담당교수:** {PROFESSOR_NAME} ({PROFESSOR_EMAIL})
    - **강의시간:** {DAY_TIME}
    - **강의장소:** {CLASSROOM}
    - **강의 목표:** 
        1. 역사학 논문 쓰기를 단계별로 진행한다.  
        2. 연구계획 수립부터 연구사 정리, 사료 정리, 초고 작성, 논문 형식 준수 등 논문 쓰기의 기본을 익힌다.  
        3. 자신의 연구 주제에 관하여 동료 수강생들과 원활하게 의사 소통한다.  
    - **평가 방법:** 출석(10%), 과제(60%), 최종 연구계획서(30%)
    """)

# --- Tab 2: 주차별 강의 (디자인 개선) ---
with tab2:
    st.header("🗓️ 주차별 강의 계획")

    table_css = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            border: 2px solid #333;
        }
        th {
            background-color: #f2f2f2;
            text-align: center;
            font-weight: bold;
            border: 1px solid #333;
            padding: 8px;
        }
        td {
            border: 1px solid #333;
            padding: 8px;
            text-align: left;
            vertical-align: middle;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
    </style>
    """
    st.markdown(table_css, unsafe_allow_html=True)

    header_html = "<tr>"
    for col in df_schedule.columns:
        if col != 'rowspan':
            header_html += f"<th>{col}</th>"
    header_html += "</tr>"

    body_html = ""
    for index, row in df_schedule.iterrows():
        body_html += "<tr>"
        
        if row['단계'] != '':
            body_html += f"<td rowspan='{row['rowspan']}'>{row['단계']}</td>"
        
        for col in df_schedule.columns:
            if col not in ['단계', 'rowspan']:
                cell_value = row[col]
                if col == '일자' and cell_value == '10.07':
                    body_html += f'<td><font color="red">{cell_value}</font></td>'
                else:
                    body_html += f"<td>{cell_value}</td>"

        body_html += "</tr>"

    full_html = f"<table><thead>{header_html}</thead><tbody>{body_html}</tbody></table>"
    st.markdown(full_html, unsafe_allow_html=True)

with tab5:
    st.header("📢 실시간 발표 일정")
    st.info("이곳의 내용은 구글 시트와 실시간으로 연동됩니다.")
    my_sheet_url = "https://docs.google.com/spreadsheets/d/16dMmgZc9-R-dbW6WrdXBdCAH21AknJJcRmRC54u8CLQ/edit?gid=1293592544#gid=1293592544"
    result = load_schedule_data(my_sheet_url)
    if isinstance(result, pd.DataFrame) and not result.empty:
        df = result.copy()
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            sort_column = st.selectbox("**정렬 기준 선택**", options=['정렬 안함', '순번', '성명'], index=0)
        with col2:
            sort_order = st.radio("**정렬 순서**", options=['오름차순', '내림차순'], horizontal=True)
        if sort_column != '정렬 안함':
            is_ascending = (sort_order == '오름차순')
            df.sort_values(by=sort_column, ascending=is_ascending, inplace=True, na_position='last')
        html_table = generate_styled_html_table(df)
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.error("구글 시트를 불러오는 데 실패했거나 시트가 비어있습니다.")
        st.warning("URL, 공유 설정, 시트 이름을 다시 확인해주세요.")
        if not isinstance(result, pd.DataFrame):
            st.error(f"상세 에러: {result}")

with tab3:
    st.header("📚 강의 자료실")
    st.markdown("수업 관련 참고 자료나 과제 파일을 이곳에 업로드합니다.")
    st.subheader("주 교재 및 관련 정보")

    # 열 설정
    col1, col2 = st.columns(2)

    with col1:
        # 1단계에서 images 폴더에 넣은 첫 번째 이미지 파일을 불러옵니다.
        # "images/book1.jpg"는 실제 파일 이름에 맞게 수정해주세요.
        st.image("images/역사논문작성법_표지.jpg", caption="주교재: 역사논문 작성법")
        st.markdown("- [역사논문 작성법 (임경석 저, 푸른역사, 2023)](https://snu-primo.hosted.exlibrisgroup.com/primo-explore/fulldisplay?vid=82SNU&search_scope=ALL&docid=82SNU_INST21901566720002591&lang=ko_KR)")

    with col2:
        # 1단계에서 images 폴더에 넣은 두 번째 이미지 파일을 불러옵니다.
        # "images/book2.png"는 실제 파일 이름에 맞게 수정해주세요.
        st.markdown("- [역사논문 작성법 - 블로그 (Eastone / chdi07)](https://blog.naver.com/chdi07/223226944519)")

with tab4:
    st.header("🙋 질의응답 (Q&A)")
    st.info("강의 내용에 대해 궁금한 점을 자유롭게 질문하세요. 제출된 질문은 아래 목록에 나타납니다.")
    qna_sheet_url = "https://docs.google.com/spreadsheets/d/1Z7pzDbXWjQ0vZnz9sWI0ln6zUtAqWaENKCQxGACrQtU/edit?usp=sharing"
    with st.form("question_form", clear_on_submit=True):
        student_name = st.text_input("이름 (선택사항, 익명으로 제출 시 비워두세요)")
        question_text = st.text_area("질문 내용 (필수)")
        submitted = st.form_submit_button("질문 제출하기")
        if submitted:
            if not question_text:
                st.warning("질문 내용을 입력해주세요!")
            else:
                name_to_save = student_name if student_name else "익명"
                success = save_question_to_gsheet(qna_sheet_url, name_to_save, question_text)
                if success:
                    st.success("질문이 성공적으로 제출되었습니다! 아래 목록에서 확인하세요.")
                    st.cache_data.clear()
    st.markdown("---")
    st.header("📜 제출된 질문 목록")
    qna_result = load_qna_data(qna_sheet_url)
    if isinstance(qna_result, pd.DataFrame) and not qna_result.empty:
        qna_result = qna_result.sort_index(ascending=False)
        for index, row in qna_result.iterrows():
            with st.expander(f"**Q: {row['Question']}** (작성자: {row['Name']}, 시간: {row['Timestamp']})"):
                if row['Answer']:
                    st.markdown(f"**A:** {row['Answer']}")
                else:
                    st.info("아직 답변이 등록되지 않았습니다.")
    else:
        st.success("아직 제출된 질문이 없습니다. 첫 번째 질문을 남겨보세요!")

