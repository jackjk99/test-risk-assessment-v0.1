import streamlit as st
from PIL import Image
from openai import OpenAI
import pandas as pd
import json
import os
import base64
import io
from datetime import datetime
import locale

# 한국 로케일 설정 (선택사항)
try:
    locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')  
except:
    pass  # 로케일 설정 실패해도 계속 진행


# OpenAI API 키 읽기 함수
def load_openai_api_key() -> str:
    """환경변수에서 OpenAI API 키를 읽어옵니다."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    return api_key

# 사전 등록된 체크리스트 파일 로드 함수
def load_predefined_checklist(file_path: str = "SGR현장 체크리스트_변환2.xlsx") -> pd.DataFrame:
    """
    사전에 등록된 체크리스트 파일을 로드합니다.
    
    Args:
        file_path (str): 체크리스트 파일 경로
    
    Returns:
        pd.DataFrame: 체크리스트 데이터
    """
    try:
        if os.path.exists(file_path):
            checklist = pd.read_excel(file_path)
            return checklist
        else:
            # 파일이 없는 경우 기본 체크리스트 생성
            st.warning(f"⚠️ 사전 등록된 체크리스트 파일 '{file_path}'을 찾을 수 없습니다. 기본 체크리스트를 사용합니다.")
            return create_default_checklist()
    except Exception as e:
        st.error(f"❌ 체크리스트 파일 로드 중 오류: {str(e)}")
        return create_default_checklist()

def create_default_checklist() -> pd.DataFrame:
    """기본 SGR 체크리스트를 생성합니다."""
    default_checklist = {
        "번호": list(range(1, 17)),
        "체크리스트 항목": [
            "모든 작업자는 작업조건에 맞는 안전보호구를 착용한다.",
            "모든 공사성 작업시에는 위험성평가를 시행하고 결과를 기록/보관한다.",
            "작업 전 반드시 TBM작업계획 공유 및 위험성 예지 등 시행",
            "고위험 작업 시에는 2인1조 작업 및 작업계획서를 비치한다.",
            "이동식사다리 및 고소작업대(차량) 사용 시 안전수칙 준수",
            "전원작업 및 고압선 주변 작업 시 감전예방 조치",
            "도로 횡단 및 도로 주변 작업 시 교통안전 시설물과 신호수를 배치한다.",
            "밀폐공간(맨홀 등) 작업 시 산소/유해가스 농도 측정 및 감시인 배치",
            "하절기/동절기 기상상황에 따른 옥외작업 금지",
            "유해위험물 MSDS의 관리 및 예방 조치",
            "중량물 이동 인력, 장비 이용 시 안전 조치",
            "화기 작업 화상, 화재 위험 예방 조치",
            "추락 예방 안전 조치",
            "건설 기계장비, 설비 등 안전 및 방호조치(끼임)",
            "혼재 작업(부딪힘) 시 안전 예방 조치",
            "충돌 방지 조치(부딪힘)"
        ]
    }
    return pd.DataFrame(default_checklist)

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

def analyze_multiple_images_comprehensive(images: list, checklist: pd.DataFrame, image_names: list) -> dict:
    """
    여러 이미지를 통합하여 단일 공사현장의 종합적인 안전 위험성 평가를 수행합니다.
    
    Args:
        images (list): 업로드된 이미지 파일들 (PIL Image 객체 리스트)
        checklist (pd.DataFrame): 참조 체크리스트 데이터
        image_names (list): 이미지 파일명 리스트
    
    Returns:
        dict: 통합된 종합 안전 위험성 평가 보고서
    """
    if client is None:
        raise Exception("OpenAI 클라이언트가 초기화되지 않았습니다.")
    
    # 모든 이미지를 base64로 인코딩
    base64_images = []
    for image in images:
        base64_images.append(encode_image(image))
    
    # 통합 분석을 위한 향상된 프롬프트
    prompt = f"""
Role(역할지정): 산업안전 위험성 평가 전문가로서 동일한 공사현장의 여러 사진을 종합적으로 분석하여 통합된 작업전 위험성 평가서를 작성합니다.

목표: 첨부된 {len(images)}장의 현장 사진들을 종합적으로 분석하여 다음과 같은 통합 위험성 평가서를 작성하세요:

**중요사항**: 
- 제공된 {len(images)}장의 사진은 모두 동일한 공사현장의 서로 다른 각도/영역을 촬영한 것입니다.
- 모든 사진을 종합적으로 분석하여 현장 전체의 통합된 위험성 평가를 수행해주세요.
- 각 사진별로 개별 분석하지 말고, 전체 현장의 종합적인 관점에서 분석해주세요.

분석 대상 이미지: {', '.join(image_names)}

1. 통합 작업 환경 설명 (Integrated Work Environment Description)
2. 현장 전체 잠재 위험요인 분석 및 위험성 감소대책 표
3. SGR 체크리스트 항목별 통합 체크 결과
4. 현장 전체 추가 권장사항

출력 형식:
다음과 같은 마크다운 형식으로 출력해주세요:

## 통합 작업 환경 설명
[제공된 {len(images)}장의 현장 사진을 종합적으로 분석하여 작업 환경, 작업 내용, 주요 장비 및 시설물, 현장 레이아웃 등에 대한 통합적이고 상세한 설명을 작성]

## 1. 현장 전체 잠재 위험요인 분석 및 위험성 감소대책

| 번호 | 잠재 위험요인 | 잠재 위험요인 설명 | 위험성 감소대책 |
|------|---------------|-------------------|----------------|
| 1 | [위험요인1] | [현장 전체 관점에서의 상세 설명] | ① [대책1] ② [대책2] ③ [대책3] ④ [대책4] |
| 2 | [위험요인2] | [현장 전체 관점에서의 상세 설명] | ① [대책1] ② [대책2] ③ [대책3] ④ [대책4] |
[현장 전체에서 식별된 모든 주요 위험요인들...]

## 2. SGR 체크리스트 항목별 통합 체크 결과

| 체크리스트 항목 | 체크여부 | 현장 확인 상세 내용 |
|----------------|----------|-------------------|
| 1. 모든 작업자는 작업조건에 맞는 안전보호구를 착용한다. | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 2. 모든 공사성 작업시에는 위험성평가를 시행하고 결과를 기록/보관한다. | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 3. 작업 전 반드시 TBM작업계획 공유 및 위험성 예지 등 시행 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 4. 고위험 작업 시에는 2인1조 작업 및 작업계획서를 비치한다. | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 5. 이동식사다리 및 고소작업대(차량) 사용 시 안전수칙 준수 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 6. 전원작업 및 고압선 주변 작업 시 감전예방 조치 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 7. 도로 횡단 및 도로 주변 작업 시 교통안전 시설물과 신호수를 배치한다. | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 8. 밀폐공간(맨홀 등) 작업 시 산소/유해가스 농도 측정 및 감시인 배치 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 9. 하절기/동절기 기상상황에 따른 옥외작업 금지 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 10. 유해위험물 MSDS의 관리 및 예방 조치 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 11. 중량물 이동 인력, 장비 이용 시 안전 조치 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 12. 화기 작업 화상, 화재 위험 예방 조치 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 13. 추락 예방 안전 조치 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 14. 건설 기계장비, 설비 등 안전 및 방호조치(끼임) | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 15. 혼재 작업(부딪힘) 시 안전 예방 조치 | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |
| 16. 충돌 방지 조치(부딪힘) | [✓ 또는 (필요시) 또는 (해당없음)] | [현장 사진들에서 확인된 구체적 상황] |

## 3. 현장 전체 통합 추가 권장사항
[현장 전체 특성에 맞는 종합적이고 구체적인 안전 권장사항을 작성]

## 4. 현장 사진별 주요 관찰 사항
[각 사진에서 특별히 주목할 만한 안전 관련 사항들을 간략히 정리]

제약사항:
- 모든 내용은 실제 산업안전보건 기준에 부합하도록 구체적이고 실무적인 수준으로 작성
- 위험성 감소대책은 각각 4개 이상의 구체적인 조치로 구성
- 체크리스트는 현장 전체 상황에 맞게 ✓, (필요시), (해당없음) 중 하나로 표시하고 구체적인 확인 내용도 포함
- 모든 출력은 한국어로 작성
- 실무에서 바로 활용 가능한 수준의 상세한 내용 포함
- 개별 사진 분석이 아닌 현장 전체의 통합적 관점에서 분석

첨부된 {len(images)}장의 이미지를 모두 종합적으로 분석하여 위 지침에 따라 통합된 위험성 평가서를 작성해주세요.
"""
    
    # 이미지 메시지 구성
    message_content = [
        {
            "type": "text",
            "text": prompt
        }
    ]
    
    # 모든 이미지를 메시지에 추가
    for idx, base64_image in enumerate(base64_images):
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
            }
        })
    
    # OpenAI API 호출
    response = client.chat.completions.create(
        model="gpt-4o",  # 다중 이미지 분석을 위해 최신 모델 사용
        messages=[
            {
                "role": "user",
                "content": message_content
            }
        ],
        max_tokens=4000  # 통합 분석을 위해 토큰 수 증가
    )
    
    # GPT의 분석 결과를 가져오기
    analysis_result = response.choices[0].message.content
    
    # 결과를 구조화된 형태로 파싱
    return {
        "image_names": image_names,
        "image_count": len(images),
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
st.header("📋 사전 등록된 체크리스트 및 현장 이미지 업로드")

# OpenAI API 키 상태 확인
if client is None:
    st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. 설정을 확인해주세요.")
else:
    st.success("✅ OpenAI API 연결 완료")

# 사전 등록된 체크리스트 자동 로드
@st.cache_data
def load_checklist():
    return load_predefined_checklist()

checklist = load_checklist()

if checklist is not None and not checklist.empty:
    st.success("✅ 사전 등록된 SGR 체크리스트 로드 완료!")
    st.info("📋 체크리스트가 자동으로 로드되었습니다. 이제 작업 환경 이미지를 업로드하여 분석을 시작하세요.")
    
    with st.expander("체크리스트 미리보기 (클릭하여 확장)"):
        st.dataframe(checklist, use_container_width=True)
        st.caption(f"총 {len(checklist)}개의 체크리스트 항목이 로드되었습니다.")
else:
    st.error("❌ 체크리스트를 로드할 수 없습니다.")

# 작업 환경 이미지 업로드
st.markdown("### 📸 작업 환경 이미지 업로드")
uploaded_images = st.file_uploader(
    "동일한 공사현장의 작업 환경 이미지를 업로드하세요 (다중 업로드 가능)", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True,
    help="동일한 현장의 여러 각도/영역 사진을 업로드하면 통합된 위험성 평가를 수행합니다."
)

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
    
    if len(uploaded_images) == 1:
        st.info(f"💡 1개의 이미지가 업로드되었습니다. 단일 이미지 기반 위험성 평가를 수행합니다.")
    else:
        st.info(f"💡 총 {len(uploaded_images)}개의 이미지가 업로드되었습니다. 동일한 현장의 사진들로 간주하여 **통합 위험성 평가**를 수행합니다.")

# 분석 시작 버튼
if uploaded_images:
    st.markdown("### 🚀 통합 위험성 평가서 생성")
    
    analysis_mode = "통합 분석" if len(uploaded_images) > 1 else "단일 이미지 분석"
    
    if st.button(f"📊 {analysis_mode} - 종합 위험성 평가서 생성", type="primary", use_container_width=True):
        if client is None:
            st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
        elif checklist is None or checklist.empty:
            st.error("❌ 체크리스트를 로드할 수 없습니다.")
        else:
            try:
                # 진행 상황 표시
                with st.spinner(f"AI가 {len(uploaded_images)}장의 현장 사진을 종합 분석하여 통합 위험성 평가서를 생성하고 있습니다..."):
                    
                    # 이미지들을 PIL Image 객체로 변환
                    images = []
                    image_names = []
                    
                    for image_file in uploaded_images:
                        image = Image.open(image_file)
                        images.append(image)
                        image_names.append(image_file.name)
                    
                    # 통합 분석 수행
                    result = analyze_multiple_images_comprehensive(images, checklist, image_names)
                
                st.success("✅ 통합 위험성 평가서 생성 완료!")


                # 한국 로케일 설정 (선택사항)
                try:
                  locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')  
                except:
                  pass  # 로케일 설정 실패해도 계속 진행
  
                # 결과 출력
                st.markdown("---")
                st.header("📊 통합 현장 안전 위험성 평가서")
                
                # 분석 정보 표시
                st.markdown(f"**분석 대상 이미지**: {', '.join(result['image_names'])}")
                st.markdown(f"**총 이미지 수**: {result['image_count']}장")
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
                    csv = risk_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label=f"📥 통합 위험성 평가 표 CSV 다운로드",
                        data=csv,
                        file_name=f"통합_위험성평가표_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.warning(f"⚠️ 위험성 평가 표 파싱 중 오류: {str(e)}")
                
                # 마크다운 파일 다운로드 버튼 (전체 보고서)
                md_content = f"# 통합 현장 안전 위험성 평가서\n\n"
                md_content += f"**분석 대상 이미지:** {', '.join(result['image_names'])}\n\n"
                md_content += f"**총 이미지 수:** {result['image_count']}장\n\n"
                md_content += f"**생성 시간:** {result['timestamp']}\n\n"
                md_content += result['full_report']
                
                st.download_button(
                    label=f"📄 통합 종합 평가서 MD 다운로드",
                    data=md_content.encode('utf-8'),
                    file_name=f"통합_종합위험성평가서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"❌ 분석 중 오류 발생: {str(e)}")
                st.info("💡 오류가 지속되면 이미지 크기를 줄이거나 장수를 줄여서 다시 시도해보세요.")

else:
    st.info("📋 작업 환경 이미지를 업로드하면 분석 버튼이 활성화됩니다.")

# 사용법 안내
with st.expander("📖 사용법 안내"):
    st.markdown("""
    ### 🔧 사용 방법
    1. **자동 체크리스트 로드**: SGR현장 체크리스트가 자동으로 로드됩니다.
    2. **현장 이미지 업로드**: 동일한 공사현장의 작업 환경 사진을 업로드하세요 (여러 장 권장).
    3. **통합 분석 실행**: '통합 분석 - 종합 위험성 평가서 생성' 버튼을 클릭하세요.
    4. **결과 확인**: 생성된 통합 평가서를 확인하고 필요한 형식으로 다운로드하세요.
    
    ### 🆕 주요 개선사항
    - **자동 체크리스트**: 사전 등록된 'SGR현장 체크리스트_변환2.xlsx' 파일을 자동으로 로드
    - **통합 위험성 평가**: 여러 이미지를 동일한 현장으로 간주하여 종합적인 분석 수행
    - **개별 분석 vs 통합 분석**: 단일 이미지는 개별 분석, 다중 이미지는 통합 분석으로 자동 전환
    
    ### 📋 출력 결과
    - **통합 종합 위험성 평가서**: 현장 전체 관점에서의 작업 환경 설명, 위험요인 분석, 체크리스트 확인, 추가 권장사항
    - **위험성 평가 표**: DataFrame 형태의 구조화된 데이터
    - **다운로드 옵션**: 마크다운(.md) 파일, CSV 파일 형태로 다운로드 가능
    - **현장 사진별 관찰 사항**: 각 이미지에서 특별히 주목할 만한 안전 관련 사항들
    
    ### ⚠️ 주의사항
    - 이미지는 JPG, JPEG, PNG 형식만 지원됩니다.
    - 여러 이미지 업로드 시 동일한 공사현장의 사진으로 간주됩니다.
    - 분석 시간은 이미지 수와 복잡도에 따라 달라질 수 있습니다.
    - 체크리스트 파일이 없으면 기본 SGR 체크리스트를 사용합니다.
    
    ### 💡 최적 사용 팁
    - **다양한 각도**: 현장의 여러 각도/영역을 촬영한 사진들을 업로드하면 더 정확한 평가가 가능합니다.
    - **고해상도 이미지**: 세부 안전장비나 시설물이 잘 보이는 고화질 이미지를 권장합니다.
    - **작업 상황 포함**: 실제 작업자나 장비가 포함된 현장 사진이 더 실용적인 평가 결과를 제공합니다.
    """)

# 파일 정보 및 버전 정보
st.markdown("---")
st.markdown("**Version**: v0.4 (통합 분석 기능 추가)")
st.markdown("**Last Updated**: 2024년 개선 버전")
st.markdown("**Features**: 자동 체크리스트 로드 + 다중 이미지 통합 위험성 평가")
