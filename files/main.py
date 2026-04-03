from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API test route
@app.get("/test")
def test():
    return {"message": "API working"}

# ✅ Serve frontend
@app.get("/")
def serve():
    return FileResponse("frontend/index.html")
