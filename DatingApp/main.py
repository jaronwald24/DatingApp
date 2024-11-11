from datetime import datetime
import dateutil.tz

from flask import Blueprint, render_template, request, abort,redirect, url_for, flash, current_app
import flask_login
import pathlib
from sqlalchemy.orm import joinedload

from . import db
from . import model

from utilities.helperFunctions import photo_filename

bp = Blueprint("main", __name__)


@bp.route("/")
@flask_login.login_required
def index():
    curUser = flask_login.current_user
    current_year = datetime.now().year
    age_min = current_year - curUser.profile.age_maximum
    age_max = current_year - curUser.profile.age_minimum
    gender_pref = curUser.profile.genderPreference
    
    blocked_users = [blocked_user.id for blocked_user in curUser.blocking]     
    
    defaultUsers = db.session.query(model.User).join(model.Profile).filter(
        model.User.id != curUser.id,
        model.User.id.notin_(blocked_users),
        model.Profile.birth_year.between(age_min, age_max),
        model.Profile.gender == gender_pref,
        model.Profile.genderPreference == curUser.profile.gender
    ).limit(10).all()




    return render_template("main/index.html", user=curUser, defaultUsers = defaultUsers, current_year=current_year)


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
    
    if curUser.id == user.id:
        block_button = None
    elif user in curUser.blocking:
        block_button = "unblock"
    else:
        block_button = "block"
        
        
        
    current_year = datetime.now().year

    return render_template("main/profile.html", user=user, curUser=curUser, like_button=like_button, current_year=current_year, block_button=block_button)

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
    flash("You're now liking {}.".format(likee.username))
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
    flash("You've unliked {}.".format(unlikee.username))
    return redirect(url_for("main.profile", user_id=user_id))

@bp.route("/block/<int:user_id>", methods=["POST"])
@flask_login.login_required
def block(user_id):
    blockee = db.session.get(model.User, user_id)
    if not blockee:
        abort(404, "User id {} doesn't exist.".format(user_id))
    
    if flask_login.current_user == blockee:
        abort(403, "You can't block yourself.")
    if blockee in flask_login.current_user.blocking:
        abort(403, "You have already blocked this user.")
        
    flask_login.current_user.blocking.append(blockee)
    
    if blockee in flask_login.current_user.liking:
        flask_login.current_user.liking.remove(blockee)
    
    db.session.commit()
    flash("You're now blocking {}.".format(blockee.username))
    return redirect(url_for("main.profile", user_id=user_id))

@bp.route("/unblock/<int:user_id>", methods=["POST"])
@flask_login.login_required
def unblock(user_id):
    unblockee = db.session.get(model.User, user_id)
    if not unblockee:
        abort(404, "User id {} doesn't exist.".format(user_id))
    
    if flask_login.current_user == unblockee:
        abort(403, "You can't unblock yourself.")
    if unblockee not in flask_login.current_user.blocking:
        abort(403, "You're not blocking this user.")
    
    flask_login.current_user.blocking.remove(unblockee)
    db.session.commit()
    flash("You've unblocked {}.".format(unblockee.username))
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
        
    dbUser.profile.fullname = request.form.get("name") or dbUser.profile.fullname

    dbUser.profile.bio = request.form.get("bio")
    print('bio', request.form.get("bio"))
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
    
@bp.route('/search', methods=['GET'])
@flask_login.login_required
def search():
    curUser = flask_login.current_user
    nameQuery = request.args.get("name", '').strip()
    age_minimum = request.args.get("age_minimum", type=int)
    age_maximum = request.args.get("age_maximum", type=int)
    gender = request.args.get("gender", '').strip()
    gender_pref = request.args.get("genderPreference", '').strip()
    users = []

    if nameQuery or age_minimum or age_maximum or gender or gender_pref:
        query = db.session.query(model.User).join(model.Profile).options(
            joinedload(model.User.profile)
        ).filter(model.User.id != curUser.id)  # Exclude the current user

        if nameQuery:
            query = query.filter(
                db.or_(
                    model.Profile.fullname.ilike(f"%{nameQuery}%"),
                    model.User.username.ilike(f"%{nameQuery}%")
                )
            )
        if age_minimum:
            query = query.filter(model.Profile.birth_year <= datetime.now().year - age_minimum)
        if age_maximum:
            query = query.filter(model.Profile.birth_year >= datetime.now().year - age_maximum)
        if gender:
            query = query.filter(model.Profile.gender == gender)
        if gender_pref:
            query = query.filter(model.Profile.genderPreference == gender_pref)
            
        blocked_users = [blocked_user.id for blocked_user in curUser.blocking]
        query = query.filter(model.User.id.notin_(blocked_users))        
        
        users = query.all()

    current_year = datetime.now().year

    age_min = current_year - curUser.profile.age_maximum
    age_max = current_year - curUser.profile.age_minimum
    gender_pref = curUser.profile.genderPreference
    blocked_users = [blocked_user.id for blocked_user in curUser.blocking]
    
    defaultUsers = db.session.query(model.User).join(model.Profile).filter(
        model.User.id != curUser.id,
        model.User.id.notin_(blocked_users),
        model.Profile.birth_year.between(age_min, age_max),
        model.Profile.gender == gender_pref,
        model.Profile.genderPreference == curUser.profile.gender
    ).limit(10).all()
        
    defaultUsers = [user for user in defaultUsers if user not in curUser.blocking]
    
    return render_template("main/index.html", user=curUser, searchUsers=users, defaultUsers = defaultUsers, current_year=current_year)