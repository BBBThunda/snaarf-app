from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

TWITCH_UN_MAX_LENGTH = 25
POLL_DESCRIPTION_MAX_LENGTH = 256
POLL_OPTION_MAX_LENGTH = 64


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    twitch_id: Mapped[int] = mapped_column(index=True)
    twitch_username: Mapped[str] = mapped_column(String(TWITCH_UN_MAX_LENGTH))
    created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    modified: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r},"
        + " twitch_id={self.twitch_id!r},"
        + " twitch_username={self.twitch_username!r},"
        + " created={self.created!r},"
        + " modified={self.modified!r})"


class Poll(Base):
    __tablename__ = "poll"

    id: Mapped[int] = mapped_column(primary_key=True)
    target: Mapped[str] = mapped_column(
        String(TWITCH_UN_MAX_LENGTH),
        index=True,
    )
    creator_twitch_id: Mapped[int] = mapped_column()
    description: Mapped[str] = mapped_column(
        String(POLL_DESCRIPTION_MAX_LENGTH)
    )
    start: Mapped[datetime] = mapped_column(DateTime)
    end: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[int] = mapped_column()
    options: Mapped[List["PollOption"]] = relationship()
    created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    modified: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"Poll(id={self.id!r},"
        + " target={self.target!r},"
        + " creator_twitch_id={self.creator_twitch_id!r},"
        + " description={self.description!r},"
        + " start={self.start!r},"
        + " end={self.end!r},"
        + " status={self.status!r},"
        + " created={self.created!r},"
        + " modified={self.modified!r})"


class PollOption(Base):
    __tablename__ = "poll_option"

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("poll.id"))
    number: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(String(POLL_DESCRIPTION_MAX_LENGTH))
    created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    modified: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"PollOption(id={self.id!r},"
        + " poll_id={self.poll_id!r},"
        + " number={self.number!r},"
        + " text={self.text!r},"
        + " created={self.created!r},"
        + " modified={self.modified!r})"


class PollSelection(Base):
    __tablename__ = "poll_selection"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column()
    poll_id: Mapped[int] = mapped_column()
    option_id: Mapped[int] = mapped_column()
    created: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    modified: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"PollOption(id={self.id!r},"
        + " poll_id={self.poll_id!r},"
        + " number={self.number!r},"
        + " text={self.text!r},"
        + " created={self.created!r},"
        + " modified={self.modified!r})"
