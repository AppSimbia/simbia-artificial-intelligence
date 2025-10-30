from ..repository import gemini_repository
import json

agents_functions = {
    "features": gemini_repository.call_features,
    "industry_data": gemini_repository.call_industry_data
}

BLOCKED_WORLDS = [
    # 1. Conteúdo sexual ou explícito
    "pornografia","pornô","porno","porn","nude","nudes","erótico","erotico","masturbação","masturbacao",
    "orgasmo","penetração","penetracao","pênis","penis","vagina","sexo explicito","sexo explícito",
    "onlyfans","boquete","pau","buceta","cu","foder","punheta","ejaculação","ejaculacao","transar",
    "anal","oral","chupar","broxa","broxar","prostíbulo","prostituição","prostituicao","fetiche",
    "peitinho","bunda","tesão","tesao","pornos","dp","bdsm",

    # 2. Discurso de ódio e discriminação
    "nazismo","neonazista","racista","racismo","antissemita","antissemitismo","homofóbico","homofobico",
    "homofobia","transfobia","misógino","misogino","misoginia","xenofobia","xenófobo",
    "supremacista","eugenia","escravizar","degenerado","cripple","aleijado",

    # 3. Informações pessoais e confidenciais
    "cpf","rg","senha","token","api key","chave de acesso","cartão de crédito","cartao de credito",
    "cvv","pix","telefone pessoal","endereço residencial","endereco residencial",
    "número do cartão","numero do cartao","localização exata","geolocalização",

    # 4. Atividades ilegais
    "pedofilia","pornografia infantil","estupro","incesto","tráfico humano","trafico humano",
    "sequestro","extorsão","extorsao","genocídio","genocidio","terrorismo","bomba","explosivo",
    "assassinato","homicídio","homicidio","tortura","mutilação","mutilacao","zoofilia","bestialidade",
    "necrofilia","fraude bancária","fraude fiscal","hackear","invasão de sistema","pirataria","roubo"
    ,"estelionato","lavagem de dinheiro","tráfico","trafico","crime organizado",

    # 5. Linguagem ofensiva ou desrespeitosa
    "porra","caralho","arrombado","otário","otario","imbecil","idiota",
    "fdp","corno","vagabundo","desgraçado","escroto","burro","retardado",
    "babaca","otaria","nojento","nojenta","pau no cu","boceta","piranha","cadela"
]

def get_judge_response(user_input: str, agent_return:str, user_id: str, session_id:str) -> str:
    judge_message = f"""
    PERGUNTA_ORIGINAL={user_input}
    RESPOSTA_AGENTE={agent_return}
    """
   
    for x in judge_message.split(" "):
        if x.lower() in BLOCKED_WORLDS:
            return "Não posso responder essa pergunta no momento, reformule a pergunta e tente novamente."

    judge_response = str(gemini_repository.call_judge(judge_message, user_id, session_id))
    if judge_response != "APROVADO":
        return "Não posso responder essa pergunta no momento, reformule a pergunta e tente novamente."
    return agent_return

def get_AI_response(user_input: str, user_id: str, session_id:str):
    agent_return = ""
    # Pega a resposta do roteador
    route_response = str(gemini_repository.call_router(user_input, user_id, session_id))
    if route_response.startswith("AGENTE="):
        # Se tiver rota, manda pra rota
        route_agent = route_response.split("\n")[0].split("AGENTE=")[1].strip().lower()
        if route_agent not in agents_functions:
            raise Exception(f"Agente '{route_agent}' não encontrado.")
        else:
            agent_return = str(agents_functions[route_agent](route_response, user_id, session_id))
    else:
        # Se não tiver rota, responde com o que o agente pediu
        agent_return = route_response
    # Passa pelo juíz e retorna o que ele devolver
    agent_return = get_judge_response(user_input, agent_return, user_id, session_id)  

    return str(agent_return)


