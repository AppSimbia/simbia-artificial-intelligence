# SIMBIA ARTIFICIAL INTELLIGENCE

Este projeto engloba toda a parte de inteligência artificial e machine learning do **SIMBIA**, por meio de uma API, consumida pelas APIs do aplicativo.

---

## Módulos

### 1. EVA

Chat bot do aplicativo, consegue buscar informações no banco de dados, fora responder sobre o funcionamento do aplicativo como um todo

#### Endpoint: /api/chat/question
- **Body**: {"industry_id": <id consulta>, "message": <pergunta>}
- **Header**: Authorization: <token>
- **Retorno**: {"msg": <ok/error>, "data": <retorno>, "error": <erro>}

#### Funcionamento

LangChain agent usando api do Gemini, usando uma arquitetura de agentes descrita a seguir:

<img width="1378" height="622" alt="image" src="https://github.com/user-attachments/assets/59e93dbb-56cc-4b78-9baf-14a62113728a" />


### 2. Match Inteligente

Modelo de Machine Learning que recebe dados do usuário e sugere um Post baseado no seu pedido, dando a melhor opção disponível.

#### Endpoint: /api/match/suggest
- **Body**: {"industry_id": <id consulta>, "category_id": <id categoria pedida>, "quantity": <quantidade pedida>, "measure_unit": <unidade de medida pedida>}
- **Header**: Authorization: <token>
- **Retorno**: {"msg": <ok/error>, "data": <retorno>, "error": <erro>}

#### Funcionamento

Usa a biblioteca KMeans para agrupar os Posts em N grupos e decidir o grupo do input do usuário.
Após decidir o grupo, filtra pelo grupo e aplica a distância euclidiana, para ordenar os posts do grupo do mais próximo até o mais distante e retorna os IDs ordenadamente.

---

## Estrutura de Arquivos
- **.github**: Apenas armazena o workflow para subir a imagem a qualquer atualização
- **app**: Armazena código do aplicativo: 
  - **common**: arquivos em comum para todas as pastas
    - **utils.py**: funções úteis para todos os arquivos
    - **wrapper.py**: wrappers criados paras funções
  - **gemini_data**: Dados do gemini
    - **agents**: Todos os agentes do sistema
      - **base_agent.py**: Classe base que gera agentes com base nos parâmetros
    - **prompts**: prompts dos agentes
    - **tools**: ferramentas usadas pelos agentes
  - **repository**: Armazena arquivos de conexões externas
    - **gemini_repository.py**: Armazena acessos ao gemini_data
    - **mongo_repository.py**: Armazena conexões com o mongo
    - **postgres_repository.py**: Armazena conexões com o postgres
    - **redis_repository.py**: Armazena conexões com o redis
  - **routes**: Armazena as rotas da API
  - **security**: Armazena funções de segurança de acesso a API
    - **authentication.py**: Armazena validações da segurança da API
  - **service**: Armazena as regras de negócio e lógica dos endpoints
- **.dockerignore**: Arquivos que o docker irá ignorar ao subir a imagem
- **.gitignore**: Arquivos ignorados pelo github
- **Dockerfile**: Passo a passo de como gerar a imagem
- **LICENSE**: Licença do aplicativo
- **README.md**: Esse arquivo
- **.env.example**: Exemplo de .env
- **requirements.txt**: Bibliotecas python necessárias para rodar o projeto
---

## Requisitos Necessários
- Banco de dados Redis, para armazenar alguns dados fixos
- Banco de dados Mongo, para armazenar dados dos Matchs
- Banco de dados Postgres, para armazenar usuários e posts
- API Key do Gemini, para o LLM

## Como Executar - Docker
1. Baixe o docker localmente
2. Execute a imagem preenchendo as envs
```bash
docker run -d -p 80:80`
  -e REDIS_URL="" `
  -e REDISKEY_AUTH="" `
  -e REDISKEY_ELBOW="" `
  -e MONGODB_URL="" `
  -e MONGODB_DB_NAME="" `
  -e MONGODB_EVA_COLLECTION="" `
  -e MONGODB_MATCH_COLLECTION="" `
  -e MONGODB_CHALLENGE_COLLECTION="" `
  -e POSTGRES_DB_NAME="" `
  -e POSTGRES_USER="" `
  -e POSTGRES_PASSWORD="" `
  -e POSTGRES_HOST="" `
  -e POSTGRES_PORT="" `
  -e GEMINI_API_KEY="" `
  --name simbia_app `
  simbiaapp/simbia-artificial-intelligence
```

## Como Executar - Python
1. Clone o projeto localmente
2. Baseando-se no .env.example, preencha os dados de ENV
3. Instale os pacotes em requirements.txt
```bash
pip install -r requirements.txt 
```
4. Rode o projeto
```bash
flask run
```
