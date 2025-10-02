from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate
)
from langchain_core.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.memory import ChatMessageHistory

import os

store = {}

def get_session_history(session_id) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


cut_shots = """
### ALERTA
A região abaixo é apenas para exemplo, você não deve considerá-la para responder o usuário, serve apenas como exemplo para voce saber como responder.
O usuário não sabe e não deve saber dos dados dos shots.
"""

class Agent:
    def __init__(self,
                llm_model:str,   
                llm_temperature:Optional[str], 
                llm_top_p: Optional[str],     
                prompt: str, 
                shots: List, 
                tools: Optional[List], 
                has_history: bool,
                json_output: bool
                ):
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.llm_top_p = llm_top_p
        self.prompt = prompt
        self.shots = shots
        self.tools = tools
        self.has_history = has_history
        self.json_output = json_output

    def generate_chain(self):
        llm = ChatGoogleGenerativeAI(
            model=self.llm_model,
            temperature = self.llm_temperature,
            top_p= self.llm_top_p,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        example_prompt_base = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate.from_template("{human}"),
            AIMessagePromptTemplate.from_template("{ai}"),
        ])

        system_prompt = ("system", self.prompt)
        shots = self.shots
        fewshots = FewShotChatMessagePromptTemplate(
            examples=shots,
            example_prompt=example_prompt_base,
        )
        messages = [
            system_prompt,
            cut_shots,
            fewshots,
        ]
        if self.has_history:
            messages.append(MessagesPlaceholder("chat_history"))

        messages.append(("human", "{input}"))
        has_tools = self.tools and len(self.tools) > 0
        if has_tools:
            messages.append(MessagesPlaceholder("agent_scratchpad"))

        prompt = ChatPromptTemplate.from_messages(messages)
        
        parser = JsonOutputParser() if self.json_output else StrOutputParser()

        if not self.has_history:
            chain = prompt | llm | parser
            return chain
        else:
            if has_tools:
                agent = create_tool_calling_agent(llm, self.tools, prompt)   
                agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
                chain = RunnableWithMessageHistory(
                    agent_executor,                           #chain_original (agora é o agente)
                    get_session_history=get_session_history,  #funcao para historico de sessao
                    input_messages_key="input",               #tudo no prompt que for {input} ele coloca o prompt do usuario
                    history_messages_key="chat_history"       #tudo que for {chat_history} ele coloca o histórico do usuario
                )           
                return chain
            else:
                baseChain = prompt | llm | parser
                chain = RunnableWithMessageHistory(
                    baseChain,                                #chain_original
                    get_session_history=get_session_history,  #funcao para historico de sessao
                    input_messages_key="input",               #tudo no prompt que for {usuario} ele coloca o prompt do usuario
                    history_messages_key="chat_history"       #tudo que for {chat_history} ele coloca o histórico do usuario
                )
                return chain



    