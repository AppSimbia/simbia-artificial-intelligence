from ..repository import gemini_repository
import json

agents_functions = {
    "features": gemini_repository.call_features
}

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

    return str(agent_return)


