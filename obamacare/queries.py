import pdb
import sys
import transaction
import datetime
import random
from datetime import date

from sqlalchemy import (
    engine_from_config,
    or_,
    and_
    )

from sqlalchemy.exc import (
    IntegrityError,
    DBAPIError
    )

from pyramid.security import (
    remember,
    forget,
    authenticated_userid
    )

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from .models import (
    DBSession,
    User,
    Person,
    RadiologyRecord,
    PacsImage
    )

from .security import (
    getRole
    )

from utilities import *

def get_name(person):
    return format_name(person.first_name, person.last_name)

def get_person(person_id):
    if not person_id:
        return None
    try:
        person = DBSession.query(Person).filter(Person.person_id==person_id).first()
        return person
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

def get_user(user_name):
    if not user_name:
        return None
    try:
        user = DBSession.query(
                        User
                     ).filter(
                        User.user_name==user_name
                     ).first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    
    return user

def get_record(request, record_id):
    user = get_user(authenticated_userid(request))
    role = getRole(user.user_name, request)
    record = DBSession.query(
            RadiologyRecord
        ).filter(
            and_(
                RadiologyRecord.record_id==record_id,
                or_(
                    RadiologyRecord.patient_id==user.person_id,
                    RadiologyRecord.doctor_id==user.person_id,
                    RadiologyRecord.radiologist_id==user.person_id,
                    'group:a' in role
                    )
                )
        ).first()

    return record

def get_records(request, start=None, end=None, search_filter=None):
    if start == None or start == '':
        start = '0001-01-01'
    if end == None or end == '':
        end = '9999-12-31'
    if search_filter == None or search_filter == '':
        search_filter = '%%'
    else:
        search_filter = '%' + search_filter + '%'

    search_filter = search_filter.replace('*', '%')
    user = get_user(authenticated_userid(request))
    role = getRole(user.user_name, request)

    return DBSession.query(
                 RadiologyRecord
             ).filter(
                 and_(RadiologyRecord.test_date.between(
                    start, end), 
                    or_(
                        RadiologyRecord.diagnosis.like(search_filter),
                        RadiologyRecord.description.like(search_filter),
                        RadiologyRecord.test_type.like(search_filter)
                        ),
                    or_(
                        RadiologyRecord.patient_id==user.person_id,
                        RadiologyRecord.doctor_id==user.person_id,
                        RadiologyRecord.radiologist_id==user.person_id,
                        'group:a' in role
                        )
                 )
             ).order_by(RadiologyRecord.test_date)

# TODO: Possible permission check here
def get_images(request, record_id):
    if not record_id:
        return None

    images = DBSession.query(
            PacsImage.image_id
        ).filter(
            PacsImage.record_id==record_id
        )

    return images.all()

def get_image(request, image_id):
    if not record_id:
        return None
    image = DBSession.query(
                    PacsImage
                ).filter(
                    PacsImage.image_id==image_id
                ).first()

    return image
