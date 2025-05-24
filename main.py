from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_query import llm_response
from ingestion_vector import ingestion
from webscraper import run_scraper
import uvicorn

app = FastAPI(title="PromoSensei API", 
              description="API for Puma deals shopping assistant")

class QueryRequest(BaseModel):
    query: str
    command_type: str = "search" 

@app.post("/query")
def query_endpoint(request: QueryRequest):
    try:
        response = llm_response(request.command_type, request.query)
        return {"status": "success", "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/refresh")
def refresh_endpoint():
    try:
        run_scraper()
        ingestion()
        return {"status": "success", "message": "Data refreshed and ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)