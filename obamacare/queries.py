import pdb
import sys
import transaction
import datetime
import random
from datetime import date

from sqlalchemy import (
    engine_from_config,
    or_,
    and_,
    func,
    join
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
    PacsImage,
    FamilyDoctor,
    Role
    )

from .security import (
    getRole
    )

from utilities import *

"""
returns a list of all valid roles for a user
"""
def get_roles():
    roles = DBSession.query(
                        Role.role
                    ).all()
    return roles

"""
returns a query for the join of RadiologyRecord, PacsImage, and Person
"""
def get_cube():
    query = DBSession.query().select_from(
                        RadiologyRecord,
                        PacsImage,
                        Person,
                    ).filter(
                        RadiologyRecord.record_id==PacsImage.record_id,
                        RadiologyRecord.patient_id==Person.person_id,
                    )
    return query

"""
returns a properly formatted name corresponding to person
"""
def get_name(person):
    return format_name(person.first_name, person.last_name)

"""
returns a person object corresponding to person_id
"""
def get_person(person_id):
    if not person_id:
        return None
    try:
        person = DBSession.query(
                            Person
                        ).filter(
                            Person.person_id==person_id
                        ).first()
        return person
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

"""
takes a patient person_id and returns a list of doctor person ids who are the family
doctor of the person
"""
def get_fdoctors(pid):
    dids = DBSession.query(FamilyDoctor.doctor_id).filter(
                        FamilyDoctor.patient_id==pid
            ).all()

    return dids

"""
takes a doctor person_id and returns a list of patient person_ids who 
"""
def get_fpatients(did):
    pids = DBSession.query(FamilyDoctor.patient_id).filter(
                        FamilyDoctor.doctor_id==did
                    ).all()

    return pids

"""
takes a patient_id and doctor_id and inserts it into the family_doctor table
"""
def add_fdoctor(request, did, pid):
    
    user = get_user(authenticated_userid(request))
    
    permission = False
    print "add family doctor for patient", pid, "and doctor", did
    print "role", user.role, "person_id", user.person_id
    #pdb.set_trace()
    if user.role == 'a':
        permission = True
    elif int(pid) == int(user.person_id):
        permission = True
    else:
        print "Failed to get permissions"
    
    if permission:
        with transaction.manager:
            DBSession.add(FamilyDoctor(
                did,
                pid
            ))
            transaction.manager.commit()
    else:
        return None


"""
takes a patient_id and doctor_id and inserts it into the family_doctor table
"""
def add_fpatient(request, pid, did):
    user_name = authenticated_userid(request)
    person = get_user(user_name)
    print "add family patient for paitient", pid, "and doctor", did

    permission = False
    if person.role == 'a':
        permission = True
    elif person.role == 'd' and int(did)==int(person.person_id):
        permission = True
    
    if permission:
        with transaction.manager:
            DBSession.add(FamilyDoctor(
                did,
                pid
            ))
            transaction.manager.commit()
    else:
        return None


"""
returns a list of tuples, (user_name, role), attached to person_id, pid
"""
def get_attached_users(pid):
    user_list = DBSession.query(
                        User.user_name,
                        User.role
                    ).filter(
                        User.person_id==pid
                    ).all()

    return user_list

#returns a list of all persons in the form
#[(id, name, email), ...]
def get_persons(roles=['d','r','p','a']):
    persons = DBSession.query(
                        Person.person_id,
                        Person.first_name,
                        Person.last_name,
                        Person.email,
                        User.role
                    ).select_from(
                        join(Person, User, User.person_id)
                    ).filter(
                        User.person_id==Person.person_id
                    ).filter(
                        User.role.in_(roles)
                    )

    print "PERSONS============================"
    print persons
    print "==================================="

    persons = persons.all()
    
    data = []
    for i in persons:
        data.append((
                  i.person_id,
                  format_name(i.first_name, i.last_name),
                  i.email
                     ))

    return data

"""
returns a user object corresponding to user_name
"""
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

"""
returns a record object corresponding to record_id if user in 'request' has
permission to view that record
"""
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
        )

    print "SINGLE RECORD================="
    print record
    print "=============================="

    record = record.first()

    return record

"""
returns a list of tuples containing record information
"""
def get_records(request, start=None, end=None, search_filter=None, method='freq'):
    if start == None or start == '':
        start = '0001-01-01'
    if end == None or end == '':
        end = '9999-12-31'

    print start
    print end
    print search_filter
    print method

    user = get_user(authenticated_userid(request))
    role = getRole(user.user_name, request)

    records = DBSession.query(
                 RadiologyRecord.record_id,
                 RadiologyRecord.patient_id,
                 RadiologyRecord.doctor_id,
                 RadiologyRecord.radiologist_id,
                 RadiologyRecord.test_type,
                 RadiologyRecord.test_date,
                 RadiologyRecord.diagnosis,
                 RadiologyRecord.description 
             ).filter(
                 RadiologyRecord.test_date.between(start, end), 
                 or_(
                     RadiologyRecord.patient_id==user.person_id,
                     RadiologyRecord.doctor_id==user.person_id,
                     RadiologyRecord.radiologist_id==user.person_id,
                     'group:a' in role
                     )
             )

    print "RECORDS(HOME):=========================="
    print records
    print "========================================"

    records = records.all()

    formatted = []
    for i in records:
        pname = get_name(get_person(i[1]))
        dname = get_name(get_person(i[2]))
        rname = get_name(get_person(i[3]))
        formatted.append((i[:1] + (pname, dname, rname) + i[4:]))

    if method == 'freq' and (search_filter == '' or search_filter == None):
        method = 'new'
    cols = (None, 'pname', None, None, None, 'tdate', 'diag', 'desc')
    formatted = apply_filter(search_filter, formatted, cols, method=method)

    return formatted


#TODO discuss the extent of permissions necessary here
def insert_record(request, patient_id, doctor_id, radiologist_id, test_type,
                  prescribing_date, test_date, diagnosis='', description='',
                  image=None):
    user = get_user(authenticated_userid(request))
    person = user.person_id
    role = getRole(user.user_name, request)

    permission = True
    if 'group:r' in role and not person.person_id == radiologist_id:
        permission = False
    if 'group:d' in role and not person.person_id == doctor_id:
        permission = False
    if 'group:p' in role:
        permission = False
    #test if persons have correct roles to be inserted? 

    if permission:
        with transaction.manager:
            new_record = RadiologyRecord(
                patient_id,
                doctor_id,
                radiologist_id,
                test_type,
                prescribing_date,
                test_date,
                diagnosis,
                description
            )
            DBSession.add(new_record)
            DBSession.flush()
            
            new_recid = new_record.record_id

            transaction.manager.commit()
        
        if image != None:
            fd = image.file
            img = Image.open(fd)
            thumb = img.copy()
            reg = img.copy()
            
            thumb.thumbnail((60,60), Image.ANTIALIAS)
            reg.thumbnail((200,200), Image.ANTIALIAS)

            img.thumbnail = jpeg_toBinary(thumb)
            img.regular = jpeg_toBinary(reg)
            img.full_size = jpeg_toBinary(img)
            with transaction.manager:
                print img.thumbnail
                DBSession.add(PacsImage(new_recid,
                                        img.thumbnail,
                                        img.regular,
                                        img.full_size
                                        ))
                transaction.manager.commit()
            

def insert_image(request, record_id):
    user = get_user(authenticated_userid(request))
    person = user.person_id
    role = getRole(user.user_name, request)

    authd_persons = []
    authd_persons.append(record.doctor_id)
    authd_persons.append(record.radiologist_id)

        #TODO insert image

def get_image(request, img_id):
    if not img_id:
        return None
    
    user = get_user(authenticated_userid(request))
    person = user.person_id
    role = getRole(user.user_name, request)
    
    image = DBSession.query(
                    PacsImage
                ).filter(
                    PacsImage.image_id==img_id
                ).first()
    record = DBSession.query(
                    RadiologyRecord
                ).filter(
                    RadiologyRecord.record_id==image.record_id
                ).first()

    authd_persons = []
    authd_persons.append(record.patient_id)
    authd_persons.append(record.doctor_id)
    authd_persons.append(record.radiologist_id)

    if 'group:a' in role or person in authd_persons:
        return image
    else:
        return None

def get_images(request, record_id):
    if not record_id:
        return None

    user = get_user(authenticated_userid(request))
    person = user.person_id
    role = getRole(user.user_name, request)

    record = DBSession.query(
            RadiologyRecord
        ).filter(
            RadiologyRecord.record_id==record_id
        ).first()

    authd_persons = []
    authd_persons.append(record.patient_id)
    authd_persons.append(record.doctor_id)
    authd_persons.append(record.radiologist_id)

    if (person in authd_persons or 'group:a' in role):
        images = DBSession.query(
                PacsImage.image_id
            ).filter(
                PacsImage.record_id==record_id
            )
        print "IMAGES================"
        print images
        print "======================"
        return images.all()
    else:
        return None


def get_report(request, diag_filter, start, end):
    user_name = authenticated_userid(request)
    role = getRole(user_name, request)
    
    if 'group:a' in role:
        report = DBSession.query(
                            Person,
                            RadiologyRecord
                        ).select_from(
                            join(RadiologyRecord, Person, RadiologyRecord.patient_id)
                        ).filter(
                            or_(
                                RadiologyRecord.test_date.between(start, end),
                                RadiologyRecord.prescribing_date.between(start, end)
                               )
                        ).filter(
                            RadiologyRecord.patient_id==Person.person_id
                        ).filter(
                            RadiologyRecord.diagnosis.contains(diag_filter)
                        ).order_by(
                            RadiologyRecord.test_date.desc()
                        )

        print "REPORT==========================="
        print report
        print "================================="
        return report
    else:
        return None
