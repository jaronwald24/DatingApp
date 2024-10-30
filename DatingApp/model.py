import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import flask_login

from . import db

class FollowingAssociation(db.Model):
    follower_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    followed_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)

class User(flask_login.UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    password: Mapped[str] = mapped_column(String(256))
    posts: Mapped[List["Post"]] = relationship(back_populates="user")
    
    following: Mapped[List["User"]] = relationship(
    secondary=FollowingAssociation.__table__,
    primaryjoin=FollowingAssociation.follower_id == id,
    secondaryjoin=FollowingAssociation.followed_id == id,
    back_populates="followers",
    )
    
    followers: Mapped[List["User"]] = relationship(
        secondary=FollowingAssociation.__table__,
        primaryjoin=FollowingAssociation.followed_id == id,
        secondaryjoin=FollowingAssociation.follower_id == id,
        back_populates="following",
    )


class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="posts")
    text: Mapped[str] = mapped_column(String(512))
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    response_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("post.id"))
    response_to: Mapped["Post"] = relationship(
        back_populates="responses", remote_side=[id]
    )
    responses: Mapped[List["Post"]] = relationship(
        back_populates="response_to", remote_side=[response_to_id]
    )