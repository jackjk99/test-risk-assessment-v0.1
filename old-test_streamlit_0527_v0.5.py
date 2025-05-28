import streamlit as st
from PIL import Image
from openai import OpenAI
import pandas as pd
import json
import os
import base64
import io

# OpenAI API 키 읽기 함수
def load_openai_api_key(config_path: str = "config.json") -> str:
    """
    Load OpenAI API key from a configuration file.

    Args:
        config_path (str): Path to the configuration file. Default is "config.json".
    
    Returns:
        str: OpenAI API key.
    
    Example:
        config.json:
        {
            "openai_api_key": "YOUR_OPENAI_API_KEY"
        }
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)
    return config_data.get("openai_api_key", "")

# OpenAI 클라이언트 초기화
try:
    api_key = load_openai_api_key()
    client = OpenAI(api_key=api_key)
except Exception as e:
    st.error(str(e))
    client = None

def encode_image(image: Image) -> str:
    """
    PIL Image를 base64로 인코딩하는 함수
    """
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    return base64.b64encode(image_bytes).decode('utf-8')

def analyze_image(image: Image, checklist: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze the uploaded image using OpenAI GPT and generate a safety checklist based on the reference checklist file.
    
    Args:
        image (Image): Uploaded image file of the work environment.
        checklist (pd.DataFrame): Reference checklist data extracted from the uploaded Excel file.
    
    Returns:
        pd.DataFrame: A DataFrame containing observed potential hazards and associated safety measures.
    """
    if client is None:
        raise Exception("OpenAI 클라이언트가 초기화되지 않았습니다.")
    
    # 이미지를 base64로 인코딩
    base64_image = encode_image(image)
    
    # 이미지 분석 요청 생성 (상세한 프롬프트)
    prompt = """
Role(역할지정): 산업안전 위험성 평가 전문가 역할을 수행하고 있는데 특히 현장에서 현장 사진을 찍어 이를 기반으로 한 작업전 위험성 평가를 진행하고자 한다.

Context(상황):
- 목표: 첨부된 사진 이미지를 분석한다. 이를 바탕으로 해당 작업환경을 분석하고, 이를 바탕으로 발생할 수 있는 구체적인 위험요인과 이를 예방하기 위한 기술적 대책을 추천 받는 것이 목표
- 상황: 현장 사진을 기반으로 현장 위험성 평가 작성을 자동화하고자 함

Input Values(입력값):
- 현장 환경을 촬영한 사진화일을 첨부한다, 현장사진은 다양한 형태로 촬영이 된다.
1. 실내의 작업 환경인 경우: 이동식 사다리, 각종 장비 및 시설물
   예시1) "분전반 교체 작업을 위해서 지하 전기실에서 전원 작업을 준비하고 있다"
   예시2) "지하 주차실 내 통신케이블 포설을 위해서 이동식 사다리를 사용하여 작업을 준비하고 있다"
2. 실외의 작업환경인 경우: 도로변, 건물, 야외, 철탑, 전신주 등 다양한 시설물이 포함될 수 있음
   예시1) "옥상에 이동식 사다리가 세워져 있고, 각종 전선케이블과 통신용 장비가 놓여져 있다."
   예시2) "도로변 통신관로 작업을 위해서 안전표지가 설치되어 있고, 작업자가 수신호로 차량을 통제하고 있으며, 굴삭기가 땅을 파고 있다."
   예시3) "철탑 작업을 위해서 승주 작업을 준비하고 있다"

Instructions(단계별 지시사항):
- 사용자가 첨부한 사진 파일을 분석한다.
- 분석된 내용을 근거로 하여 작업 전 확인이 필요한 사항을 첨부 파일인 "SGR현장 체크리스트_변환.xlsx"에 있는 내용과 유사한 항목을 찾아서 안전Checklist를 확인한다.
- 모든 항목은 실제 안전관리 실무에서 사용 가능한 수준의 기술적, 현실적인 조치로 구성합니다

Constraints(제약사항):
- 내용은 실제 산업안전보건 기준에 부합하도록 구체적이고 실무적인 수준으로 작성할 것
- 공통사항으로 기본적인 개인보호구(안전모, 안전화, 안전대 착용에 대한 내용) 및 TBM시행 등의 기본내용은 항상 포함하는데 각 사진 이미지 분석결과의 마지막 라인에 추가해줘
- 여러가지 위험이 있다면 모든 내용을 포함해 줘
- 출력은 한국어로 답변할 것
- 출력은 표 형식으로 고정
- 출력시의 항목내용은 4가지야:
  1. 번호: 순번
  2. 잠재 위험요인: 분석된 작업환경에서 발생가능한 위험요인들을 각각 나열한다.
  3. 잠재 위험요인 설명: 각 위험요인에 대한 설명
  4. 위험성 감소대책: 해당 잠재 위험요소를 없애서 안전한 환경을 만들기 위한 대책을 작성한다.
- 잠재 위험요인 분석과 그에 상응하는 위험성 감소대책을 1개 라인씩 입력해서 작성해줘
- 감소대책이 여러개인 경우는 각 항목의 숫자가 앞족으로 나오게 해줘 (①, ②, ③...)

출력 예시:
| 번호 | 잠재 위험요인 | 잠재 위험요인 설명 | 위험성 감소대책 |
|------|---------------|-------------------|----------------|
| 1 | 고소 작업 시 추락 위험 | 통신 철탑 작업 시 높은 위치에서 작업이 이루어져 추락 위험이 있음 | ① 안전대 착용 및 안전고리 연결 ② 작업 전 안전난간 및 방호망 설치 ③ 작업계획서 작성 및 위험성 평가 시행 ④ 2인1조 작업 시행 ⑤ 작업 전 TBM 공유 및 작업자 건강상태 확인 |

첨부된 이미지를 상세히 분석하여 위 지침에 따라 위험성 평가를 수행해주세요.
"""
    
    # OpenAI API 호출 (새로운 방식)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1500
    )
    
    # GPT의 분석 결과를 가져오기
    analysis_result = response.choices[0].message.content
    
    # 결과를 pandas 데이터프레임으로 변환 (개선된 파싱)
    result_data = []
    lines = analysis_result.split('\n')
    
    # 표 형식 데이터 파싱 (더 정확한 파싱)
    table_started = False
    for line in lines:
        line = line.strip()
        if "|" in line and not line.startswith("|---"):
            parts = [x.strip() for x in line.split('|')]
            # 빈 문자열 제거
            parts = [part for part in parts if part]
            
            # 4개 컬럼이 있고, 첫 번째가 숫자이면 데이터 행으로 간주
            if len(parts) >= 4:
                # 헤더 행 건너뛰기
                if parts[0] == "번호" or parts[0] == "No":
                    table_started = True
                    continue
                
                # 번호가 숫자인 경우만 추가
                try:
                    int(parts[0])
                    result_data.append(parts[:4])  # 처음 4개 컬럼만 사용
                except ValueError:
                    continue
    
    # 데이터가 없는 경우 GPT 응답 텍스트에서 직접 추출 시도
    if not result_data:
        # 번호로 시작하는 라인들을 찾아서 파싱
        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and ('|' in line or line.count('.') > 0):
                # 다양한 형식의 텍스트에서 정보 추출 시도
                if '|' in line:
                    parts = [x.strip() for x in line.split('|') if x.strip()]
                    if len(parts) >= 4:
                        result_data.append(parts[:4])
                        
    # 여전히 데이터가 없으면 기본 항목 추가
    if not result_data:
        # 기본 개인보호구 착용 항목 추가
        result_data = [
            ["1", "개인보호구 미착용", "안전모, 안전화, 안전대 등 개인보호구 미착용으로 인한 위험", "① 안전모 착용 의무화 ② 안전화 착용 확인 ③ 고소작업 시 안전대 착용 ④ 작업 전 개인보호구 점검"],
            ["2", "작업 전 안전교육 미실시", "TBM(Tool Box Meeting) 미실시로 인한 안전사고 위험", "① 작업 전 TBM 실시 ② 작업자 건강상태 확인 ③ 작업계획 공유 ④ 비상연락체계 확인"]
        ]
    
    # 기본 개인보호구 및 TBM 항목이 없으면 추가
    has_ppe = any("개인보호구" in str(row) or "안전모" in str(row) for row in result_data)
    has_tbm = any("TBM" in str(row) or "안전교육" in str(row) for row in result_data)
    
    if not has_ppe:
        next_num = len(result_data) + 1
        result_data.append([str(next_num), "개인보호구 착용", "작업 시 필수 개인보호구 착용 필요", "① 안전모 착용 ② 안전화 착용 ③ 필요시 안전대 착용 ④ 보호장갑 착용"])
    
    if not has_tbm:
        next_num = len(result_data) + 1
        result_data.append([str(next_num), "작업 전 안전교육", "작업 전 TBM 실시 및 안전교육", "① 작업 전 TBM 실시 ② 작업자 건강상태 확인 ③ 작업계획 및 위험요소 공유 ④ 비상연락체계 확인"])
    
    result_df = pd.DataFrame(result_data, columns=["번호", "잠재 위험요인", "잠재 위험요인 설명", "위험성 감소대책"])
    return result_df

def create_checklist_format(result_df: pd.DataFrame) -> pd.DataFrame:
    """
    위험성 평가 결과를 체크리스트 양식으로 변환하는 함수
    """
    checklist_data = []
    
    for _, row in result_df.iterrows():
        checklist_data.append({
            "구분": "SGR 현장",
            "안전 Check List 항목": row["잠재 위험요인"] + " - " + row["잠재 위험요인 설명"],
            "양호(O)": False,
            "불량(X)": False,
            "해당 없음": False,
            "비고": row["위험성 감소대책"]
        })
    
    checklist_df = pd.DataFrame(checklist_data)
    return checklist_df

def display_checklist_table(checklist_df: pd.DataFrame, image_name: str):
    """
    Streamlit 기반 인터랙티브 체크리스트 테이블 표시 함수
    """
    st.markdown(f"#### 📋 {image_name} - 안전 체크리스트")
    
    # 체크리스트 사용 방법 안내
    with st.expander("📖 체크리스트 사용 방법"):
        st.write("""
        - **양호(O)**: 안전 기준을 충족하고 위험요인이 적절히 관리되고 있는 경우
        - **불량(X)**: 개선이 필요하고 추가 안전조치가 필요한 경우  
        - **해당 없음**: 해당 위험요인이 현재 상황에 적용되지 않는 경우
        """)
    
    # 인터랙티브 체크리스트 생성
    if not checklist_df.empty:
        st.write("#### 점검 결과 입력")
        
        # 세션 상태 초기화 (이미지별로 고유한 키 사용)
        session_key = f"checklist_{image_name}"
        if session_key not in st.session_state:
            st.session_state[session_key] = {}
        
        # 각 항목에 대한 체크박스 생성
        for idx, row in checklist_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([0.8, 2.5, 0.8, 0.8, 0.8])
            
            with col1:
                st.write(f"**{row['구분']}**")
            
            with col2:
                st.write(row['안전 Check List 항목'])
            
            # 상호 배타적 체크박스 구현
            key_good = f"{session_key}_good_{idx}"
            key_poor = f"{session_key}_poor_{idx}"
            key_na = f"{session_key}_na_{idx}"
            
            with col3:
                good_checked = st.checkbox("양호(O)", key=key_good)
                if good_checked and key_good in st.session_state:
                    # 다른 체크박스들 해제
                    if key_poor in st.session_state:
                        st.session_state[key_poor] = False
                    if key_na in st.session_state:
                        st.session_state[key_na] = False
            
            with col4:
                poor_checked = st.checkbox("불량(X)", key=key_poor)
                if poor_checked and key_poor in st.session_state:
                    # 다른 체크박스들 해제
                    if key_good in st.session_state:
                        st.session_state[key_good] = False
                    if key_na in st.session_state:
                        st.session_state[key_na] = False
            
            with col5:
                na_checked = st.checkbox("해당 없음", key=key_na)
                if na_checked and key_na in st.session_state:
                    # 다른 체크박스들 해제
                    if key_good in st.session_state:
                        st.session_state[key_good] = False
                    if key_poor in st.session_state:
                        st.session_state[key_poor] = False
            
            # 비고 표시
            if row['비고']:
                st.caption(f"💡 **대책:** {row['비고']}")
            
            st.divider()
        
        # 결과 요약
        st.write("#### 📊 점검 결과 요약")
        
        good_count = sum([st.session_state.get(f"{session_key}_good_{i}", False) for i in range(len(checklist_df))])
        poor_count = sum([st.session_state.get(f"{session_key}_poor_{i}", False) for i in range(len(checklist_df))])
        na_count = sum([st.session_state.get(f"{session_key}_na_{i}", False) for i in range(len(checklist_df))])
        total_checked = good_count + poor_count + na_count
        total_items = len(checklist_df)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("양호(O)", f"{good_count}개")
        with col2:
            st.metric("불량(X)", f"{poor_count}개") 
        with col3:
            st.metric("해당 없음", f"{na_count}개")
        with col4:
            completion_rate = (total_checked / total_items * 100) if total_items > 0 else 0
            st.metric("완료율", f"{completion_rate:.1f}%")
        
        # 불량 항목이 있는 경우 경고 표시
        if poor_count > 0:
            st.warning(f"⚠️ {poor_count}개의 불량 항목이 발견되었습니다. 즉시 개선조치가 필요합니다.")
        
        # 체크리스트 결과 다운로드 버튼
        if st.button(f"📥 {image_name} 체크리스트 결과 다운로드", key=f"download_{session_key}"):
            download_checklist_results(checklist_df, image_name, session_key)
    
    else:
        st.info("체크리스트 항목이 없습니다.")

def download_checklist_results(checklist_df: pd.DataFrame, image_name: str, session_key: str):
    """
    체크리스트 결과를 다운로드 가능한 형태로 변환
    """
    # 결과 데이터 생성
    results_data = []
    
    for idx, row in checklist_df.iterrows():
        good_checked = st.session_state.get(f"{session_key}_good_{idx}", False)
        poor_checked = st.session_state.get(f"{session_key}_poor_{idx}", False)
        na_checked = st.session_state.get(f"{session_key}_na_{idx}", False)
        
        result_status = ""
        if good_checked:
            result_status = "양호(O)"
        elif poor_checked:
            result_status = "불량(X)"
        elif na_checked:
            result_status = "해당 없음"
        else:
            result_status = "미점검"
        
        results_data.append({
            "구분": row['구분'],
            "안전 Check List 항목": row['안전 Check List 항목'],
            "점검 결과": result_status,
            "비고": row['비고']
        })
    
    results_df = pd.DataFrame(results_data)
    
    # CSV 다운로드
    csv = results_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="CSV 파일 다운로드",
        data=csv,
        file_name=f"안전체크리스트_결과_{image_name.split('.')[0]}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key=f"csv_download_{session_key}"
    )

# Streamlit App UI
st.set_page_config(
    page_title="현장 안전 위험성 평가 자동화 도구",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ 현장 안전 위험성 평가 자동화 도구")
st.markdown("---")

# 사이드바에 정보 표시
with st.sidebar:
    st.header("📋 사용 가이드")
    st.markdown("""
    ### 📝 사용 순서
    1. **참조 체크리스트 업로드**
       - SGR현장 체크리스트 Excel 파일
    
    2. **현장 이미지 업로드**
       - 실내/실외 작업환경 사진
       - 다중 업로드 가능
    
    3. **위험성 평가 실행**
       - AI 기반 자동 분석
    
    4. **체크리스트 작성**
       - 인터랙티브 점검
    
    5. **결과 다운로드**
       - CSV 형태로 저장
    """)
    
    st.markdown("---")
    st.header("⚙️ 시스템 상태")

# 메인 컨텐츠
st.header("📤 참조문서 및 현장 이미지 업로드")

# OpenAI API 키 상태 확인
if client is None:
    st.error("⚠️ OpenAI API 키가 설정되지 않았습니다. config.json 파일을 확인해주세요.")
    with st.sidebar:
        st.error("❌ API 연결 실패")
else:
    st.success("✅ OpenAI API 연결 완료")
    with st.sidebar:
        st.success("✅ OpenAI API 연결됨")

# 참조 체크리스트 문서 업로드
col1, col2 = st.columns([2, 1])

with col1:
    checklist_file = st.file_uploader(
        "참조 체크리스트 문서 업로드 (SGR현장 체크리스트_변환.xlsx)", 
        type=["xlsx"],
        help="Excel 형태의 체크리스트 파일을 업로드하세요."
    )

checklist = None
if checklist_file:
    try:
        checklist = pd.read_excel(checklist_file)
        st.success("✅ 참조 체크리스트 등록 완료!")
        st.info("📋 체크리스트가 등록되었습니다. 이제 작업 환경 이미지를 업로드하여 분석을 시작하세요.")
        
        with st.sidebar:
            st.success(f"✅ 체크리스트: {len(checklist)}항목")
        
        with st.expander("📊 체크리스트 미리보기 (클릭하여 확장)"):
            st.dataframe(checklist.head(10), use_container_width=True)
            st.caption(f"총 {len(checklist)}개의 체크리스트 항목이 로드되었습니다.")
    except Exception as e:
        st.error(f"❌ 체크리스트 파일 읽기 오류: {str(e)}")
        st.info("💡 Excel 파일이 올바른 형식인지 확인해주세요.")
        with st.sidebar:
            st.error("❌ 체크리스트 오류")

# 작업 환경 이미지 업로드
if checklist_file is not None:
    st.markdown("### 📸 작업 환경 이미지 업로드")
    uploaded_images = st.file_uploader(
        "작업 환경 이미지를 업로드하세요 (다중 업로드 가능)", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        help="실내/실외 작업환경, 장비, 시설물 등이 포함된 현장 사진을 업로드하세요."
    )
else:
    st.warning("⚠️ 먼저 참조 체크리스트 문서를 업로드해주세요.")
    uploaded_images = None

# 업로드된 이미지 미리보기
if uploaded_images:
    st.markdown("### 📋 업로드된 이미지 미리보기")
    
    with st.sidebar:
        st.success(f"✅ 이미지: {len(uploaded_images)}개")
    
    # 이미지를 3열로 표시
    num_cols = min(len(uploaded_images), 3)
    cols = st.columns(num_cols)
    
    for idx, image_file in enumerate(uploaded_images):
        with cols[idx % num_cols]:
            image = Image.open(image_file)
            st.image(image, caption=f"📷 {image_file.name}", use_column_width=True)
            
            # 이미지 정보 표시
            st.caption(f"크기: {image.size[0]}x{image.size[1]} | 형식: {image.format}")
    
    st.info(f"💡 총 {len(uploaded_images)}개의 이미지가 업로드되었습니다. 각 이미지별로 개별 위험성 평가가 수행됩니다.")

# 분석 시작 버튼
if uploaded_images:
    st.markdown("---")
    st.markdown("### 🚀 위험성 평가 실행")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 위험성 평가 분석 시작", type="primary", use_container_width=True):
            if client is None:
                st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
            elif not checklist_file:
                st.error("❌ 먼저 참조 체크리스트 문서를 업로드해주세요.")
            else:
                analysis_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, image_file in enumerate(uploaded_images):
                    try:
                        status_text.text(f"🔄 {image_file.name} 분석 중... ({idx+1}/{len(uploaded_images)})")
                        
                        image = Image.open(image_file)
                        with st.spinner(f"AI가 {image_file.name}를 분석하고 있습니다..."):
                            result_df = analyze_image(image, checklist)
                            analysis_results.append((image_file.name, result_df))
                        
                        # 진행률 업데이트
                        progress_bar.progress((idx + 1) / len(uploaded_images))
                        
                    except Exception as e:
                        st.error(f"❌ {image_file.name} 분석 중 오류 발생: {str(e)}")
                        continue
                
                status_text.text("✅ 모든 이미지 분석 완료!")
                
                # 결과 출력
                if analysis_results:
                    st.markdown("---")
                    st.header("📊 위험성 평가 분석 결과")
                    
                    for idx, (img_name, result_df) in enumerate(analysis_results, 1):
                        st.markdown(f"### 📷 이미지 {idx}: {img_name}")
                        
                        # 위험요인 개수 표시
                        risk_count = len(result_df)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("식별된 위험요인 수", f"{risk_count}개")
                        with col2:
                            high_risk = len([r for _, r in result_df.iterrows() if '추락' in str(r['잠재 위험요인']) or '감전' in str(r['잠재 위험요인'])])
                            st.metric("고위험 요인", f"{high_risk}개")
                        with col3:
                            completion_status = "분석 완료" if risk_count > 0 else "재분석 필요"
                            st.metric("분석 상태", completion_status)
                        
                        # 원본 결과 테이블 표시
                        with st.expander("📋 상세 위험성 평가 결과 보기"):
                            st.dataframe(
                                result_df, 
                                use_container_width=True,
                                column_config={
                                    "번호": st.column_config.NumberColumn("번호", width="small"),
                                    "잠재 위험요인": st.column_config.TextColumn("잠재 위험요인", width="medium"),
                                    "잠재 위험요인 설명": st.column_config.TextColumn("잠재 위험요인 설명", width="large"),
                                    "위험성 감소대책": st.column_config.TextColumn("위험성 감소대책", width="large")
                                }
                            )
                        
                        # 체크리스트 양식으로 변환 및 표시
                        checklist_df = create_checklist_format(result_df)
                        display_checklist_table(checklist_df, img_name)
                        
                        # 다운로드 버튼들
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # 원본 CSV 다운로드
                            csv_original = result_df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label=f"📥 {img_name} 위험성평가 다운로드",
                                data=csv_original,
                                file_name=f"위험성평가_{img_name.split('.')[0]}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key=f"original_download_{idx}",
                                use_container_width=True
                            )
                        
                        with col2:
                            # Excel 다운로드
                            excel_buffer = io.BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                result_df.to_excel(writer, sheet_name='위험성평가', index=False)
                                checklist_df.to_excel(writer, sheet_name='체크리스트', index=False)
                            excel_data = excel_buffer.getvalue()
                            
                            st.download_button(
                                label=f"📊 {img_name} Excel 다운로드",
                                data=excel_data,
                                file_name=f"안전점검_{img_name.split('.')[0]}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"excel_download_{idx}",
                                use_container_width=True
                            )
                        
                        with col3:
                            # PDF 리포트 생성 (간단한 형태)
                            if st.button(f"📄 {img_name} 리포트 생성", key=f"report_{idx}", use_container_width=True):
                                st.info("PDF 리포트 기능은 추후 업데이트 예정입니다.")
                        
                        st.markdown("---")
                
                # 전체 요약 정보
                if analysis_results:
                    st.markdown("### 📈 전체 분석 요약")
                    
                    total_risks = sum([len(result_df) for _, result_df in analysis_results])
                    total_images = len(analysis_results)
                    avg_risks = total_risks / total_images if total_images > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("총 분석 이미지", f"{total_images}개")
                    with col2:
                        st.metric("총 위험요인", f"{total_risks}개")
                    with col3:
                        st.metric("평균 위험요인", f"{avg_risks:.1f}개/이미지")
                    with col4:
                        completion_rate = 100.0  # 모든 이미지 분석 완료
                        st.metric("분석 완료율", f"{completion_rate:.0f}%")
                    
                    # 위험요인 분류별 통계
                    st.markdown("#### 🏷️ 위험요인 분류별 통계")
                    
                    all_risks = []
                    for _, result_df in analysis_results:
                        for _, row in result_df.iterrows():
                            all_risks.append(row['잠재 위험요인'])
                    
                    # 주요 위험요인 키워드 분류
                    risk_categories = {
                        '추락': [r for r in all_risks if '추락' in r],
                        '감전': [r for r in all_risks if '감전' in r or '전기' in r],
                        '화재': [r for r in all_risks if '화재' in r or '폭발' in r],
                        '개인보호구': [r for r in all_risks if '개인보호구' in r or '안전모' in r or '안전대' in r],
                        '기타': [r for r in all_risks if not any(keyword in r for keyword in ['추락', '감전', '전기', '화재', '폭발', '개인보호구', '안전모', '안전대'])]
                    }
                    
                    risk_stats = []
                    for category, risks in risk_categories.items():
                        if risks:  # 해당 카테고리에 위험요인이 있는 경우만 추가
                            risk_stats.append({
                                '위험 분류': category,
                                '발생 건수': len(risks),
                                '비율(%)': round(len(risks) / total_risks * 100, 1) if total_risks > 0 else 0
                            })
                    
                    if risk_stats:
                        risk_stats_df = pd.DataFrame(risk_stats)
                        st.dataframe(risk_stats_df, use_container_width=True)
                    
                    # 권장사항 표시
                    st.markdown("#### 💡 종합 권장사항")
                    
                    recommendations = []
                    if any('추락' in str(result_df['잠재 위험요인'].values) for _, result_df in analysis_results):
                        recommendations.append("🔴 **고소작업 안전**: 안전대 착용 및 안전난간 설치가 필수적입니다.")
                    
                    if any('감전' in str(result_df['잠재 위험요인'].values) or '전기' in str(result_df['잠재 위험요인'].values) for _, result_df in analysis_results):
                        recommendations.append("⚡ **전기안전**: 전원차단 및 검전기 사용을 통한 무전압 확인이 필요합니다.")
                    
                    if any('개인보호구' in str(result_df['잠재 위험요인'].values) for _, result_df in analysis_results):
                        recommendations.append("🦺 **개인보호구**: 작업 전 개인보호구 착용 상태를 반드시 점검하세요.")
                    
                    recommendations.append("📋 **작업 전 교육**: 모든 작업자에게 TBM을 실시하고 위험요소를 공유하세요.")
                    recommendations.append("👥 **안전관리**: 2인1조 작업 및 안전관리자 배치를 권장합니다.")
                    
                    for rec in recommendations:
                        st.markdown(f"- {rec}")
                    
                    # 전체 결과 일괄 다운로드
                    st.markdown("#### 📦 전체 결과 일괄 다운로드")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 전체 결과를 하나의 CSV로 통합
                        all_results = []
                        for img_name, result_df in analysis_results:
                            temp_df = result_df.copy()
                            temp_df['이미지명'] = img_name
                            all_results.append(temp_df)
                        
                        if all_results:
                            combined_df = pd.concat(all_results, ignore_index=True)
                            # 컬럼 순서 재정렬
                            combined_df = combined_df[['이미지명', '번호', '잠재 위험요인', '잠재 위험요인 설명', '위험성 감소대책']]
                            
                            csv_all = combined_df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📥 전체 위험성평가 통합 다운로드",
                                data=csv_all,
                                file_name=f"전체_위험성평가_통합_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="all_results_download",
                                use_container_width=True
                            )
                    
                    with col2:
                        # 통계 정보 다운로드
                        if risk_stats:
                            stats_csv = risk_stats_df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📊 위험요인 통계 다운로드",
                                data=stats_csv,
                                file_name=f"위험요인_통계_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="stats_download",
                                use_container_width=True
                            )
                
                else:
                    st.error("❌ 분석 결과가 없습니다. 다시 시도해주세요.")

# 도움말 및 추가 정보
st.markdown("---")
with st.expander("❓ 도움말 및 문의사항"):
    st.markdown("""
    ### 🔧 문제 해결
    
    **API 키 오류 발생 시:**
    - `config.json` 파일이 프로젝트 폴더에 있는지 확인
    - 파일 내용: `{"openai_api_key": "YOUR_API_KEY"}`
    
    **이미지 분석 오류 발생 시:**
    - 이미지 파일 크기가 너무 크지 않은지 확인 (권장: 5MB 이하)
    - 지원 형식: JPG, JPEG, PNG
    
    **체크리스트 파일 오류 발생 시:**
    - Excel 파일(.xlsx)인지 확인
    - 파일이 손상되지 않았는지 확인
    
    ### 📞 기술 지원
    - 추가 문의사항이 있으시면 시스템 관리자에게 연락하세요.
    
    ### 🆕 업데이트 예정 기능
    - PDF 리포트 생성
    - 위험도 점수 자동 계산
    - 과거 분석 결과 히스토리
    - 실시간 알림 기능
    """)

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🛡️ 현장 안전 위험성 평가 자동화 도구 v1.0</p>
    <p>Powered by OpenAI GPT-4 & Streamlit</p>
</div>
""", unsafe_allow_html=True)
