import os
from hashlib import sha1

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

PRIORITY_KEYWORDS = {
    "alta": ["urgente", "produccion", "caido", "caida", "no funciona", "bloqueado", "todos", "empresa"],
    "media": ["no puedo", "error", "falla", "problema", "lento", "intermitente"],
    "seguridad": ["virus", "phishing", "malware", "hack", "sospechoso", "ransomware"],
}

AGENT_OPENERS = [
    "Gracias por reportarlo. Ya estoy tomando el caso y voy a guiarte con el diagnostico inicial.",
    "Recibido. Lo voy a manejar como incidente de mesa de ayuda y te dejo los pasos de validacion.",
    "Entiendo el caso. Primero voy a separar impacto, evidencia y acciones inmediatas para avanzar ordenadamente.",
    "De acuerdo. Con la informacion que compartiste, voy a abrir el analisis tecnico inicial.",
]

CATEGORY_RUNBOOKS = {
    "credenciales": {
        "impact": "posible bloqueo de cuenta o problema de autenticacion",
        "steps": [
            "Confirma si el usuario puede entrar a otros sistemas con la misma cuenta.",
            "Valida si hubo cambio reciente de contrasena o intentos fallidos.",
            "Prueba restablecimiento de contrasena solo si el usuario confirma identidad.",
        ],
        "question": "Puedes confirmar si el error dice contrasena incorrecta, cuenta bloqueada o usuario no encontrado?",
    },
    "red": {
        "impact": "posible falla de conectividad local, WiFi, cable o VPN",
        "steps": [
            "Prueba abrir una pagina externa y una pagina interna de la empresa.",
            "Confirma si el equipo esta por WiFi, cable o VPN.",
            "Ejecuta una prueba rapida reiniciando adaptador/red o cambiando de red si es posible.",
        ],
        "question": "El problema afecta solo a tu equipo o tambien a otros usuarios cercanos?",
    },
    "correo": {
        "impact": "posible incidencia de acceso, envio, recepcion o espacio de buzon",
        "steps": [
            "Verifica si el correo abre desde navegador y desde la aplicacion instalada.",
            "Revisa si puedes enviar un mensaje de prueba a un usuario interno.",
            "Confirma si aparece error de credenciales, conexion o buzon lleno.",
        ],
        "question": "El problema es al iniciar sesion, enviar correos, recibir correos o abrir adjuntos?",
    },
    "impresion": {
        "impact": "posible falla de cola de impresion, consumibles o conexion de impresora",
        "steps": [
            "Revisa si la impresora aparece en linea y sin trabajos atascados.",
            "Confirma papel, toner y mensajes en pantalla de la impresora.",
            "Prueba imprimir una pagina de prueba desde otro equipo si esta disponible.",
        ],
        "question": "La impresora muestra algun codigo de error o solo no imprime?",
    },
    "rendimiento": {
        "impact": "posible saturacion de recursos o problema de aplicacion/equipo",
        "steps": [
            "Cierra aplicaciones no necesarias y verifica si mejora.",
            "Revisa espacio disponible en disco y consumo de CPU/memoria.",
            "Anota si la lentitud ocurre al iniciar sesion, abrir una app o durante todo el dia.",
        ],
        "question": "La lentitud ocurre en todo el equipo o solo en una aplicacion especifica?",
    },
    "backup": {
        "impact": "posible perdida de informacion o necesidad de restauracion",
        "steps": [
            "Evita modificar la carpeta o archivo afectado para no sobrescribir evidencia.",
            "Confirma nombre, ruta y fecha aproximada del archivo perdido.",
            "Solicita restauracion desde el ultimo backup disponible.",
        ],
        "question": "Que archivo o carpeta necesitas restaurar y desde que fecha aproximada?",
    },
    "seguridad": {
        "impact": "posible incidente de seguridad que requiere contencion",
        "steps": [
            "No abras enlaces ni archivos sospechosos adicionales.",
            "Desconecta el equipo de la red si sospechas infeccion activa.",
            "Escala el caso a seguridad TI con captura, remitente y hora del evento.",
        ],
        "question": "Puedes indicar si recibiste un correo, enlace, archivo o alerta del antivirus?",
    },
    "general": {
        "impact": "incidente general pendiente de clasificacion",
        "steps": [
            "Describe el sistema afectado y el mensaje exacto de error.",
            "Confirma desde cuando ocurre y si ya probaste reiniciar.",
            "Adjunta captura si el sistema muestra una alerta o codigo.",
        ],
        "question": "Que sistema o aplicacion esta fallando y que mensaje exacto aparece?",
    },
}


def detect_category(text: str) -> str:
    normalized = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "general"


def detect_priority(text: str, category: str) -> str:
    normalized = text.lower()
    if category == "seguridad" or any(keyword in normalized for keyword in PRIORITY_KEYWORDS["seguridad"]):
        return "alta"
    if any(keyword in normalized for keyword in PRIORITY_KEYWORDS["alta"]):
        return "alta"
    if any(keyword in normalized for keyword in PRIORITY_KEYWORDS["media"]):
        return "media"
    return "baja"


def stable_choice(text: str, options: list[str]) -> str:
    digest = sha1(text.encode("utf-8")).hexdigest()
    return options[int(digest[:4], 16) % len(options)]


def build_ticket_id(text: str) -> str:
    digest = sha1(text.encode("utf-8")).hexdigest().upper()
    return f"HD-{digest[:6]}"


def build_fallback_reply(user_message: str, category: str) -> str:
    runbook = CATEGORY_RUNBOOKS[category]
    priority = detect_priority(user_message, category)
    ticket_id = build_ticket_id(user_message)
    opener = stable_choice(user_message, AGENT_OPENERS)
    escalation = {
        "alta": "Si afecta a varios usuarios o impide trabajar, lo escalaria como prioridad alta.",
        "media": "Si despues de estas pruebas continua, lo dejaria como prioridad media para seguimiento.",
        "baja": "Por ahora lo dejaria como prioridad baja, salvo que el impacto aumente.",
    }[priority]
    evidence = (
        "Como adjuntaste evidencia, la mantendria asociada al caso para que soporte no tenga que pedirla otra vez."
        if "adjunto" in user_message.lower() or "captura" in user_message.lower()
        else "Si puedes, adjunta una captura del mensaje de error para acelerar el diagnostico."
    )

    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(runbook["steps"], start=1))
    return "\n".join(
        [
            opener,
            f"Ticket sugerido: {ticket_id}",
            f"Categoria detectada: {category}",
            f"Prioridad inicial: {priority}",
            f"Impacto probable: {runbook['impact']}.",
            steps,
            f"Pregunta para continuar: {runbook['question']}",
            evidence,
            escalation,
        ]
    )


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
