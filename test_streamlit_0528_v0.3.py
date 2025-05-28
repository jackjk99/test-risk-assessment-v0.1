import streamlit as st
from PIL import Image
from openai import OpenAI
import pandas as pd
import json
import os
import base64
import io
from datetime import datetime

# # OpenAI API 키 읽기 함수
# def load_openai_api_key(config_path: str = "config.json") -> str:
#     """
#     Load OpenAI API key from a configuration file.

#     Args:
#         config_path (str): Path to the configuration file. Default is "config.json".
    
#     Returns:
#         str: OpenAI API key.
    
#     Example:
#         config.json:
#         {
#             "openai_api_key": "YOUR_OPENAI_API_KEY"
#         }
#     """
#     if not os.path.exists(config_path):
#         raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
#     with open(config_path, 'r') as config_file:
#         config_data = json.load(config_file)
#     return config_data.get("openai_api_key", "")

# OpenAI API 키 읽기 함수
def load_openai_api_key() -> str:
    """환경변수에서 OpenAI API 키를 읽어옵니다."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    return api_key

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

def analyze_image_comprehensive(image: Image, checklist: pd.DataFrame, image_name: str) -> dict:
    """
    Analyze the uploaded image using OpenAI GPT and generate a comprehensive safety assessment report.
    
    Args:
        image (Image): Uploaded image file of the work environment.
        checklist (pd.DataFrame): Reference checklist data extracted from the uploaded Excel file.
        image_name (str): Name of the image file.
    
    Returns:
        dict: A comprehensive safety assessment report containing:
            - work_description: 작업 환경 설명
            - risk_assessment_table: 위험성 평가 표
            - checklist_results: 체크리스트 확인 결과
            - additional_recommendations: 추가 권장사항
    """
    if client is None:
        raise Exception("OpenAI 클라이언트가 초기화되지 않았습니다.")
    
    # 이미지를 base64로 인코딩
    base64_image = encode_image(image)
    
    # 향상된 프롬프트
    prompt = """
Role(역할지정): 산업안전 위험성 평가 전문가로서 현장 사진을 기반으로 한 종합적인 작업전 위험성 평가서를 작성합니다.

목표: 첨부된 현장 사진을 분석하여 다음과 같은 종합적인 위험성 평가서를 작성하세요:

1. 작업 환경 설명 (Work Description)
2. 잠재 위험요인 분석 및 위험성 감소대책 표
3. SGR 체크리스트 항목별 체크 결과
4. 추가 권장사항

출력 형식:
다음과 같은 마크다운 형식으로 출력해주세요:

## 작업 환경 설명
[현장 사진을 기반으로 작업 환경, 작업 내용, 주요 장비 및 시설물에 대한 상세한 설명을 작성]

## 1. 잠재 위험요인 분석 및 위험성 감소대책

| 번호 | 잠재 위험요인 | 잠재 위험요인 설명 | 위험성 감소대책 |
|------|---------------|-------------------|----------------|
| 1 | [위험요인1] | [상세 설명] | ① [대책1] ② [대책2] ③ [대책3] ④ [대책4] |
| 2 | [위험요인2] | [상세 설명] | ① [대책1] ② [대책2] ③ [대책3] ④ [대책4] |
[추가 위험요인들...]

## 2. SGR 체크리스트 항목별 체크 결과

| 체크리스트 항목 | 체크여부 |
|----------------|----------|
| 1. 모든 작업자는 작업조건에 맞는 안전보호구를 착용한다. | [✓ 또는 (필요시) 또는 (해당없음)] |
| 2. 모든 공사성 작업시에는 위험성평가를 시행하고 결과를 기록/보관한다. | [✓ 또는 (필요시) 또는 (해당없음)] |
| 3. 작업 전 반드시 TBM작업계획 공유 및 위험성 예지 등 시행 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 4. 고위험 작업 시에는 2인1조 작업 및 작업계획서를 비치한다. | [✓ 또는 (필요시) 또는 (해당없음)] |
| 5. 이동식사다리 및 고소작업대(차량) 사용 시 안전수칙 준수 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 6. 전원작업 및 고압선 주변 작업 시 감전예방 조치 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 7. 도로 횡단 및 도로 주변 작업 시 교통안전 시설물과 신호수를 배치한다. | [✓ 또는 (필요시) 또는 (해당없음)] |
| 8. 밀폐공간(맨홀 등) 작업 시 산소/유해가스 농도 측정 및 감시인 배치 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 9. 하절기/동절기 기상상황에 따른 옥외작업 금지 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 10. 유해위험물 MSDS의 관리 및 예방 조치 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 11. 중량물 이동 인력, 장비 이용 시 안전 조치 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 12. 화기 작업 화상, 화재 위험 예방 조치 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 13. 추락 예방 안전 조치 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 14. 건설 기계장비, 설비 등 안전 및 방호조치(끼임) | [✓ 또는 (필요시) 또는 (해당없음)] |
| 15. 혼재 작업(부딪힘) 시 안전 예방 조치 | [✓ 또는 (필요시) 또는 (해당없음)] |
| 16. 충돌 방지 조치(부딪힘) | [✓ 또는 (필요시) 또는 (해당없음)] |

## 3. 추가 권장사항
[현장 특성에 맞는 추가적인 안전 권장사항을 작성]

제약사항:
- 모든 내용은 실제 산업안전보건 기준에 부합하도록 구체적이고 실무적인 수준으로 작성
- 위험성 감소대책은 각각 4개 이상의 구체적인 조치로 구성
- 체크리스트는 현장 상황에 맞게 ✓, (필요시), (해당없음) 중 하나로 표시
- 모든 출력은 한국어로 작성
- 실무에서 바로 활용 가능한 수준의 상세한 내용 포함

첨부된 이미지를 상세히 분석하여 위 지침에 따라 종합적인 위험성 평가서를 작성해주세요.
"""
    
    # OpenAI API 호출
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
        max_tokens=2500
    )
    
    # GPT의 분석 결과를 가져오기
    analysis_result = response.choices[0].message.content
    
    # 결과를 구조화된 형태로 파싱
    return {
        "image_name": image_name,
        "full_report": analysis_result,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def parse_risk_table_from_markdown(markdown_text: str) -> pd.DataFrame:
    """
    마크다운 텍스트에서 위험성 평가 표를 추출하여 DataFrame으로 변환
    """
    lines = markdown_text.split('\n')
    risk_data = []
    
    # 위험성 평가 표 섹션 찾기
    in_risk_table = False
    for line in lines:
        line = line.strip()
        
        # 표 시작 감지
        if "잠재 위험요인 분석" in line:
            in_risk_table = True
            continue
        
        # 다음 섹션 시작 시 표 종료
        if in_risk_table and line.startswith("## 2."):
            break
            
        # 표 데이터 파싱
        if in_risk_table and "|" in line and not line.startswith("|---"):
            parts = [x.strip() for x in line.split('|')]
            parts = [part for part in parts if part]
            
            # 헤더 건너뛰기
            if len(parts) >= 4 and parts[0] != "번호":
                try:
                    int(parts[0])  # 번호가 숫자인지 확인
                    risk_data.append(parts[:4])
                except ValueError:
                    continue
    
    if risk_data:
        return pd.DataFrame(risk_data, columns=["번호", "잠재 위험요인", "잠재 위험요인 설명", "위험성 감소대책"])
    else:
        # 기본 데이터 반환
        return pd.DataFrame([
            ["1", "개인보호구 착용", "작업 시 필수 개인보호구 착용 필요", "① 안전모 착용 ② 안전화 착용 ③ 필요시 안전대 착용 ④ 보호장갑 착용"],
            ["2", "작업 전 안전교육", "작업 전 TBM 실시 및 안전교육", "① 작업 전 TBM 실시 ② 작업자 건강상태 확인 ③ 작업계획 및 위험요소 공유 ④ 비상연락체계 확인"]
        ], columns=["번호", "잠재 위험요인", "잠재 위험요인 설명", "위험성 감소대책"])

# Streamlit App UI
st.title("🏗️ 이미지 분석 현장 안전 위험성 평가 Tool")
st.header("📋 참조문서 및 현장 이미지 업로드")

# OpenAI API 키 상태 확인
if client is None:
    st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. 설정을 확인해주세요.")
else:
    st.success("✅ OpenAI API 연결 완료")

# 참조 체크리스트 문서 업로드
checklist_file = st.file_uploader("참조 체크리스트 문서 업로드 (SGR현장 체크리스트_변환2.xlsx)", type=["xlsx"])
checklist = None
if checklist_file:
    try:
        checklist = pd.read_excel(checklist_file)
        st.success("✅ 참조 체크리스트 등록 완료!")
        st.info("📋 체크리스트가 등록되었습니다. 이제 작업 환경 이미지를 업로드하여 분석을 시작하세요.")
        
        with st.expander("체크리스트 미리보기 (클릭하여 확장)"):
            #st.dataframe(checklist.head(20), use_container_width=True)
            st.dataframe(checklist.head(len(checklist)), use_container_width=True)
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
            st.image(image, caption=f"📷 {image_file.name}", use_container_width=True)
            
            # 이미지 정보 표시
            st.caption(f"크기: {image.size[0]}x{image.size[1]} | 형식: {image.format}")
    
    st.info(f"💡 총 {len(uploaded_images)}개의 이미지가 업로드되었습니다. 각 이미지별로 종합 위험성 평가서가 생성됩니다.")

# 분석 시작 버튼
if uploaded_images:
    st.markdown("### 🚀 종합 위험성 평가서 생성")
    
    if st.button("📊 종합 위험성 평가서 생성 시작", type="primary", use_container_width=True):
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
                    status_text.text(f"🔄 {image_file.name} 종합 분석 중... ({idx+1}/{len(uploaded_images)})")
                    
                    image = Image.open(image_file)
                    with st.spinner(f"AI가 {image_file.name}의 종합 위험성 평가서를 생성하고 있습니다..."):
                        result = analyze_image_comprehensive(image, checklist, image_file.name)
                        analysis_results.append(result)
                    
                    # 진행률 업데이트
                    progress_bar.progress((idx + 1) / len(uploaded_images))
                    
                except Exception as e:
                    st.error(f"❌ {image_file.name} 분석 중 오류 발생: {str(e)}")
                    continue
            
            status_text.text("✅ 모든 이미지 종합 분석 완료!")
            
            # 결과 출력
            if analysis_results:
                st.markdown("---")
                st.header("📊 종합 위험성 평가서")
                
                for idx, result in enumerate(analysis_results, 1):
                    st.markdown(f"## 📷 현장 {idx}: {result['image_name']}")
                    st.caption(f"생성 시간: {result['timestamp']}")
                    
                    # 종합 평가서를 마크다운으로 표시
                    st.markdown(result['full_report'])
                    
                    # 위험성 평가 표를 DataFrame으로 추출하여 별도 표시
                    try:
                        risk_df = parse_risk_table_from_markdown(result['full_report'])
                        st.markdown("### 📋 위험성 평가 표 (데이터프레임)")
                        st.dataframe(
                            risk_df, 
                            use_container_width=True,
                            column_config={
                                "번호": st.column_config.NumberColumn("번호", width="small"),
                                "잠재 위험요인": st.column_config.TextColumn("잠재 위험요인", width="medium"),
                                "잠재 위험요인 설명": st.column_config.TextColumn("잠재 위험요인 설명", width="large"),
                                "위험성 감소대책": st.column_config.TextColumn("위험성 감소대책", width="large")
                            }
                        )
                        
                        # CSV 다운로드 버튼 (표 데이터)
                        csv = risk_df.to_csv(index=False, encoding='utf-8')
                        st.download_button(
                            label=f"📥 위험성 평가 표 CSV 다운로드",
                            data=csv,
                            file_name=f"위험성평가표_{result['image_name'].split('.')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key=f"csv_download_{idx}"
                        )
                    except Exception as e:
                        st.warning(f"⚠️ 위험성 평가 표 파싱 중 오류: {str(e)}")
                    
                    # 마크다운 파일 다운로드 버튼 (전체 보고서)
                    md_content = f"# {result['image_name']} 현장 안전 위험성 평가서\n\n"
                    md_content += f"**생성 시간:** {result['timestamp']}\n\n"
                    md_content += result['full_report']
                    
                    st.download_button(
                        label=f"📄 종합 평가서 MD 다운로드",
                        data=md_content.encode('utf-8'),
                        file_name=f"종합위험성평가서_{result['image_name'].split('.')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        key=f"md_download_{idx}"
                    )
                    
                    if idx < len(analysis_results):
                        st.markdown("---")
                
                # 전체 결과 통합 다운로드
                if len(analysis_results) > 1:
                    st.markdown("### 📦 전체 결과 통합 다운로드")
                    
                    # 전체 마크다운 통합
                    combined_md = f"# 전체 현장 안전 위험성 평가서\n\n"
                    combined_md += f"**총 {len(analysis_results)}개 현장 분석 결과**\n\n"
                    combined_md += f"**생성 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    combined_md += "---\n\n"
                    
                    for idx, result in enumerate(analysis_results, 1):
                        combined_md += f"# 현장 {idx}: {result['image_name']}\n\n"
                        combined_md += result['full_report']
                        combined_md += "\n\n---\n\n"
                    
                    # 통합 CSV (모든 위험성 평가 표)
                    combined_df = pd.DataFrame()
                    for result in analysis_results:
                        try:
                            risk_df = parse_risk_table_from_markdown(result['full_report'])
                            temp_df = risk_df.copy()
                            temp_df.insert(0, '현장이미지', result['image_name'])
                            combined_df = pd.concat([combined_df, temp_df], ignore_index=True)
                        except:
                            continue
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            label="📄 전체 종합 평가서 MD 다운로드",
                            data=combined_md.encode('utf-8'),
                            file_name=f"전체_종합위험성평가서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    with col2:
                        if not combined_df.empty:
                            combined_csv = combined_df.to_csv(index=False, encoding='utf-8')
                            st.download_button(
                                label="📊 전체 위험성 평가표 CSV 다운로드",
                                data=combined_csv,
                                file_name=f"전체_위험성평가표_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
else:
    st.info("📋 체크리스트를 업로드한 후 이미지를 업로드하면 분석 버튼이 활성화됩니다.")

# 사용법 안내
with st.expander("📖 사용법 안내"):
    st.markdown("""
    ### 🔧 사용 방법
    1. **참조 체크리스트 업로드**: SGR현장 체크리스트_변환2.xlsx 파일을 업로드하세요.
    2. **현장 이미지 업로드**: 작업 환경 사진을 업로드하세요 (여러 장 가능).
    3. **분석 실행**: '종합 위험성 평가서 생성 시작' 버튼을 클릭하세요.
    4. **결과 확인**: 생성된 종합 평가서를 확인하고 필요한 형식으로 다운로드하세요.
    
    ### 📋 출력 결과
    - **종합 위험성 평가서**: 작업 환경 설명, 위험요인 분석, 체크리스트 확인, 추가 권장사항
    - **위험성 평가 표**: DataFrame 형태의 구조화된 데이터
    - **다운로드 옵션**: 마크다운(.md) 파일, CSV 파일 형태로 다운로드 가능
    
    ### ⚠️ 주의사항
    - 이미지는 JPG, JPEG, PNG 형식만 지원됩니다.
    - 분석 시간은 이미지 크기와 복잡도에 따라 달라질 수 있습니다.
    """)
