from datetime import datetime
import random

from orm import db, MagicLink, TZ


def generate_magic_number():
    return str(random.randint(111111, 999999))


async def verify_magic_number(magic_number: str) -> bool:
    magic_number = db.query(MagicLink).filter_by(code=magic_number).first()
    if not magic_number:
        return False
    if (
        bool(magic_number.consumed)
        or magic_number.expires_at.timestamp() < datetime.now(TZ).timestamp()
    ):
        return False
    return True


async def confirm_user(
    magic_number: str,
):
    magic_number = db.query(MagicLink).filter_by(code=magic_number).first()
    if not magic_number:
        return None
    magic_number.consumed = True  # type: ignore
    magic_number.user.verified = True
    db.commit()
    return magic_number.user.email
