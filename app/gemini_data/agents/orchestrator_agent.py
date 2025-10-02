from .base_agent import Agent

with open("./app/gemini_data/prompts/orchestrator_prompt.txt", 'r', encoding="utf-8") as file:
    prompt = file.read()

orchestrator_chain = Agent (
    llm_model='gemini-2.5-flash',
    llm_temperature=0.7,
    llm_top_p=0.95,
    prompt=prompt,
    shots=[],
    has_history=True,
    tools=None,
    json_output=False    
).generate_chain()

