from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import flask_login

import pathlib
from .helperFunctions import photo_filename
from . import db
from . import model

bp = Blueprint("auth", __name__)


@bp.route("/signup")
def signup():
    return render_template("auth/signup.html")


@bp.route("/signup", methods=["POST"])
def signup_post():
    
    #user table
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    # Check that passwords are equal
    if password != request.form.get("password_repeat"):
        flash("Sorry, passwords are different")
        return redirect(url_for("auth.signup"))
    # Check if the email is already at the database
    
    query = db.select(model.User).where(model.User.email == email)
    user = db.session.execute(query).scalar_one_or_none()
    if user:
        flash("Sorry, the email you provided is already registered")
        return redirect(url_for("auth.signup"))
    password_hash = generate_password_hash(password)
    new_user = model.User(email=email, name=username, password=password_hash)
    db.session.add(new_user)
    db.session.commit()
    
    # profile table
    bio = request.form.get("bio")
    birth_year = int(request.form.get("birth_year"))
    gender = request.form.get("gender")
    genderPreference = request.form.get("genderPreference")
    ageMinimum = int(request.form.get("age_minimum"))
    ageMaximum = int(request.form.get("age_maximum"))


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
        db.session.commit()

        filename = f"photo-{new_photo.id}.{file_extension}"
        file_path = pathlib.Path(current_app.root_path) / "static" / "photos" / filename
        uploaded_file.save(file_path)
            
    new_profile = model.Profile(
        user_id=new_user.id,
        bio=bio,
        birth_year=birth_year,
        gender=gender,
        genderPreference=genderPreference,
        age_minimum=ageMinimum,
        age_maximum=ageMaximum,
        photo_id=new_photo.id if uploaded_file else None
    )
    
    db.session.add(new_profile)
    db.session.commit()
    
    flash("You've successfully signed up!")
    return redirect(url_for("main.index"))

@bp.route("/login")
def login():
    return render_template("auth/login.html")



@bp.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")
    
    query = db.select(model.User).where(model.User.email == email)
    user = db.session.execute(query).scalar_one_or_none()
    
    if user and check_password_hash(user.password, password):
        flask_login.login_user(user)
        return redirect(url_for("main.index"))
    else:
        flash("Sorry, the email or password is incorrect")
        return redirect(url_for("auth.login"))

@bp.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for("auth.login"))
