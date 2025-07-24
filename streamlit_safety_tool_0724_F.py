import streamlit as st
from PIL import Image
from openai import OpenAI
import pandas as pd
import json
import os
import base64
import io
from datetime import datetime
from dotenv import load_dotenv
import locale
import zipfile #7/21 추가

# 한국 로케일 설정 (선택사항)
try:
    locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')  
except:
    pass  # 로케일 설정 실패해도 계속 진행


# .env 파일 로드
load_dotenv()

# 새로운 함수 추가 (기존 코드에 추가)/ 7/21 추가

def parse_analysis_sections(analysis_text: str) -> dict:
    """
    GPT 분석 결과를 5개 섹션으로 구분하여 파싱하는 함수 ( 7/21 6시 각 섹션별로 본문 내용만 저장)
    
    Args:
        analysis_text (str): GPT 분석 결과 전체 텍스트
    
    Returns:
        dict: 5개 섹션으로 구분된 결과
    """
    sections = {
        "work_environment": "",        # 0. 통합 작업 환경 설명
        "risk_analysis": "",           # 1. 현장 전체 잠재 위험요인 분석 및 위험성 감소대책
        "sgr_checklist": "",          # 2. SGR 체크리스트 항목별 통합 체크 결과
        "recommendations": "",         # 3. 현장 전체 통합 추가 권장사항
        "photo_observations": ""       # 4. 현장 사진별 주요 관찰 사항
    }
    
    lines = analysis_text.split('\n')
    current_section = None
    current_content = []
    section_started = False #7/21 6시
    
    for line in lines:
        line_stripped = line.strip()

        # 섹션 시작을 감지하고 제목은 제외 (7/21 6시 수정 반영)
        if "통합 작업 환경 설명" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "work_environment"
            current_content = []
            section_started = True
            continue

        elif "1. 현장 전체 잠재 위험요인 분석" in line_stripped or "잠재 위험요인 분석" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "risk_analysis"
            current_content = []
            section_started = True
            continue

        elif "2. SGR 체크리스트" in line_stripped or "체크리스트 항목별" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "sgr_checklist"
            current_content = []
            section_started = True
            continue

        elif "3. 현장 전체" in line_stripped and "추가 권장사항" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "recommendations"
            current_content = []
            section_started = True
            continue

        elif "4. 현장 사진별" in line_stripped or "사진별 주요 관찰" in line_stripped:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "photo_observations"
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
        
    #     # 섹션 구분 (제목 기반) /7/21 6시 이전
    #     if "통합 작업 환경 설명" in line_stripped or "## 통합 작업 환경 설명" in line_stripped:
    #                 if current_section and current_content:
    #                     sections[current_section] = '\n'.join(current_content)
    #                 current_section = "work_environment"
    #                 current_content = [line]        


    #     elif "1. 현장 전체 잠재 위험요인 분석" in line_stripped or "잠재 위험요인 분석" in line_stripped:
    #         if current_section and current_content:
    #             sections[current_section] = '\n'.join(current_content)
    #         current_section = "risk_analysis"
    #         current_content = [line]
            
    #     elif "2. SGR 체크리스트" in line_stripped or "체크리스트 항목별" in line_stripped:
    #         if current_section and current_content:
    #             sections[current_section] = '\n'.join(current_content)
    #         current_section = "sgr_checklist"
    #         current_content = [line]
            
    #     elif "3. 현장 전체" in line_stripped and "추가 권장사항" in line_stripped:
    #         if current_section and current_content:
    #             sections[current_section] = '\n'.join(current_content)
    #         current_section = "recommendations"
    #         current_content = [line]
            
    #     elif "4. 현장 사진별" in line_stripped or "사진별 주요 관찰" in line_stripped:
    #         if current_section and current_content:
    #             sections[current_section] = '\n'.join(current_content)
    #         current_section = "photo_observations"
    #         current_content = [line]
            
    #     else:
    #         if current_section:
    #             current_content.append(line)
    
    # # 마지막 섹션 저장
    # if current_section and current_content:
    #     sections[current_section] = '\n'.join(current_content)
    
    # return sections

def create_section_files(sections: dict, timestamp: str) -> dict:
    """
    각 섹션을 개별 파일로 생성하는 함수
    
    Args:
        sections (dict): 파싱된 섹션 데이터
        timestamp (str): 타임스탬프
    
    Returns:
        dict: 각 섹션의 파일 내용
    """
    files = {}

    # 0. 통합 작업 환경 설명
    if sections["work_environment"]:
        files["work_environment"] = f"""# 통합 작업 환경 설명

생성 시간: {timestamp}

{sections["work_environment"]}
"""
        
    # 1. 위험요인 분석
    if sections["risk_analysis"]:
        files["risk_analysis"] = f"""# 현장 전체 잠재 위험요인 분석 및 위험성 감소대책

생성 시간: {timestamp}

{sections["risk_analysis"]}
"""

    # 2. SGR 체크리스트
    if sections["sgr_checklist"]:
        files["sgr_checklist"] = f"""# SGR 체크리스트 항목별 통합 체크 결과

생성 시간: {timestamp}

{sections["sgr_checklist"]}
"""

    # 3. 추가 권장사항
    if sections["recommendations"]:
        files["recommendations"] = f"""# 현장 전체 통합 추가 권장사항

생성 시간: {timestamp}

{sections["recommendations"]}
"""

    # 4. 사진별 관찰사항
    if sections["photo_observations"]:
        files["photo_observations"] = f"""# 현장 사진별 주요 관찰 사항

생성 시간: {timestamp}

{sections["photo_observations"]}
"""

    return files  # 7/21 추가 내용



# OpenAI API 키 읽기 함수
def load_openai_api_key() -> str:
    """환경변수에서 OpenAI API 키를 읽어옵니다."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    return api_key

# 사전 등록된 체크리스트 파일 로드 함수
def load_predefined_checklist(file_path: str ="SGR현장 체크리스트_변환2.xlsx") -> pd.DataFrame:
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

| 번호  | 잠재 위험요인 | 잠재 위험요인 설명             | 위험성 감소대책                        |
|------|-------------|--------------------------- --|--------------------------------------|
| 1    | [위험요인1]  | [현장 전체 관점에서의 상세 설명] | ① [대책1] ② [대책2] ③ [대책3] ④ [대책4] |
| 2    | [위험요인2]  | [현장 전체 관점에서의 상세 설명] | ① [대책1] ② [대책2] ③ [대책3] ④ [대책4] |
[현장 전체에서 식별된 모든 주요 위험요인들...]

## 2. SGR 체크리스트 항목별 통합 체크 결과

|  항목 | 준수여부 | 세부 내용 |
|----------------|----------|-------------------|
| 1. 모든 작업자는 작업조건에 맞는 안전보호구를 착용한다. | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 2. 모든 공사성 작업시에는 위험성평가를 시행하고 결과를 기록/보관한다. | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 3. 작업 전 반드시 TBM작업계획 공유 및 위험성 예지 등 시행 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 4. 고위험 작업 시에는 2인1조 작업 및 작업계획서를 비치한다. | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 5. 이동식사다리 및 고소작업대(차량) 사용 시 안전수칙 준수 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 6. 전원작업 및 고압선 주변 작업 시 감전예방 조치 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 7. 도로 횡단 및 도로 주변 작업 시 교통안전 시설물과 신호수를 배치한다. | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 8. 밀폐공간(맨홀 등) 작업 시 산소/유해가스 농도 측정 및 감시인 배치 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 9. 하절기/동절기 기상상황에 따른 옥외작업 금지 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 10. 유해위험물 MSDS의 관리 및 예방 조치 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 11. 중량물 이동 인력, 장비 이용 시 안전 조치 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 12. 화기 작업 화상, 화재 위험 예방 조치 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 13. 추락 예방 안전 조치 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 14. 건설 기계장비, 설비 등 안전 및 방호조치(끼임) | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 15. 혼재 작업(부딪힘) 시 안전 예방 조치 | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |
| 16. 충돌 방지 조치(부딪힘) | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |

## 3. 현장 전체 통합 추가 권장사항
[현장 전체 특성에 맞는 종합적이고 구체적인 안전 권장사항을 작성]


제약사항:
- 모든 내용은 실제 산업안전보건 기준에 부합하도록 구체적이고 실무적인 수준으로 작성
- 위험성 감소대책은 각각 4개 이상의 구체적인 조치로 구성
- 체크리스트는 현장 전체 상황에 맞게 O, X , 해당없음 , 알수없음 중 하나로 표시하고 구체적인 확인 내용도 포함
  o: 사진에서 준수가 명확히 확인됨, x: 사진에서 명확히 미준수가 확인됨, 해당없음: 준수가 필요 없는 항목임, 알수없음: 이미지의 내용으로 확인 불가한 경우
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
        model="gpt-4.1",  # 다중 이미지 분석을 위해 최신 모델 사용(4o --> 4.1로 변경,7/17일)
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
        "sections": parse_analysis_sections(analysis_result),  # 섹션 파싱 추가, 7/21
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# 기존 코드에 이 함수를 추가(7/24)
def format_checklist_content(content: str) -> str:
    """
    SGR 체크리스트 내용에서 준수여부에 따라 스타일을 적용하는 함수
    - X: 빨간색 굵게
    - 알수없음: 굵게
    """
    if not content:
        return content
    
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 테이블 구분선은 그대로 유지
        if line_stripped.startswith('|---') or line_stripped.startswith('|==='):
            formatted_lines.append(line)
            continue
        
        # 테이블 행인지 확인 (|로 구분된 행)
        if '|' in line and line_stripped.startswith('|') and line_stripped.endswith('|'):
            # 파이프를 기준으로 분할
            parts = line.split('|')
            
            # 테이블 데이터 행인지 확인 (최소 4개 컬럼: 빈값, 항목, 준수여부, 세부내용)
            if len(parts) >= 4:
                # 각 컬럼의 내용 추출 (앞뒤 공백 제거)
                col0 = parts[0]  # 시작 빈 컬럼
                col1 = parts[1].strip()  # 항목
                col2 = parts[2].strip()  # 준수여부
                col3 = parts[3].strip() if len(parts) > 3 else ""  # 세부내용
                col4 = parts[4] if len(parts) > 4 else ""  # 끝 빈 컬럼
                
                # 헤더 행은 제외 (항목, 준수여부 등의 헤더 텍스트 포함)
                if any(header in col1.lower() for header in ['항목', 'header', '준수여부']):
                    formatted_lines.append(line)
                    continue
                
                # 준수여부에 따른 스타일 적용
                if col2 == 'X':
                    # X인 경우 전체 행을 빨간색 굵게
                    formatted_line = f"{col0}| **<span style='color: red; font-weight: bold;'>{col1}</span>** | **<span style='color: red; font-weight: bold;'>{col2}</span>** | **<span style='color: red; font-weight: bold;'>{col3}</span>** |{col4}"
                    formatted_lines.append(formatted_line)
                    
                elif col2 == '알수없음':
                    # 알수없음인 경우 전체 행을 굵게
                    formatted_line = f"{col0}| **{col1}** | **{col2}** | **{col3}** |{col4}"
                    formatted_lines.append(formatted_line)
                    
                else:
                    # 일반 항목은 그대로
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        else:
            # 테이블이 아닌 일반 텍스트는 그대로
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

# CSS 스타일을 추가하여 더 나은 렌더링 지원
def add_custom_css():
    """체크리스트 스타일링을 위한 CSS 추가"""
    st.markdown("""
    <style>
    .stMarkdown table {
        width: 100%;
        border-collapse: collapse;
    }
    .stMarkdown table td, .stMarkdown table th {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .stMarkdown table th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    .risk-item {
        color: red !important;
        font-weight: bold !important;
    }
    .unknown-item {
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
st.title("🏗️ AI 위험성평가")

# 숨김 처리( 7/17)

# st.header("📋 사전 등록된 체크리스트 및 현장 이미지 업로드")

# # OpenAI API 키 상태 확인
# if client is None:
#     st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. 설정을 확인해주세요.")
# else:
#     st.success("✅ OpenAI API 연결 완료")

# 사전 등록된 체크리스트 자동 로드
@st.cache_data
def load_checklist():
    return load_predefined_checklist()

checklist = load_checklist()

# if checklist is not None and not checklist.empty:
#     st.success("✅ 사전 등록된 SGR 체크리스트 로드 완료!")
#     st.info("📋 체크리스트가 자동으로 로드되었습니다. 이제 작업 환경 이미지를 업로드하여 분석을 시작하세요.")
    
#     with st.expander("체크리스트 미리보기 (클릭하여 확장)"):
#         st.dataframe(checklist, use_container_width=True)
#         st.caption(f"총 {len(checklist)}개의 체크리스트 항목이 로드되었습니다.")
# else:
#     st.error("❌ 체크리스트를 로드할 수 없습니다.")

# 작업 환경 이미지 업로드
st.markdown("#       ")
st.markdown("### 📸 작업 환경 이미지 업로드")
uploaded_images = st.file_uploader(
    "동일한 공사현장의 작업 환경 이미지를 업로드하세요 (다중 업로드 가능)", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True,
    help="동일한 현장의 여러 각도/영역 사진을 업로드하면 통합된 위험성 평가를 수행합니다."
)

# 업로드된 이미지 미리보기
if uploaded_images:
    # st.markdown("### 📋 업로드된 이미지 미리보기") (7/17 삭제)
    
    # 이미지를 3열로 표시
    num_cols = min(len(uploaded_images), 3)
    cols = st.columns(num_cols)
    
    for idx, image_file in enumerate(uploaded_images):
        with cols[idx % num_cols]:
            image = Image.open(image_file)
            st.image(image, caption=f"📷 {image_file.name}", use_container_width=True)
            
            # 이미지 정보 표시(7/17 제외)
            # st.caption(f"크기: {image.size[0]}x{image.size[1]} | 형식: {image.format}")
    
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
                
                # 분석 결과를 세션 상태에 저장 (7/21 추가)
                st.session_state['analysis_result'] = result
                st.session_state['analysis_completed'] = True  #7/21 추가

                st.success("✅ 통합 위험성 평가서 생성 완료!")

            except Exception as e:
                        st.error(f"❌ 분석 중 오류 발생: {str(e)}")
                        st.info("💡 오류가 지속되면 이미지 크기를 줄이거나 장수를 줄여서 다시 시도해보세요.")
    
            # 분석 결과가 세션 상태에 있으면 화면에 표시 7/21 추가
            if st.session_state.get('analysis_completed', False) and 'analysis_result' in st.session_state:
                result = st.session_state['analysis_result']

                # # 결과 출력 (7/21 제외)
                # st.markdown("---")
                # st.header("📊 통합 현장 안전 위험성 평가서")
                
                # 분석 정보 표시( 7/17 제외)
                # st.markdown(f"**분석 대상 이미지**: {', '.join(result['image_names'])}")
                # st.markdown(f"**총 이미지 수**: {result['image_count']}장")
                # st.caption(f"생성 시간: {result['timestamp']}")
                
                # # 종합 평가서를 마크다운으로 표시 7/21 제외
                # st.markdown(result['full_report'])
                
                # # 위험성 평가 표를 DataFrame으로 추출하여 별도 표시 7/21제외함
                # try:
                #     risk_df = parse_risk_table_from_markdown(result['full_report'])
                #     st.markdown("### 📋 위험성 평가 표 (데이터프레임)")
                #     st.dataframe(
                #         risk_df, 
                #         use_container_width=True,
                #         hide_index=True,
                #         column_config={
                #             "번호": st.column_config.NumberColumn("번호", width="small"),
                #             "잠재 위험요인": st.column_config.TextColumn("잠재 위험요인", width="medium"),
                #             "잠재 위험요인 설명": st.column_config.TextColumn("잠재 위험요인 설명", width="large"),
                #             "위험성 감소대책": st.column_config.TextColumn("위험성 감소대책", width="large")
                #         }
                #     )
                    
                #     # CSV 다운로드 버튼 (표 데이터)
                #     csv = risk_df.to_csv(index=False, encoding='utf-8-sig')
                #     st.download_button(
                #         label=f"📥 통합 위험성 평가 표 CSV 다운로드",
                #         data=csv,
                #         file_name=f"통합_위험성평가표_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                #         mime="text/csv"
                #     )
                # except Exception as e:
                #     st.warning(f"⚠️ 위험성 평가 표 파싱 중 오류: {str(e)}")
                
                # # 마크다운 파일 다운로드 버튼 (전체 보고서)
                # md_content = f"# 통합 현장 안전 위험성 평가서\n\n"
                # md_content += f"**분석 대상 이미지:** {', '.join(result['image_names'])}\n\n"
                # md_content += f"**총 이미지 수:** {result['image_count']}장\n\n"
                # md_content += f"**생성 시간:** {result['timestamp']}\n\n"
                # md_content += result['full_report']
                
                # st.download_button(
                #     label=f"📄 통합 종합 평가서 MD 다운로드",
                #     data=md_content.encode('utf-8-sig'),
                #     file_name=f"통합_종합위험성평가서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                #     mime="text/markdown"
                # )

                # ================================
                # 2. UI 부분에서 결과 출력 코드 수정 7/21 추가 내용
                # ================================

                # 기존 결과 출력 부분 다음에 추가할 코드:

                # 섹션별 결과 출력 및 다운로드
                st.markdown("---")
                st.header("📁 현장 위험성 평가")

                # 섹션별 탭 생성
                tab0, tab1, tab2 = st.tabs([
                    "✅ SGR 체크리스트", 
                    "🔍 위험요인 분석", 
                    "💡 추가 권장사항" 
                ])

                sections = result.get('sections', {})
                section_files = create_section_files(sections, result['timestamp'])

                # with tab2:
                #     st.subheader("작업 환경 설명")
                #     if sections.get("work_environment"):
                #         st.markdown(sections["work_environment"])
                #         if "work_environment" in section_files:
                #             st.download_button(
                #                 label="📥 작업환경 설명 다운로드 (.md)",
                #                 data=section_files["work_environment"].encode('utf-8-sig'),
                #                 file_name=f"작업환경설명_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                #                 mime="text/markdown",
                #                 key="env_download"
                #             )
                #     else:
                #         st.info("해당 섹션의 내용을 찾을 수 없습니다.")
                
                with tab1:
                    st.subheader("잠재 위험요인/감소대책")
                    if sections.get("risk_analysis"):
                        st.markdown(sections["risk_analysis"])
                        if "risk_analysis" in section_files:
                            st.download_button(
                                label="📥 위험요인 분석 결과 다운로드 (.md)",
                                data=section_files["risk_analysis"].encode('utf-8-sig'),
                                file_name=f"위험요인분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                key="risk_download"
                            )
                    else:
                        st.info("해당 섹션의 내용을 찾을 수 없습니다.")

                # 기존의 tab0 부분을 다음과 같이 수정:
                with tab0:
                    st.subheader("체크리스트 결과")
                    
                    # CSS 스타일 추가
                    add_custom_css()
                    
                    if sections.get("sgr_checklist"):
                        # 원본 내용 확인을 위한 디버깅 (필요시 주석 해제)
                        # st.text("원본 내용:")
                        # st.text(sections["sgr_checklist"][:500])  # 처음 500자만 표시
                        
                        # 체크리스트 내용에 스타일 적용
                        formatted_checklist = format_checklist_content(sections["sgr_checklist"])
                        
                        # 포맷팅 결과 확인을 위한 디버깅 (필요시 주석 해제)
                        # st.text("포맷팅된 내용:")
                        # st.text(formatted_checklist[:500])  # 처음 500자만 표시
                        
                        st.markdown(formatted_checklist, unsafe_allow_html=True)
                        
                        if "sgr_checklist" in section_files:
                            st.download_button(
                                label="📥 SGR 체크리스트 결과 다운로드 (.md)",
                                data=section_files["sgr_checklist"].encode('utf-8-sig'),
                                file_name=f"SGR체크리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                key="sgr_download"
                            )
                    else:
                        st.info("해당 섹션의 내용을 찾을 수 없습니다.")

                # with tab0:
                #     st.subheader("체크리스트 결과")
                #     if sections.get("sgr_checklist"):
                #         st.markdown(sections["sgr_checklist"])
                #         if "sgr_checklist" in section_files:
                #             st.download_button(
                #                 label="📥 SGR 체크리스트 결과 다운로드 (.md)",
                #                 data=section_files["sgr_checklist"].encode('utf-8-sig'),
                #                 file_name=f"SGR체크리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                #                 mime="text/markdown",
                #                 key="sgr_download"
                #             )
                #     else:
                #         st.info("해당 섹션의 내용을 찾을 수 없습니다.")

                with tab2:
                    st.subheader("현장 추가 권장사항")
                    if sections.get("recommendations"):
                        st.markdown(sections["recommendations"])
                        if "recommendations" in section_files:
                            st.download_button(
                                label="📥 추가 권장사항 다운로드 (.md)",
                                data=section_files["recommendations"].encode('utf-8-sig'),
                                file_name=f"추가권장사항_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                key="rec_download"
                            )
                    else:
                        st.info("해당 섹션의 내용을 찾을 수 없습니다.")


                # 전체 섹션 ZIP 파일로 다운로드
                if section_files:
                    st.markdown("---")
                    st.subheader("📦 전체 섹션 통합 다운로드")
                    
                    # # ZIP 파일 생성을 위한 import 추가 필요
                    # import zipfile
                    # import io
                    
                    # ZIP 파일 생성
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for file_name, content in section_files.items():
                            korean_names = {
                                "risk_analysis": "1.위험요인분석",
                                "sgr_checklist": "2.체크리스트", 
                                "work_environment": "3.작업환경설명",
                                "recommendations": "4.추가권장사항"
                            }
                            zip_file.writestr(
                                f"{korean_names.get(file_name, file_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                content.encode('utf-8-sig')
                            )
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="📁 전체 섹션 ZIP 다운로드",
                        data=zip_buffer.getvalue(),
                        file_name=f"전체섹션_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        key="zip_download"
                    )                
                
            

        # # 새로운 분석을 위한 초기화 버튼 추가 (7/21 만들었다가 제외, 6시)
        # st.markdown("---")
        # if st.button("🔄 새로운 분석 시작", type="secondary"):
        #     st.session_state['analysis_completed'] = False
        #     if 'analysis_result' in st.session_state:
        #         del st.session_state['analysis_result']
        #     st.rerun()


else:
    st.info("📋 작업 환경 이미지를 업로드하면 분석 버튼이 활성화됩니다.")

# # 사용법 안내 (7/21 제외 처리함)
# with st.expander("📖 사용법 안내"):
#     st.markdown("""
#     ### 🔧 사용 방법
#     1. **자동 체크리스트 로드**: SGR현장 체크리스트가 자동으로 로드됩니다.
#     2. **현장 이미지 업로드**: 동일한 공사현장의 작업 환경 사진을 업로드하세요 (여러 장 권장).
#     3. **통합 분석 실행**: '통합 분석 - 종합 위험성 평가서 생성' 버튼을 클릭하세요.
#     4. **결과 확인**: 생성된 통합 평가서를 확인하고 필요한 형식으로 다운로드하세요.
    
#     ### 🆕 주요 개선사항
#     - **자동 체크리스트**: 사전 등록된 'SGR현장 체크리스트' 파일을 자동으로 로드
#     - **통합 위험성 평가**: 여러 이미지를 동일한 현장으로 간주하여 종합적인 분석 수행
#     - **개별 분석 vs 통합 분석**: 단일 이미지는 개별 분석, 다중 이미지는 통합 분석으로 자동 전환
    
#     ### 📋 출력 결과
#     - **통합 종합 위험성 평가서**: 현장 전체 관점에서의 작업 환경 설명, 위험요인 분석, 체크리스트 확인, 추가 권장사항
#     - **위험성 평가 표**: DataFrame 형태의 구조화된 데이터
#     - **다운로드 옵션**: 마크다운(.md) 파일, CSV 파일 형태로 다운로드 가능
#     - **현장 사진별 관찰 사항**: 각 이미지에서 특별히 주목할 만한 안전 관련 사항들
    
#     ### ⚠️ 주의사항
#     - 이미지는 JPG, JPEG, PNG 형식만 지원됩니다.
#     - 여러 이미지 업로드 시 동일한 공사현장의 사진으로 간주됩니다.
#     - 분석 시간은 이미지 수와 복잡도에 따라 달라질 수 있습니다.
#     - 체크리스트 파일이 없으면 기본 SGR 체크리스트를 사용합니다.
    
#     ### 💡 최적 사용 팁
#     - **다양한 각도**: 현장의 여러 각도/영역을 촬영한 사진들을 업로드하면 더 정확한 평가가 가능합니다.
#     - **고해상도 이미지**: 세부 안전장비나 시설물이 잘 보이는 고화질 이미지를 권장합니다.
#     - **작업 상황 포함**: 실제 작업자나 장비가 포함된 현장 사진이 더 실용적인 평가 결과를 제공합니다.
#     """)

# # 파일 정보 및 버전 정보
# st.markdown("---")
# st.markdown("**Version**: v0.4 (통합 분석 기능 추가)")
# st.markdown("**Last Updated**: 2025년 7월 개선 버전")
# st.markdown("**Features**: 자동 체크리스트 로드 + 다중 이미지 통합 위험성 평가")
