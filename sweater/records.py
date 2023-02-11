from datetime import datetime

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from sweater import app, db
from sweater.functions import get_main_data, clear_auto_past, get_patient_id, get_doctor_id
from sweater.models import Patient, Doctors, MainData, AnalysisName


@app.route('/record/<int:record>/del', methods=['POST', 'GET'])
@login_required
def record_delete(record):
	if not current_user.get_admin_level():
		flash('У вас недостаточно прав для совершения данной операции.')
		return redirect(url_for('records'))

	main_data = MainData.query.get_or_404(record)
	try:
		db.session.delete(main_data)
		db.session.commit()
		return redirect(url_for('records'))
	except:
		return 'При удалении записи произошла ошибка! (db.session.delete(main_data))'


@app.route('/record/<int:record>/update', methods=['POST', 'GET'])
@login_required
def record_update(record):
	if not current_user.get_admin_level():
		flash('У вас недостаточно прав для совершения данной операции.')
		return redirect(url_for('records'))

	analysis_name_list = AnalysisName.query.all()
	main_data = get_main_data('one', id=record)
	auto_past = clear_auto_past('update_record', main_data=main_data)
	if request.method == 'POST':
		# Fill auto past
		for key in auto_past.keys():
			if key == 'fio':
				auto_past[key] = request.form[key].title().strip()
			elif key == 'analysis_name' and request.form[key].isdigit():
				auto_past[key] = AnalysisName.query.get(int(request.form[key])).analysis_name
			else:
				auto_past[key] = request.form[key]

		fio = [x.strip() for x in auto_past['fio'].split(' ')]
		date_birth = datetime.strptime(auto_past['date_birth'], '%Y-%m-%d') if auto_past['date_birth'] else None
		date_analysis = datetime.strptime(auto_past['date_analysis'], '%Y-%m-%d') if auto_past[
																						'date_analysis'] else None
		# Check content
		error = []
		if len(fio) not in (2, 3):
			error.append('fio')
		if auto_past['analysis_name'] != 'Выберите исследование' and not auto_past['analysis_result']:
			error.append('analysis_result')
		if auto_past['analysis_result'] and auto_past['analysis_name'] == 'Выберите исследование':
			error.append('analysis_name')
		if error:
			return render_template('update-record.html', analysis_name_list=analysis_name_list, error=error,
								   auto_past=auto_past, id=record)

		if not get_patient_id(fio, date_birth):
			patient = Patient(
				patient_surname=fio[0].upper(),
				patient_name=fio[1].upper(),
				patient_patronymic=fio[2].upper() if len(fio) == 3 else None,
				patient_date_birth=date_birth
			)
			try:
				db.session.add(patient)
				db.session.commit()
			except:
				return 'При изменении записи произошла ошибка! (db.session.add(Patient))'

		if not get_doctor_id(auto_past['referred_doctor']):
			doctors = Doctors(doctor_name=auto_past['referred_doctor'].strip())
			try:
				db.session.add(doctors)
				db.session.commit()
			except:
				return 'При изменении записи произошла ошибка! (db.session.add(Doctors))'

		main_data = MainData.query.get(record)
		main_data.date_analysis = date_analysis
		main_data.analysis_id = auto_past['analysis_name'] if auto_past['analysis_name'].isdigit() \
			else AnalysisName.query.filter_by(analysis_name=auto_past['analysis_name']).first().analysis_id
		main_data.doctor_id = get_doctor_id(auto_past['referred_doctor']).doctor_id
		main_data.patient_id = get_patient_id(fio, date_birth).patient_id
		main_data.analysis_result = auto_past['analysis_result']

		try:
			db.session.commit()
		except:
			return 'При изменении записи произошла ошибка! (db.session.add(main_data))'

		main_data = get_main_data('one', id=record)
		auto_past = clear_auto_past('update_record', main_data=main_data)
		return render_template('update-record.html', analysis_name_list=analysis_name_list, error='success',
							   auto_past=auto_past, id=record)

	return render_template('update-record.html', analysis_name_list=analysis_name_list,	auto_past=auto_past, id=record)


@app.route('/records', methods=['POST', 'GET'])
@app.route('/records/<int:page>', methods=['POST', 'GET'])
@login_required
def records(page=1):
	posts_per_page = 20
	filter_list = []
	auto_past = clear_auto_past('records')
	analysis_name_list = AnalysisName.query.all()
	sort_method_list = {
		'По умолчанию': MainData.id.desc(),
		'По фамилии пациента': Patient.patient_surname,
		'По фамилии пациента (перевернуть)': Patient.patient_surname.desc(),
		'По дате рождения': Patient.patient_date_birth,
		'По дате рождения (перевернуть)': Patient.patient_date_birth.desc(),
		'По дате исследования': MainData.date_analysis,
		'По дате исследования (перевернуть)': MainData.date_analysis.desc(),
		'По врачу': Doctors.doctor_name,
		'По врачу (перевернуть)': Doctors.doctor_name.desc(),
		'По исследованию': AnalysisName.analysis_name,
		'По исследованию (перевернуть)': AnalysisName.analysis_name.desc(),
		'По результату': MainData.analysis_result,
		'По результату (перевернуть)': MainData.analysis_result.desc()
	}

	if request.method == 'POST':
		if request.form['submit_button'] == 'Отчистить фильтр':
			main_data = get_main_data('all', page=1, POSTS_PER_PAGE=posts_per_page)
			return render_template('records.html', main_data=main_data, auto_past=auto_past,
								   analysis_name_list=analysis_name_list, sort_method_list=sort_method_list)
		# Fill auto past
		for key in auto_past:
			if request.form[key]:
				if key == 'analysis_name':
					if request.form[key].isdigit():
						auto_past[key] = AnalysisName.query.get(int(request.form[key])).analysis_name
						filter_list.append(key)
					elif request.form[key] == 'Выберите исследование':
						auto_past[key] = ''
				elif key == 'sort_method':
					if request.form[key].isdigit():
						auto_past[key] = [k for k in sort_method_list][int(request.form[key])]
						filter_list.append(key)
					elif request.form[key] == 'Отсортировать по...':
						auto_past[key] = ''
					else:
						auto_past[key] = request.form[key]
						filter_list.append(key)
				else:
					auto_past[key] = request.form[key]
					filter_list.append(key)

		# Apply filter
		main_data = get_main_data('filter', page=1, POSTS_PER_PAGE=posts_per_page, surname=auto_past['surname'],
								  name=auto_past['name'],
								  patronymic=auto_past['patronymic'],
								  date_birth=auto_past['date_birth'], date_analysis=auto_past['date_analysis'],
								  referred_doctor=auto_past['referred_doctor'],
								  analysis_name=auto_past['analysis_name'],
								  analysis_result=auto_past['analysis_result'],
								  sort_method=sort_method_list[auto_past['sort_method']] if auto_past[
									  'sort_method'] else sort_method_list['По умолчанию'])

		return render_template('records.html', main_data=main_data, auto_past=auto_past,
							   analysis_name_list=analysis_name_list, filter=filter_list,
							   sort_method_list=sort_method_list)

	main_data = get_main_data('all', page=page, POSTS_PER_PAGE=posts_per_page)
	return render_template('records.html', main_data=main_data, auto_past=auto_past,
						   analysis_name_list=analysis_name_list, sort_method_list=sort_method_list)


@app.route('/create-record', methods=['POST', 'GET'])
@login_required
def create_record():
	if not current_user.get_admin_level():
		flash('У вас недостаточно прав для совершения данной операции.')
		return redirect(url_for('records'))

	auto_past = clear_auto_past('create_record')
	analysis_name_list = AnalysisName.query.all()
	if request.method == 'POST':
		if request.form['submit_button'] == 'Отчистить форму':
			return render_template('create-record.html', analysis_name_list=analysis_name_list, error=(),
								   auto_past=auto_past)
		# Fill auto past
		for key in auto_past.keys():
			if key == 'fio':
				auto_past[key] = request.form[key].title()
			elif key in ('analysis_name', 'analysis_name1', 'analysis_name2', 'analysis_name3') and request.form[
				key].isdigit():
				auto_past[key] = AnalysisName.query.get(int(request.form[key])).analysis_name
			else:
				auto_past[key] = request.form[key]

		fio = [x.strip() for x in auto_past['fio'].split(' ')]
		date_birth = datetime.strptime(auto_past['date_birth'], '%Y-%m-%d') if auto_past['date_birth'] else None
		date_analysis = datetime.strptime(auto_past['date_analysis'], '%Y-%m-%d') if auto_past[
			'date_analysis'] else None

		# Check content
		error = []
		if len(fio) not in (2, 3): error.append('fio')
		if auto_past['analysis_name'] != 'Выберите исследование' and not auto_past['analysis_result']:
			error.append('analysis_result')
		if auto_past['analysis_name1'] != 'Выберите исследование' and not auto_past['analysis_result1']:
			error.append('analysis_result1')
		if auto_past['analysis_name2'] != 'Выберите исследование' and not auto_past['analysis_result2']:
			error.append('analysis_result2')
		if auto_past['analysis_name3'] != 'Выберите исследование' and not auto_past['analysis_result3']:
			error.append('analysis_result3')
		if auto_past['analysis_result'] and auto_past['analysis_name'] == 'Выберите исследование':
			error.append('analysis_name')
		if auto_past['analysis_result1'] and auto_past['analysis_name1'] == 'Выберите исследование':
			error.append('analysis_name1')
		if auto_past['analysis_result2'] and auto_past['analysis_name2'] == 'Выберите исследование':
			error.append('analysis_name2')
		if auto_past['analysis_result3'] and auto_past['analysis_name3'] == 'Выберите исследование':
			error.append('analysis_name3')
		if error:
			return render_template('create-record.html', analysis_name_list=analysis_name_list, error=error,
										 auto_past=auto_past)

		if not get_patient_id(fio, date_birth):
			patient = Patient(
				patient_surname=fio[0].upper(),
				patient_name=fio[1].upper(),
				patient_patronymic=fio[2].upper() if len(fio) == 3 else None,
				patient_date_birth=date_birth
			)
			try:
				db.session.add(patient)
				db.session.commit()
			except:
				return 'При добавлении записи произошла ошибка! (db.session.add(Patient))'

		if not get_doctor_id(auto_past['referred_doctor']):
			doctors = Doctors(doctor_name=auto_past['referred_doctor'].strip())
			try:
				db.session.add(doctors)
				db.session.commit()
			except:
				return 'При добавлении записи произошла ошибка! (db.session.add(Doctors))'

		main_data = []
		if auto_past['analysis_result']:
			main_data.append(MainData(
				date_analysis=date_analysis,
				analysis_id=auto_past['analysis_name'] if auto_past['analysis_name'].isdigit()
				else AnalysisName.query.filter_by(analysis_name=auto_past['analysis_name']).first().analysis_id,
				doctor_id=get_doctor_id(auto_past['referred_doctor']).doctor_id,
				patient_id=get_patient_id(fio, date_birth).patient_id,
				analysis_result=auto_past['analysis_result']
			))
		if auto_past['analysis_result1']:
			main_data.append(MainData(
				date_analysis=date_analysis,
				analysis_id=auto_past['analysis_name1'] if auto_past['analysis_name1'].isdigit()
				else AnalysisName.query.filter_by(analysis_name=auto_past['analysis_name1']).first().analysis_id,
				doctor_id=get_doctor_id(auto_past['referred_doctor']).doctor_id,
				patient_id=get_patient_id(fio, date_birth).patient_id,
				analysis_result=auto_past['analysis_result1']
			))
		if auto_past['analysis_result2']:
			main_data.append(MainData(
				date_analysis=date_analysis,
				analysis_id=auto_past['analysis_name2'] if auto_past['analysis_name2'].isdigit()
				else AnalysisName.query.filter_by(analysis_name=auto_past['analysis_name2']).first().analysis_id,
				doctor_id=get_doctor_id(auto_past['referred_doctor']).doctor_id,
				patient_id=get_patient_id(fio, date_birth).patient_id,
				analysis_result=auto_past['analysis_result2']
			))
		if auto_past['analysis_result3']:
			main_data.append(MainData(
				date_analysis=date_analysis,
				analysis_id=auto_past['analysis_name3'] if auto_past['analysis_name3'].isdigit()
				else AnalysisName.query.filter_by(analysis_name=auto_past['analysis_name3']).first().analysis_id,
				doctor_id=get_doctor_id(auto_past['referred_doctor']).doctor_id,
				patient_id=get_patient_id(fio, date_birth).patient_id,
				analysis_result=auto_past['analysis_result3']
			))
		try:
			for data in main_data:
				db.session.add(data)
			db.session.commit()
		except:
			return 'При добавлении записи произошла ошибка! (db.session.add(main_data))'

		auto_past = clear_auto_past('create_record')
		return render_template('create-record.html', analysis_name_list=analysis_name_list, error='success',
								auto_past=auto_past)

	return render_template('create-record.html', analysis_name_list=analysis_name_list, error=(), auto_past=auto_past)
