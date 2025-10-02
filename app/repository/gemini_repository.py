import os
from ..gemini_data.agents.router_agent import router_chain
from ..gemini_data.agents.orchestrator_agent import orchestrator_chain


def call_router(user_input: str, user_id: str):
    response = router_chain.invoke({"input": user_input}, config={"configurable": {"session_id": user_id}})
    return response

def call_orchestrator(user_input: str, user_id: str):
    response = orchestrator_chain.invoke({"input": user_input}, config={"configurable": {"session_id": user_id}})
    return response