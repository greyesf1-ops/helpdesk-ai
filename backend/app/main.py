from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.ai_service import detect_category, generate_ai_reply
from app.database import Base, engine, get_db
from app.models import Conversation, Message
from app.schemas import ChatResponse, ConversationCreate, ConversationOut, MessageCreate, MessageOut


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HelpDesk AI API",
    description="API para chatbot de soporte tecnico con historial.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "helpdesk-ai-backend"}


@app.get("/api/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)) -> list[Conversation]:
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()


@app.post("/api/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)) -> Conversation:
    title = payload.title.strip() if payload.title else "Nueva conversacion"
    conversation = Conversation(title=title[:120])
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@app.get("/api/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(conversation_id: int, db: Session = Depends(get_db)) -> list[Message]:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@app.post("/api/conversations/{conversation_id}/messages", response_model=ChatResponse)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
) -> ChatResponse:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    content = payload.content.strip()
    category = detect_category(content)
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=content,
        category=category,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    if conversation.title == "Nueva conversacion":
        conversation.title = content[:80]
        db.add(conversation)
        db.commit()

    assistant_text, assistant_category = generate_ai_reply(db, conversation_id, content)
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_text,
        category=assistant_category,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(user_message=user_message, assistant_message=assistant_message)

