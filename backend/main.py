from datetime import datetime
from typing import List, Optional
from uuid import uuid4   # for generating unique session IDs

from fastapi import FastAPI, APIRouter
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

#Models 
class ChatRequest(BaseModel):
    # session_id is now OPTIONAL
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str   


class ChatHistoryItem(BaseModel):
    session_id: str
    user_query: str
    ai_response: str
    tools_used: List[str]
    timestamp: datetime


# In-memory store for history (for demo)
CHAT_HISTORY: List[ChatHistoryItem] = []


#Router for chat-related endpoints 
chat_router = APIRouter(
    prefix="",      # endpoints stay as /chat and /history
    tags=["chat"],
)


@chat_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint:
    - If session_id is missing -> create a new one
    - Call get_reply()
    - Store this turn in CHAT_HISTORY
    - Return reply + session_id
    """
    #Decide session_id
    if request.session_id:
        session_id = request.session_id
    else:
        # create new session id if not provided
        session_id = "session-" + uuid4().hex[:8]

    #Call chatbot core
    reply_text, tools_used = get_reply(request.message)

    #Save to history
    history_item = ChatHistoryItem(
        session_id=session_id,
        user_query=request.message,
        ai_response=reply_text,
        tools_used=tools_used,
        timestamp=datetime.utcnow(),
    )
    CHAT_HISTORY.append(history_item)

    #Return reply + session_id
    return ChatResponse(reply=reply_text, session_id=session_id)


@chat_router.get("/history", response_model=List[ChatHistoryItem])
async def history_endpoint(session_id: Optional[str] = None):
    """
    History API:
    - If session_id is given, filter by that session
    - Else, return all history
    """
    if session_id:
        return [item for item in CHAT_HISTORY if item.session_id == session_id]
    return CHAT_HISTORY


# Register router with main app
app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "message": "Chatbot API is running. Send POST /chat with {'message': '...'} (session_id optional)"
    }
