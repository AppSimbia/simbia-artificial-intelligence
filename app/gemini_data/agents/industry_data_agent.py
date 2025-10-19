from .base_agent import Agent
from ..tools.db_tools import FindPostByIndustry, FindChallengesByIndustry, FindEmployeeByIndustry, FindMatchByIndustry

with open("./app/gemini_data/prompts/industry_data_prompt.txt", 'r', encoding="utf-8") as file:
    prompt = file.read()

industry_data_chain = Agent (
    llm_model='gemini-2.5-flash',
    llm_temperature=0.7,
    llm_top_p=0.95,
    prompt=prompt,
    shots=[],
    has_history=True,
    tools=[FindPostByIndustry, FindChallengesByIndustry, FindEmployeeByIndustry, FindMatchByIndustry],
    docs_route=None,
    json_output=False    
).generate_chain()

