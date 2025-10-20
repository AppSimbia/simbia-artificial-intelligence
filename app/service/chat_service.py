from ..repository import gemini_repository
import json

agents_functions = {
    "features": gemini_repository.call_features,
    "industry_data": gemini_repository.call_industry_data
}

def get_judge_response(user_input: str, agent_return:str, user_id: str) -> str:
    judge_message = f"""
    PERGUNTA_ORIGINAL={user_input}
    RESPOSTA_AGENTE={agent_return}
    """

    judge_response = str(gemini_repository.call_judge(judge_message, user_id))
    if judge_response != "APROVADO":
        return "Não posso responder essa pergunta no momento, reformule a pergunta e tente novamente."
    return agent_return

def get_AI_response(user_input: str, user_id: str):
    agent_return = ""

    route_response = str(gemini_repository.call_router(user_input, user_id))
    if route_response.startswith("AGENTE="):
        route_agent = route_response.split("\n")[0].split("AGENTE=")[1].strip().lower()
        if route_agent not in agents_functions:
            raise Exception(f"Agente '{route_agent}' não encontrado.")
        else:
            agent_return = str(agents_functions[route_agent](route_response, user_id))
    else:
        agent_return = route_response
    
    agent_return = get_judge_response(user_input, agent_return, user_id)  

    return str(agent_return)


