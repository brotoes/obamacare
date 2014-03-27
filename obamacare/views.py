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

@view_config(route_name='TESTING', renderer='templates/test.pt', permission='view')
def test_view(request):
    imgs = DBSession.query(PacsImage.image_id).all()
    return getModules(request, dict(imgs=imgs))

@view_config(route_name='user_list', renderer='templates/user_list.pt', permission='view')
def userlist_view(request):
    keys = get_standard_keys(request)
    keys['data'] = DBSession.query(Person.person_id, 
        Person.first_name, Person.last_name, Person.email).all()
    keys['headers'] = ('Person ID', 'First', 'Last', 'Email')
    keys['filter_text'] = 'Filter'
    keys['base_url'] = '/person/'
    return getModules(request, keys)


@view_config(route_name='home', renderer='templates/user_home.pt', permission='view')
def user_home(request):
    #print ('auth user', authenticated_userid(request))
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
        pait = get_person(rec.patient_id)
        doc = get_person(rec.doctor_id)
        radi = get_person(rec.radiologist_id)
        data.append((rec.record_id, pait.last_name,doc.last_name, radi.last_name,
            rec.test_type, rec.prescribing_date, rec.test_date, rec.diagnosis,
        ))
    keys = dict(
        filter_text = "Filter",  # This controls what is displayed to the user
        base_url = '/record/',
        displaysuccess = None,
        displayerror = None,
        headers= ('Record ID', 'Patient','Doctor', 'Radiologist', 
            'Test Type', 'Prescription Date','Test Date', 'Diagnosis'
        ),
        data=data, 
        name=format_name(person.first_name, person.last_name),
    )

    return getModules(request, keys)
                        
@view_config(route_name='person_info', renderer='templates/person_profile.pt', permission='view')
def person_info(request):
    uid = authenticated_userid(request)
    if not uid:
        return HTTPForbidden()

    req_id = request.matchdict['id']
    if not req_id:
        return HTTPNotFound()
    person = get_person(req_id)
    if not Person:
        return HTTPNotFound()

    keys = dict(
        user_list= (('admin', 'a'), ('devon', 'r'), ('amy', 'p'), ('wilson', 'd')),
        role = getRole(uid, request)[0],
        displaysuccess = None,
        displayerror = None,
        fname = person.first_name, lname = person.last_name, 
        address = person.address, email = person.email,
        phone =person.phone
    )
    return  getModules(request, keys)

@view_config(route_name='user_profile', renderer='templates/user_profile.pt', permission='view')
def user_profile(request):
    #print ('auth user', authenticated_userid(request))
    try:
        user = get_user(authenticated_userid(request))
        person = get_person(user.person_id)
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
   
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
                    len(password[1]) >= 6):
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

@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    print("login")
    #print ('auth user', authenticated_userid(request))
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
            print ('auth passed')
            headers = remember(request, login)
            print ('came from:', came_from)
            return HTTPFound(location = came_from,
                             headers = headers)
        else:
            print('auth failed')
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

@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.route_url('landing'),
                     headers = headers)
@view_config(route_name='record', renderer='templates/view_record.pt')
def record(request):
    rec_id = request.matchdict['id']
    if (rec_id == 'new'):
       
        post = request.POST

        if post.items() != []:
            pid = post['pid']
            did = post['did']
            rid = post['rid']
            ttype = post['ttype']
            pdate = post['pdate']
            tdate = post['tdate']
            diag = post['daig']
            desc = post['desc']

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
        
@view_config(route_name='image')
def image(request):
    img_id = request.matchdict['id']
    if (img_id == 'new'):
        return Response("Create new image")
    
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

@view_config(route_name='user', renderer='templates/user_page.pt')
def user(request):
    uname = request.matchdict['user_name']
    try:
        user_rec = get_user(uname)
        person = get_person(user_rec.person_id)
    except DBAPIError:                    
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    resp  = 'fname: ' + person.first_name + '</br>'
    resp += 'lname: ' + person.last_name + '</br>'
    resp += 'email: ' + person.email

    keys = dict(
        fname = person.first_name,
        lname = person.last_name,
        email = person.email
    )

    return Response(resp)

@view_config(route_name="image_list", renderer='json')
def image_list(request):
    rec_id = request.matchdict['id']
    if not rec_id:
        return None
    images = get_images(request, rec_id)
    if not images:
        return None
    print images
    return images

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

@view_config(route_name='landing', permission='view')
def landing(request):
    return HTTPFound(location=request.route_url('home'))

@view_config(route_name='help', renderer='templates/mytemplate.pt')
def my_view(request):
    try:
        one = DBSession.query(MyModel).filter(MyModel.name == 'one').first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return {'one': one, 'project': 'obamacare', 'logged_in': authenticated_userid(request)!=None}

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
