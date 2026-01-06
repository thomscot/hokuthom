import os
import smtplib
import time

from app import app
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, request, redirect, jsonify
from smtplib import SMTPAuthenticationError, SMTPException



@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


@app.before_request
def before_request():
    """
    Redirect to https if the environment is not dev
    """
    if not request.is_secure and app.env != "development":
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():

    return render_template('index.html', year=datetime.now().year)


@app.route('/en', methods=['GET'])
def index_en():
    # TODO: have a single index page, and just fill the text with variables that have different values
    # eg. base html ... {{ text }} ... and text is sent from backend in english or italian depending on endpoint
    return render_template('index_en.html', year=datetime.now().year)


import logging
from smtplib import SMTPAuthenticationError, SMTPException

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get("name", "").strip()
    mail = request.form.get("email", "").strip()
    subj = request.form.get("subject", "").strip()
    message_text = request.form.get("message", "").strip()

    # IMPORTANT: this can be missing -> don't use ['url_from']
    url_from = request.form.get("url_from", "")
    is_en = url_from.endswith("/en") or url_from.endswith("/en/")

    # --- Anti-spam: honeypot ---
    # If this hidden field is filled, it's very likely a bot.
    if request.form.get("company", "").strip():
        return jsonify("Thank you!"), 200

    # --- Anti-spam: time trap ---
    # Bots often submit instantly. Humans usually take a few seconds.
    ts = request.form.get("ts", "")
    try:
        ts = int(ts) / 1000.0
    except Exception:
        ts = None

    # If missing/invalid timestamp OR submitted too fast (< 3 seconds), treat as bot
    if not ts or (time.time() - ts) < 3:
        return jsonify("Thank you!"), 200

    # Basic validation (optional but helpful)
    if not mail or not message_text:
        return jsonify("Missing required fields."), 400

    body_text = f"From: {mail}\nName: {name}\n\n{message_text}"

    msg = MIMEMultipart()
    msg["Subject"] = f"From {name}: {subj}" if name else f"Contact form: {subj}"
    msg["From"] = os.environ.get("EMAIL")  # sender authenticated
    msg["To"] = os.environ.get("EMAIL_TO", "")

    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    smtp_user = os.environ.get("EMAIL")
    smtp_pwd = os.environ.get("PASSWORD")
    target_email = os.environ.get("EMAIL_TO")

    # Fail fast if env vars missing (common on Heroku)
    if not smtp_user or not smtp_pwd or not target_email:
        app.logger.error("Missing EMAIL/PASSWORD/EMAIL_TO env vars")
        return jsonify("Server configuration error."), 500

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pwd)
            server.sendmail(smtp_user, [target_email], msg.as_string())

        ok_msg = "Thank you! I will get back to you as soon as possible!" if is_en \
                 else "Grazie! Cercherò di risponderti il prima possibile!"
        return jsonify(ok_msg)

    except SMTPAuthenticationError:
        app.logger.exception("SMTP auth failed (Gmail). Likely need an App Password.")
        err_msg = "Email auth error. Please contact me via social media." if is_en \
                  else "Errore di autenticazione email. Contattami via social."
        return jsonify(err_msg), 500

    except SMTPException:
        app.logger.exception("SMTP error while sending email")
        err_msg = "An error occurred :/ Please try later or contact me via social media." if is_en \
                  else "Si è verificato un errore :/ Riprova più tardi o contattami tramite i social."
        return jsonify(err_msg), 500

    except Exception:
        app.logger.exception("Unexpected error in /contact")
        err_msg = "An error occurred :/ Please try later or contact me via social media." if is_en \
                  else "Si è verificato un errore :/ Riprova più tardi o contattami tramite i social."
        return jsonify(err_msg), 500