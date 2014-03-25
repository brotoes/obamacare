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

def get_person(person_id):
    if not person_id:
        return None
    try:
        person = DBSession.query(Person).filter(Person.person_id==person_id).first()
        return person
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

def get_loggedin(request):
    if request == None:
        return None
    try:
        user = DBSession.query(
                       User
                   ).filter(
                       User.user_name == authenticated_userid(request)
                   ).first()
        return user
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

def get_records(request, start=None, end=None, search_filter=None):
    if start == None:
        start = '0001-01-01'
    if end == None:
        end = '9999-12-31'
    if search_filter == None:
        search_filter = '%%'
    else:
        search_filter = '%' + search_filter + '%'

    return DBSession.query(
                 RadiologyRecord
             ).filter(
                 and_(RadiologyRecord.test_date.between(
                    start, end), or_(
                 RadiologyRecord.diagnosis.like(search_filter),
                 RadiologyRecord.description.like(search_filter),
                 RadiologyRecord.test_type.like(search_filter)
                 ))
             ).order_by(RadiologyRecord.test_date)
