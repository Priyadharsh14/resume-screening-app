import smtplib
from email.message import EmailMessage

import httpx

from ..config import settings

DEFAULT_TEMPLATES = {
    "selected": ("Congratulations from CloudRiq - {{job_title}}",
                 "Dear {{name}},\n\nWe are pleased to let you know that you have been selected for the "
                 "{{job_title}} position at CloudRiq. Our HR team will contact you shortly with next steps.\n\n"
                 "Best regards,\nCloudRiq HR"),
    "rejected": ("Update on your application - {{job_title}}",
                 "Dear {{name}},\n\nThank you for your interest in the {{job_title}} position at CloudRiq. "
                 "After careful review we will not be moving forward with your application at this time. "
                 "We encourage you to apply for future openings.\n\nBest regards,\nCloudRiq HR"),
    "on_hold": ("Your application is on hold - {{job_title}}",
                "Dear {{name}},\n\nThank you for applying for the {{job_title}} position at CloudRiq. "
                "Your application is currently on hold and we will get back to you as soon as we can.\n\n"
                "Best regards,\nCloudRiq HR"),
}


def render(template: str, **ctx) -> str:
    for k, v in ctx.items():
        template = template.replace("{{" + k + "}}", str(v))
    return template


def send(to: str, subject: str, body: str) -> None:
    """Raises on failure."""
    if settings.EMAIL_BACKEND == "none":
        raise RuntimeError("Email delivery is not configured (EMAIL_BACKEND=none). Set SMTP or SendGrid secrets.")
    if settings.EMAIL_BACKEND == "sendgrid":
        r = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
            json={"personalizations": [{"to": [{"email": to}]}], "from": {"email": settings.EMAIL_FROM},
                  "subject": subject, "content": [{"type": "text/plain", "value": body}]},
            timeout=15,
        )
        r.raise_for_status()
        return
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.EMAIL_FROM, to, subject
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
        if settings.SMTP_TLS:
            s.starttls()
        if settings.SMTP_USER:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.send_message(msg)
