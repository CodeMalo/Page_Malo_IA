"""
notify.py — enviar el "pack social" por email (Gmail SMTP).
==========================================================
Las credenciales se pasan por parámetro (las pide la interfaz o vienen del
entorno). NUNCA se hardcodean ni se guardan en el repo.

Para Gmail necesitás una 'App password' (no tu contraseña normal):
  Cuenta Google → Seguridad → Verificación en 2 pasos → Contraseñas de aplicación.
"""

import smtplib, ssl, mimetypes
from email.message import EmailMessage
from pathlib import Path


def send_pack(user, app_password, to, subject, body, attachments=None):
    """Manda un email con texto + adjuntos. Devuelve True o lanza excepción."""
    if not (user and app_password and to):
        raise ValueError("Faltan credenciales: GMAIL_USER, GMAIL_APP_PASSWORD y EMAIL_DESTINO.")
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = user, to, subject
    msg.set_content(body or "(sin texto)")
    for p in (attachments or []):
        p = Path(p)
        if not p.exists():
            continue
        ctype = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
        s.login(user, app_password.replace(" ", ""))   # las app-passwords vienen con espacios
        s.send_message(msg)
    return True
