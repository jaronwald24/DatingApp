from datetime import datetime
import dateutil.tz

from flask import Blueprint, render_template, request, abort,redirect, url_for, flash, current_app
import flask_login
import pathlib

from . import db
from . import model

from .helperFunctions import photo_filename

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
        
    current_year = datetime.now().year

    return render_template("main/profile.html", user=user, curUser=curUser, like_button=like_button, current_year=current_year)

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

@bp.route("/editProfile", methods=["GET"])
@flask_login.login_required
def editProfile():
    return render_template("main/editProfile.html", user=flask_login.current_user)

@bp.route("/editProfile", methods=["POST"])
@flask_login.login_required
def editProfilePost():
    curUser = flask_login.current_user
    
    dbUser = db.session.get(model.User, curUser.id)
    
    if not dbUser:
        abort(404, "User id {} doesn't exist.".format(curUser.id))
        
    dbUser.name = request.form.get("name") or curUser.name
    
    dbUser.profile.bio = request.form.get("bio") or dbUser.profile.bio
    dbUser.profile.birth_year = request.form.get("birth_year") or dbUser.profile.birth_year
    dbUser.profile.gender = request.form.get("gender") or dbUser.profile.gender
    dbUser.profile.genderPreference = request.form.get("genderPreference") or dbUser.profile.genderPreference
    dbUser.profile.age_minimum = int(request.form.get("age_minimum", dbUser.profile.age_minimum))
    dbUser.profile.age_maximum = int(request.form.get("age_maximum", dbUser.profile.age_maximum))

    # Handle uploaded photo
    uploaded_file = request.files['photo_id']
    if uploaded_file and uploaded_file.filename != '':

        content_type = uploaded_file.content_type
        if content_type == "image/png":
            file_extension = "png"
        elif content_type == "image/jpeg":
            file_extension = "jpg"
        else:
            flash("Unsupported file type. Only JPEG and PNG are supported.")
            return redirect(url_for("auth.signup"))
            
        new_photo = model.Photo(file_extension=file_extension)
        db.session.add(new_photo)

        old_photo = dbUser.profile.photo
        if old_photo is not None:
            path = photo_filename(old_photo)
            path.unlink(missing_ok=True)
            db.session.delete(old_photo)

        flask_login.current_user.profile.photo = new_photo
        new_path = photo_filename(new_photo)
        uploaded_file.save(new_path)
        
    db.session.commit()

    return redirect(url_for("main.profile", user_id=curUser.id))
    
    
@bp.route('/upload_photo', methods=['POST'])
@flask_login.login_required
def upload_photo():
    uploaded_file = request.files['photo']
    if uploaded_file.filename != '':
        content_type = uploaded_file.content_type
        if content_type == "image/png":
            file_extension = "png"
        elif content_type == "image/jpeg":
            file_extension = "jpg"
        else:
            abort(400, f"Unsupported file type {content_type}")
        
        photo = model.Photo(file_extension=file_extension)
        db.session.add(photo)
        
        old_photo = flask_login.current_user.profile.photo
        if old_photo is not None:
            path = photo_filename(old_photo)
            path.unlink(missing_ok=True)
            db.session.delete(old_photo)

        flask_login.current_user.profile.photo = photo
        db.session.commit()

        path = photo_filename(photo)
        uploaded_file.save(path)

        flash('Photo uploaded successfully!')
        return redirect(url_for('main.profile', user_id=flask_login.current_user.id))

    flash('No file selected')
    return redirect(request.url)
    
    
    
