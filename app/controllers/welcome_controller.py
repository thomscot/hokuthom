"""
Main controller handling log-in and landing page.
"""

import flask_login
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from bluebear.script import constants
from bluebear.app_pkg.forms import LoginForm
from bluebear.app_pkg.models.user_model import User


welcome_controller = Blueprint('welcome_controller', __name__)


@welcome_controller.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user log-in: redirect to landing page if log in is successful or user is
    already logged-in. Otherwise returns the log in page.

    return: login or landing html page.
    """

    form = LoginForm()

    if flask_login.current_user.is_authenticated:
        return redirect(url_for('welcome_controller.index'))

    if request.method == 'POST' and form.validate_on_submit():

        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            error = 'Invalid Credentials!'
            return render_template('login.html', error=error, form=form)

        # add again remember me checkbox to front end?
        flask_login.login_user(user, remember=form.remember_me.data)
        session['logged_in'] = True
        return redirect(url_for('welcome_controller.index'))

    return render_template('login.html', title='Log In', form=form)


@welcome_controller.route("/logout", methods=['POST'])
def logout():
    """
    Logs out user.
    :return: index()
    """
    flask_login.logout_user()
    return index()


@welcome_controller.route("/")
@flask_login.login_required
def index():
    """
    :return: landing page if user is authenticated, log-in page otherwise.
    """
    if not flask_login.current_user.is_authenticated:
        return render_template("login.html")

    return render_template("index.html", accounts=constants.ACCOUNTS)
