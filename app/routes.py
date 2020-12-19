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

    url_from = request.form['url_from']

    try:
        server.login(user=credentials['user'], password=credentials['pwd'])
        server.sendmail(from_addr=credentials['user'], to_addrs=target_email, msg=msg.as_string())

        # return message in ita or eng depending on the url (first simple fix)
        if url_from.endswith("en/"):
            message = "Thank you! I will get back to you as soon as possible!"
        else:
            message = "Grazie! Cercherò di risponderti il prima possibile!"

    except:
        if url_from.endswith("en/"):
            message = "An error occurred :/ Please try later or contact me via a social media."
        else:
            message = "Si è verificato un errore :/ Per favore riprova più tardi o contattami tramite i social media."

    return jsonify(message)
