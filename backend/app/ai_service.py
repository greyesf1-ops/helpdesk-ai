import os

from sqlalchemy.orm import Session

from app.models import Message


SYSTEM_PROMPT = (
    "Eres HelpDesk AI, un asistente de soporte tecnico para usuarios internos. "
    "Responde en espanol claro, con pasos numerados cuando sea util. "
    "Clasifica mentalmente el problema, pide datos faltantes si hacen falta y "
    "recomienda escalar si hay riesgo de seguridad, perdida de datos o caida general."
)


CATEGORY_KEYWORDS = {
    "credenciales": ["password", "contrasena", "contraseña", "login", "usuario", "acceso"],
    "red": ["internet", "wifi", "red", "conexion", "conexión", "vpn"],
    "correo": ["correo", "email", "outlook", "gmail", "buzon", "buzón"],
    "impresion": ["impresora", "imprimir", "toner", "tóner", "papel"],
    "rendimiento": ["lento", "lentitud", "congela", "trabado", "cpu", "memoria"],
    "backup": ["backup", "respaldo", "restaurar", "perdido", "borrado", "archivo"],
    "seguridad": ["virus", "phishing", "malware", "sospechoso", "hack", "seguridad"],
}


def detect_category(text: str) -> str:
    normalized = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "general"


def build_fallback_reply(user_message: str, category: str) -> str:
    intro = "Entendido. Voy a tratarlo como un caso de soporte tecnico"
    category_text = f" de categoria {category}" if category != "general" else ""
    common_steps = [
        "1. Confirma desde cuando ocurre el problema y si afecta solo a un usuario o a varios.",
        "2. Reinicia la aplicacion o equipo involucrado y vuelve a probar.",
        "3. Toma captura del error o anota el mensaje exacto si aparece alguno.",
    ]
    category_steps = {
        "credenciales": "4. Si es acceso, valida usuario, bloqueo de cuenta y ultimo cambio de contrasena.",
        "red": "4. Si es red, prueba otra pagina, verifica WiFi/cable y confirma si la VPN esta conectada.",
        "correo": "4. Si es correo, revisa conexion, espacio del buzon y prueba enviar un mensaje interno.",
        "impresion": "4. Si es impresion, revisa cola de impresion, papel, toner y conexion de la impresora.",
        "rendimiento": "4. Si es lentitud, revisa programas abiertos, espacio en disco y consumo de CPU/memoria.",
        "backup": "4. Si hubo perdida de archivos, evita sobrescribir datos y solicita restauracion desde backup.",
        "seguridad": "4. Si sospechas de seguridad, desconecta el equipo de la red y escala el incidente de inmediato.",
        "general": "4. Documenta el caso con prioridad, impacto y pasos ya probados.",
    }
    close = (
        "Si el problema continua despues de estos pasos, registra el ticket con prioridad, "
        "impacto, usuario afectado, equipo y evidencia."
    )
    return "\n".join([f"{intro}{category_text}.", *common_steps, category_steps[category], close])


def get_recent_messages(db: Session, conversation_id: int, limit: int = 8) -> list[Message]:
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def generate_ai_reply(db: Session, conversation_id: int, user_message: str) -> tuple[str, str]:
    category = detect_category(user_message)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return build_fallback_reply(user_message, category), category

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        history = get_recent_messages(db, conversation_id)
        input_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        input_messages.extend({"role": item.role, "content": item.content} for item in history)
        if not history or history[-1].role != "user" or history[-1].content != user_message:
            input_messages.append({"role": "user", "content": user_message})

        response = client.responses.create(model=model, input=input_messages)
        answer = response.output_text.strip()
        if answer:
            return answer, category
    except Exception:
        pass

    return build_fallback_reply(user_message, category), category
