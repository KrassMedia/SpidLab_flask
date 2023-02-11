from datetime import datetime

from flask_login import UserMixin

from sweater import db, manager


class AnalysisName(db.Model):
	analysis_id = db.Column(db.Integer, primary_key=True)
	analysis_name = db.Column(db.String(20), nullable=False)

	def __repr__(self):
		return 'AnalysisName %r' % self.analysis_id


class Doctors(db.Model):
	doctor_id = db.Column(db.Integer, primary_key=True)
	doctor_name = db.Column(db.String(20), nullable=False)

	def __repr__(self):
		return 'Doctors %r' % self.doctor_id


class Patient(db.Model):
	patient_id = db.Column(db.Integer, primary_key=True)
	patient_surname = db.Column(db.String(20), nullable=False)
	patient_name = db.Column(db.String(20), nullable=False)
	patient_patronymic = db.Column(db.String(20), nullable=True)
	patient_date_birth = db.Column(db.DateTime, nullable=True)

	def __repr__(self):
		return 'Patient %r' % self.patient_id


class MainData(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date_analysis = db.Column(db.DateTime, default=datetime(1970, 1, 1))
	analysis_id = db.Column(db.Integer, nullable=False)
	doctor_id = db.Column(db.String(20), nullable=False)
	patient_id = db.Column(db.Integer, nullable=False)
	analysis_result = db.Column(db.String(20), nullable=False)

	def __repr__(self):
		return 'MainData %r' % self.id


class User(db.Model, UserMixin):
	user_id = db.Column(db.Integer, primary_key=True)
	user_login = db.Column(db.String(128), nullable=False, unique=True)
	user_password = db.Column(db.String(256), nullable=False)
	user_admin = db.Column(db.Integer, default=0)
	user_date_create = db.Column(db.DateTime, default=datetime.now())

	def get_id(self):
		return self.user_id

	def get_admin_level(self):
		return self.user_admin

	def __repr__(self):
		return 'User %r' % self.user_id


@manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)
