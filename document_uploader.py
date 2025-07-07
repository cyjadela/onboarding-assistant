# document_uploader.py
import uuid
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
from azure_config import azure_config

class DocumentUploader:
    def __init__(self):
        self.blob_service_client = azure_config.get_blob_service_client()
    
    def extract_text_from_file(self, uploaded_file):
        """업로드된 파일에서 텍스트 추출"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'pdf':
                return self._extract_text_from_pdf(uploaded_file)
            elif file_extension in ['docx']:
                return self._extract_text_from_docx(uploaded_file)
            elif file_extension in ['txt', 'md']:
                return self._extract_text_from_text(uploaded_file)
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {file_extension}")
                
        except Exception as e:
            st.error(f"텍스트 추출 실패: {str(e)}")
            return None
    
    def _extract_text_from_pdf(self, uploaded_file):
        """PDF 파일에서 텍스트 추출"""
        text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            uploaded_file.seek(0)  # 파일 포인터 리셋
            return text.strip()
        except Exception as e:
            raise Exception(f"PDF 읽기 오류: {str(e)}")
    
    def _extract_text_from_docx(self, uploaded_file):
        """DOCX 파일에서 텍스트 추출"""
        try:
            doc = docx.Document(BytesIO(uploaded_file.read()))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            uploaded_file.seek(0)  # 파일 포인터 리셋
            return text.strip()
        except Exception as e:
            raise Exception(f"DOCX 읽기 오류: {str(e)}")
    
    def _extract_text_from_text(self, uploaded_file):
        """텍스트 파일에서 내용 추출"""
        try:
            content = uploaded_file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            uploaded_file.seek(0)  # 파일 포인터 리셋
            return content.strip()
        except Exception as e:
            raise Exception(f"텍스트 파일 읽기 오류: {str(e)}")
    
    def upload_to_blob_storage(self, uploaded_file):
        """파일을 Azure Blob Storage에 업로드 (단순화된 버전)"""
        try:
            # 고유한 문서 ID 생성
            document_id = str(uuid.uuid4())
            blob_name = f"{document_id}/{uploaded_file.name}"
            
            blob_client = self.blob_service_client.get_blob_client(
                container=azure_config.storage_container_name,
                blob=blob_name
            )
            
            # 파일 업로드
            uploaded_file.seek(0)
            blob_client.upload_blob(
                uploaded_file.read(),
                overwrite=True
            )
            
            return {
                "document_id": document_id,
                "blob_url": blob_client.url,
                "blob_name": blob_name
            }
            
        except Exception as e:
            raise Exception(f"Blob Storage 업로드 실패: {str(e)}")
    
    def process_single_file(self, uploaded_file):
        """단일 파일 처리: 텍스트 추출 + Blob Storage 업로드 + AI Search 인덱싱 + 요약"""
        try:
            # 1. 텍스트 추출
            st.info("텍스트 추출 중...")
            extracted_text = self.extract_text_from_file(uploaded_file)
            
            if not extracted_text:
                raise Exception("텍스트를 추출할 수 없습니다.")
            
            st.success(f"텍스트 추출 완료 (길이: {len(extracted_text)}자)")
            
            # 2. Blob Storage 업로드
            st.info("클라우드 저장 중...")
            upload_result = self.upload_to_blob_storage(uploaded_file)
            
            st.success("업로드 완료!")
            
            # 3. 기본 결과 생성
            result = {
                "success": True,
                "document_id": upload_result["document_id"],
                "file_name": uploaded_file.name,
                "file_type": uploaded_file.name.split('.')[-1].lower(),
                "extracted_text": extracted_text,
                "blob_url": upload_result["blob_url"],
                "blob_name": upload_result["blob_name"],
                "file_size": uploaded_file.size
            }
            
            # 4. 문서 처리 (인덱싱 + 요약)
            st.info("문서 분석 및 요약 중...")
            try:
                # document_processor import 확인
                try:
                    from document_processor import document_processor
                    st.info("✅ document_processor 모듈 로드 성공")
                except ImportError as e:
                    st.error(f"❌ document_processor 모듈 로드 실패: {str(e)}")
                    raise e
                
                # 문서 전체 처리
                st.info("문서 처리 시작...")
                processing_results = document_processor.process_document_complete(result)
                st.info("문서 처리 완료")
                
                # 결과에 처리 정보 추가
                result["processing_results"] = processing_results["processing_results"]
                
                # 디버깅: 결과 구조 확인
                st.write("**처리 결과 구조:**")
                st.json({
                    "summary_success": result["processing_results"].get("summary", {}).get("success", False),
                    "tech_info_success": result["processing_results"].get("technical_info", {}).get("success", False),
                    "indexing_success": result["processing_results"].get("indexing", {}).get("success", False)
                })
                
                st.success("문서 분석 완료!")
                
            except Exception as e:
                st.error(f"❌ 문서 분석 중 오류 발생: {str(e)}")
                st.write(f"오류 타입: {type(e).__name__}")
                st.write(f"오류 메시지: {str(e)}")
                result["processing_error"] = str(e)
            
            return result
            
        except Exception as e:
            st.error(f"❌ 파일 처리 실패: {str(e)}")
            st.write(f"오류 타입: {type(e).__name__}")
            return {
                "success": False,
                "error": str(e)
            }

def get_blob_files():
    """업로드된 파일 목록 조회"""
    try:
        blob_service_client = azure_config.get_blob_service_client()
        container_client = blob_service_client.get_container_client(
            azure_config.storage_container_name
        )
        
        blobs = list(container_client.list_blobs())
        return blobs
        
    except Exception as e:
        st.error(f"파일 목록 조회 실패: {str(e)}")
        return []

# 전역 업로더 객체
document_uploader = DocumentUploader()