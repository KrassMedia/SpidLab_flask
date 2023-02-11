from datetime import datetime

from sweater.models import Patient, Doctors, MainData, AnalysisName


def get_patient_id(fio, date_birth):
	return Patient.query.filter_by(patient_surname=fio[0].upper(), patient_name=fio[1].upper(),
								   patient_patronymic=fio[2].upper() if len(fio) == 3 else None,
								   patient_date_birth=date_birth).first()


def get_doctor_id(referred_doctor):
	return Doctors.query.filter_by(doctor_name=referred_doctor).first()


def get_main_data(type_request, **kwargs):
	match type_request:
		case 'one':
			return MainData.query.filter_by(id=kwargs['id']) \
				.join(Patient, MainData.patient_id == Patient.patient_id) \
				.join(AnalysisName, MainData.analysis_id == AnalysisName.analysis_id) \
				.join(Doctors, MainData.doctor_id == Doctors.doctor_id) \
				.add_columns(MainData.date_analysis, Patient.patient_name, Patient.patient_surname,
							 Patient.patient_patronymic, Patient.patient_date_birth, MainData.analysis_result,
							 AnalysisName.analysis_name, Doctors.doctor_name, MainData.id)
		case 'all':
			return MainData.query \
				.order_by(MainData.id.desc()) \
				.join(Patient, MainData.patient_id == Patient.patient_id) \
				.join(AnalysisName, MainData.analysis_id == AnalysisName.analysis_id) \
				.join(Doctors, MainData.doctor_id == Doctors.doctor_id) \
				.add_columns(MainData.date_analysis, Patient.patient_name, Patient.patient_surname,
							 Patient.patient_patronymic, Patient.patient_date_birth, MainData.analysis_result,
							 AnalysisName.analysis_name, Doctors.doctor_name, MainData.id) \
				.paginate(kwargs['page'], kwargs['POSTS_PER_PAGE'], False)
		case 'filter':
			return MainData.query \
				.order_by(kwargs['sort_method']) \
				.join(Patient, MainData.patient_id == Patient.patient_id) \
				.join(AnalysisName, MainData.analysis_id == AnalysisName.analysis_id) \
				.join(Doctors, MainData.doctor_id == Doctors.doctor_id) \
				.add_columns(MainData.date_analysis, Patient.patient_name, Patient.patient_surname,
							 Patient.patient_patronymic, Patient.patient_date_birth, MainData.analysis_result,
							 AnalysisName.analysis_name, Doctors.doctor_name, MainData.id) \
				.filter(Patient.patient_surname.contains(kwargs['surname'].upper())) \
				.filter(Patient.patient_name.contains(kwargs['name'].upper())) \
				.filter(Patient.patient_patronymic.contains(kwargs['patronymic'].upper())) \
				.filter(Patient.patient_date_birth.contains(kwargs['date_birth'])) \
				.filter(MainData.date_analysis.contains(kwargs['date_analysis'])) \
				.filter(Doctors.doctor_name.contains(kwargs['referred_doctor'])) \
				.filter(AnalysisName.analysis_name.contains(kwargs['analysis_name'])) \
				.filter(MainData.analysis_result.contains(kwargs['analysis_result'])) \
				.paginate(kwargs['page'], kwargs['POSTS_PER_PAGE'], False)


def clear_auto_past(param, **kwargs):
	match param:
		case 'update_record':
			return {
				'fio': ' '.join([kwargs['main_data'][0].patient_surname.title(),
									kwargs['main_data'][0].patient_name.title(),
									kwargs['main_data'][0].patient_patronymic.title()
									if kwargs['main_data'][0].patient_patronymic else '']).strip(),
				'date_birth': kwargs['main_data'][0].patient_date_birth,
				'date_analysis': kwargs['main_data'][0].date_analysis,
				'referred_doctor': kwargs['main_data'][0].doctor_name,
				'analysis_name': kwargs['main_data'][0].analysis_name,
				'analysis_result': kwargs['main_data'][0].analysis_result,
			}
		case 'create_record':
			return {
				'fio': None,
				'date_birth': None,
				'date_analysis': datetime.utcnow(),
				'referred_doctor': None,
				'analysis_name': None,
				'analysis_result': None,
				'analysis_name1': None,
				'analysis_result1': None,
				'analysis_name2': None,
				'analysis_result2': None,
				'analysis_name3': None,
				'analysis_result3': None
			}
		case 'records':
			return {
				'surname': '',
				'name': '',
				'patronymic': '',
				'date_birth': '',
				'date_analysis': '',
				'referred_doctor': '',
				'analysis_name': '',
				'analysis_result': '',
				'sort_method': ''
			}
