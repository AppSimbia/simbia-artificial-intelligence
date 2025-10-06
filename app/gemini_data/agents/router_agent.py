from .base_agent import Agent

with open("./app/gemini_data/prompts/router_prompt.txt", 'r', encoding="utf-8") as file:
    prompt = file.read()

router_chain = Agent (
    llm_model='gemini-2.0-flash',
    llm_temperature=0,
    llm_top_p=0.95,
    prompt=prompt,
    shots=[],
    has_history=True,
    tools=None,
    docs_route=None,
    json_output=False    
).generate_chain()
