import streamlit as st
from azure_config import azure_config
from document_uploader import document_uploader, get_blob_files

# DocumentUploader import
try:
    from document_uploader import document_uploader, get_blob_files
    UPLOADER_AVAILABLE = True
except ImportError:
    UPLOADER_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="Onboarding Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []

# 헤더
st.title("🤖 Onboarding Assistant")
st.markdown("**AI 기반 프로젝트 적응 도우미** - 문서 분석 & 기술 학습 가이드")
st.divider()

# 3분할 레이아웃 구성
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.header("📁 문서 업로드")
    st.info("운영 매뉴얼 등 프로젝트 문서들을 업로드하세요")
    
    # 파일 업로드 위젯 (기본)
    uploaded_files = st.file_uploader(
        "문서를 선택하세요",
        type=['pdf', 'docx', 'txt', 'md'],
        accept_multiple_files=True,
        help="PDF, Word, 텍스트, 마크다운 파일을 지원합니다"
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)}개 파일이 업로드되었습니다")

        # 업로드된 각 파일에 대한 처리 버튼
        for i, file in enumerate(uploaded_files):
            with st.expander(f"📄 {file.name}"):
                st.write(f"**파일 크기:** {file.size:,} bytes")
                st.write(f"**파일 타입:** {file.type}")
                
                # Blob Storage 업로드 버튼
                if UPLOADER_AVAILABLE:
                        if st.button(f"파일 업로드", key=f"upload_{i}"):
                            with st.spinner("파일 처리 중..."):
                                result = document_uploader.process_single_file(file)
                                
                                if result["success"]:
                            
                                    # 세션 상태에 결과 저장
                                    st.session_state.processed_files.append(result)
                                    
                                    # 업로드 정보 표시
                                    st.write("**업로드 완료 정보:**")
                                    st.write(f"• 문서 ID: `{result['document_id']}`")
                                    st.write(f"• 텍스트 길이: {len(result['extracted_text'])}자")
                                    
                                    # Blob URL 링크
                                    st.markdown(f"🔗 [파일 보기]({result['blob_url']})") # TODO : 링크 접근 가능하도록
                                    
                                else:
                                    st.error(f"업로드 실패: {result['error']}")
                else:
                    st.warning("DocumentUploader를 사용하려면 document_uploader.py가 필요합니다.")


with col2:
    st.header("📊 문서 요약 & 기술 정보")
    st.info("문서 요약 및 필요한 기술 정보를 자동으로 추출합니다")
    
    # 플레이스홀더 컨텐츠
    with st.container():
        st.subheader("📋 문서 통합 요약")
        st.write("업로드된 문서들을 통합하여 요약합니다.")
        
        st.subheader("🛠️ 기술 정보")
        st.write("습득이 필요한 기술 정보가 표시됩니다.")

with col3:
    st.header("💬 질의응답")
    st.info("자연어로 질문하시면 AI가 답변해드립니다")
    
    # 기본 채팅 인터페이스
    user_question = st.text_input("질문을 입력하세요:", placeholder="예: 서버 정보들은 어떤 문서에 있나요?")
    
    if st.button("질문하기"):
        if user_question:
            st.write("**AI 응답:**")
            st.write("문서를 업로드하고 분석이 완료되면 질문에 답변해드립니다.")
        else:
            st.warning("질문을 입력해주세요!")

# 푸터
st.divider()
st.markdown("*Azure OpenAI와 Azure AI Search 기반으로 구동됩니다*")