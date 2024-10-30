import datetime
import dateutil.tz

from flask import Blueprint, render_template, request, abort,redirect, url_for, flash
import flask_login

from . import db
from . import model

bp = Blueprint("main", __name__)


@bp.route("/")
@flask_login.login_required
def index():
    return render_template("main/index.html", user=flask_login.current_user)


@bp.route("/profile/<int:user_id>")
@flask_login.login_required
def profile(user_id):
    curUser = flask_login.current_user
    user = db.session.get(model.User, user_id)
    
    if curUser.id == user.id:
        like_button = None
    elif user in curUser.liking:
        like_button = "unlike"
    else:
        like_button = "like"

    return render_template("main/profile.html", user=user, curUser=curUser, like_button=like_button)

@bp.route("/like/<int:user_id>", methods=["POST"])
@flask_login.login_required
def like(user_id):
    likee = db.session.get(model.User, user_id)
    if not likee:
        abort(404, "User id {} doesn't exist.".format(user_id))
    
    if flask_login.current_user == likee:
        abort(403, "You can't like yourself.")
    if likee in flask_login.current_user.liking:
        abort(403, "You have already liked this user.")
        
    flask_login.current_user.liking.append(likee)
    db.session.commit()
    flash("You're now liking {}.".format(likee.name))
    return redirect(url_for("main.profile", user_id=user_id))

@bp.route("/unlike/<int:user_id>", methods=["POST"])
@flask_login.login_required
def unlike(user_id):
    unlikee = db.session.get(model.User, user_id)
    if not unlikee:
        abort(404, "User id {} doesn't exist.".format(user_id))
    
    if flask_login.current_user == unlikee:
        abort(403, "You can't unlike yourself.")
    if unlikee not in flask_login.current_user.liking:
        abort(403, "You're not liking this user.")
    
    flask_login.current_user.liking.remove(unlikee)
    db.session.commit()
    flash("You've unliked {}.".format(unlikee.name))
    return redirect(url_for("main.profile", user_id=user_id))
