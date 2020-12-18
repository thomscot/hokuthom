import os
import smtplib
from app import app
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, request, flash, redirect, url_for, jsonify, make_response


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():

    return render_template('index.html', year=datetime.now().year)


@app.route('/contact', methods=['POST'])
def contact():

    name = request.form.get("name")
    mail = request.form.get("email")
    subj = request.form.get("subject")
    body = f"From: {mail} \n\n" + request.form.get("message")

    msg = MIMEMultipart()
    msg['Subject'] = f"From {name}: {subj}"

    body = MIMEText(body)
    msg.attach(body)

    credentials = {'user': os.environ.get("EMAIL"), 'pwd': os.environ.get("PASSWORD")}
    target_email = os.environ.get("EMAIL_TO")
    server = smtplib.SMTP("smtp.gmail.com", port=587)
    server.starttls()

    try:
        server.login(user=credentials['user'], password=credentials['pwd'])
        server.sendmail(from_addr=credentials['user'], to_addrs=target_email, msg=msg.as_string())
        message = "Thank you! I will get back to you as soon as possible!"
    except:
        message = "An error occurred :/ Please try later or contact me via a social media."

    return jsonify(message)
