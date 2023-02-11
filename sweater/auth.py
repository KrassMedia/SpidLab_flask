from flask import render_template, request, redirect, flash, url_for
from flask_login import login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from sweater import app, db
from sweater.models import User


@app.route('/login', methods=['POST', 'GET'])
def login_page():
	login = request.form.get('login')
	password = request.form.get('password')
	if request.method == 'POST':
		if login and password:
			user = User.query.filter_by(user_login=login).first()
			if user and check_password_hash(user.user_password, password):
				login_user(user, remember=True)

				next_page = request.args.get('next')
				return redirect(next_page or url_for('index'))
			else:
				flash('Логин или пароль введены не верно!')
		else:
			flash('Для входа в систему необходимо ввести логин и пароль')

	return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
	login = request.form.get('login')
	password = request.form.get('password')
	password2 = request.form.get('password2')

	if request.method == 'POST':
		if not all([login, password, password2]):
			flash('Требуется заполнение всех полей.')
		elif len(login) < 4:
			flash('Минимальная длинна логина должна быть не менее 4-х символов.')
		elif User.query.filter_by(user_login=login).first():
			flash('Выбранный Вами логин уже занят, введите другой логин.')
		elif password != password2:
			flash('Введенные пароли не совпадают.')
		elif len(password) < 6:
			flash('Минимальная длинна пароля должна быть не менее 6-ти символов.')
		else:
			hash_pwd = generate_password_hash(password)
			new_user = User(user_login=login, user_password=hash_pwd)
			db.session.add(new_user)
			db.session.commit()

			return redirect(url_for('login_page'))

	return render_template('register.html')


@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
	logout_user()
	return redirect(url_for('login_page'))


@app.after_request
def redirect_to_signin(response):
	if response.status_code == 401:
		return redirect(url_for('login_page') + '?next=' + request.url)

	return response
