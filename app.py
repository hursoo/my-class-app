import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime # <-- 이 부분이 추가되었습니다.
from pathlib import Path
SA_PATH = Path(__file__).parent / ".streamlit" / "clever-circlet-237312-ba0859893ad2.json"


# === 추가: GSheetsConnection 사용 가능하면 먼저 시도 ===
try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS_CONN = True
except Exception:
    HAS_GSHEETS_CONN = False


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


# --- 공용: 시트 읽기 (GSheetsConnection 우선, 실패 시 gspread로 폴백) ---
@st.cache_data(ttl=15)
def read_sheet_df(sheet_url: str, worksheet: str):
    errors = []

    # 1) streamlit_gsheets 우선 시도 (secrets에 [connections.gsheets]가 있을 때)
    if HAS_GSHEETS_CONN and "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        try:
            conn: GSheetsConnection = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(spreadsheet=sheet_url, worksheet=worksheet, ttl=5)
            if isinstance(df, pd.DataFrame):
                return df
        except Exception as e:
            errors.append(f"GSheetsConnection 실패: {e}")

    # 2) gspread 서비스 계정 폴백 (secrets에 [gcp_service_account]가 있을 때)
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = st.secrets["gcp_service_account"]  # 없으면 KeyError
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        ws = gc.open_by_url(sheet_url).worksheet(worksheet)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        errors.append(f"gspread 실패: {e}")
        return " | ".join(errors)

@st.cache_data(ttl=15)
def load_schedule_data(sheet_url):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        # JSON 파일에서 바로 로드 (복붙/개행 이슈 없음)
        creds = Credentials.from_service_account_file(str(SA_PATH), scopes=scopes)
        gc = gspread.authorize(creds)

        ws = gc.open_by_url(sheet_url).worksheet("발표일정")  # 시트 탭 이름
        data = ws.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty:
            # 1행이 안내/머릿글인 경우 한 줄 내림(필요한 경우에만)
            if len(df) > 0 and (df.iloc[0].astype(str) == df.columns).any():
                df = df.iloc[1:].reset_index(drop=True)
            if '순번' in df.columns:
                df['순번'] = pd.to_numeric(df['순번'], errors='coerce').astype('Int64')
        return df
    except Exception as e:
        return str(e)
    


@st.cache_data(ttl=15)
def load_qna_data(sheet_url):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(str(SA_PATH), scopes=scopes)
        gc = gspread.authorize(creds)

        ws = gc.open_by_url(sheet_url).worksheet("Questions")
        data = ws.get_all_records()
        required = ["Timestamp", "Name", "Question", "Answer"]
        if not data:
            return pd.DataFrame(columns=required)
        df = pd.DataFrame(data)
        if not all(c in df.columns for c in required):
            return pd.DataFrame(columns=required)
        return df
    except Exception as e:
        return str(e)

    

def save_question_to_gsheet(sheet_url, name, question):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(str(SA_PATH), scopes=scopes)
        gc = gspread.authorize(creds)

        ws = gc.open_by_url(sheet_url).worksheet("Questions")
        # 완전 빈 시트일 때만 헤더 생성
        header = ws.row_values(1) if ws.row_count > 0 else []
        if header != ["Timestamp", "Name", "Question", "Answer"]:
            if not ws.get_all_values():
                ws.append_row(["Timestamp", "Name", "Question", "Answer"])

        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([ts, name, question, ""])
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
    - **강의 방식:** 개인별 프로젝트 수행
    - **평가 방법:** 출석(10%), 과제(60%), 최종 연구계획서(30%)
        1. 출석: 수업일수의 1/3을 초과하여 결석하면 성적은 "F" 또는 "U"가 됨  
           (담당교수가 불가피한 결석으로 인정하는 경우는 예외로 할 수 있음)
        2. 과제: 
            - 프로젝트 단계별 수행 여부를 최우선시 함. 
            - 최초에 개인별로 60점을 부여 -> 단계별로 감정 요건 기준에 해당하면 정해진 점수만큼 감점.
        3. 최종 연구계획서: 평가기준에 따라 질적 평가""")
    

    st.markdown("---")
    st.subheader("⚠️ 감점 기준표")

    # 평가표를 위한 HTML 및 CSS 코드 (수정된 부분)
    grading_table_html = """
    <style>
        .grading-table {
            /* 이 부분을 60%로 수정하고, 가운데 정렬을 추가합니다 */
            width: 60%;
            margin: 0 auto; 
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 0.95em;
        }
        .grading-table th, .grading-table td {
            border: 1px solid #cccccc;
            padding: 10px;
            text-align: center;
            vertical-align: middle;
        }
        .grading-table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .grading-table td.left-align {
            text-align: left;
        }
    </style>
    <table class="grading-table">
        <thead>
            <tr>
                <th>항목</th>
                <th>감점 요건</th>
                <th>감점 점수</th>
                <th>감점 요건 기준</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>발표</b></td>
                <td>불이행</td>
                <td>-5</td>
                <td class="left-align">정해진 날짜 발표 펑크</td>
            </tr>
            <tr>
                <td><b>면담</b></td>
                <td>불이행</td>
                <td>-5</td>
                <td class="left-align">교수 날인 한 면담지 기한 내 미제출</td>
            </tr>
            <tr>
                <td><b>글쓰기</b></td>
                <td>기한 내 불이행</td>
                <td>-5</td>
                <td class="left-align">글쓰기 지도 받은 기록 기한 내 미제출</td>
            </tr>
            <tr>
                <td rowspan="3"><b>제출</b></td>
                <td>미제출</td>
                <td>-4</td>
                <td class="left-align">수업 시간까지 미제출</td>
            </tr>
            <tr>
                <td>지각</td>
                <td>-2</td>
                <td class="left-align">마감 기한 내 미제출</td>
            </tr>
            <tr>
                <td>미비</td>
                <td>-1</td>
                <td class="left-align">형식 요건을 갖추지 못함</td>
            </tr>
            <tr>
                <td rowspan="2"><b>출결</b></td>
                <td>결석</td>
                <td>-1</td>
                <td class="left-align">유계 결석은 제외</td>
            </tr>
            <tr>
                <td>지각</td>
                <td>-0.3</td>
                <td class="left-align">출석 전체 호명 종료 후 출석</td>
            </tr>
            <tr>
                <td rowspan="4"><b>기말</b></td>
                <td>미제출</td>
                <td>F</td>
                <td class="left-align">성적 마감일까지 제출하지 않은 경우</td>
            </tr>
            <tr>
                <td>지각제출</td>
                <td>-15</td>
                <td class="left-align">기한 후 제출한 경우</td>
            </tr>
            <tr>
                <td>형식 미비</td>
                <td>-10 ~ -5</td>
                <td class="left-align">주요 항목 최소 1가지 이상 누락 혹은 정해진 규격 기준 분량이 1/2 미만</td>
            </tr>
            <tr>
                <td>내용 미흡</td>
                <td>-10 ~ -5</td>
                <td class="left-align">인용 윤리 위반 / 챗지피티 무단 활용 등</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(grading_table_html, unsafe_allow_html=True)
 


# --- Tab 2: 주차별 강의 (세부강의일정 임베드 + 캐시버스터) ---
with tab2:
    st.header("🗓️ 주차별 강의 계획")
    st.info("구글 시트 '세부강의일정'을 '웹에 게시(Publish to the web)' 링크로 임베드합니다. 새로고침 버튼은 캐시를 우회합니다.")

    # 1) '웹에 게시'에서 복사한 iframe의 src를 여기에 붙여넣으세요.
    DETAIL_EMBED_SRC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR-7ESO9FAkuSbxl0BbqFvtIyVnVi_Rhk7lW2Nf54jQV90p2IaHk_OijM2eSy3R-nLYSSAs3_X7YUQM/pubhtml?gid=0&amp;single=true&amp;widget=true&amp;headers=false"
    #    ↑ 반드시 /d/e/.../pubhtml?... 형태여야 하며, 편집 URL(/edit...)은 안 됩니다.

    # 2) HTML 엔티티 정리 (&amp; → &)
    DETAIL_EMBED_SRC = DETAIL_EMBED_SRC.replace("&amp;", "&")

    # 3) 높이 지정(필요하면 조절)
    h = st.slider("임베드 창 높이", min_value=600, max_value=1200, value=900, step=50)

    # 4) 캐시버스터용 nonce (세션 상태)
    if "detail_nonce" not in st.session_state:
        st.session_state.detail_nonce = 0

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 새로고침", help="URL 뒤에 nonce를 붙여 강제 재로딩합니다."):
            st.session_state.detail_nonce += 1
    with col2:
        st.link_button("🗗 새 창에서 열기", DETAIL_EMBED_SRC)

    # 5) 매번 다른 쿼리로 강제 리로드 (클라이언트 캐시 우회)
    src = f"{DETAIL_EMBED_SRC}&t={st.session_state.detail_nonce}"
    st.components.v1.iframe(src, height=h, scrolling=True)


def force_rerun():
    """Streamlit 버전에 맞춰 안전하게 rerun."""
    try:
        import streamlit as st  # 이미 있음
        st.rerun()  # 신버전
    except AttributeError:
        # 구버전 호환 (있을 때만 실행)
        try:
            st.experimental_rerun()
        except Exception:
            pass



# --- Tab 5: 실시간 발표 일정 (임베드 + 캐시버스터) ---
with tab5:
    st.header("📢 실시간 발표 일정")
    st.info("구글 시트 ‘발표일정’을 '웹에 게시' 링크로 임베드합니다. (원본 스타일, 약간의 반영 지연 가능)")

    # '웹에 게시' → iframe 코드의 src를 그대로 붙여넣으세요.
    LIVE_EMBED_SRC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR-7ESO9FAkuSbxl0BbqFvtIyVnVi_Rhk7lW2Nf54jQV90p2IaHk_OijM2eSy3R-nLYSSAs3_X7YUQM/pubhtml?gid=1293592544&amp;single=true&amp;widget=true&amp;headers=false"
    LIVE_EMBED_SRC = LIVE_EMBED_SRC.replace("&amp;", "&")  # &amp; → &

    if "live_nonce" not in st.session_state:
        st.session_state.live_nonce = 0
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🔄 새로고침(임베드)"):
            st.session_state.live_nonce += 1   # 캐시버스터
    with colB:
        st.link_button("🗗 새 창에서 열기", LIVE_EMBED_SRC)

    src = f"{LIVE_EMBED_SRC}&t={st.session_state.live_nonce}"
    st.components.v1.iframe(src, height=900, scrolling=True)





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

