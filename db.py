"""Postgres persistence for TableScore rooms (JSONB documents)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import DateTime, String, create_engine, delete, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.orm.attributes import flag_modified

load_dotenv()

ROOM_TTL_ACTIVE = timedelta(hours=48)
ROOM_TTL_ENDED = timedelta(hours=24)


def _normalize_database_url(url: str) -> str:
    """Hosts often provide postgresql://; SQLAlchemy+psycopg needs postgresql+psycopg://."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg" not in url.split("://", 1)[0]:
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env or set the variable in your host."
    )

engine = create_engine(_normalize_database_url(DATABASE_URL), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class RoomRow(Base):
    __tablename__ = "rooms"

    room_token: Mapped[str] = mapped_column(String(64), primary_key=True)
    password: Mapped[str] = mapped_column(String(4), unique=True, nullable=False, index=True)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def expire_old_rooms(session: Session) -> int:
    """Free passwords by deleting stale rooms. Returns number deleted."""
    now = datetime.now(timezone.utc)
    active_cutoff = now - ROOM_TTL_ACTIVE
    ended_cutoff = now - ROOM_TTL_ENDED

    rows = session.scalars(select(RoomRow)).all()
    to_delete: list[str] = []
    for row in rows:
        status = (row.state or {}).get("status", "active")
        updated = row.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        if status == "ended" and updated < ended_cutoff:
            to_delete.append(row.room_token)
        elif updated < active_cutoff:
            to_delete.append(row.room_token)

    if not to_delete:
        return 0

    session.execute(delete(RoomRow).where(RoomRow.room_token.in_(to_delete)))
    return len(to_delete)


def used_passwords(session: Session) -> set[str]:
    return set(session.scalars(select(RoomRow.password)).all())


def password_taken(session: Session, password: str) -> bool:
    return (
        session.scalar(select(RoomRow.room_token).where(RoomRow.password == password))
        is not None
    )


def insert_room(session: Session, room: dict) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        RoomRow(
            room_token=room["room_token"],
            password=room["password"],
            state=deepcopy(room),
            created_at=now,
            updated_at=now,
        )
    )


def fetch_room(session: Session, room_token: str, *, for_update: bool = False) -> Optional[dict]:
    stmt = select(RoomRow).where(RoomRow.room_token == room_token)
    if for_update:
        stmt = stmt.with_for_update()
    row = session.scalar(stmt)
    if not row:
        return None
    return deepcopy(row.state)


def fetch_room_by_password(
    session: Session, password: str, *, for_update: bool = False
) -> Optional[dict]:
    stmt = select(RoomRow).where(RoomRow.password == password)
    if for_update:
        stmt = stmt.with_for_update()
    row = session.scalar(stmt)
    if not row:
        return None
    return deepcopy(row.state)


def persist_room(session: Session, room: dict) -> None:
    row = session.scalar(
        select(RoomRow).where(RoomRow.room_token == room["room_token"]).with_for_update()
    )
    if not row:
        raise KeyError(room["room_token"])
    row.password = room["password"]
    row.state = deepcopy(room)
    row.updated_at = datetime.now(timezone.utc)
    flag_modified(row, "state")


@contextmanager
def room_transaction(room_token: str) -> Generator[dict, None, None]:
    """Load a room with a row lock, yield mutable state dict, persist on success."""
    session = get_session()
    try:
        room = fetch_room(session, room_token, for_update=True)
        if room is None:
            raise LookupError(room_token)
        yield room
        persist_room(session, room)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
