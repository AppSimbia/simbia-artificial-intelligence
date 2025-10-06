from .base_agent import Agent

FEATURES_FOLDER = "./app/gemini_data/prompts/features/"

with open("./app/gemini_data/prompts/features_prompt.txt", 'r', encoding="utf-8") as file:
    prompt = file.read()

features_chain = Agent (
    llm_model='gemini-2.5-flash',
    llm_temperature=0.7,
    llm_top_p=0.95,
    prompt=prompt,
    shots=[],
    has_history=True,
    tools=None,
    docs_route=FEATURES_FOLDER,
    json_output=False    
).generate_chain()

