# 0. 필수 라이브러리 import
from dotenv import load_dotenv
from langchain.chains import RetrievalQA

from langchain_community.chat_models import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate

from colorama import Fore
import os
import warnings

warnings.filterwarnings("ignore")  # 경고 메시지 무시

# 1. 환경 변수 로드 (.env 파일에서 OPENAI_API_KEY 불러오기)
load_dotenv()

# 2. OpenAI 모델 초기화
model = ChatOpenAI(model="gpt-4o-2024-05-13")

# 3. 웹 문서 로드 (LangChain 소개 페이지 크롤링)
loader = WebBaseLoader("https://python.langchain.com/docs/get_started/introduction")
documents = loader.load()

# 4. 문서 텍스트 청크 분할 (RAG 최적화를 위한 전처리)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 500,      # 한 조각당 최대 길이 (토큰/문자 기준)
    chunk_overlap = 50     # 앞뒤로 겹치는 부분 설정 (문맥 유지)
)
split_documents = text_splitter.split_documents(documents)

# 5. 문서 임베딩 생성 및 FAISS 벡터 저장소 생성
embeddings = OpenAIEmbeddings()
vector_store = FAISS.from_documents(split_documents, embeddings)

# 6. 프롬프트 템플릿 정의 (question, context 기반 응답 생성 지시)
template = """You are a senior developer. Use the following context to answer the question:

                Context:
                {context}

                Question: {question}
                Answer:
            """
prompt = PromptTemplate(template=template, input_variables=["question", "context"])

# 7. 질문에 대한 답변을 생성하는 함수 정의 (RAG 체인 실행)
def generate(query): 
    chain_type_kwargs = {
        "prompt": prompt
    }
    chain = RetrievalQA.from_chain_type(
        llm = model,
        chain_type = "stuff",
        retriever = vector_store.as_retriever(search_kwargs={"k": 3}),  # 관련 문서 3개까지 검색
        chain_type_kwargs = chain_type_kwargs,
    )
    response = chain.run(query)
    return response

# 8. 메인 메뉴 UI 출력 함수
def start():
    print("OPENAI API KEY:", os.getenv("OPENAI_API_KEY"))
    print(f"Number of split documents loaded: {len(split_documents)}")
    instructions = (
        "Type your question and press ENTER. Type 'x' to go back to the MAIN menu.\n"
    )
    print(Fore.BLUE + "\n\x1B[3m" + instructions + "\x1B[0m" + Fore.RESET)

    print("MENU")
    print("====")
    print("[1]- Ask a question")
    print("[2]- Exit")
    choice = input("Enter your choice: ")
    if choice == "1":
        ask()
    elif choice == "2":
        print("Goodbye!")
        exit()
    else:
        print("Invalid choice")
        start()

# 9. 질문 받고 답변 출력하는 함수 (루프 방식)
def ask():
    while True:
        user_input = input("Q: ")
        if user_input.lower() == "x":
            start()
        else:
            response = generate(user_input)
            print(Fore.BLUE + f"A: {response}" + Fore.RESET)
            print(Fore.WHITE + "\n-------------------------------------------------")

# 10. 프로그램 실행 시작점
if __name__ == "__main__":
    start()
