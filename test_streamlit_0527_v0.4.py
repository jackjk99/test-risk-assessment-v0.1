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
        model="gpt-4.1",
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
            "양호(O)": "",
            "불량(X)": "",
            "해당 없음": "",
            "비고": row["위험성 감소대책"]
        })
    
    checklist_df = pd.DataFrame(checklist_data)
    return checklist_df

def display_checklist_table(checklist_df: pd.DataFrame, image_name: str):
    """
    체크리스트를 HTML 테이블 형식으로 표시하는 함수
    """
    st.markdown(f"#### 📋 {image_name} - 안전 체크리스트")
    
    # HTML 테이블 생성
    html_table = """
    <style>
    .checklist-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 14px;
    }
    .checklist-table th, .checklist-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
        vertical-align: top;
    }
    .checklist-table th {
        background-color: #f2f2f2;
        font-weight: bold;
        text-align: center;
    }
    .checklist-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .checklist-table .check-column {
        width: 60px;
        text-align: center;
    }
    .checklist-table .category-column {
        width: 80px;
        text-align: center;
    }
    .checklist-table .item-column {
        width: 40%;
    }
    .checklist-table .remark-column {
        width: 35%;
    }
    </style>
    
    <table class="checklist-table">
        <thead>
            <tr>
                <th class="category-column">구분</th>
                <th class="item-column">안전 Check List 항목</th>
                <th class="check-column">양호(O)</th>
                <th class="check-column">불량(X)</th>
                <th class="check-column">해당 없음</th>
                <th class="remark-column">비고</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for _, row in checklist_df.iterrows():
        html_table += f"""
            <tr>
                <td class="category-column">{row['구분']}</td>
                <td class="item-column">{row['안전 Check List 항목']}</td>
                <td class="check-column">☐</td>
                <td class="check-column">☐</td>
                <td class="check-column">☐</td>
                <td class="remark-column">{row['비고']}</td>
            </tr>
        """
    
    html_table += """
        </tbody>
    </table>
    """
    
    st.markdown(html_table, unsafe_allow_html=True)

# Streamlit App UI
st.title("현장 안전 위험성 평가 자동화 도구")
st.header("참조문서 및 현장 이미지 업로드")

# OpenAI API 키 상태 확인
if client is None:
    st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. config.json 파일을 확인해주세요.")
else:
    st.success("✅ OpenAI API 연결 완료")

# 참조 체크리스트 문서 업로드
checklist_file = st.file_uploader("참조 체크리스트 문서 업로드 (SGR현장 체크리스트_변환.xlsx)", type=["xlsx"])
checklist = None
if checklist_file:
    try:
        checklist = pd.read_excel(checklist_file)
        st.success("✅ 참조 체크리스트 등록 완료!")
        st.info("📋 체크리스트가 등록되었습니다. 이제 작업 환경 이미지를 업로드하여 분석을 시작하세요.")
        
        with st.expander("체크리스트 미리보기 (클릭하여 확장)"):
            st.dataframe(checklist.head(10), use_container_width=True)
            st.caption(f"총 {len(checklist)}개의 체크리스트 항목이 로드되었습니다.")
    except Exception as e:
        st.error(f"❌ 체크리스트 파일 읽기 오류: {str(e)}")
        st.info("💡 Excel 파일이 올바른 형식인지 확인해주세요.")

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
    st.markdown("### 🚀 위험성 평가 실행")
    
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
                    st.metric("식별된 위험요인 수", f"{risk_count}개")
                    
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
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 원본 CSV 다운로드
                        csv_original = result_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label=f"📥 원본 결과 CSV 다운로드",
                            data=csv_original,
                            file_name=f"위험성평가_원본_{img_name.split('.')[0]}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key=f"download_original_{idx}"
                        )
                    
                    with col2:
                        # 체크리스트 CSV 다운로드
                        csv_checklist = checklist_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label=f"📋 체크리스트 CSV 다운로드",
                            data=csv_checklist,
                            file_name=f"안전체크리스트_{img_name.split('.')[0]}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key=f"download_checklist_{idx}"
                        )
                    
                    if idx < len(analysis_results):
                        st.markdown("---")
                
                # 전체 결과 통합 다운로드
                if len(analysis_results) > 1:
                    st.markdown("### 📦 전체 결과 통합 다운로드")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 원본 결과 통합
                        combined_original_df = pd.DataFrame()
                        for img_name, result_df in analysis_results:
                            temp_df = result_df.copy()
                            temp_df.insert(0, '이미지파일', img_name)
                            combined_original_df = pd.concat([combined_original_df, temp_df], ignore_index=True)
                        
                        combined_original_csv = combined_original_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📦 전체 원본결과 통합 CSV",
                            data=combined_original_csv,
                            file_name=f"위험성평가_전체원본결과_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        # 체크리스트 결과 통합
                        combined_checklist_df = pd.DataFrame()
                        for img_name, result_df in analysis_results:
                            checklist_df = create_checklist_format(result_df)
                            temp_df = checklist_df.copy()
                            temp_df.insert(0, '이미지파일', img_name)
                            combined_checklist_df = pd.concat([combined_checklist_df, temp_df], ignore_index=True)
                        
                        combined_checklist_csv = combined_checklist_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📋 전체 체크리스트 통합 CSV",
                            data=combined_checklist_csv,
                            file_name=f"안전체크리스트_전체결과_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
else:
    st.info("📋 체크리스트를 업로드한 후 이미지를 업로드하면 분석 버튼이 활성화됩니다.")