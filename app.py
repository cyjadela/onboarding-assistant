import streamlit as st
from azure_config import azure_config
from document_uploader import document_uploader, get_blob_files

# DocumentUploader import
try:
    from document_uploader import document_uploader, get_blob_files

    UPLOADER_AVAILABLE = True
except ImportError:
    UPLOADER_AVAILABLE = False

# DocumentProcessor import
try:
    from document_processor import document_processor

    PROCESSOR_AVAILABLE = True
except ImportError:
    PROCESSOR_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="Onboarding Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 스타일
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        text-align: center;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }

    /* 섹션 헤더 스타일 */
    .section-header {
        background: #495057;
        color: white;
        padding: 0.8rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: 500;
        font-size: 1.1rem;
    }
    
    /* 답변 박스 스타일 */
    .answer-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 6px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    
    /* 간단한 정보 표시 */
    .simple-info {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        color: #495057;
    }
    
    .success-info {
        background: #d4edda;
        color: #155724;
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        border: 1px solid #c3e6cb;
    }
    
    .warning-info {
        background: #fff3cd;
        color: #856404;
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        border: 1px solid #ffeaa7;
    }
    
    /* 텍스트 하이라이트 */
    .highlight {
        background: #fff3cd;
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
        font-weight: 500;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 세션 상태 초기화
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []
if "integrated_tech_guide" not in st.session_state:
    st.session_state.integrated_tech_guide = None

# 메인 헤더
st.markdown(
    """
<div class="main-header">
    <h1>🤖 Onboarding Assistant</h1>
    <p>AI 기반 프로젝트 적응 도우미 - 문서 분석 & 기술 학습 가이드</p>
</div>
""",
    unsafe_allow_html=True,
)

# 3분할 레이아웃 구성
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown(
        '<div class="section-header">📁 문서 업로드</div>', unsafe_allow_html=True
    )

    st.info("운영 매뉴얼, 기술 문서 등을 업로드하세요")

    # 파일 업로드 위젯
    uploaded_files = st.file_uploader(
        "문서를 선택하세요",
        type=["pdf", "docx", "txt", "md", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="PDF, DOCX, Word, 이미지, 텍스트, 마크다운 파일을 지원합니다",
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)}개 파일이 선택되었습니다")

        # 업로드된 파일들 처리
        for i, file in enumerate(uploaded_files):
            with st.expander(f"📄 {file.name}", expanded=False):
                st.write(f"**파일 크기:** {file.size:,} bytes")
                st.write(f"**파일 타입:** {file.type}")

                if UPLOADER_AVAILABLE:
                    if st.button(f"처리하기", key=f"upload_{i}"):
                        with st.spinner("파일 처리 중..."):
                            result = document_uploader.process_single_file(file)

                            if result["success"]:
                                st.session_state.processed_files.append(result)

                                st.markdown(
                                    f"""
                                <div class="success-info">
                                    <strong>✅ 처리 완료</strong><br>
                                    문서 ID: <code>{result['document_id']}</code><br>
                                    텍스트 길이: {len(result['extracted_text'])}자<br>
                                    <a href="{result['blob_url']}" target="_blank">🔗 파일 보기</a>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                st.session_state.integrated_tech_guide = None
                                st.rerun()
                            else:
                                st.markdown(
                                    f"""
                                <div class="warning-info">
                                    <strong>⚠️ 처리 실패</strong><br>
                                    {result['error']}
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                else:
                    st.warning("DocumentUploader 모듈이 필요합니다.")

with col2:
    st.markdown(
        '<div class="section-header">📊 문서 요약 & 통합 기술 가이드</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.processed_files:
        # 개별 문서 요약들
        st.subheader("📄 개별 문서 요약")

        for file_result in st.session_state.processed_files:
            if file_result.get("success") and "processing_results" in file_result:
                with st.expander(f"📄 {file_result['file_name']} 요약", expanded=False):
                    if "summary" in file_result["processing_results"]:
                        summary_result = file_result["processing_results"]["summary"]
                        if summary_result.get("success"):
                            # Streamlit 기본 컨테이너 사용
                            with st.container():
                                # st.markdown("---")  # 구분선
                                st.markdown(summary_result["summary"])
                                # st.markdown("---")  # 구분선
                        else:
                            st.error(
                                f"요약 생성 실패: {summary_result.get('error', '알 수 없는 오류')}"
                            )

                    if "indexing" in file_result["processing_results"]:
                        index_result = file_result["processing_results"]["indexing"]
                        if index_result.get("success"):
                            st.success(
                                f"✅ AI Search 인덱싱 완료 ({index_result['indexed_chunks']}개 청크)"
                            )
                        else:
                            st.error(
                                f"인덱싱 실패: {index_result.get('error', '알 수 없는 오류')}"
                            )

            elif file_result.get("processing_error"):
                st.warning(f"⚠️ {file_result['file_name']}: 분석 중 오류 발생")

        # 통합 기술 가이드 섹션
        #    st.subheader("🚀 통합 기술 학습 가이드")

        generate_guide_btn = st.button(
            "통합 기술 가이드 생성", type="primary", use_container_width=True
        )

        if generate_guide_btn and PROCESSOR_AVAILABLE:
            with st.spinner("통합 기술 가이드를 생성하고 있습니다..."):
                try:
                    guide_result = document_processor.generate_integrated_tech_guide(
                        st.session_state.processed_files
                    )

                    if guide_result["success"]:
                        st.session_state.integrated_tech_guide = guide_result
                        st.success("✅ 통합 기술 가이드 생성 완료!")
                        st.rerun()
                    else:
                        st.error(f"가이드 생성 실패: {guide_result['error']}")

                except Exception as e:
                    st.error(f"예외 발생: {str(e)}")

        # 통합 기술 가이드 표시
        if st.session_state.integrated_tech_guide:
            guide_data = st.session_state.integrated_tech_guide

            #  st.markdown("### 🎯 프로젝트 기술 학습 가이드")
            # Streamlit 기본 컨테이너 사용
            with st.container():
                # st.markdown("---")  # 구분선
                st.markdown(guide_data["tech_guide"])
                st.markdown("---")  # 구분선

            with st.expander("📊 분석 정보"):
                st.write(
                    f"• 분석된 문서 수: **{guide_data['processed_files_count']}개**"
                )
                st.write(f"• 발견된 기술 키워드: **{guide_data['total_keywords']}**")

    else:
        st.info("먼저 왼쪽에서 문서를 업로드하고 처리해주세요.")

with col3:
    st.markdown('<div class="section-header">💬 질의응답</div>', unsafe_allow_html=True)

    if not PROCESSOR_AVAILABLE:
        st.error("DocumentProcessor 모듈을 사용할 수 없습니다.")
    elif not st.session_state.processed_files:
        st.info("먼저 문서를 업로드하고 처리해주세요.")
    else:
        # 질문 입력
        user_question = st.text_input(
            "질문을 입력하세요:",
            placeholder="예: 서버 아키텍처 구조는?",
            key="user_question",
        )

        ask_button = st.button("질문하기", type="primary", use_container_width=True)

        # 질문 처리
        if ask_button and user_question:
            with st.spinner("AI가 답변을 생성하고 있습니다..."):
                try:
                    answer_result = document_processor.answer_question(user_question)

                    if answer_result["success"]:
                        st.subheader("🤖 AI 답변")
                        # Streamlit 기본 컨테이너 사용
                        with st.container():
                            # st.markdown("---")  # 구분선
                            st.markdown(answer_result["answer"])
                            st.markdown("---")  # 구분선

                        # 참고 문서 표시
                        if answer_result["sources"]:
                            st.subheader("📚 참고 문서")
                            for source in set(answer_result["sources"]):
                                st.write(f"• {source}")

                        # 검색 결과 상세
                        if answer_result["search_results"]:
                            with st.expander("🔍 검색된 문서 내용 보기"):
                                for i, result in enumerate(
                                    answer_result["search_results"]
                                ):
                                    st.write(
                                        f"**{i+1}. {result['file_name']} (점수: {result['score']:.2f})**"
                                    )
                                    st.write(
                                        result["content"][:300] + "..."
                                        if len(result["content"]) > 300
                                        else result["content"]
                                    )
                                    st.divider()
                    else:
                        st.error(f"답변 생성 실패: {answer_result['error']}")

                except Exception as e:
                    st.error(f"예외 발생: {str(e)}")

        elif ask_button and not user_question:
            st.warning("질문을 입력해주세요!")

# 푸터
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
<div class="simple-info" style="text-align: center;">
    <p style="margin: 0;">⚡ Azure OpenAI와 Azure AI Search 기반으로 구동됩니다</p>
</div>
""",
    unsafe_allow_html=True,
)
