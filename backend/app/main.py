from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai_service import detect_category, generate_ai_reply
from app.database import Base, engine, get_db
from app.models import Conversation, Message
from app.schemas import ChatResponse, ConversationCreate, ConversationOut, MessageCreate, MessageOut


UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

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

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def ensure_schema() -> None:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS attachment_url VARCHAR(255)"))


ensure_schema()


async def save_image_attachment(file: UploadFile | None) -> str | None:
    if not file or not file.filename:
        return None

    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if not extension:
        raise HTTPException(status_code=400, detail="Solo se permiten imagenes JPG, PNG, WEBP o GIF")

    content = await file.read()
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 5 MB")

    filename = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(content)
    return f"/uploads/{filename}"


def persist_chat_message(
    conversation_id: int,
    content: str,
    db: Session,
    attachment_url: str | None = None,
) -> ChatResponse:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    normalized_content = content.strip()
    if not normalized_content:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacio")

    category = detect_category(normalized_content)
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=normalized_content,
        category=category,
        attachment_url=attachment_url,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    if conversation.title == "Nueva conversacion":
        conversation.title = normalized_content[:80]
        db.add(conversation)
        db.commit()

    prompt_content = normalized_content
    if attachment_url:
        prompt_content = (
            f"{normalized_content}\n\nEl usuario adjunto una imagen o captura como evidencia tecnica."
        )

    assistant_text, _assistant_category = generate_ai_reply(db, conversation_id, prompt_content)
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_text,
        category=category,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(user_message=user_message, assistant_message=assistant_message)


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
    return persist_chat_message(conversation_id, payload.content, db)


@app.post("/api/conversations/{conversation_id}/messages-with-attachment", response_model=ChatResponse)
async def send_message_with_attachment(
    conversation_id: int,
    content: str = Form(..., min_length=1, max_length=4000),
    attachment: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> ChatResponse:
    attachment_url = await save_image_attachment(attachment)
    return persist_chat_message(conversation_id, content, db, attachment_url)
