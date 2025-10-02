from ..repository import gemini_repository
import json

def call_orchestrator(user_input: str, agents:list, user_id: str):
    orchestrator_object = {}
    orchestrator_object["pergunta_inicial"] = user_input
    orchestrator_object["agentes"] = agents

    orchestrator_input = json.dumps(orchestrator_object, ensure_ascii=False)
    return gemini_repository.call_orchestrator(orchestrator_input, user_id)

def get_AI_response(user_input: str, user_id: str):
    route_response = list(gemini_repository.call_router(user_input, user_id))
    final_response = ""
    print(route_response)
    if len(route_response) == 0:
        final_response = call_orchestrator(user_input, [], user_id)
    
    return final_response


