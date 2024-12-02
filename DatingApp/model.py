import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
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
    
class Restaurant(enum.Enum):
    mexican = 0
    italian = 1
    chinese = 2
    japanese = 3
    indian = 4
    thai = 5

class LikingAssociation(db.Model):
    liker_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    liked_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)

class BlockingAssociation(db.Model):
    blocker_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    blocked_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    
class Photo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    profile: Mapped["Profile"] = relationship(back_populates="photo")
    file_extension: Mapped[str] = mapped_column(String(8))

class User(flask_login.UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    username: Mapped[str] = mapped_column(String(64))
    password: Mapped[str] = mapped_column(String(256))
    profile: Mapped["Profile"] = relationship(back_populates="user")
    liking: Mapped[List["User"]] = relationship(
        secondary=LikingAssociation.__table__,
        primaryjoin=LikingAssociation.liker_id == id,
        secondaryjoin=LikingAssociation.liked_id == id,
        back_populates="likers",
    )
    
    likers: Mapped[List["User"]] = relationship(
        secondary=LikingAssociation.__table__,
        primaryjoin=LikingAssociation.liked_id == id,
        secondaryjoin=LikingAssociation.liker_id == id,
        back_populates="liking",
    )
    
    blocking: Mapped[List["User"]] = relationship(
        secondary=BlockingAssociation.__table__,
        primaryjoin=BlockingAssociation.blocker_id == id,
        secondaryjoin=BlockingAssociation.blocked_id == id,
        back_populates="blockers",
    )
    
    blockers: Mapped[List["User"]] = relationship(
        secondary=BlockingAssociation.__table__,
        primaryjoin=BlockingAssociation.blocked_id == id,
        secondaryjoin=BlockingAssociation.blocker_id == id,
        back_populates="blocking",
    )

    sent_proposals: Mapped[List["DateProposal"]] = relationship(
        back_populates="proposer", foreign_keys="DateProposal.proposer_id"
    )
    received_proposals: Mapped[List["DateProposal"]] = relationship(
        back_populates="recipient", foreign_keys="DateProposal.recipient_id"
    )
    
    sent_compliments: Mapped[List["Compliments"]] = relationship(
        back_populates="sender", foreign_keys="Compliments.sender_id"
    )
    
    received_compliments: Mapped[List["Compliments"]] = relationship(
        back_populates="recipient", foreign_keys="Compliments.recipient_id"
    )

class Profile(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)
    user: Mapped["User"] = relationship(
        back_populates="profile",
        single_parent=True,
    )
    fullname: Mapped[str] = mapped_column(String(128))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    instagram_username: Mapped[Optional[str]] = mapped_column(String(64))
    birth_year: Mapped[Optional[int]] = mapped_column(Integer)
    age_minimum: Mapped[Optional[int]] = mapped_column(Integer)
    age_maximum: Mapped[Optional[int]] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(16))
    genderPreference: Mapped[Optional[str]] = mapped_column(String(16))
    photo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("photo.id"))
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
    created_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    response_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    proposed_day: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    restaurant_type: Mapped[Optional[Restaurant]] = mapped_column(String(16))
    status: Mapped[ProposalStatus] = mapped_column(String(16))
    proposingMessage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    replyMessage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    

class Compliments(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    recipient_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    message: Mapped[str] = mapped_column(Text)
    created_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    
    sender: Mapped["User"] = relationship(
        foreign_keys=[sender_id], back_populates="sent_compliments"
    )
    
    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id], back_populates="received_compliments"
    )

