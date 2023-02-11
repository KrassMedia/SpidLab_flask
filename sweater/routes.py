from flask import render_template
from flask_login import login_required

from sweater import app


@app.route('/home')
@app.route('/')
def index():
	return render_template('index.html')


@app.route('/profile')
@login_required
def profile():
	return render_template('profile.html')