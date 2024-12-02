from datetime import datetime, timedelta
import random
import dateutil.tz

from flask import Blueprint, render_template, request, abort,redirect, url_for, flash, current_app
import flask_login
import pathlib
from sqlalchemy.orm import joinedload

from . import db
from . import model
from .model import DateProposal

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
        model.Profile.birth_year.between(age_min, age_max),
        model.User.id.notin_(blocked_users),
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
        
        
    # Received proposals are filtered out after 10 days, keeping the user's profile page clean
    # Note this gets all received proposals, and we filter by proposed/rejected/ignored in the template
    received_proposals = (
        DateProposal.query.filter(
            DateProposal.recipient_id == user.id,
            DateProposal.created_time >= datetime.now() - timedelta(days=10)
        ).all()
        if curUser.id == user.id else []
    )
    sent_proposals = DateProposal.query.filter_by(proposer_id=curUser.id).all()

    set_dates = DateProposal.query.filter(
        db.or_(
            DateProposal.recipient_id == user.id,
            DateProposal.proposer_id == user.id
        ),
        DateProposal.status == model.ProposalStatus.accepted.value
    ).all()

    current_year = datetime.now().year

    return render_template("main/profile.html", user=user, curUser=curUser, like_button=like_button, block_button=block_button,
                           current_year=current_year, received_proposals=received_proposals,
                           sent_proposals=sent_proposals, set_dates=set_dates)

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
    dbUser.profile.instagram_username = request.form.get("ig") or dbUser.instagram_username
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
        
    return render_template("main/index.html", user=curUser, searchUsers=users, defaultUsers = defaultUsers, current_year=current_year)

@bp.route('/getRandom', methods=['GET'])
@flask_login.login_required
def getRandom():
    curUser = flask_login.current_user

    gender = request.args.get("gender", '').strip()
    gender_pref = request.args.get("genderPreference", '').strip()
    users = []

    if gender or gender_pref:
        query = db.session.query(model.User).join(model.Profile).options(
            joinedload(model.User.profile)
        ).filter(model.User.id != curUser.id)  # Exclude the current user

        if gender:
            query = query.filter(model.Profile.gender == gender)
        if gender_pref:
            query = query.filter(model.Profile.genderPreference == gender_pref)

        blocked_users = [blocked_user.id for blocked_user in curUser.blocking]
        query = query.filter(model.User.id.notin_(blocked_users))        
        
        users = query.all()

    current_year = datetime.now().year

    gender_pref = curUser.profile.genderPreference
    blocked_users = [blocked_user.id for blocked_user in curUser.blocking]


    defaultUsers = db.session.query(model.User).join(model.Profile).filter(
        model.User.id != curUser.id,
        model.User.id.notin_(blocked_users),
        model.Profile.gender == gender_pref,
        model.Profile.genderPreference == curUser.profile.gender
    ).all()
    
    if defaultUsers:
        random_user = random.choice(defaultUsers)
        return redirect(url_for("main.profile", user_id=random_user.id))
        
    return render_template("main/index.html", user=curUser, searchUsers=users, defaultUsers = defaultUsers, current_year=current_year)





@bp.route('/propose_date/<int:recipient_id>', methods=['POST'])
@flask_login.login_required
def propose_date(recipient_id):
    curUser = flask_login.current_user
    recipient = db.session.get(model.User, recipient_id)

    if curUser.id != recipient.id:
        proposed_day_str = request.form.get("proposed_day")
        try:
            proposed_day = datetime.strptime(proposed_day_str, "%Y-%m-%d")
            if proposed_day < datetime.now():
                flash("Please select a future date.")
                return redirect(url_for("main.profile", user_id=recipient_id))
            

            proposals_on_day = DateProposal.query.filter_by(
                proposed_day=proposed_day, status=model.ProposalStatus.proposed.value
            ).count()

            dates_on_day = DateProposal.query.filter_by(
                proposed_day=proposed_day, status=model.ProposalStatus.accepted.value
            ).count()

            max_tables = 10  # Assuming 10 tables per night

            if proposals_on_day + dates_on_day >= max_tables:
                flash("No available tables for the selected night.")
                return redirect(url_for("main.profile", user_id=recipient_id))

            # Create the date proposal
            optional_message = request.form.get("optional_message")
            restaurant = request.form.get("restaurant")
            if curUser in recipient.blocking:
                setStatus = model.ProposalStatus.ignored.value
            else:
                setStatus = model.ProposalStatus.proposed.value
            proposal = DateProposal(
                proposer_id=curUser.id,
                recipient_id=recipient.id,
                created_time=datetime.now(),
                proposed_day=proposed_day,
                restaurant_type=restaurant,
                status=setStatus,  
                proposingMessage=optional_message
            )
            db.session.add(proposal)
            db.session.commit()

        except ValueError:
            flash("Invalid date format.")
        
        return redirect(url_for("main.profile", user_id=recipient_id))


@bp.route('/respond_proposal/<int:proposal_id>', methods=['POST'])
@flask_login.login_required
def respond_proposal(proposal_id):
    curUser = flask_login.current_user
    proposal = DateProposal.query.get_or_404(proposal_id)
    
    # Ensure only the recipient can respond
    if proposal.recipient_id != curUser.id:
        flash("You do not have permission to respond to this proposal.")
        return redirect(url_for('main.index'))

    action = request.form.get('action')
    
    if action == 'accept':
        proposal.status = model.ProposalStatus.accepted.value
        proposal.response_time = datetime.now()
    elif action == 'reject':
        proposal.status = model.ProposalStatus.rejected.value
        proposal.response_time = datetime.now()
    elif action == 'ignore':
        proposal.status = model.ProposalStatus.ignored.value
        proposal.response_time = datetime.now()
    elif action == 'reschedule':
        proposal.status = model.ProposalStatus.reschedule.value
        proposal.response_time = datetime.now()
    else:
        flash("Invalid action.")
        return redirect(url_for('main.profile', user_id=curUser.id))
    
    message = request.form.get('optional_message')
    proposal.replyMessage = message
    
    db.session.commit()
    return redirect(url_for('main.profile', user_id=curUser.id))

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