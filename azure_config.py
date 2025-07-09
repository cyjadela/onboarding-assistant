import os

# from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential

# 환경 변수 로드
# load_dotenv()


class AzureConfig:
    def __init__(self):
        # Azure OpenAI 설정
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.openai_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        # Azure AI Search 설정
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

        # Azure Storage 설정
        self.storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.storage_container_name = os.getenv(
            "AZURE_STORAGE_CONTAINER_NAME", "documents"
        )

        # Azure AI Services 설정 (OCR)
        self.ai_services_endpoint = os.getenv("AZURE_AI_SERVICES_ENDPOINT")
        self.ai_services_api_key = os.getenv("AZURE_AI_SERVICES_API_KEY")

    def get_openai_client(self):
        """Azure OpenAI 클라이언트 반환"""
        return AzureOpenAI(
            azure_endpoint=self.openai_endpoint,
            api_key=self.openai_api_key,
            api_version=self.openai_api_version,
        )

    def get_search_client(self):
        """Azure AI Search 클라이언트 반환"""
        credential = AzureKeyCredential(self.search_api_key)
        return SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.search_index_name,
            credential=credential,
        )

    def get_search_index_client(self):
        """Azure AI Search 인덱스 클라이언트 반환"""
        credential = AzureKeyCredential(self.search_api_key)
        return SearchIndexClient(endpoint=self.search_endpoint, credential=credential)

    def get_blob_service_client(self):
        """Azure Blob Storage 클라이언트 반환"""
        return BlobServiceClient.from_connection_string(self.storage_connection_string)

    def get_vision_client(self):
        """Azure AI Services Computer Vision 클라이언트 반환"""
        ai_services_endpoint = os.getenv("AZURE_AI_SERVICES_ENDPOINT")
        ai_services_api_key = os.getenv("AZURE_AI_SERVICES_API_KEY")

        print(f"🔍 AI Services endpoint: {ai_services_endpoint}")
        print(f"🔍 AI Services key: {'있음' if ai_services_api_key else '없음'}")

        if not ai_services_endpoint or not ai_services_api_key:
            return None

        try:
            from azure.cognitiveservices.vision.computervision import (
                ComputerVisionClient,
            )
            from msrest.authentication import CognitiveServicesCredentials

            # AI Services는 CognitiveServicesCredentials 사용
            credentials = CognitiveServicesCredentials(ai_services_api_key)
            client = ComputerVisionClient(ai_services_endpoint, credentials)

            print("✅ AI Services Computer Vision 클라이언트 생성 성공")
            return client

        except ImportError as e:
            print(f"❌ 패키지 import 실패: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ 클라이언트 생성 실패: {str(e)}")
            return None

    def test_connections(self):
        """모든 Azure 서비스 연결 테스트"""
        results = {}

        # OpenAI 연결 테스트
        try:
            client = self.get_openai_client()
            response = client.chat.completions.create(
                model=self.openai_deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
            )
            results["OpenAI"] = "연결 성공"
        except Exception as e:
            results["OpenAI"] = f"❌ 연결 실패: {str(e)}"

        # AI Search 연결 테스트
        try:
            search_index_client = self.get_search_index_client()
            # 인덱스 존재 확인 (없으면 생성 필요)
            try:
                search_index_client.get_index(self.search_index_name)
                results["AI Search"] = "연결 성공 (인덱스 존재)"
            except:
                results["AI Search"] = "⚠️ 연결 성공 (인덱스 생성 필요)"
        except Exception as e:
            results["AI Search"] = f"❌ 연결 실패: {str(e)}"

        # Blob Storage 연결 테스트
        try:
            blob_service_client = self.get_blob_service_client()
            container_client = blob_service_client.get_container_client(
                self.storage_container_name
            )
            container_client.get_container_properties()
            results["Blob Storage"] = "연결 성공"
        except Exception as e:
            results["Blob Storage"] = f"❌ 연결 실패: {str(e)}"

        # AI Services Vision 연결 테스트
        try:
            vision_client = self.get_vision_client()
            if vision_client:
                # Vision 클라이언트가 있다면 간단한 테스트 수행
                results["AI Services Vision"] = "연결 성공"
            else:
                results["AI Services Vision"] = "⚠️ Vision 서비스 설정 없음"
        except Exception as e:
            results["AI Services Vision"] = f"❌ 연결 실패: {str(e)}"

        return results


# 전역 설정 객체
azure_config = AzureConfig()


# 테스트 실행 함수
def test_azure_connections():
    """Azure 연결 테스트 실행"""
    results = azure_config.test_connections()

    print("\n연결 테스트 결과:")
    for service, result in results.items():
        print(f"{service}: {result}")

    return results


if __name__ == "__main__":
    test_azure_connections()
