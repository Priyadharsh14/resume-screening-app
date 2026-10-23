from sqlalchemy.orm import Session

from .models import AuditLog


def log(db: Session, user, action: str, entity: str = "", entity_id: int | None = None, **detail):
    db.add(AuditLog(user_id=getattr(user, "id", None), action=action, entity=entity,
                    entity_id=entity_id, detail=detail))
