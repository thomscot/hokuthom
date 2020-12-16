from app import app
from datetime import datetime
from flask import render_template

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.route('/')
@app.route('/index')
def index():
     return render_template('index.html', year=datetime.now().year)
