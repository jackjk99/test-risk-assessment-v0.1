# 7/31, 체크리스트의 대분류와 소분류의 내용으로 세분화하여 결과를 보여주도록 수정함

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
import zipfile
import re

# 페이지 설정 (가장 먼저 실행되어야 함)
st.set_page_config(
    page_title="AI 위험성 평가",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한국 로케일 설정
try:
    locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')  
except:
    pass

# .env 파일 로드
load_dotenv()

# CSS 스타일 추가
def add_custom_css():
    """체크리스트 스타일링을 위한 CSS 추가"""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px dashed #dee2e6;
        margin: 1rem 0;
    }
    .category-header {
        background-color: #e3f2fd;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        color: #1976d2;
        margin: 0.5rem 0;
    }
    .stMarkdown table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .stMarkdown table td, .stMarkdown table th {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
    }
    .stMarkdown table th {
        background-color: #f2f2f2;
        font-weight: bold;
        color: #333;
    }
    .risk-item {
        color: #dc3545 !important;
        font-weight: bold !important;
        background-color: #f8d7da !important;
    }
    .unknown-item {
        font-weight: bold !important;
        background-color: #fff3cd !important;
    }
    .success-item {
        color: #155724 !important;
        background-color: #d4edda !important;
    }
    .info-box {
        background-color: #e7f3ff;
        border-left: 5px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 초기 설정
def initialize_app():
    """앱 초기 설정"""
    add_custom_css()
    
    # 세션 상태 초기화
    if 'analysis_result' not in st.session_state:
        st.session_state['analysis_result'] = None
    if 'analysis_completed' not in st.session_state:
        st.session_state['analysis_completed'] = False

# OpenAI API 키 및 클라이언트 설정
@st.cache_resource
def initialize_openai_client():
    """OpenAI 클라이언트 초기화"""
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
            return None
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"❌ OpenAI 클라이언트 초기화 실패: {str(e)}")
        return None

# 기본 체크리스트 생성 (A열: 대분류, B열: 소분류)
@st.cache_data
def create_default_checklist():
    """Excel 파일의 A열(대분류)과 B열(소분류)을 기반으로 한 SGR 체크리스트를 생성합니다."""
    
    checklist_data = [
        # SGR 준수 (9개 항목 +1)
        {"번호": 1, "대분류": "SGR 준수", "소분류": "모든 작업자는 작업조건에 맞는 안전보호구를 착용한다."},
        {"번호": 2, "대분류": "SGR 준수", "소분류": "모든 공사성 작업시에는 위험성평가를 시행하고 결과를 기록/보관한다."},
        {"번호": 3, "대분류": "SGR 준수", "소분류": "작업 전 반드시 TBM작업계획 공유 및 위험성 예지 등 시행 및 결과등록을 하고 위험성 감소대책을 시행한다."},
        {"번호": 4, "대분류": "SGR 준수", "소분류": "고위험 작업 시에는 2인1조 작업 및 작업계획서를 비치한다."},
        {"번호": 5, "대분류": "SGR 준수", "소분류": "이동식사다리 및 고소작업대(차량) 사용 시 안전수칙을 준수한다."},
        {"번호": 6, "대분류": "SGR 준수", "소분류": "이동식사다리 및 고소작업대(차량) 사용 시 안전수칙을 준수한다."},
        {"번호": 7, "대분류": "SGR 준수", "소분류": "전원작업 및 고압선 주변 작업 시 반드시 감전예방 조치를 취한다."},
        {"번호": 8, "대분류": "SGR 준수", "소분류": "도로 횡단 및 도로 주변 작업 시 교통안전 시설물과 신호수를 배치한다."},
        {"번호": 9, "대분류": "SGR 준수", "소분류": "밀폐공간(맨홀 등) 작업 시 산소/유해가스 농도를 측정하고 감시인을 배치한다."},
        {"번호": 10, "대분류": "SGR 준수", "소분류": "하절기 체감온도 35도 이상 및 동절기 -12도 이하 시 불가피한 경우 외 옥외작업을 금지한다."},
        
        # 유해위험물 (4개 항목)
        {"번호": 11, "대분류": "유해위험물", "소분류": "MSDS-인화성,가연성물질 관리"},
        {"번호": 12, "대분류": "유해위험물", "소분류": "MSDS-스티커 비치 여부"},
        {"번호": 13, "대분류": "유해위험물", "소분류": "MSDS-화재대비 휴대용소화기 배치 여부"},
        {"번호": 14, "대분류": "유해위험물", "소분류": "MSDS-차량 내 유류보관 금지"},
        
        # 중량물 이동 (6개 항목)
        {"번호": 15, "대분류": "중량물 이동", "소분류": "중량물이동-안전작업계획서 작성 및 승인"},
        {"번호": 16, "대분류": "중량물 이동", "소분류": "중량물이동-평지 이동 시 이동수레 활용 주의사항"},
        {"번호": 17, "대분류": "중량물 이동", "소분류": "중량물이동-계단 이동 시 2인1조 이동 여부"},
        {"번호": 18, "대분류": "중량물 이동", "소분류": "중량물이동-고소차량 활용 낙화물 방지 고정"},
        {"번호": 19, "대분류": "중량물 이동", "소분류": "중량물이동-산길이동 시 이동용 가방 활용"},
        {"번호": 20, "대분류": "중량물 이동", "소분류": "중량물이동-중량물 인양 시 풀림방지 기능 도르레 활용"},
        
        # 화기 작업 (5개 항목)
        {"번호": 21, "대분류": "화기 작업", "소분류": "화기 작업-적절한 보호구/보호조치 시행"},
        {"번호": 22, "대분류": "화기 작업", "소분류": "화기 작업-소화기 및 비상시 행동요령 숙지"},
        {"번호": 23, "대분류": "화기 작업", "소분류": "화기 작업-작업공간 출입통제 및 작업구역 환기"},
        {"번호": 24, "대분류": "화기 작업", "소분류": "화기 작업-가연성,인화성 물질에 대한 보양조치"},
        {"번호": 25, "대분류": "화기 작업", "소분류": "화기 작업-용접케이블 및 호스 손상 유무 확인"},
        
        # 3대 사고 예방 조치 (추락/끼임/부딪힘) (12개 항목)
        {"번호": 26, "대분류": "3대 사고 예방 조치", "소분류": "추락 예방 안전 조치-안전난간,추락방호망,안전대 착용"},
        {"번호": 27, "대분류": "3대 사고 예방 조치", "소분류": "추락 예방 안전 조치-달비계 작업용로프, 안전대 체결"},
        {"번호": 28, "대분류": "3대 사고 예방 조치", "소분류": "추락 예방 안전 조치-이동식 비계 최상단 안전난간 및 작업발판 설치"},
        {"번호": 29, "대분류": "3대 사고 예방 조치", "소분류": "건설 기계장비, 설비 등 안전 및 방호조치-차량계 건설기계, 하역운반기계 안전 조치"},
        {"번호": 30, "대분류": "3대 사고 예방 조치", "소분류": "건설 기계장비, 설비 등 안전 및 방호조치-정비,보수 시 안전수칙"},
        {"번호": 31, "대분류": "3대 사고 예방 조치", "소분류": "혼재 작업(부딪힘) 시 안전 예방 조치-관계자외 출입금지"},
        {"번호": 32, "대분류": "3대 사고 예방 조치", "소분류": "혼재 작업(부딪힘) 시 안전 예방 조치-작업구간,이동동선 구획 상태"},
        {"번호": 33, "대분류": "3대 사고 예방 조치", "소분류": "혼재 작업(부딪힘) 시 안전 예방 조치-작업지휘자,유도자,신호수배치,통제"},
        {"번호": 34, "대분류": "3대 사고 예방 조치", "소분류": "충돌 방지 조치-건설기계장비 결함 및 작동이상 여부 확인"},
        {"번호": 35, "대분류": "3대 사고 예방 조치", "소분류": "충돌 방지 조치-인양/하역작업시 부딪힘 안전 조치"},
        {"번호": 36, "대분류": "3대 사고 예방 조치", "소분류": "충돌 방지 조치-차량계 건설기계의 주용도 외 사용금지"},
        {"번호": 37, "대분류": "3대 사고 예방 조치", "소분류": "충돌 방지 조치-자재,중량물의 적재장소 상태 확인"}
    ]
    
    return pd.DataFrame(checklist_data)

# Excel 파일에서 체크리스트 로드
@st.cache_data
def load_predefined_checklist(file_path="SGR현장 체크리스트_변환2_수정.xlsx"):
    """Excel 파일의 A열(대분류)과 B열(소분류)에서 체크리스트를 로드합니다."""
    try:
        if os.path.exists(file_path):
            # pandas로 Excel 파일 읽기
            df = pd.read_excel(file_path, sheet_name=0)
            
            if len(df.columns) >= 2:
                checklist_items = []
                current_category = ""
                item_number = 1
                
                for idx, row in df.iterrows():
                    a_value = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                    b_value = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                    
                    # A열에 값이 있으면 대분류 업데이트
                    if a_value and a_value not in ["구분", "nan"]:
                        # 줄바꿈 문자 제거
                        current_category = a_value.replace('\n', ' ').replace('\r', ' ').strip()
                    
                    # B열 값이 체크리스트 항목인지 확인
                    if b_value and current_category and current_category != "구분":
                        # 번호가 포함된 항목들 처리
                        if any(b_value.startswith(f"{i})") for i in range(1, 20)):
                            # 번호 제거
                            clean_item = b_value.split(')', 1)[1].strip() if ')' in b_value else b_value
                            checklist_items.append({
                                "번호": item_number,
                                "대분류": current_category,
                                "소분류": clean_item
                            })
                            item_number += 1
                        # 특정 키워드가 포함된 항목들도 포함
                        elif any(keyword in b_value for keyword in ['MSDS', '중량물이동', '화기 작업', '추락 예방', '건설 기계장비', '혼재 작업', '충돌 방지']):
                            checklist_items.append({
                                "번호": item_number,
                                "대분류": current_category,
                                "소분류": b_value
                            })
                            item_number += 1
                
                if checklist_items:
                    checklist_df = pd.DataFrame(checklist_items)
                    st.success(f"✅ Excel 파일에서 {len(checklist_items)}개의 체크리스트 항목을 로드했습니다.")
                    return checklist_df
                else:
                    st.warning("⚠️ Excel 파일에서 체크리스트 항목을 찾을 수 없습니다. 기본 체크리스트를 사용합니다.")
                    return create_default_checklist()
            else:
                st.warning("⚠️ Excel 파일에 A열, B열 데이터가 부족합니다. 기본 체크리스트를 사용합니다.")
                return create_default_checklist()
                
        else:
            st.info(f"ℹ️ 체크리스트 파일 '{file_path}'을 찾을 수 없습니다. 기본 체크리스트를 사용합니다.")
            return create_default_checklist()
            
    except Exception as e:
        st.warning(f"⚠️ 체크리스트 파일 로드 중 오류: {str(e)}. 기본 체크리스트를 사용합니다.")
        return create_default_checklist()

# 이미지 인코딩 함수
def encode_image(image: Image) -> str:
    """PIL Image를 base64로 인코딩하는 함수"""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    return base64.b64encode(image_bytes).decode('utf-8')

# 분석 결과 파싱 함수들
def parse_analysis_sections(analysis_text: str) -> dict:
    """GPT 분석 결과를 섹션으로 구분하여 파싱하는 함수"""
    sections = {
        "work_environment": "",
        "risk_analysis": "",
        "sgr_checklist": "",
        "recommendations": ""
    }
    
    lines = analysis_text.split('\n')
    current_section = None
    current_content = []
    section_started = False
    
    for line in lines:
        line_stripped = line.strip()

        # 섹션 감지
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

        # 본문 내용 수집
        if current_section and section_started:
            current_content.append(line)

    # 마지막 섹션 저장
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections

def parse_sgr_checklist_to_dataframe(checklist_text: str) -> pd.DataFrame:
    """SGR 체크리스트 마크다운 텍스트를 DataFrame으로 변환하는 함수"""
    if not checklist_text or checklist_text.strip() == "":
        return pd.DataFrame(columns=["번호", "대분류", "소분류", "준수여부", "세부내용"])
    
    lines = checklist_text.split('\n')
    checklist_data = []
    
    for line in lines:
        line = line.strip()
        
        # 빈 줄이나 구분선 건너뛰기
        if not line or line.startswith('|---') or line.startswith('|===') or line.startswith('#'):
            continue
            
        # 테이블 행 파싱 - 파이프(|)로 구분된 행 찾기
        if "|" in line and line.count('|') >= 4:  # 최소 5개 컬럼 필요
            parts = [x.strip() for x in line.split('|')]
            
            # 빈 문자열 제거 (맨 앞과 뒤)
            while parts and parts[0] == '':
                parts = parts[1:]
            while parts and parts[-1] == '':
                parts = parts[:-1]
            
            # 최소 4개 컬럼이 있어야 함 (번호, 대분류, 소분류, 준수여부, 세부내용)
            if len(parts) >= 4:
                # 헤더 행 건너뛰기
                first_col = parts[0].lower()
                if any(header in first_col for header in ['번호', 'header', '대분류']):
                    continue
                
                try:
                    # 첫 번째 컬럼이 번호인지 확인
                    int(parts[0])  # 숫자인지 확인
                    
                    checklist_data.append([
                        parts[0],  # 번호
                        parts[1],  # 대분류
                        parts[2],  # 소분류
                        parts[3],  # 준수여부
                        parts[4] if len(parts) > 4 else ""   # 세부내용
                    ])
                        
                except (ValueError, IndexError, AttributeError):
                    # 파싱 실패 시 건너뛰기
                    continue
    
    # DataFrame 생성
    if checklist_data:
        df = pd.DataFrame(checklist_data, columns=["번호", "대분류", "소분류", "준수여부", "세부내용"])
        # 번호 순으로 정렬
        try:
            df['번호_int'] = df['번호'].astype(int)
            df = df.sort_values('번호_int').drop('번호_int', axis=1)
        except:
            pass
        return df
    else:
        return pd.DataFrame(columns=["번호", "대분류", "소분류", "준수여부", "세부내용"])

def parse_risk_analysis_to_dataframe(risk_text: str) -> pd.DataFrame:
    """위험요인 분석 마크다운 텍스트를 DataFrame으로 변환하는 함수"""
    lines = risk_text.split('\n')
    risk_data = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('|---') or line.startswith('|==='):
            continue
            
        if "|" in line and line.startswith('|') and line.endswith('|'):
            parts = [x.strip() for x in line.split('|')]
            parts = [part for part in parts if part]
            
            if len(parts) >= 4 and not any(header in parts[0].lower() for header in ['번호', 'header']):
                try:
                    int(parts[0])
                    if len(parts) >= 4:
                        risk_data.append([
                            parts[0],
                            parts[1],
                            parts[2],
                            parts[3]
                        ])
                except ValueError:
                    continue
    
    if risk_data:
        df = pd.DataFrame(risk_data, columns=["번호", "잠재 위험요인", "잠재 위험요인 설명", "위험성 감소대책"])
    else:
        df = pd.DataFrame([
            ["1", "개인보호구 착용", "작업 시 필수 개인보호구 착용 필요", "① 안전모 착용 ② 안전화 착용 ③ 필요시 안전대 착용 ④ 보호장갑 착용"],
            ["2", "작업 전 안전교육", "작업 전 TBM 실시 및 안전교육", "① 작업 전 TBM 실시 ② 작업자 건강상태 확인 ③ 작업계획 및 위험요소 공유 ④ 비상연락체계 확인"]
        ], columns=["번호", "잠재 위험요인", "잠재 위험요인 설명", "위험성 감소대책"])
    
    return df

def format_checklist_content(content: str) -> str:
    """SGR 체크리스트 내용에서 준수여부에 따라 스타일을 적용하는 함수"""
    if not content:
        return content
    
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith('|---') or line_stripped.startswith('|==='):
            formatted_lines.append(line)
            continue
        
        if '|' in line and line_stripped.startswith('|') and line_stripped.endswith('|'):
            parts = line.split('|')
            
            if len(parts) >= 4:  # 번호, 체크리스트항목, 준수여부, 세부내용
                col0 = parts[0]
                col1 = parts[1].strip()  # 번호 + 체크리스트항목
                col2 = parts[2].strip()  # 준수여부  
                col3 = parts[3].strip()  # 세부내용
                col4 = parts[4] if len(parts) > 4 else ""
                
                # 헤더 행 확인
                if any(header in col1.lower() for header in ['번호', 'header', '준수여부', '체크리스트']):
                    formatted_lines.append(line)
                    continue
                
                # 준수여부에 따른 스타일 적용
                if col2 == 'X':
                    formatted_line = f"{col0}| **<span style='color: red; font-weight: bold;'>{col1}</span>** | **<span style='color: red; font-weight: bold;'>{col2}</span>** | **<span style='color: red; font-weight: bold;'>{col3}</span>** |{col4}"
                    formatted_lines.append(formatted_line)
                elif col2 == '알수없음':
                    formatted_line = f"{col0}| **{col1}** | **{col2}** | **{col3}** |{col4}"
                    formatted_lines.append(formatted_line)
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

# 체크리스트를 대분류, 소분류 별도 컬럼으로 프롬프트 생성
def generate_checklist_prompt(checklist_df: pd.DataFrame) -> str:
    """체크리스트를 대분류, 소분류 별도 컬럼으로 프롬프트 생성"""
    prompt_lines = []
    
    # 번호 순으로 정렬
    sorted_checklist = checklist_df.sort_values('번호')
    
    for _, item in sorted_checklist.iterrows():
        prompt_lines.append(f"| {item['번호']} | {item['대분류']} | {item['소분류']} | [O 또는 X 또는 해당없음 또는 알수없음] | [현장 사진들에서 확인된 구체적 상황] |")
    
    return '\n'.join(prompt_lines)

# 메인 분석 함수
def analyze_multiple_images_comprehensive(images: list, checklist: pd.DataFrame, image_names: list) -> dict:
    """여러 이미지를 통합하여 종합적인 안전 위험성 평가를 수행합니다."""
    client = initialize_openai_client()
    if client is None:
        raise Exception("OpenAI 클라이언트가 초기화되지 않았습니다.")
    
    # 모든 이미지를 base64로 인코딩
    base64_images = []
    for image in images:
        base64_images.append(encode_image(image))
    
    # 체크리스트 프롬프트 생성
    checklist_prompt = generate_checklist_prompt(checklist)
    
    # 통합 분석을 위한 프롬프트
    prompt = f"""
Role(역할지정): 산업안전 위험성 평가 전문가로서 동일한 공사현장의 여러 사진을 종합적으로 분석하여 통합된 작업전 위험성 평가서를 작성합니다.

목표: 첨부된 {len(images)}장의 현장 사진들을 종합적으로 분석하여 다음과 같은 통합 위험성 평가서를 작성하세요:

**중요사항**: 
- 제공된 {len(images)}장의 사진은 모두 동일한 공사현장의 서로 다른 각도/영역을 촬영한 것입니다.
- 모든 사진을 종합적으로 분석하여 현장 전체의 통합된 위험성 평가를 수행해주세요.
- 각 사진별로 개별 분석하지 말고, 전체 현장의 종합적인 관점에서 분석해주세요.

분석 대상 이미지: {', '.join(image_names)}

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

| 번호 | 대분류 | 소분류 | 준수여부 | 세부 내용 |
|------|--------|--------|----------|-----------|
{checklist_prompt}

## 3. 현장 전체 통합 추가 권장사항
[현장 전체 특성에 맞는 종합적이고 구체적인 안전 권장사항을 작성]

제약사항:
- 모든 내용은 실제 산업안전보건 기준에 부합하도록 구체적이고 실무적인 수준으로 작성
- 위험성 감소대책은 각각 4개 이상의 구체적인 조치로 구성
- 체크리스트는 현장 전체 상황에 맞게 O, X , 해당없음 , 알수없음 중 하나로 표시하고 구체적인 확인 내용도 포함
  O: 사진에서 준수가 명확히 확인됨, X: 사진에서 명확히 미준수가 확인됨, 해당없음: 준수가 필요 없는 항목임, 알수없음: 이미지의 내용으로 확인 불가한 경우
- 모든 출력은 한국어로 작성
- 실무에서 바로 활용 가능한 수준의 상세한 내용 포함
- 개별 사진 분석이 아닌 현장 전체의 통합적 관점에서 분석
- 체크리스트는 번호 순서대로 연속적으로 작성 (대분류 구분 없이 하나의 테이블로 작성)

첨부된 {len(images)}장의 이미지를 모두 종합적으로 분석하여 위 지침에 따라 통합된 위험성 평가서를 작성해주세요.
"""
    
    # 이미지 메시지 구성
    message_content = [{"type": "text", "text": prompt}]
    
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
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": message_content
            }
        ],
        max_tokens=4000
    )
    
    # GPT의 분석 결과를 가져오기
    analysis_result = response.choices[0].message.content
    
    return {
        "image_names": image_names,
        "image_count": len(images),
        "full_report": analysis_result,
        "sections": parse_analysis_sections(analysis_result),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def create_section_files(sections: dict, timestamp: str) -> dict:
    """각 섹션을 개별 파일로 생성하는 함수"""
    files = {}

    if sections["work_environment"]:
        files["work_environment"] = f"""# 통합 작업 환경 설명

생성 시간: {timestamp}

{sections["work_environment"]}
"""
        
    if sections["risk_analysis"]:
        files["risk_analysis"] = f"""# 현장 전체 잠재 위험요인 분석 및 위험성 감소대책

생성 시간: {timestamp}

{sections["risk_analysis"]}
"""

    if sections["sgr_checklist"]:
        files["sgr_checklist"] = f"""# SGR 체크리스트 항목별 통합 체크 결과

생성 시간: {timestamp}

{sections["sgr_checklist"]}
"""

    if sections["recommendations"]:
        files["recommendations"] = f"""# 현장 전체 통합 추가 권장사항

생성 시간: {timestamp}

{sections["recommendations"]}
"""

    return files

# 파일 다운로드 관련 함수들
def create_zip_download(sections: dict, timestamp: str) -> bytes:
    """전체 섹션을 ZIP 파일로 생성"""
    section_files = create_section_files(sections, timestamp)
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 마크다운 파일 추가
        korean_names = {
            "risk_analysis": "1.위험요인분석",
            "sgr_checklist": "2.체크리스트",
            "recommendations": "3.추가권장사항"
        }
        
        for file_name, content in section_files.items():
            if file_name in korean_names:
                zip_file.writestr(
                    f"{korean_names[file_name]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    content.encode('utf-8-sig')
                )
        
        # CSV 파일 추가
        try:
            if sections.get("risk_analysis"):
                risk_df = parse_risk_analysis_to_dataframe(sections["risk_analysis"])
                if not risk_df.empty:
                    risk_csv = risk_df.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr(
                        f"1.위험요인분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        risk_csv.encode('utf-8-sig')
                    )
            
            if sections.get("sgr_checklist"):
                checklist_df = parse_sgr_checklist_to_dataframe(sections["sgr_checklist"])
                if checklist_df is not None and not checklist_df.empty:
                    checklist_csv = checklist_df.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr(
                        f"2.체크리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        checklist_csv.encode('utf-8-sig')
                    )
        except Exception as e:
            st.warning(f"⚠️ CSV 파일 생성 중 일부 오류 발생: {str(e)}")
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# 메인 UI 함수들
def render_header():
    """헤더 렌더링"""
    st.markdown("""
    <div class="main-header">
        <h1>🏗️ AI 위험성 평가 시스템</h1>
        <p>현장 사진을 업로드하여 종합적인 안전 위험성 평가를 받으세요</p>
    </div>
    """, unsafe_allow_html=True)

def render_image_upload():
    """이미지 업로드 섹션 렌더링"""
    st.markdown("""
    <div class="upload-section">
        <h3>📸 작업 환경 이미지 업로드</h3>
        <p>동일한 공사현장의 작업 환경 이미지를 업로드하세요 (다중 업로드 가능)</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_images = st.file_uploader(
        "이미지 파일을 선택하세요",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="동일한 현장의 여러 각도/영역 사진을 업로드하면 통합된 위험성 평가를 수행합니다.",
        key="image_uploader"
    )
    
    return uploaded_images

def render_image_preview(uploaded_images):
    """업로드된 이미지 미리보기"""
    if uploaded_images:
        st.markdown("### 📷 업로드된 이미지")
        
        # 이미지를 3열로 표시
        num_cols = min(len(uploaded_images), 3)
        cols = st.columns(num_cols)
        
        for idx, image_file in enumerate(uploaded_images):
            with cols[idx % num_cols]:
                image = Image.open(image_file)
                st.image(image, caption=f"📷 {image_file.name}", use_container_width=True)
        
        # 정보 메시지
        if len(uploaded_images) == 1:
            st.markdown("""
            <div class="info-box">
                💡 1개의 이미지가 업로드되었습니다. 단일 이미지 기반 위험성 평가를 수행합니다.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="info-box">
                💡 총 {len(uploaded_images)}개의 이미지가 업로드되었습니다. 동일한 현장의 사진들로 간주하여 <strong>통합 위험성 평가</strong>를 수행합니다.
            </div>
            """, unsafe_allow_html=True)

def render_analysis_button(uploaded_images, checklist):
    """분석 버튼 및 분석 실행"""
    if not uploaded_images:
        return False
        
    analysis_mode = "통합 분석" if len(uploaded_images) > 1 else "단일 이미지 분석"
    
    st.markdown("### 🚀 위험성 평가 분석")
    
    if st.button(
        f"📊 {analysis_mode} - 종합 위험성 평가서 생성", 
        type="primary", 
        use_container_width=True,
        key="analysis_button"
    ):
        client = initialize_openai_client()
        if client is None:
            st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
            return False
        elif checklist is None or checklist.empty:
            st.error("❌ 체크리스트를 로드할 수 없습니다.")
            return False
        else:
            try:
                # 진행 상황 표시
                with st.spinner(f"🤖 AI가 {len(uploaded_images)}장의 현장 사진을 종합 분석하여 통합 위험성 평가서를 생성하고 있습니다..."):
                    
                    # 이미지들을 PIL Image 객체로 변환
                    images = []
                    image_names = []
                    
                    for image_file in uploaded_images:
                        image = Image.open(image_file)
                        images.append(image)
                        image_names.append(image_file.name)
                    
                    # 통합 분석 수행
                    result = analyze_multiple_images_comprehensive(images, checklist, image_names)
                
                # 분석 결과를 세션 상태에 저장
                st.session_state['analysis_result'] = result
                st.session_state['analysis_completed'] = True

                st.success("✅ 통합 위험성 평가서 생성 완료!")
                return True

            except Exception as e:
                st.error(f"❌ 분석 중 오류 발생: {str(e)}")
                st.info("💡 오류가 지속되면 이미지 크기를 줄이거나 장수를 줄여서 다시 시도해보세요.")
                return False
    
    return False

def render_analysis_results():
    """분석 결과 렌더링"""
    if not st.session_state.get('analysis_completed', False) or 'analysis_result' not in st.session_state:
        return
    
    result = st.session_state['analysis_result']
    sections = result.get('sections', {})
    section_files = create_section_files(sections, result['timestamp'])

    st.markdown("---")
    st.header("📋 AI 위험성 평가 결과")

    # 결과 요약 정보
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("분석된 이미지", f"{result['image_count']}장")
    with col2:
        st.metric("생성 시간", result['timestamp'])
    with col3:
        st.metric("분석 섹션", f"{len([s for s in sections.values() if s])-1}개")

    # 섹션별 탭 생성
    tab1, tab2, tab3 = st.tabs([
        "✅ SGR 체크리스트",
        "🔍 위험요인 분석", 
        "💡 추가 권장사항"
    ])

    with tab1:
        st.subheader("📋 SGR 체크리스트 결과")
        
        if sections.get("sgr_checklist"):
            # 체크리스트 내용에 스타일 적용
            formatted_checklist = format_checklist_content(sections["sgr_checklist"])
            st.markdown(formatted_checklist, unsafe_allow_html=True)
            
            # 다운로드 버튼
            try:
                checklist_df = parse_sgr_checklist_to_dataframe(sections["sgr_checklist"])
                if checklist_df is not None and not checklist_df.empty:
                    checklist_csv = checklist_df.to_csv(index=False, encoding='utf-8-sig')
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 체크리스트 CSV 다운로드",
                            data=checklist_csv.encode('utf-8-sig'),
                            file_name=f"SGR체크리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="checklist_csv_download"
                        )
                    with col2:
                        if "sgr_checklist" in section_files:
                            st.download_button(
                                label="📥 체크리스트 MD 다운로드",
                                data=section_files["sgr_checklist"].encode('utf-8-sig'),
                                file_name=f"SGR체크리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                key="sgr_md_download"
                            )
                else:
                    st.warning("⚠️ 체크리스트를 DataFrame으로 변환할 수 없습니다.")
                    # MD 파일만 다운로드 제공
                    if "sgr_checklist" in section_files:
                        st.download_button(
                            label="📥 체크리스트 MD 다운로드",
                            data=section_files["sgr_checklist"].encode('utf-8-sig'),
                            file_name=f"SGR체크리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            key="sgr_md_download_only"
                        )
            except Exception as e:
                st.warning(f"⚠️ 체크리스트 파싱 중 오류: {str(e)}")
                # 오류 발생 시에도 MD 파일은 다운로드 가능하도록
                if "sgr_checklist" in section_files:
                    st.download_button(
                        label="📥 체크리스트 MD 다운로드 (원본)",
                        data=section_files["sgr_checklist"].encode('utf-8-sig'),
                        file_name=f"SGR체크리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        key="sgr_md_download_error"
                    )
        else:
            st.info("체크리스트 섹션의 내용을 찾을 수 없습니다.")

    with tab2:
        st.subheader("🔍 잠재 위험요인 및 감소대책")
        
        if sections.get("risk_analysis"):
            st.markdown(sections["risk_analysis"])
            
            try:
                risk_df = parse_risk_analysis_to_dataframe(sections["risk_analysis"])
                if not risk_df.empty:
                    risk_csv = risk_df.to_csv(index=False, encoding='utf-8-sig')
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 위험요인 분석 CSV 다운로드",
                            data=risk_csv.encode('utf-8-sig'),
                            file_name=f"위험요인분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="risk_csv_download"
                        )
                    with col2:
                        if "risk_analysis" in section_files:
                            st.download_button(
                                label="📥 위험요인 분석 MD 다운로드",
                                data=section_files["risk_analysis"].encode('utf-8-sig'),
                                file_name=f"위험요인분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                key="risk_md_download"
                            )
            except Exception as e:
                st.warning(f"⚠️ 위험요인 분석 파싱 중 오류: {str(e)}")
        else:
            st.info("위험요인 분석 섹션의 내용을 찾을 수 없습니다.")

    with tab3:
        st.subheader("💡 현장 추가 권장사항")
        
        if sections.get("recommendations"):
            st.markdown(sections["recommendations"])
            if "recommendations" in section_files:
                st.download_button(
                    label="📥 추가 권장사항 다운로드",
                    data=section_files["recommendations"].encode('utf-8-sig'),
                    file_name=f"추가권장사항_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="rec_download"
                )
        else:
            st.info("추가 권장사항 섹션의 내용을 찾을 수 없습니다.")

    # 전체 통합 다운로드
    if section_files:
        st.markdown("---")
        st.subheader("📦 전체 결과 통합 다운로드")
        
        zip_data = create_zip_download(sections, result['timestamp'])
        st.download_button(
            label="📁 전체 결과 ZIP 다운로드 (MD + CSV 파일 포함)",
            data=zip_data,
            file_name=f"위험성평가결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            key="zip_download"
        )

def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.markdown("### ℹ️ 사용 방법")
        st.markdown("""
        1. **이미지 업로드**: 현장 사진을 업로드하세요
        2. **분석 시작**: 분석 버튼을 클릭하세요
        3. **결과 확인**: 생성된 보고서를 확인하세요
        4. **파일 다운로드**: 필요한 파일을 다운로드하세요
        """)
        
        st.markdown("### ⚙️ 시스템 정보")
        client = initialize_openai_client()
        if client:
            st.success("✅ OpenAI API 연결됨")
        else:
            st.error("❌ OpenAI API 연결 실패")
        
        # 체크리스트 미리보기
        st.markdown("### 📋 SGR 체크리스트 미리보기")
        checklist = load_predefined_checklist()
        if not checklist.empty:
            st.success(f"✅ {len(checklist)}개 항목 로드됨")
            
            # 대분류별 통계
            category_counts = checklist['대분류'].value_counts()
            
            with st.expander("대분류별 항목 수", expanded=False):
                for category, count in category_counts.items():
                    st.markdown(f"**{category}**: {count}개")
            
            # 체크리스트 항목 미리보기
            with st.expander("체크리스트 항목 미리보기", expanded=False):
                # 각 대분류별로 첫 번째 항목만 표시
                for category in checklist['대분류'].unique():
                    category_items = checklist[checklist['대분류'] == category]
                    st.markdown(f"**📂 {category}**")
                    first_item = category_items.iloc[0]
                    st.markdown(f"   {first_item['번호']}. {first_item['소분류'][:40]}{'...' if len(first_item['소분류']) > 40 else ''}")
                    if len(category_items) > 1:
                        st.markdown(f"   ... 외 {len(category_items) - 1}개 항목")
                    st.markdown("")
        else:
            st.error("❌ 체크리스트 로드 실패")
        
        st.markdown("### 📞 지원")
        st.markdown("""
        문제가 발생하면 다음을 확인하세요:
        - 이미지 파일 크기 (5MB 이하 권장)
        - 지원 파일 형식: JPG, JPEG, PNG
        - 인터넷 연결 상태
        - OpenAI API 키 설정
        """)
        
        st.markdown("### 📄 체크리스트 구조")
        st.markdown("""
        **대분류별 구성:**
        - **SGR 준수** (9개 항목)
        - **유해위험물** (4개 항목)  
        - **중량물 이동** (6개 항목)
        - **화기 작업** (5개 항목)
        - **3대 사고 예방 조치** (12개 항목)
        
        총 **36개 세부 체크리스트 항목**으로 구성되어 있습니다.
        """)

# 메인 앱 실행
def main():
    """메인 애플리케이션 함수"""
    # 앱 초기화
    initialize_app()
    
    # 사이드바 렌더링
    render_sidebar()
    
    # 헤더 렌더링
    render_header()
    
    # 체크리스트 로드
    checklist = load_predefined_checklist()
    
    # 이미지 업로드 섹션
    uploaded_images = render_image_upload()
    
    # 이미지 미리보기
    render_image_preview(uploaded_images)
    
    # 분석 버튼 및 실행
    if uploaded_images:
        render_analysis_button(uploaded_images, checklist)
    else:
        st.markdown("""
        <div class="info-box">
            📋 작업 환경 이미지를 업로드하면 분석 버튼이 활성화됩니다.
        </div>
        """, unsafe_allow_html=True)
    
    # 분석 결과 표시
    render_analysis_results()

# 앱 실행
if __name__ == "__main__":
    main()