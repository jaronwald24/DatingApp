import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import flask_login
import enum

from . import db

class ProposalStatus(enum.Enum):
    proposed = 0
    accepted = 1
    rejected = 2
    ignored = 3
    reschedule = 4

class LikingAssociation(db.Model):
    liker_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    liked_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)

class Photo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    profile: Mapped["Profile"] = relationship(back_populates="photo")
    file_extension: Mapped[str] = mapped_column(String(8))

class User(flask_login.UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    password: Mapped[str] = mapped_column(String(256))
    
    liking: Mapped[List["User"]] = relationship(
        secondary=LikingAssociation.__table__,
        primaryjoin=LikingAssociation.liker_id == id,
        secondaryjoin=LikingAssociation.liked_id == id,
        back_populates="likers",
    )
    
    likers: Mapped[List["User"]] = relationship(
        secondary=LikingAssociation.__table__,
        primaryjoin=LikingAssociation.liked_id == id,
        secondaryjoin=LikingAssociation.liker_ud == id,
        back_populates="liking",
    )

    sent_proposals: Mapped[List["DateProposal"]] = relationship(
        back_populates="proposer", foreign_keys="DateProposal.proposer_id"
    )
    received_proposals: Mapped[List["DateProposal"]] = relationship(
        back_populates="recipient", foreign_keys="DateProposal.recipient_id"
    )

class Profile(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)
    bio: Mapped[Optional[str]] = mapped_column(String(256))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    ageMiminum: Mapped[Optional[int]] = mapped_column(Integer)
    ageMaximum: Mapped[Optional[int]] = mapped_column(Integer)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photo.id"))
    photo: Mapped[Optional["Photo"]] = relationship(back_populates="profile")


class DateProposal(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    proposer_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    proposer: Mapped["User"] = relationship(
        foreign_keys=[proposer_id], back_populates="sent_proposals"
    )
    recipient_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id], back_populates="received_proposals"
    )
    time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[ProposalStatus] = mapped_column(String(16))