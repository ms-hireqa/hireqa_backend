# app/main.py
# virtual environment: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass      .\venv\Scripts\Activate.ps1
# run statement: uvicorn app.main:app --reload


from fastapi import FastAPI
from app.routes import router

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is working!"}

# Include signup route
app.include_router(router)
