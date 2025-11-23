from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chatbot_core import get_reply

app = FastAPI(
    title="Chatbot Backend API",
    description="FastAPI backend for a Groq + LangChain tools-based chatbot",
)

# Allow frontend (HTML/JS) to call this API from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    reply_text = get_reply(request.message)
    return ChatResponse(reply=reply_text)

@app.get("/")
async def root():
    return {
        "message": "Chatbot API is running. Send POST /chat with {'message': '...'}"
    }
