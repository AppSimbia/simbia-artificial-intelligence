from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate
)
from langchain_core.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.memory import ChatMessageHistory
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
today = datetime.now().date()

import os

store = {}
MONGO_URI = os.getenv("MONGODB_URL")
MONGO_DB_NAME = os.getenv("MONGODB_DB_NAME")
MONGO_COLLECTION_NAME = os.getenv("MONGODB_EVA_COLLECTION")

def get_session_history(session_id) -> ChatMessageHistory:
    return MongoDBChatMessageHistory(
        connection_string=MONGO_URI,
        database_name=MONGO_DB_NAME,
        collection_name=MONGO_COLLECTION_NAME,
        session_id=session_id
    )

def inject_industry_id(inputs, config):
    industry_id = config.get("configurable", {}).get("industry_id")
    return {**inputs, "session_id": industry_id}

cut_shots = """
### ALERTA
A região abaixo é apenas para exemplo, você não deve considerá-la para responder o usuário, serve apenas como exemplo para voce saber como responder.
O usuário não sabe e não deve saber dos dados dos shots.
"""

today_date_info = """
### DATA ATUAL
- Hoje é {today_local} (timezone: America/Sao_Paulo).
- Sempre interprete expressões relativas como "hoje", "ontem", "semana passada" a partir dessa data, nunca invente ou assuma data diferentes.
"""

class Agent:
    def __init__(self,
                api_key_env:str,
                llm_model:str,   
                llm_temperature:Optional[str], 
                llm_top_p: Optional[str],     
                prompt: str, 
                shots: List, 
                tools: Optional[List], 
                docs_route: Optional[str],
                has_history: bool,
                json_output: bool
                ):
        self.api_key_env = api_key_env
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.llm_top_p = llm_top_p
        self.prompt = prompt
        self.shots = shots
        self.tools = tools
        self.docs_route = docs_route
        self.has_history = has_history
        self.json_output = json_output

    def generate_chain(self):
        # Criando o LLM
        llm = ChatGoogleGenerativeAI(
            model=self.llm_model,
            temperature = self.llm_temperature,
            top_p= self.llm_top_p,
            google_api_key=os.getenv(self.api_key_env)
        )
        # Adicionando base do prompt
        example_prompt_base = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate.from_template("{human}"),
            AIMessagePromptTemplate.from_template("{ai}"),
        ])

        # Criando o prompt
        system_prompt = ("system", self.prompt)
        shots = self.shots
        fewshots = FewShotChatMessagePromptTemplate(
            examples=shots,
            example_prompt=example_prompt_base,
        )
        messages = [
            system_prompt,
            today_date_info,
            cut_shots,
            fewshots,
        ]
        # Coloca o chat_history se tiver historico
        if self.has_history:
            messages.append(MessagesPlaceholder("chat_history"))

        messages.append(("human", "{input}"))
        
        # Se tiver docs (embedding), adiciona nas tools
        if self.docs_route:
            # Separa os documentos
            docs = []
            for file in os.listdir(self.docs_route):
                if file.endswith(".txt"):
                    caminho = os.path.join(self.docs_route, file)
                    loader = TextLoader(caminho, encoding="utf-8")
                    docs.extend(loader.load())

            splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            docs_split = splitter.split_documents(docs)

            # Carregar embeddings do HuggingFaceEmbeddings (gratuito)
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=os.getenv("GEMINI_API_KEY5")
            )

            # Criar o vetor FAISS
            faiss = FAISS.from_documents(docs_split, embeddings)

            # Criar a tool e adicionar no agete
            retriever_tool = create_retriever_tool(
                faiss.as_retriever(search_kwargs={"k": 4}),
                name="busca_informacoes",
                description="Use esta ferramenta para pesquisar em arquivos, usando os para responder ao usuário. Use apenas UMA palavra para buscar, trazendo o máximo de informações possível. Consulte varias vezes com palavras diferentes para achar o máximo de dados possível."
            )
            if not self.tools:
                self.tools = []
            self.tools.append(retriever_tool)

        # Se tiver tools coloca o agent_scratchpad
        has_tools = self.tools and len(self.tools) > 0
        if has_tools:
            messages.append(MessagesPlaceholder("agent_scratchpad"))

        # Instancia o prompt
        prompt = ChatPromptTemplate.from_messages(messages)

        # Coloca a data atual no prompt
        prompt = prompt.partial(today_local=today.isoformat())

        # Decide o parser caso seja json ou nao
        parser = JsonOutputParser() if self.json_output else StrOutputParser()

        
        if not self.has_history:
            # Chain basica
            chain = prompt | llm | parser
            return chain
        else:
            if has_tools:
                # Chain com tools
                agent = create_tool_calling_agent(llm, self.tools, prompt)   
                agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
                chain = RunnableWithMessageHistory(
                    RunnableLambda(inject_industry_id) | agent_executor,                           #chain_original (agora é o agente)
                    get_session_history=get_session_history,  #funcao para historico de sessao
                    input_messages_key="input",               #tudo no prompt que for {input} ele coloca o prompt do usuario
                    history_messages_key="chat_history"       #tudo que for {chat_history} ele coloca o histórico do usuario
                )           
                return chain
            else:
                # Chain sem tools
                baseChain = prompt | llm | parser

                chain = RunnableWithMessageHistory(
                    RunnableLambda(inject_industry_id) | baseChain,                                #chain_original
                    get_session_history=get_session_history,  #funcao para historico de sessao
                    input_messages_key="input",               #tudo no prompt que for {usuario} ele coloca o prompt do usuario
                    history_messages_key="chat_history"       #tudo que for {chat_history} ele coloca o histórico do usuario
                )
                return chain