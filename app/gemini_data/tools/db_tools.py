from typing import Optional
from langchain.tools import tool
from datetime import datetime
from ...repository.mongo_repository import get_collection
from ...repository.postgres_repository import open_connection 
import re
 
collectionMatch = get_collection("MONGODB_MATCH_COLLECTION")
collectionDesafios = get_collection("MONGODB_CHALLENGE_COLLECTION")

from typing import Optional
from langchain.pydantic_v1 import BaseModel, Field

class FindByIndustryBaseModel(BaseModel):
    idindustry: int = Field(..., description="Id da industria (sempre use o campo ID_INDUSTRIA vindo do prompt).")
    date_from_local: Optional[str] = Field(default=None, description="Data local inicial (America/Sao_Paulo) no formato YYYY-MM-DD (opcional).")
    date_to_local: Optional[str] = Field(default=None, description="Data local final (America/Sao_Paulo) no formato YYYY-MM-DD (opcional).")
    date_local: Optional[str] = Field(default=None, description="Data local (America/Sao_Paulo) no formato YYYY-MM-DD (opcional).")
    text: Optional[str] = Field(default=None, description="Texto para buscar caso necessário (opcional).")

@tool("FindPostByIndustry", args_schema=FindByIndustryBaseModel)
def FindPostByIndustry(
    idindustry: int,
    date_local: Optional[str] = None,
    date_from_local: Optional[str] = None,
    date_to_local: Optional[str] = None,
    text : Optional[str] = None,
) -> dict:
    """Consulta todos os Post realizados por uma empresa, baseando se nos filtros de data (text não é usado aqui).""" # docstring obrigatório da @tools do langchain
    conn, cur = open_connection()
    try:
       
        query = """
             SELECT pc.cCategoryName
                  , e.cEmployeeName
                  , i.cIndustryName
                  , p.cTitle
                  , p.cDescription
                  , p.nQuantity
                  , p.cMeasureUnit
                  , p.dPublication
                  , p.cStatus
               FROM Post p
               JOIN productcategory pc ON pc.idproductcategory = p.idproductcategory
               JOIN industry        i  ON i.idindustry         = p.idindustry
               JOIN industrytype    it ON it.idindustrytype    = i.idindustrytype
               JOIN employee       e  ON e.idemployee        = p.idemployee
              WHERE p.cActive = '1'
                AND pc.cActive = '1'
                AND i.cActive  = '1'
                AND it.cActive = '1'
                AND e.cActive  = '1'
        """
        conditions = ["i.idIndustry = %s"]
        params = [idindustry]
 
        if date_local:
            conditions.append("p.dPublication::date = %s::date")
            params.append(date_local)
        if date_from_local:
            conditions.append("p.dPublication::date >= %s::date")
            params.append(date_from_local)
        if date_to_local:
            conditions.append("p.dPublication::date <= %s::date")
            params.append(date_to_local)
 
        if conditions:
            query += " AND " + " AND ".join(conditions)
 
        cur.execute(query, tuple(params))
 
        columns = [desc[0] for desc in cur.description]
        data = [dict(zip(columns, row)) for row in cur.fetchall()]
 
        return {"status": "ok", "data": data}
 
    except Exception as e:
        return {"status": "error", "message": str(e)}
 
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
 
@tool ("FindEmployeeByIndustry", args_schema=FindByIndustryBaseModel)
def FindEmployeeByIndustry(
    idindustry: int,
    date_local: Optional[str] = None,
    date_from_local: Optional[str] = None,
    date_to_local: Optional[str] = None,
    text: Optional[str] = None,
) -> dict:
    """Lista todos os funcionários da industria e suas informações (textos e datas não importam aqui)."""
 
    try:
        conn, cur = open_connection()
        query = """
            SELECT Employee.idemployee
                 , cEmployeeName
                 , Employee.cActive
              FROM Employee
              JOIN Industry I on Employee.idIndustry = I.idIndustry
             WHERE I.idIndustry = %s
        """
        cur.execute(query, (idindustry,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        employees = [dict(zip(columns, row)) for row in rows]
        return {"status": "ok", "industry_id": idindustry, "total_employees": len(employees), "employees": employees}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
 
@tool("FindMatchByIndustry", args_schema=FindByIndustryBaseModel)
def FindMatchByIndustry(
    idindustry: int,
    date_local: Optional[str] = None,
    date_from_local: Optional[str] = None,
    date_to_local: Optional[str] = None,
    text : Optional[str] = None,
) -> dict:
    """Consulta todos os Matches realizados por uma indústria, com filtros de data opcionais ."""
    
    
    sql_query = """
        SELECT cCNPJ
          FROM Industry
         WHERE idIndustry = %s
           AND cActive = '1';
    """
    params = [idindustry]
    conn, cur = open_connection()
    try:
        cur.execute(sql_query, tuple(params))
        rows = cur.fetchall()
        cCNPJ = [row[0] for row in rows]
    except Exception as e:
        return {"status": "error", "message": "Erro ao buscar os CNPJ no SQL", "detail": str(e)}
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

    if not cCNPJ:
        return {"status": "ok", "message": "Nenhuma empresa ativa encontrada.", "matches": []}
 
    match_cond = {
        "$or": [
            {"idIndustryPurchaser": {"$in": cCNPJ}},
            {"idIndustrySeller": {"$in": cCNPJ}},
        ]
    }
 
    if date_from_local or date_to_local:
        date_range = {}
        if date_from_local:
            date_range["$gte"] = datetime.strptime(date_from_local, "%Y-%m-%d")
        if date_to_local:
            date_range["$lt"] = datetime.strptime(date_to_local, "%Y-%m-%d")
 
        match_cond = {"$and": [match_cond, {"data": date_range}]}
 
    pipeline = [
        {"$match": match_cond},
        {"$project": {
            "_id": 0,
            "idPost": 1,
            "idEmployeePurchaser": 1,
            "idEmployeeSeller": 1,
            "idIndustryPurchaser": 1,
            "idIndustrySeller":1,
            "status": 1,
            "data": 1
        }},
        {"$sort": {"data": -1}}
    ]
 
 
    try:
        matches = list(collectionMatch.aggregate(pipeline))
    except Exception as e:
        return {"status": "error", "message": "Erro ao consultar MongoDB", "detail": str(e)}
 
    return {
        "status": "ok",
        "industry_id": idindustry,
        "filters": {
            "date_local": date_local,
            "date_from_local": date_from_local,
            "date_to_local": date_to_local
        },
        "total_matches": len(matches),
        "matches": matches
    }
  
@tool("FindChallengesByIndustry", args_schema=FindByIndustryBaseModel)
def FindChallengesByIndustry(
    idindustry: int,
    date_local: Optional[str] = None,
    date_from_local: Optional[str] = None,
    date_to_local: Optional[str] = None,
    text: Optional[str] = None,
) -> dict:
    """Consulta todos os desafios/soluções (perguntas e respostas) de todas as indústrias, com filtros de texto opcionais (datas são desconsideradas)."""
 
    match_cond = {}
     
    if text:
        palavras = [p.strip() for p in text.split() if p.strip()]
        regexes = [re.compile(p, re.IGNORECASE) for p in palavras]
 
       
        match_cond["$or"] = []
        for regex in regexes:
            match_cond["$or"].extend([
                {"title": regex},
                {"text": regex},
                {"solutions.title": regex},
                {"solutions.text": regex}
            ])
 
    pipeline = [
        {"$match": match_cond},
        {"$project": {
            "_id": 0,
            "idEmployeeQuestion": 1,
            "title": 1,
            "text": 1,
            "solutions": 1
        }},
        {"$sort": {"_id": -1}}
    ]
 
    try:
        desafios = list(collectionDesafios.aggregate(pipeline))
    except Exception as e:
        return {"status": "error", "message": "Erro ao consultar MongoDB", "detail": str(e)}
 
    return {
        "status": "ok",
        "industry_id": idindustry,
        "filters": {
            "text": text
        },
        "total_desafios": len(desafios),
        "desafios": desafios
    }

