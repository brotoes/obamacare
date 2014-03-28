from pyramid.response import Response

from sqlalchemy.exc import DBAPIError
from sqlalchemy import or_

from pyramid.view import (
    view_config,
    forbidden_view_config,
    )

from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )

from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.renderers import render_to_response

from .models import (
    DBSession,
    MyModel,
    Person,
    User,
    RadiologyRecord,
    PacsImage
    )
from .security import(
    authenticate,
    getRole,
    getModules,
)
from datetime import date
import pdb
from utilities import *
from queries import *
from json import loads
import json
import random

MIN_PASS_LEN = 6

"""
For testing use only: to be removed for production release
"""
@view_config(route_name='TESTING', renderer='templates/test.pt', permission='view')
def test_view(request):
    imgs = DBSession.query(PacsImage.image_id).all()
    return getModules(request, dict(imgs=imgs))

"""
Renders a list of people for the administrator to view an edit

/users

takes one GET argument
'filter'
"""
@view_config(route_name='user_list', renderer='templates/user_list.pt',
             permission='admin')
def userlist_view(request):
    keys = get_standard_keys(request)
    keys['data'] = DBSession.query(Person.person_id, 
        Person.first_name, Person.last_name, Person.email).all()
    keys['headers'] = ('Person ID', 'First', 'Last', 'Email')
    keys['filter_text'] = 'Filter'
    keys['base_url'] = '/person/'
    return getModules(request, keys)

"""
This is the start page, after logging in
It shows a list of all records relevant to the user

/home

takes three GET arguments
'start'
'end'
'filter'
"""
@view_config(route_name='home', renderer='templates/user_home.pt', permission='view')
def user_home(request):
    user = get_user(authenticated_userid(request))
    person = get_person(user.person_id)
    if not user:
        return HTTPForbidden()

    get = request.GET

    search_filter = ''
    start = '0001-01-01'
    end = '9999-12-31'

    if 'filter' in get:
        search_filter = clean(get['filter'])
    if 'start' in get:
        temp = format_date(clean(get['start']))
        if temp != None:
            start = temp
    if 'end' in get:
        temp = format_date(clean(get['end']))
        if temp != None:
            end = temp
    
    records = get_records(request, start, end, search_filter)

    data = []
    for rec in records:
        data.append((rec[0],
                     rec[1],
                     rec[2],
                     rec[3],
                     rec[4],
                     rec[5],
                     rec[6],
                     rec[7],
                    ))
    keys = dict(
        filter_text = "Filter",  # This controls what is displayed to the user
        base_url = '/record/',
        displaysuccess = None,
        displayerror = None,
        headers= ('Record ID',
                  'Patient',
                  'Doctor',
                  'Radiologist', 
                  'Test Type',
                  'Test Date',
                  'Diagnosis'
        ),
        data=data, 
        name=format_name(person.first_name, person.last_name),
    )

    return getModules(request, keys)

"""
Allows any user to view another person's information corresponding to id
in the case of the administrator, this information is edittable

/person/{id}
"""
@view_config(route_name='person_info', renderer='templates/person_profile.pt', permission='view')
def person_info(request):
    error_message = None
    success_message = None

    uid = authenticated_userid(request)
    if not uid:
        return HTTPForbidden()

    role = getRole(uid, request)

    req_id = request.matchdict['id']
    if not req_id:
        return HTTPNotFound()
    person = get_person(req_id)
    if not Person:
        return HTTPNotFound()

    user_list = get_attached_users(person.person_id)

    post = request.POST
    #process post for admin
    if 'group:a' in role and post.items() != []:
        #put post args in vars
        if 'fname' in post:
            new_fname = clean(post['fname'])
        else:
            new_fname = None
        if 'lname' in post:
            new_lname = clean(post['lname'])
        else:
            new_lname = None
        if 'address' in post:
            new_address = clean(post['address'])
        else:
            new_address = None
        if 'email' in post:
            new_email = format_email(clean(post['email']))
            if new_email == 'BAD FORMAT':
                new_email = None
                error_message = 'Incorrect Email Format'
        else:
            new_email = None
        if 'phone' in post:
            new_phone = format_phone(clean(post['phone']))
            if new_phone == 'BAD FORMAT':
                new_phone = None
                error_message = 'Incorrect Phone Format'
        else:
            new_phone = None

        uid_to_up = [i.split(':')[0] for i in post if 'newpass' in i]
        data = []
        for i in uid_to_up:
            temp_list = []
            temp_list.append(post[i + ':newpass'])
            temp_list.append(post[i + ':confirmpass'])
            temp_list.append(post[i + ':role'])
            data.append(temp_list)

        #verify post args
        if new_fname and new_fname != person.first_name \
            and new_fname != '':
            person.first_name = new_fname
            success_message = mess_cat(
                            success_message,
                            'First Name Updated Successfully'
                                      )
        if new_lname and new_lname != person.last_name \
            and new_lname != '':
            person.last_name = new_lname
            success_message = mess_cat(
                            success_message,
                            'Last Name Updated Successfully'
                                      )
        if new_address and new_address != person.address \
            and new_address != '':
            person.address = new_address
            success_message = mess_cat(
                            success_message,
                            'Address Updated Successfully'
                                      )
        if new_email and new_email != person.email \
            and new_email != '':
            person.email = new_email
            success_message = mess_cat(
                            success_message,
                            'Email Updated Successfully'
                                      )
        if new_phone and new_phone != person.phone \
            and new_phone != '':
            person.phone = new_phone
            success_message = mess_cat(
                            success_message,
                            'Phone Updated Successfully'
                                      )

        for i in range(len(uid_to_up)):
            user = get_user(uid_to_up[i])

            new = data[i][0]
            con = data[i][1]
            new_role = data[i][2]

            if new_role in get_roles():
                if new_role != user.role:
                    user.role = new_role
                    success_message = mess_cat(
                        success_message,
                        'Role Updated For ' + uid_to_up[i]
                                              )
            else:
                error_message = mess_cat(
                    error_message,
                    'Invalid Role For '+ uid_to_up[i]
                                        )
            if not 'New Password' in new or not 'Confirm New Password' in con:
                if new != con:
                    print con
                    error_message = mess_cat(
                        error_message,
                        'Passwords Do Not Match For ' + uid_to_up[i]
                                            )
                elif len(new) < MIN_PASS_LEN:
                    error_message = mess_cat(
                        error_message,
                        'Password Too Short For ' + uid_to_up[i]
                                            )
                elif user.password != new:
                    user.password = new
                    success_message = mess_cat(
                        success_message,
                        'Password Updated For ' + uid_to_up[i]
                                              )


        if not success_message and not error_message:
            error_message = 'Nothing Updated'

    keys = dict(
        role = role[0],
        displaysuccess = success_message,
        displayerror = error_message,
        fname = person.first_name,
        lname = person.last_name, 
        address = person.address,
        email = person.email,
        phone = person.phone,
        user_list = user_list
    )
    return  getModules(request, keys)

"""
Allows a user to view and edit their own information

/profile
"""
@view_config(route_name='user_profile', renderer='templates/user_profile.pt', permission='view')
def user_profile(request):
    user = get_user(authenticated_userid(request))
    person = get_person(user.person_id)
   
    error_message = ""

    #update database
    if (request.POST.items() != []):
        post = request.POST
        fname = clean(post['fname'])
        lname = clean(post['lname'])
        address = clean(post['address'])
        email = clean(post['email'])
        phone = format_phone(post['phone'])

        password = []
        password.append(clean(post['existing']))
        password.append(clean(post['newpass']))
        password.append(clean(post['newconfirm']))
        
        if fname != '':
            person.first_name = fname
        if lname != '':
            person.last_name = lname
        if address != '':
            person.address = address
        if email != '':
            person.email = email
        if phone != '':
            if phone != 'BAD FORMAT':
                person.phone = phone
            else:
                error_message = "Bad Phone Format"
        
        full_fields = [x for x in password if x != '']
        if len(full_fields) > 0:
            if len(full_fields) == 3:
                if (password[0] == user.password and
                    password[1] == password[2] and
                    len(password[1]) >= MIN_PASS_LEN):
                    user.password = password[1]
                else:
                    error_message = "Password Fields Must Match"
            else:
                error_message = "Some Password Fields Empty"
                     
    keys = dict(
        displaysuccess = None,
        displayerror = None,
        fname = person.first_name, lname = person.last_name, 
        address = person.address, email = person.email,
        phone =person.phone
    )

    if error_message != "":
        keys['displayerror'] = error_message

    return  getModules(request, keys)

"""
Here, a user may log in.

/login
"""
@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        if authenticate(login, password):
            headers = remember(request, login)
            return HTTPFound(location = came_from,
                             headers = headers)
        else:
            message = 'Failed login'

    return dict(
        displaysuccess = message,
        displayerror = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = login,
        password = password,
        logged_in = authenticated_userid(request)
    )

"""
Logs a user out

/logout
"""
@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.route_url('landing'),
                     headers = headers)

"""
View a records, corresponding to {id}  information and associated images

/record/{id}
"""
@view_config(route_name='record', renderer='templates/view_record.pt')
def record(request):
    rec_id = request.matchdict['id']
    if (rec_id == 'new'):
       
        post = request.POST

        if post.items() != []:
            pid = clean(post['pid'])
            did = clean(post['did'])
            rid = clean(post['rid'])
            ttype = clean(post['ttype'])
            pdate = clean(post['pdate'])
            tdate = clean(post['tdate'])
            diag = clean(post['diag'])
            desc = clean(post['desc'])

            insert_record(request, pid, did, rid, ttype, pdate, tdate,
                          diagnosis=diag, description=desc)
        
        return render_to_response('templates/new_record.pt', 
            getModules(request,  people_list(request, dict(request=request, displaysuccess = None,displayerror = None)))
            )

    record = get_record(request, rec_id)
    if record:
        imgs = get_images(request, rec_id)
        patient = get_person(record.patient_id)
        doctor = get_person(record.doctor_id)
        radi = get_person(record.radiologist_id)
    else:
        return HTTPForbidden()

      
    keys = dict(
        displaysuccess = None,
        displayerror = None,
        imgs = imgs,
        recid = record.record_id,
        pid = record.patient_id,
        pname = format_name(patient.first_name, patient.last_name),
        did = record.doctor_id,
        dname = format_name(doctor.first_name, doctor.last_name),
        rid = record.radiologist_id,
        rname = format_name(radi.first_name, radi.last_name),
        ttype = record.test_type,
        pdate = record.prescribing_date,
        tdate = record.test_date,
        diag = record.diagnosis,
        descr = record.description,
    )
    return  getModules(request, keys)
        
"""
displays a single image corresponding to id

/i/{id}

takes a single GET argument, 's=[t,r,f]' specifying the size of the image
"""
@view_config(route_name='image')
def image(request):
    img_id = request.matchdict['id']
    img = get_image(request, img_id)

    if not img:
        return Response('Image Not Found')
   
    if 's' in request.GET:
        size = request.GET['s']
    else: 
        size = "r"

    if size == 't':
        resp = img.thumbnail
    elif size == 'f':
        resp = img.full_size
    else:   
        resp = img.regular_size

    return Response(body=resp,  content_type='image/jpeg')

"""
returns the name and email of a user specified by 'user_name'

/user/{user_name}

***Not in use, likely to be removed
"""
@view_config(route_name='user', renderer='templates/user_page.pt')
def user(request):
    uname = request.matchdict['user_name']
    user_rec = get_user(uname)
    person = get_person(user_rec.person_id)
    resp  = 'fname: ' + person.first_name + '</br>'
    resp += 'lname: ' + person.last_name + '</br>'
    resp += 'email: ' + person.email

    keys = dict(
        fname = person.first_name,
        lname = person.last_name,
        email = person.email
    )

    return Response(resp)

"""
returns a json list of images belonging to the record corresponding to 'id'

/images/{id}
"""
@view_config(route_name="image_list", renderer='json')
def image_list(request):
    rec_id = request.matchdict['id']
    if not rec_id:
        return None
    images = get_images(request, rec_id)
    if not images:
        return None
    return images

"""
Allows the user to get a list of patients who, between the time of start and end
where diagnosed with a specified diagnosis.

/report

takes three GET arguments
'start'
'end'
'filter'
"""
#I'm using user_home.pt for testing purposes only; it already renders a table
@view_config(route_name='report', renderer='templates/user_home.pt',
permission='admin')
def report(request):
    get = request.GET
    user = get_user(authenticated_userid(request))
    person = get_person(user.person_id)
    if not user:
        return HTTPForbidden()

    diag_filter = ''
    start = '0001-01-01'
    end = '9999-12-31'

    if 'filter' in get:
        diag_filter = clean(get['filter'])
    if 'start' in get:
        temp = format_date(clean(get['start']))
        if temp != None:
            start = temp
    if 'end' in get:
        temp = format_date(clean(get['end']))
        if temp != None:
            end = temp

    report = get_report(request, diag_filter, start, end)
    
    duplicates = []
    data = []
    ids = []
    for i in report:
        duplicates.append((
                    i[0].person_id,
                    format_name(i[0].first_name, i[0].last_name),
                    i[1].diagnosis
                    ))
    def append_(item):
        data.append(item)
        ids.append(item[0])
    
    [append_(item) for item in duplicates if item[0] not in ids]
    keys = dict(
        filter_text = "Diagnosis",      # this changes what is displayed to user 
        base_url = '/person/',
        displayerror = None,
        displaysuccess = None,
        headers= (
                 'Patient ID',
                 'Name',
                 'Diagnosis'
                 ),
       data=data, 
       name=format_name(person.first_name, person.last_name),
    )
    return getModules(request, keys)

"""
returns a JSON list of people who have an attached user account with a specified
role

/p

takes one GET argument
'r=[d,r,p,a]'
"""
@view_config(route_name='people_list', permission='view', renderer='json')
def people_list(request, keys=None):
    if not keys:
        keys = {}
    get = request.GET
    role_arg = 'd,r,p,a'
    if 'r' in get:
        role_arg = clean(get['r'])
    roles = role_arg.split(',')
    
    data = get_persons(roles=roles)
    
    keys['data'] = data
    keys['headers'] = ('ID', 'Name', 'Email')
    
    return keys 

"""
forwards user to /home

/
"""
@view_config(route_name='landing', permission='view')
def landing(request):
    return HTTPFound(location=request.route_url('home'))

"""
Here for more testing -- as a reference
"""
@view_config(route_name='help', renderer='templates/mytemplate.pt')
def my_view(request):
    try:
        one = DBSession.query(MyModel).filter(MyModel.name == 'one').first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return {'one': one, 'project': 'obamacare', 'logged_in': authenticated_userid(request)!=None}


"""
Adds a family doctor to the logged in user
"""
@view_config(route_name='add_familydoctor', permission='view')
def afd(request):
    user = get_user(authenticated_userid(request))
    patient_id = user.person_id
    role = getRole(user.user_name, request)

    did = request.matchdict['id']

    if 'group:p' in role:
        add_fdoctor(request, did, patient_id)
        return Response("added")
    else:
        return Response("you are not a patient")
    
"""
displays a list of doctors if user is a patient, or a list of patients if user
is a doctor
"""
@view_config(route_name='family', permission='view', renderer='json')
def family(request):
    user = get_user(authenticated_userid(request))
    person_id = user.person_id
    role = getRole(user.user_name, request)

    print role

    if 'group:p' in role:
        persons = get_fdoctors(person_id)
    elif 'group:d' in role:
        persons = get_fpatients(person_id)
    else:
        return HTTPForbidden()

    return persons


conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_obamacare_db" script
    to initialize your database tables.  Check your virtual 
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""
