from .base_agent import Agent

with open("./app/gemini_data/prompts/judge_prompt.txt", 'r', encoding="utf-8") as file:
    prompt = file.read()

judge_shots = [
    {
        "human":"""PERGUNTA_ORIGINAL=Quais são os meus posts?
RESPOSTA=No momento a sua empresa possui 2 posts. O primeiro post tem a categoria organico o funcionario que realizou foi o Marcelo Bezerra o titulo do seu Post é Bagaço de Cana de açucar a unidade de medida é kg e possui 1000kg e a data da postagem foi 10/10/2025, deseja as informações do outro post?.""",
        "ai":"APROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Quais são os meus funcionários?
RESPOSTA=Sua empresa possui 6 funcionais sendo eles o Marcelo Bezerra, Ana Claudia, Joao Pedro, Lucas Silva, Mariana Costa e Pedro Henrique.""",
        "ai":"APROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Quais os match realizados com minha empresa entre os dias 10/10/2023 e 10/10/2024?
RESPOSTA=Nesse periodo, sua empresa participou de 3 matches. O primeiro match foi com a empresa Madeiras Ltda para o resíduo de madeira, o segundo match foi com a empresa Plásticos S/A para o resíduo plástico e o terceiro match foi com a empresa Metais Industriais para o resíduo metálico.""",
        "ai":"APROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Quais os desafios criados que falam de sustentabilidade?
RESPOSTA=Um desafio criado por outra empresa que fala sobre sustentabilidade foi 'Reduzir o desperdício de água na produção industrial'. Outro desafio é 'Implementar práticas de reciclagem de resíduos sólidos', e a resposta proposta foi 'Adotar um sistema de coleta seletiva e parcerias com cooperativas de reciclagem'.""",
        "ai":"APROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Quantos posts foram realizados pela minha empresa no período de 20/12/2022 a 20/01/2025?
RESPOSTA=Sua empresa fez 28 posts.""",
        "ai":"APROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Quais são os meus posts?
RESPOSTA=Você pode ver seus posts no Instagram ou LinkedIn. Basta acessar seu perfil por lá.""",
        "ai":"REPROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Quais são os meus funcionários?
RESPOSTA=Seus funcionários são incríveis! Você deveria premiá-los com um almoço especial.""",
        "ai":"REPROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Quais os match realizados com minha empresa entre os dias 10/10/2023 e 10/10/2024?
RESPOSTA=Não sei, mas você pode tentar perguntar para o seu gerente ou procurar no Google.""",
        "ai":"REPROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Qual o CNPJ da minha empresa?
RESPOSTA=O CNPJ da sua empresa é 31.809.777/0001-25.""",
        "ai":"REPROVADO"
    },
    {
        "human":"""PERGUNTA_ORIGINAL=Quantos posts foram realizados pela minha empresa no período de 20/12/2022 a 20/01/2025?
RESPOSTA=Não faço ideia, mas você pode verificar isso com o setor de marketing ou usar o Excel.""",
        "ai":"REPROVADO"
    }
]


judge_chain = Agent (
    api_key_env="GEMINI_API_KEY3",
    llm_model='gemini-2.0-flash',
    llm_temperature=0,
    llm_top_p=0.95,
    prompt=prompt,
    shots=judge_shots,
    has_history=False,
    tools=None,
    docs_route=None,
    json_output=False    
).generate_chain()
