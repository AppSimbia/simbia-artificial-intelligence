import os
from ..gemini_data.agents.router_agent import router_chain
from ..gemini_data.agents.features_agent import features_chain
from ..gemini_data.agents.industry_data_agent import industry_data_chain
from ..gemini_data.agents.judge_agent import judge_chain

def call_router(input: str, user_id: str, session_history_id:str):
    response = router_chain.invoke({"input": input}, config={"configurable": {"session_id": session_history_id, "industry_id": user_id}})
    return response

def call_features(input: str, user_id: str, session_history_id:str):
    response = features_chain.invoke({"input": input}, config={"configurable": {"session_id": session_history_id, "industry_id": user_id}})
    return response["output"]

def call_industry_data(input: str, user_id: str, session_history_id:str):
    response = industry_data_chain.invoke({"input": input}, config={"configurable": {"session_id": session_history_id, "industry_id": user_id}})
    return response["output"]

def call_judge(input: str, user_id: str, session_history_id:str):
    response = judge_chain.invoke({"input": input}, config={"configurable": {"session_id": session_history_id, "industry_id": user_id}})
    return response