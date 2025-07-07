# document_processor.py (간단한 Key 사용)
import json
import uuid
from datetime import datetime
from azure.search.documents import SearchClient
from azure_config import azure_config

class DocumentProcessor:
    def __init__(self):
        self.search_client = azure_config.get_search_client()
        self.openai_client = azure_config.get_openai_client()
        self.deployment_name = azure_config.openai_deployment_name
    
    def chunk_text(self, text, chunk_size=1500, overlap=150):
        """텍스트를 청크로 분할"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            if end > len(text):
                end = len(text)
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end == len(text):
                break
                
            start = end - overlap
        
        return chunks
    
    def index_document(self, document_result):
        """문서를 AI Search에 인덱싱 - 기존 스키마 활용 (간단한 Key)"""
        try:
            # 문서 텍스트를 청크로 분할
            chunks = self.chunk_text(document_result["extracted_text"])
            
            # 각 청크를 개별 문서로 인덱싱
            documents = []
            for i, chunk in enumerate(chunks):
                # 간단한 Key 생성 (문자, 숫자, 언더스코어, 대시만 사용)
                # UUID에서 하이픈 제거하고 청크 인덱스 추가
                clean_doc_id = document_result['document_id'].replace('-', '')
                storage_path = f"doc_{clean_doc_id}_chunk_{i}"
                
                document = {
                    # 기존 스키마의 필수 필드들
                    "metadata_storage_path": storage_path,  # key 필드 (간단한 형식)
                    "metadata_storage_name": f"{document_result['file_name']}_chunk_{i}",
                    "metadata_storage_size": len(chunk.encode('utf-8')),
                    "metadata_storage_last_modified": datetime.now().isoformat() + "Z",
                    "metadata_storage_content_type": "text/plain",
                    "metadata_storage_file_extension": document_result["file_type"],
                    
                    # 컨텐츠 필드들
                    "content": chunk,
                    "merged_content": chunk,
                    "text": [chunk],  # Collection 타입
                    "layoutText": [chunk],  # Collection 타입
                    
                    # 언어 관련
                    "language": "ko",
                    "metadata_language": "ko",
                    
                    # 날짜 필드
                    "metadata_creation_date": datetime.now().isoformat() + "Z",
                    
                    # 빈 컬렉션들 (오류 방지)
                    "organizations": [],
                    "keyphrases": [],
                    "pii_entities": []
                }
                
                documents.append(document)
            
            # AI Search에 문서들 업로드
            result = self.search_client.upload_documents(documents)
            
            return {
                "success": True,
                "indexed_chunks": len(documents),
                "document_id": document_result["document_id"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_document_summary(self, document_result):
        """문서 요약 생성"""
        try:
            # 문서가 너무 길면 일부만 처리
            text = document_result["extracted_text"]
            # if len(text) > 8000:
            #     text = text[:8000] + "..."
            
            # 요약 프롬프트
            summary_prompt = f"""다음 문서를 분석하여 핵심 내용을 요약해주세요:

문서명: {document_result["file_name"]}
문서 타입: {document_result["file_type"]}

내용:
{text}

다음 형식으로 요약해주세요:
1. 문서 개요 (2-3줄)
2. 주요 내용 (3-5개 요점)
3. 핵심 기술/시스템 (있는 경우)
4. 중요 참고사항 (있는 경우)
"""

            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "당신은 프로젝트 문서 분석 전문가입니다. 핵심 내용을 정확하고 간결하게 요약합니다."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_completion_tokens=7000
            )
            
            summary = response.choices[0].message.content
            
            return {
                "success": True,
                "summary": summary,
                "document_id": document_result["document_id"],
                "file_name": document_result["file_name"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_technical_info(self, document_result):
        """기술 정보 추출 (간단한 버전)"""
        try:
            text = document_result["extracted_text"]
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            tech_prompt = f"""다음 문서에서 기술 키워드들을 간단히 추출해주세요:

문서 내용:
{text}

기술 키워드만 추출해서 콤마로 구분해주세요 (예: Python, React, Docker, AWS):"""

            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "기술 문서에서 기술 키워드만 간단히 추출합니다."},
                    {"role": "user", "content": tech_prompt}
                ],
                max_completion_tokens=7000
            )
            
            tech_keywords = response.choices[0].message.content
            
            return {
                "success": True,
                "technical_keywords": tech_keywords,
                "document_id": document_result["document_id"],
                "file_name": document_result["file_name"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_integrated_tech_guide(self, processed_files):
        """전체 문서들을 통합해서 기술 학습 가이드 생성"""
        try:
            # 모든 문서의 내용을 수집
            all_content = []
            tech_keywords = []
            
            for file_result in processed_files:
                if file_result.get("success") and "extracted_text" in file_result:
                    # 문서 내용 일부 추가
                    content = file_result["extracted_text"][:2000]  # 각 문서당 2000자까지
                    all_content.append(f"[{file_result['file_name']}]\n{content}")
                    
                    # 기술 키워드 수집
                    if "processing_results" in file_result:
                        tech_result = file_result["processing_results"].get("technical_info", {})
                        if tech_result.get("success"):
                            tech_keywords.append(tech_result.get("technical_keywords", ""))
            
            # 통합 컨텐츠 생성
            combined_content = "\n\n".join(all_content)
            combined_keywords = ", ".join([k for k in tech_keywords if k])
            
            # 통합 기술 가이드 프롬프트
            guide_prompt = f"""다음은 프로젝트의 모든 문서들입니다. 이를 바탕으로 신규 투입자를 위한 기술 학습 가이드를 작성해주세요.

문서 내용:
{combined_content[:8000]}  # 최대 8000자까지

발견된 기술 키워드들:
{combined_keywords}

다음 형식으로 학습 가이드를 작성해주세요:

## 🚀 프로젝트 기술 스택
- 주요 기술들의 간단한 설명

## 📚 우선 학습 기술 (중요도 순)
1. **기술명1**: 학습 이유 및 중요도
2. **기술명2**: 학습 이유 및 중요도
...

## 📖 추천 학습 리소스
- 각 기술별 추천 문서나 튜토리얼"""

            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "당신은 개발자를 위한 기술 학습 가이드 작성 전문가입니다. 제공된 문서를 바탕으로 신규 투입자를 위한 기술 학습 가이드를 작성합니다."},
                    {"role": "user", "content": guide_prompt}
                ],
                max_completion_tokens=7000
            )
            
            tech_guide = response.choices[0].message.content
            
            return {
                "success": True,
                "tech_guide": tech_guide,
                "processed_files_count": len(processed_files),
                "total_keywords": combined_keywords
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        

    def answer_question(self, question, search_results=None):
        """질문에 대한 답변 생성 (RAG)"""
        try:
            # 검색 결과가 없으면 검색 수행
            if search_results is None:
                search_result = self.search_documents(question)
                if not search_result["success"]:
                    raise Exception(f"검색 실패: {search_result['error']}")
                search_results = search_result["results"]
            
            # 검색 결과를 컨텍스트로 구성
            context = ""
            if search_results:
                context = "\n\n".join([
                    f"[문서: {result['file_name']}]\n{result['content']}"
                    for result in search_results[:3]  # 상위 3개만 사용
                ])
            
            # 검색 결과가 없는 경우 처리
            if not context.strip():
                return {
                    "success": True,
                    "answer": "죄송합니다. 업로드된 문서에서 관련 정보를 찾을 수 없습니다. 다른 키워드로 검색해보시거나 관련 문서를 업로드해주세요.",
                    "sources": [],
                    "search_results": []
                }
            
            # 답변 생성 프롬프트
            prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.

질문: {question}

참고 문서:
{context}

답변 규칙:
1. 문서에 있는 정보를 우선적으로 사용하세요
2. 문서에 없는 내용은 일반적인 지식으로 보완하되, 이를 명시하세요
3. 한국어로 명확하고 도움이 되는 답변을 작성하세요
4. 문서 출처를 답변에 포함하세요"""

            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "당신은 기술 문서 기반 질의응답 전문가입니다. 제공된 문서를 바탕으로 정확하고 도움이 되는 답변을 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            return {
                "success": True,
                "answer": answer,
                "sources": [result["file_name"] for result in search_results] if search_results else [],
                "search_results": search_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }       
    
    def search_documents(self, query, top_k=3):
        """문서 검색 - 기존 스키마 필드 사용"""
        try:
            search_results = self.search_client.search(
                search_text=query,
                top=top_k,
                include_total_count=True,
                select=["content", "merged_content", "metadata_storage_name", "metadata_storage_path"]
            )
            
            results = []
            for result in search_results:
                # 안전하게 필드 접근
                content = result.get("content") or result.get("merged_content", "")
                file_name = result.get("metadata_storage_name", "Unknown")
                
                # 원본 파일명 추출 (chunk 정보 제거)
                if "_chunk_" in file_name:
                    file_name = file_name.split("_chunk_")[0]
                
                results.append({
                    "content": content,
                    "file_name": file_name,
                    "score": result["@search.score"],
                    "storage_path": result.get("metadata_storage_path", "")
                })
            
            return {
                "success": True,
                "results": results,
                "total_count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_document_complete(self, document_result):
        """문서 전체 처리 파이프라인"""
        results = {
            "document_id": document_result["document_id"],
            "file_name": document_result["file_name"],
            "processing_results": {}
        }
        
        # 1. AI Search 인덱싱
        print("AI Search 인덱싱 중...")
        index_result = self.index_document(document_result)
        results["processing_results"]["indexing"] = index_result
        
        # 2. 문서 요약 생성
        print("문서 요약 생성 중...")
        summary_result = self.generate_document_summary(document_result)
        results["processing_results"]["summary"] = summary_result
        
        # 3. 기술 키워드 추출 (간단화)
        print("기술 키워드 추출 중...")
        tech_result = self.extract_technical_info(document_result)
        results["processing_results"]["technical_info"] = tech_result
        
        return results

# 전역 프로세서 객체
document_processor = DocumentProcessor()