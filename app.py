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
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []
if "integrated_tech_guide" not in st.session_state:
    st.session_state.integrated_tech_guide = None

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
                                    
                                    # 통합 기술 가이드 초기화 (새 파일 추가시)
                                    st.session_state.integrated_tech_guide = None
                                    
                                else:
                                    st.error(f"업로드 실패: {result['error']}")
                else:
                    st.warning("DocumentUploader를 사용하려면 document_uploader.py가 필요합니다.")


with col2:
    st.header("📊 문서 요약 & 통합 기술 가이드")
    st.info("문서 요약 및 통합 기술 학습 가이드를 제공합니다")
    
    # 처리된 파일들의 요약만 표시
    if st.session_state.processed_files:

        # 개별 문서 요약들
        st.subheader("📄 개별 문서 요약")
        for file_result in st.session_state.processed_files:
            if file_result.get("success") and "processing_results" in file_result:
                with st.expander(f"📄 {file_result['file_name']} 요약"):
                    
                    # 문서 요약 표시
                    if "summary" in file_result["processing_results"]:
                        summary_result = file_result["processing_results"]["summary"]
                        if summary_result.get("success"):
                            st.markdown(summary_result["summary"])
                        else:
                            st.error(f"요약 생성 실패: {summary_result.get('error', '알 수 없는 오류')}")
                    
                    # 인덱싱 정보 표시
                    if "indexing" in file_result["processing_results"]:
                        index_result = file_result["processing_results"]["indexing"]
                        if index_result.get("success"):
                            st.success(f"✅ AI Search 인덱싱 완료 ({index_result['indexed_chunks']}개 청크)")
                        else:
                            st.error(f"인덱싱 실패: {index_result.get('error', '알 수 없는 오류')}")
            
            elif file_result.get("processing_error"):
                st.warning(f"⚠️ {file_result['file_name']}: 분석 중 오류 발생")
                st.error(file_result["processing_error"])

        # 전체 통합 기술 가이드 버튼
        st.subheader("🚀 통합 기술 학습 가이드")
        
        col_btn, col_status = st.columns([1, 2])
        with col_btn:
            generate_guide_btn = st.button("📚 통합 기술 가이드 생성", type="primary")

        
        # 통합 기술 가이드 생성
        if generate_guide_btn and PROCESSOR_AVAILABLE:
            with st.spinner("🤖 모든 문서를 분석하여 통합 기술 가이드를 생성하고 있습니다..."):
                try:
                    guide_result = document_processor.generate_integrated_tech_guide(st.session_state.processed_files)
                    
                    if guide_result["success"]:
                        st.session_state.integrated_tech_guide = guide_result
                        st.success("✅ 통합 기술 가이드 생성 완료!")
                    else:
                        st.error(f"❌ 가이드 생성 실패: {guide_result['error']}")
                        
                except Exception as e:
                    st.error(f"❌ 예외 발생: {str(e)}")
        
        # 통합 기술 가이드 표시
        if st.session_state.integrated_tech_guide:
            guide_data = st.session_state.integrated_tech_guide
            
            with st.container():
                st.markdown("---")
                st.markdown("### 🎯 프로젝트 기술 학습 가이드")
                st.markdown(guide_data["tech_guide"])
                
                # 메타 정보
                with st.expander("📊 분석 정보"):
                    st.write(f"• 분석된 문서 수: {guide_data['processed_files_count']}개")
                    st.write(f"• 발견된 기술 키워드: {guide_data['total_keywords']}")
        
        st.divider()

    else:
        st.write("📋 **문서 업로드 안내**")
        st.write("먼저 왼쪽에서 문서를 업로드해주세요.")
        st.write("업로드 완료 후 '통합 기술 가이드 생성' 버튼을 눌러주세요.")

with col3:
    st.header("💬 질의응답")
    st.info("자연어로 질문하시면 AI가 답변해드립니다")
    
    if not PROCESSOR_AVAILABLE:
        st.error("❌ DocumentProcessor 모듈을 사용할 수 없습니다.")
    elif not st.session_state.processed_files:
        st.info("📋 먼저 문서를 업로드하고 처리해주세요.")
    else:
            # 질문 입력
            user_question = st.text_input(
                "질문을 입력하세요:",
                placeholder="예: 이 프로젝트에서 사용하는 주요 기술 스택은 무엇인가요?",
                key="user_question"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                ask_button = st.button("🤔 질문하기", type="primary")
            
            # 질문 처리
            if ask_button and user_question:
                with st.spinner("AI가 답변을 생성하고 있습니다..."):
                    try:
                        # 문서 검색 및 답변 생성
                        answer_result = document_processor.answer_question(user_question)
                        
                        if answer_result["success"]:
                            st.subheader("🤖 AI 답변")
                            st.markdown(answer_result["answer"])
                            
                            # 참고 문서 표시
                            if answer_result["sources"]:
                                st.subheader("📚 참고 문서")
                                for source in set(answer_result["sources"]):
                                    st.write(f"• {source}")
                            
                            # 검색 결과 상세 (접기 가능)
                            if answer_result["search_results"]:
                                with st.expander("🔍 검색된 문서 내용 보기"):
                                    for i, result in enumerate(answer_result["search_results"]):
                                        st.write(f"**{i+1}. {result['file_name']} (점수: {result['score']:.2f})**")
                                        st.write(result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"])
                                        st.divider()
                        else:
                            st.error(f"❌ 답변 생성 실패: {answer_result['error']}")
                            
                    except Exception as e:
                        st.error(f"❌ 예외 발생: {str(e)}")
            
            elif ask_button and not user_question:
                st.warning("질문을 입력해주세요!")
            

# 푸터
st.divider()
st.markdown("*Azure OpenAI와 Azure AI Search 기반으로 구동됩니다*")