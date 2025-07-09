## 1️⃣ 프로젝트 개요

### ✅ 문제 정의

- 신규 프로젝트 투입 시 오래된 운영 매뉴얼과 분산된 문서들로 인한 업무 파악 지연
- 새로운 기술 스택에 대한 부담감과 학습 시간 부족

### ✅ 대상 사용자

- 신규 프로젝트에 투입되는 개발자
- 운영 매뉴얼과 기술 문서를 효율적으로 활용하고자 하는 팀원

### 💡 솔루션 개요

- Azure OpenAI와 Azure AI Search를 기반으로 문서들을 통합하여 요약하고, 관련 기술에 대한 학습 가이드를 통합 제공하는 솔루션

<br>

## 2️⃣ 아키텍처

![아키텍처](https://github.com/user-attachments/assets/32925289-b67f-46f5-b7d9-ed807fb89e05)


- Azure Services

| Azure Services | 사용 용도 |
| --- | --- |
| Azure OpenAI Service (GPT) | 문서 요약, 기술 질문 응답 |
| Azure AI Search | 문서 인덱싱 및 RAG 근거 제공 |
| Azure Blob Storage | PDF, Word, 이미지, 텍스트 등 문서 저장 |
| Azure AI Services | 이미지 OCR 처리 |
| Azure Web App | 서비스 배포 |

<br>

## 3️⃣ 핵심 기술 포인트

### ✅ 커스텀 프롬프트 & 주요 코드

**기능 1) 문서 요약**

- prompt
    
    ```python
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
    ```
    
- system message
    
    ```python
    messages=[
        {
            "role": "system",
             "content": "당신은 프로젝트 문서 분석 전문가입니다. 핵심 내용을 정확하고 간결하게 요약합니다.",
         },
         {"role": "user", "content": summary_prompt},
    ]
    ```

<br>

**기능 2) 통합 기술 학습 가이드**

- prompt
    
    ```python
    guide_prompt = f"""다음은 프로젝트의 모든 기존 문서들입니다. 이를 바탕으로 신규 투입자를 위한 기술 학습 가이드를 작성해주세요.
    
    문서 내용:
    {combined_content}
    
    발견된 기술 키워드들:
    {combined_keywords}
    
    다음 형식으로 학습 가이드를 작성해주세요:
    
    ### 🚀 프로젝트 기술 스택
    - 주요 기술들의 간단한 설명
    
    ### 📚 우선 학습 기술 (중요도 순)
    1. **기술명1**: 학습 이유 및 중요도
    2. **기술명2**: 학습 이유 및 중요도
    ...
    
    ## 📖 추천 학습 리소스
    - 각 기술별 추천 문서나 튜토리얼"""
    ```
    
- system message
    
    ```python
    messages=[
        {
            "role": "system",
             "content": "당신은 개발자를 위한 기술 학습 가이드 작성 전문가입니다. 제공된 문서를 통합하여 신규 투입자를 위한 기술 학습 가이드를 작성합니다.",
         },
         {"role": "user", "content": guide_prompt},
    ]
    ```

<br>

**기능 3) 질의 응답**

- 하단 [✅ 질의 응답 기능 고도화] 참고

<br> 

### ✅ OCR 처리 기능 추가

- 기존에는 텍스트 바탕으로 이루어진 pdf, docx, txt, md 파일만 제공했지만 서버 아키텍처 등의 이미지 문서도 존재하기 때문에 OCR 처리 기능을 추가로 구현

<br>

### ✅ 질의 응답 기능 고도화

- 문서 정보 기반 RAG 답변이 나오지 않는 경우, 일반 지식으로 답변을 보완하도록 구현
- 사용자가 답변의 정확성을 파악할 수 있도록, 답변의 출처가 되는 문서 표시
- prompt
    
    ```python
    # 문서 기반 답변
    prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.
    
    질문: {question}
    
    참고 문서:
    {context}
    
    답변 규칙:
    1. 먼저 문서에 있는 정보를 기반으로 답변하세요
    2. 문서 정보가 부족하면 일반적인 지식으로 보완하되, 이를 명시하세요
    3. 한국어로 명확하고 도움이 되는 답변을 작성하세요
    4. 답변 마지막에 참고한 문서를 명시하세요
    
    답변 형식:
    ### 문서 기반 답변
    ### 추가 일반 지식 (해당하는 경우)
    
    **참고 문서:** [문서명들]"""
    
    answer_type = "document_based"
    
    else:
    # 일반 지식 기반 답변
    prompt = f"""다음 질문에 대해 일반적인 지식을 바탕으로 답변해주세요.
    
    질문: {question}
    
    답변 규칙:
    1. 프로젝트 신규 투입 및 기술 학습 관점에서 도움이 되는 답변을 제공하세요
    2. 한국어로 명확하고 실용적인 답변을 작성하세요
    3. 가능하면 구체적인 예시나 방법을 포함하세요
    4. 답변 마지막에 "※ 업로드된 문서에서 관련 정보를 찾을 수 없어 일반적인 지식으로 답변했습니다."라고 명시하세요"""
    
    answer_type = "general_knowledge"
    ```
    
- system message
    
    ```python
    messages=[
        {
            "role": "system",
             "content": "당신은 프로젝트 수행 중 신규 투입자에게 인수인계를 하는 전문가입니다. 기술 문서와 일반 지식을 활용하여 신규 투입자에게 도움이 되는 답변을 제공합니다.",
         },
         {"role": "user", "content": prompt},
    ]
    ```


<br>

## 4️⃣ 시연

### ✅ 주요 기능

1. 다양한 형식의 문서 업로드
2. 문서 요약 및 통합 기술 정보 제공
3. 문서 기반 질의 응답 제공

### ✅ 시연 영상
https://drive.google.com/file/d/1yPxxiCxXs59k5-PiONDYhLNewBk2eWaI/view?usp=sharing

![시연 캡처](https://github.com/user-attachments/assets/68704dd6-c5a3-421e-a7b2-be18e5ac991c)

<br>

## 5️⃣ 향후 개선 방향

### ✅ 기능 고도화

- 문서 업로드 비동기 처리
- 중복 문서 blob storage 업로드 제거 및 중복 내용 처리 기능
- LangChain 또는 LangGraph 적용
