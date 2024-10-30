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
    query = db.select(model.Post).where(model.Post.response_to == None).order_by(model.Post.timestamp.desc()).limit(10)
    posts = db.session.execute(query).scalars().all()
    
    followers = db.aliased(model.User)
    following_query = (
        db.select(model.Post)
        .join(model.User)
        .join(followers, model.User.followers)
        .where(followers.id == flask_login.current_user.id)
        .where(model.Post.response_to == None)
        .order_by(model.Post.timestamp.desc())
        .limit(10)
    )
    
    followingPost = db.session.execute(following_query).scalars().all()
    
    
    return render_template("main/index.html", latest_posts=posts, following_posts=followingPost)


@bp.route("/profile/<int:user_id>")
@flask_login.login_required
def profile(user_id):
    curUser = flask_login.current_user
    user = db.session.get(model.User, user_id)
    
    if curUser.id == user.id:
        follow_button = None
    elif user in curUser.following:
        follow_button = "unfollow"
    else:
        follow_button = "follow"

    return render_template("main/profile.html", user=user, posts=posts, follow_button=follow_button)


@bp.route("/post/<int:post_id>")
@flask_login.login_required
def post(post_id):
    post = db.session.get(model.Post, post_id)
    query = db.select(model.Post).where(model.Post.response_to_id == post_id).order_by(model.Post.timestamp.desc())
    responses = db.session.execute(query).scalars().all()
    if not post:
        abort(404, "Post id {} doesn't exist.".format(post_id))
    if post.response_to != None:
        abort(403, "Post id {} is a response.".format(post_id))
        
    return render_template("main/post.html", post=post, responses=responses)


@bp.route("/new_post")
@flask_login.login_required
def new_post_form():
    return render_template("main/new_post.html")


@bp.route("/new_post", methods=["POST"])
@flask_login.login_required
def new_post():
    text = request.form.get("text")
    user = flask_login.current_user
    response = request.form.get("response_to")
    
    if response:
        originalPost = db.session.get(model.Post, response)
        if not originalPost:
            abort(404, "Post id {} doesn't exist.".format(response))
        post = model.Post(user=user, text=text, timestamp=datetime.datetime.now(dateutil.tz.tzlocal()), response_to=originalPost)
    else:
        post = model.Post(user=user, text=text, timestamp=datetime.datetime.now(dateutil.tz.tzlocal()), response_to=None)
        
    db.session.add(post)
    db.session.commit()
    
    if response:
        return redirect(url_for("main.post", post_id=response))
    else:
        return redirect(url_for("main.post", post_id=post.id))
    
    
@bp.route("/follow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def follow(user_id):
    followee = db.session.get(model.User, user_id)
    if not followee:
        abort(404, "User id {} doesn't exist.".format(user_id))
    
    if flask_login.current_user == followee:
        abort(403, "You can't follow yourself.")
    if followee in flask_login.current_user.following:
        abort(403, "You're already following this user.")
        
    flask_login.current_user.following.append(followee)
    db.session.commit()
    flash("You're now following {}.".format(followee.name))
    return redirect(url_for("main.profile", user_id=user_id))

@bp.route("/unfollow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def unfollow(user_id):
    unfollowee = db.session.get(model.User, user_id)
    if not unfollowee:
        abort(404, "User id {} doesn't exist.".format(user_id))
    
    if flask_login.current_user == unfollowee:
        abort(403, "You can't unfollow yourself.")
    if unfollowee not in flask_login.current_user.following:
        abort(403, "You're not following this user.")
    
    flask_login.current_user.following.remove(unfollowee)
    db.session.commit()
    flash("You've unfollowed {}.".format(unfollowee.name))
    return redirect(url_for("main.profile", user_id=user_id))
