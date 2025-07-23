import streamlit as st
from openai import OpenAI
import pandas as pd
import json
import os
import base64
import io
from datetime import datetime
from dotenv import load_dotenv
import locale
import zipfile

# 한국 로케일 설정 (선택사항)
try:
    locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')  
except:
    pass  # 로케일 설정 실패해도 계속 진행

# .env 파일 로드
load_dotenv()

# OpenAI API 키 읽기 함수 (기존 코드 재사용)
def load_openai_api_key() -> str:
    """환경변수에서 OpenAI API 키를 읽어옵니다."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    return api_key

# OpenAI 클라이언트 초기화 (기존 코드 재사용)
try:
    api_key = load_openai_api_key()
    client = OpenAI(api_key=api_key)
except Exception as e:
    st.error(str(e))
    client = None

def parse_analysis_sections(analysis_text: str) -> dict:
    """
    GPT 분석 결과를 섹션으로 구분하여 파싱하는 함수 (기존 코드 수정)
    """
    sections = {
        "work_analysis": "",           # 작업 내용 분석
        "risk_table": "",             # 위험성 평가 표
        "additional_safety": "",      # 추가 안전 조치
        "safety_checklist": ""        # 작업 전 체크리스트
    }
    
    lines = analysis_text.split('\n')
    current_section = None
    current_content = []
    section_started = False
    
    for line in lines:
        line_stripped = line.strip()

        # 섹션 시작을 감지
        if "작업 내용 분석" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "work_analysis"
            current_content = []
            section_started = True
            continue

        elif "위험성 평가 표" in line_stripped or "위험요인과 감소대책" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "risk_table"
            current_content = []
            section_started = True
            continue

        elif "추가 안전 조치" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "additional_safety"
            current_content = []
            section_started = True
            continue

        elif "작업 전 체크리스트" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "safety_checklist"
            current_content = []
            section_started = True
            continue

        # 본문 내용 수집
        if current_section and section_started:
            current_content.append(line)

    # 마지막 섹션 저장
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections

def create_section_files(sections: dict, timestamp: str, work_description: str) -> dict:
    """
    각 섹션을 개별 파일로 생성하는 함수 (기존 코드 수정)
    """
    files = {}

    # 작업 내용 분석
    if sections["work_analysis"]:
        files["work_analysis"] = f"""# 작업 내용 분석

작업 설명: {work_description}
생성 시간: {timestamp}

{sections["work_analysis"]}
"""
        
    # 위험성 평가 표
    if sections["risk_table"]:
        files["risk_table"] = f"""# 위험성 평가 표

작업 설명: {work_description}
생성 시간: {timestamp}

{sections["risk_table"]}
"""

    # 추가 안전 조치
    if sections["additional_safety"]:
        files["additional_safety"] = f"""# 추가 안전 조치

작업 설명: {work_description}
생성 시간: {timestamp}

{sections["additional_safety"]}
"""

    # 작업 전 체크리스트
    if sections["safety_checklist"]:
        files["safety_checklist"] = f"""# 작업 전 체크리스트

작업 설명: {work_description}
생성 시간: {timestamp}

{sections["safety_checklist"]}
"""

    return files

def load_reference_file(uploaded_file) -> str:
    """
    업로드된 참조 파일을 읽어서 텍스트로 변환
    """
    try:
        # 파일 포인터를 처음으로 리셋
        uploaded_file.seek(0)
        
        if uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            # Excel 파일 처리
            try:
                df = pd.read_excel(uploaded_file)
                if df.empty:
                    st.warning("⚠️ Excel 파일이 비어있습니다.")
                    return None
                # DataFrame을 텍스트로 변환
                text_content = df.to_string(index=False)
                return text_content
            except Exception as e:
                st.error(f"Excel 파일 읽기 오류: {str(e)}")
                return None
                
        elif uploaded_file.type == "text/csv":
            # CSV 파일 처리
            try:
                # 파일 내용을 먼저 확인
                content = uploaded_file.read().decode('utf-8')
                uploaded_file.seek(0)  # 다시 처음으로 리셋
                
                if not content.strip():
                    st.warning("⚠️ CSV 파일이 비어있습니다.")
                    return None
                
                # pandas로 읽기 시도
                df = pd.read_csv(uploaded_file, encoding='utf-8')
                if df.empty:
                    st.warning("⚠️ CSV 파일에 데이터가 없습니다.")
                    return None
                    
                text_content = df.to_string(index=False)
                return text_content
                
            except pd.errors.EmptyDataError:
                st.error("❌ CSV 파일에 파싱할 수 있는 컬럼이 없습니다. 파일 형식을 확인해주세요.")
                return None
            except UnicodeDecodeError:
                try:
                    # 다른 인코딩으로 시도
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='cp949')
                    if df.empty:
                        st.warning("⚠️ CSV 파일에 데이터가 없습니다.")
                        return None
                    text_content = df.to_string(index=False)
                    return text_content
                except Exception as e:
                    st.error(f"CSV 파일 인코딩 오류: {str(e)}")
                    return None
            except Exception as e:
                st.error(f"CSV 파일 읽기 오류: {str(e)}")
                return None
                
        elif uploaded_file.type == "text/plain":
            # 텍스트 파일 처리
            try:
                content = uploaded_file.read().decode('utf-8')
                if not content.strip():
                    st.warning("⚠️ 텍스트 파일이 비어있습니다.")
                    return None
                return content
            except UnicodeDecodeError:
                try:
                    uploaded_file.seek(0)
                    content = uploaded_file.read().decode('cp949')
                    if not content.strip():
                        st.warning("⚠️ 텍스트 파일이 비어있습니다.")
                        return None
                    return content
                except Exception as e:
                    st.error(f"텍스트 파일 인코딩 오류: {str(e)}")
                    return None
        else:
            st.error("지원하지 않는 파일 형식입니다. Excel(.xlsx), CSV(.csv), 또는 텍스트(.txt) 파일을 업로드해주세요.")
            return None
            
    except Exception as e:
        st.error(f"파일 읽기 중 예상치 못한 오류 발생: {str(e)}")
        return None

def analyze_work_risk(work_description: str, reference_content: str) -> dict:
    """
    작업 내용을 기반으로 위험성 분석을 수행하는 함수
    """
    if client is None:
        raise Exception("OpenAI 클라이언트가 초기화되지 않았습니다.")
    
    # 위험성 평가를 위한 프롬프트
    prompt = f"""
너는 안전보건 담당자야. 현장의 작업자에게 작업전 위험성 평가를 가이드하는 업무를 담당하고 있어.

첨부의 참조자료는 각 작업에서 발생할 수 있는 유해, 위험요인들과 그에 대한 개선방안이 정리되어 있어.

내가 특정 작업에 대해서 말하면, 위험요인은 참조자료를 참고해서 최대한 자세히 답변해줘.

**작업 내용**: {work_description}

**참조자료**:
{reference_content}

**답변 형식**:

## 작업 내용 분석
[작업의 특성, 주요 위험 포인트, 작업 환경 등을 분석]

## 오늘 작업에서 예상되는 위험요인과 감소대책은 아래와 같습니다. 확인해주세요.

| 순번 | 작업 내용 | 작업등급 | 재해유형 | 세부 위험요인 | 위험등급-개선전 | 위험성 감소대책 | 위험등급-개선후 |
|------|-----------|----------|----------|---------------|----------------|----------------|----------------|
| 1 | [구체적 작업] | [S/A/B등급] | [재해유형] | [세부 위험요인] | [C1-C4] | [구체적 대책] | [C1-C4] |
| 2 | [구체적 작업] | [S/A/B등급] | [재해유형] | [세부 위험요인] | [C1-C4] | [구체적 대책] | [C1-C4] |
[참조자료를 바탕으로 해당 작업과 관련된 모든 위험요인을 나열]

## 추가 안전 조치
[작업 특성에 맞는 추가적인 안전 조치사항]

## 작업 전 체크리스트
[작업 시작 전 반드시 확인해야 할 사항들]

**중요사항**:
- 참조자료의 내용을 최대한 활용하여 해당 작업과 관련된 모든 위험요인을 식별
- 위험등급은 C1(낮음), C2(보통), C3(높음), C4(매우높음)으로 표시
- 작업등급은 S(특별관리), A(중점관리), B(일반관리)로 구분
- 실무에서 바로 활용 가능한 구체적이고 실용적인 대책 제시
- 모든 내용은 한국어로 작성
"""
    
    # OpenAI API 호출
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=3000
    )
    
    # GPT의 분석 결과를 가져오기
    analysis_result = response.choices[0].message.content
    
    # 결과를 구조화된 형태로 파싱
    return {
        "work_description": work_description,
        "full_report": analysis_result,
        "sections": parse_analysis_sections(analysis_result),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Streamlit App UI
st.title("🛠️ 작업 위험성 평가 가이드")

# 세션 상태 초기화
if 'reference_uploaded' not in st.session_state:
    st.session_state['reference_uploaded'] = False
if 'reference_content' not in st.session_state:
    st.session_state['reference_content'] = None
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None

# OpenAI API 키 상태 확인
if client is None:
    st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. 설정을 확인해주세요.")
else:
    st.success("✅ OpenAI API 연결 완료")

# 1. 참조 파일 업로드 섹션
st.header("📁 위험성분석 참조 파일 업로드")

uploaded_reference = st.file_uploader(
    "위험성분석 참조 파일을 업로드하세요",
    type=["xlsx", "csv", "txt"],
    help="Excel, CSV, 또는 텍스트 파일을 업로드할 수 있습니다."
)

if uploaded_reference is not None:
    with st.spinner("참조 파일을 로딩하고 있습니다..."):
        reference_content = load_reference_file(uploaded_reference)
        
        if reference_content:
            st.session_state['reference_content'] = reference_content
            st.session_state['reference_uploaded'] = True
            st.success("✅ 참조 파일이 성공적으로 로드되었습니다!")
            
            # 참조 파일 미리보기
            with st.expander("📋 참조 파일 미리보기 (클릭하여 확장)"):
                try:
                    if uploaded_reference.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                        uploaded_reference.seek(0)
                        df = pd.read_excel(uploaded_reference)
                        st.dataframe(df, use_container_width=True)
                    elif uploaded_reference.type == "text/csv":
                        uploaded_reference.seek(0)
                        try:
                            df = pd.read_csv(uploaded_reference, encoding='utf-8')
                            st.dataframe(df, use_container_width=True)
                        except:
                            uploaded_reference.seek(0)
                            df = pd.read_csv(uploaded_reference, encoding='cp949')
                            st.dataframe(df, use_container_width=True)
                    else:
                        preview_text = reference_content[:1000] + "..." if len(reference_content) > 1000 else reference_content
                        st.text_area("참조 파일 내용", preview_text, height=200, disabled=True)
                except Exception as e:
                    st.warning(f"미리보기 표시 중 오류: {str(e)}")
                    preview_text = reference_content[:1000] + "..." if len(reference_content) > 1000 else reference_content
                    st.text_area("참조 파일 내용 (텍스트)", preview_text, height=200, disabled=True)

# 2. 작업 내용 입력 섹션
st.header("✍️ 작업 내용 입력")

work_input = st.text_area(
    "오늘 수행할 작업 내용을 자세히 입력해주세요",
    placeholder="예시: 오늘 철탑에서 안테나 재설치 작업이 있어 위험성 평가 안내해줘.",
    height=100,
    help="작업 장소, 작업 내용, 사용 장비 등을 구체적으로 입력하면 더 정확한 위험성 평가를 받을 수 있습니다."
)

# 3. 분석 실행 버튼
if st.session_state['reference_uploaded'] and work_input.strip():
    if st.button("🔍 위험성 평가 분석 시작", type="primary", use_container_width=True):
        if client is None:
            st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
        else:
            try:
                with st.spinner("AI가 작업 내용을 분석하여 위험성 평가를 수행하고 있습니다..."):
                    result = analyze_work_risk(work_input, st.session_state['reference_content'])
                    st.session_state['analysis_result'] = result
                
                st.success("✅ 위험성 평가 분석 완료!")
                
            except Exception as e:
                st.error(f"❌ 분석 중 오류 발생: {str(e)}")

elif not st.session_state['reference_uploaded']:
    st.info("📁 먼저 위험성분석 참조 파일을 업로드해주세요.")
elif not work_input.strip():
    st.info("✍️ 작업 내용을 입력해주세요.")

# 4. 분석 결과 표시
if st.session_state['analysis_result']:
    result = st.session_state['analysis_result']
    
    st.markdown("---")
    st.header("📊 위험성 평가 결과")
    
    # 작업 정보 표시
    st.markdown(f"**작업 내용**: {result['work_description']}")
    st.caption(f"생성 시간: {result['timestamp']}")
    
    # 섹션별 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 전체 보고서",
        "🔍 작업 분석", 
        "⚠️ 위험성 평가표", 
        "✅ 안전 조치"
    ])
    
    sections = result.get('sections', {})
    section_files = create_section_files(sections, result['timestamp'], result['work_description'])
    
    with tab1:
        st.subheader("전체 위험성 평가 보고서")
        st.markdown(result['full_report'])
        
        # 전체 보고서 다운로드
        md_content = f"# 작업 위험성 평가 보고서\n\n"
        md_content += f"**작업 내용:** {result['work_description']}\n\n"
        md_content += f"**생성 시간:** {result['timestamp']}\n\n"
        md_content += result['full_report']
        
        st.download_button(
            label="📄 전체 보고서 다운로드 (.md)",
            data=md_content.encode('utf-8-sig'),
            file_name=f"위험성평가보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            key="full_report_download"
        )
    
    with tab2:
        st.subheader("작업 내용 분석")
        if sections.get("work_analysis"):
            st.markdown(sections["work_analysis"])
            if "work_analysis" in section_files:
                st.download_button(
                    label="📥 작업 분석 다운로드 (.md)",
                    data=section_files["work_analysis"].encode('utf-8-sig'),
                    file_name=f"작업분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="work_analysis_download"
                )
        else:
            st.info("작업 분석 내용을 찾을 수 없습니다.")
    
    with tab3:
        st.subheader("위험성 평가표")
        if sections.get("risk_table"):
            st.markdown(sections["risk_table"])
            if "risk_table" in section_files:
                st.download_button(
                    label="📥 위험성 평가표 다운로드 (.md)",
                    data=section_files["risk_table"].encode('utf-8-sig'),
                    file_name=f"위험성평가표_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="risk_table_download"
                )
        else:
            st.info("위험성 평가표 내용을 찾을 수 없습니다.")
    
    with tab4:
        st.subheader("안전 조치 사항")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**추가 안전 조치**")
            if sections.get("additional_safety"):
                st.markdown(sections["additional_safety"])
            else:
                st.info("추가 안전 조치 내용을 찾을 수 없습니다.")
        
        with col2:
            st.markdown("**작업 전 체크리스트**")
            if sections.get("safety_checklist"):
                st.markdown(sections["safety_checklist"])
            else:
                st.info("체크리스트 내용을 찾을 수 없습니다.")
    
    # 전체 섹션 ZIP 파일로 다운로드
    if section_files:
        st.markdown("---")
        st.subheader("📦 전체 결과 통합 다운로드")
        
        # ZIP 파일 생성
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_name, content in section_files.items():
                korean_names = {
                    "work_analysis": "1.작업분석",
                    "risk_table": "2.위험성평가표",
                    "additional_safety": "3.추가안전조치",
                    "safety_checklist": "4.작업전체크리스트"
                }
                zip_file.writestr(
                    f"{korean_names.get(file_name, file_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    content.encode('utf-8-sig')
                )
            
            # 전체 보고서도 포함
            full_report_content = f"# 작업 위험성 평가 보고서\n\n"
            full_report_content += f"**작업 내용:** {result['work_description']}\n\n"
            full_report_content += f"**생성 시간:** {result['timestamp']}\n\n"
            full_report_content += result['full_report']
            
            zip_file.writestr(
                f"0.전체보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                full_report_content.encode('utf-8-sig')
            )
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📁 전체 결과 ZIP 다운로드",
            data=zip_buffer.getvalue(),
            file_name=f"위험성평가결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            key="zip_download"
        )

# 사용법 안내
with st.expander("📖 사용법 안내"):
    st.markdown("""
    ### 🔧 사용 방법
    1. **참조 파일 업로드**: 위험성분석 참조 데이터(Excel, CSV, 텍스트)를 업로드하세요.
    2. **작업 내용 입력**: 수행할 작업을 구체적으로 입력하세요.
    3. **분석 실행**: '위험성 평가 분석 시작' 버튼을 클릭하세요.
    4. **결과 확인**: 생성된 위험성 평가 보고서를 확인하고 다운로드하세요.
    
    ### 📋 출력 결과
    - **작업 내용 분석**: 입력한 작업의 특성과 주요 위험 포인트 분석
    - **위험성 평가표**: 순번, 작업내용, 재해유형, 위험요인, 감소대책을 표 형태로 제공
    - **추가 안전 조치**: 작업 특성에 맞는 추가적인 안전 조치사항
    - **작업 전 체크리스트**: 작업 시작 전 반드시 확인해야 할 사항들
    
    ### 💡 작업 입력 예시
    - "오늘 철탑에서 안테나 재설치 작업이 있어 위험성 평가 안내해줘"
    - "지하 맨홀에서 케이블 교체 작업을 진행할 예정입니다"
    - "고압 전선 근처에서 장비 설치 작업이 예정되어 있습니다"
    
    ### ⚠️ 주의사항
    - 참조 파일은 Excel(.xlsx), CSV(.csv), 텍스트(.txt) 형식만 지원됩니다.
    - 작업 내용을 구체적으로 입력할수록 더 정확한 위험성 평가를 받을 수 있습니다.
    - 생성된 결과는 참조용이므로, 실제 현장에서는 추가적인 안전 점검이 필요합니다.
    """)

# 파일 정보 및 버전 정보
st.markdown("---")
st.markdown("**Version**: v1.0 (텍스트 기반 위험성 평가)")
st.markdown("**Last Updated**: 2025년 7월")
st.markdown("**Features**: 작업 내용 입력 → AI 위험성 분석 → 맞춤형 안전 가이드 제공")