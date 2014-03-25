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

import pdb
from utilities import *
from queries import *
from json import loads
import json
import random

@view_config(route_name='home', renderer='templates/user_home.pt', permission='view')
def user_home(request):
    #print("landing view")
    #print ('auth user', authenticated_userid(request))
    uid = authenticated_userid(request)
    if not uid:
        return HTTPForbidden

    try:
        user = DBSession.query(User).filter(User.user_name==uid).first()
        person = DBSession.query(Person).filter(Person.person_id==user.person_id).first()

    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    role = getRole(user.user_name, request)[0].split(':')[1].strip()   
    users = role == 'a'
    reports = role == 'a'
    new = role!='p'

    get = request.GET

    
    if uid == 'admin':
        results =  DBSession.query(RadiologyRecord)
    else:
        results = DBSession.query(RadiologyRecord).filter(or_(RadiologyRecord.patient_id==person.person_id,
            RadiologyRecord.doctor_id==person.person_id, RadiologyRecord.radiologist_id==person.person_id))

    images = DBSession.query(PacsImage).all() 
    if get.items() != []:
        print ("\n\ngot filters\n\n")
        search_filter = clean(get['filter'])
        start = clean(get['start'])
        end = clean(get['end'])

        try:
            if search_filter:
                print("filtering")
                results = results.filter(or_(RadiologyRecord.diagnosis.contains(search_filter), 
                    RadiologyRecord.description.contains(search_filter)))       
            # this query should be looked at..
            """records.filter(
                RadiologyRecord.test_date >= start and
                RadiologyRecord.test_date <= end and
                (search_filter.upper in
                RadiologyRecord.diagnosis.upper or
                 search_filter.upper in
                 RadiologyRecord.description.upper))"""  
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain', status_int=500)

    # I added some more back end stuff that will show all records belonging to the signed in user
    # This is the type of thing that should probably be in the queuys oh i mean queries thing.
    records = results.all()
    data = []
    for rec in records:
        pait = get_person(rec.patient_id)
        doc = get_person(rec.doctor_id)
        radi = get_person(rec.radiologist_id)
        data.append(
            (rec.record_id, images[random.randrange(len(images))].image_id, format_name(pait.first_name, pait.last_name), 
                format_name(doc.last_name, doc.first_name),
                format_name(radi.first_name,radi.last_name), rec.prescribing_date))
                        
    keys = dict(
        headers=('record id', 'image', 'patient', 'doctor', 'Radiologist','date'),
        data=data, name= format_name(person.first_name, person.last_name),
    )
    return getModules(request, keys)

                        
@view_config(route_name='person_info', renderer='templates/person_profile.pt', permission='view')
def person_info(request):
    uid = authenticated_userid(request)
    if not uid:
        return HTTPForbidden
    req_id = request.matchdict['id']
    if not req_id:
        return HTTPNotFound()
    person = get_person(req_id)
    if not Person:
        return HTTPNotFound()

    keys = dict(
        fname = person.first_name, lname = person.last_name, 
        address = person.address, email = person.email,
        phone =person.phone
    )
    return  getModules(request, keys)

@view_config(route_name='user_profile', renderer='templates/user_profile.pt', permission='view')
def user_profile(request):
    #print ('auth user', authenticated_userid(request))
    try:
        user = DBSession.query(User).filter(User.user_name==authenticated_userid(request)).first()
        person = DBSession.query(Person).filter(Person.person_id==user.person_id).first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
   
    #update database
    if (request.POST.items() != []):
        try:
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
                    print "TODO: ERROR MESSAGE: BAD PHONE FORMAT"
            
            full_fields = [x for x in password if x != '']
            if len(full_fields) > 0:
                if len(full_fields) == 3:
                    if (password[0] == user.password and
                        password[1] == password[2] and
                        len(password[1]) >= 6):
                        user.password = password[1]
                    else:
                        print "TODO: Error message: fields must match"
                else:
                    print "TODO: Error message: empty pass fields"
                     
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain', status_int=500)

    keys = dict(
         fname = person.first_name, lname = person.last_name, 
         address = person.address, email = person.email,
         phone =person.phone
         )
    #return { new = new, users = users, reports':reports, 'logged_in': authenticated_userid(request),
    #        'fname':person.first_name, 'lname':person.last_name, 'address':person.address, 'email':person.email,
    #       'phone':person.phone,}
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
        message = message,
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
#TODO: Permissions
@view_config(route_name='record', renderer='templates/view_record.pt')
def record(request):
    rec_id = request.matchdict['id']
    if (rec_id == 'new'):
        return render_to_response('templates/new_record.pt',
                              getModules(request),request=request)
    else:
        resp = ''
        try:
            record = DBSession.query(RadiologyRecord).filter(
                RadiologyRecord.record_id==rec_id).first()
            imgs = DBSession.query(
                             PacsImage
                       ).filter(
                             PacsImage.record_id==rec_id
                       ).all()
            patient = get_person(record.patient_id)
            doctor = get_person(record.doctor_id)
            radi = get_person(record.radiologist_id)

        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain', status_int=500)
    
        keys = dict(
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
            descr = record.description,)
        
        return  getModules(request, keys)
        
#TODO: Permissions
@view_config(route_name='image')
def image(request):
    img_id = request.matchdict['id']
    if (img_id == 'new'):
        return Response("Create new image")
    
    # TODO: no db stuff in views
    # TODO: only return images user is allowed to see
    try:
        img = DBSession.query(PacsImage).filter(PacsImage.image_id==img_id).first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

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

    # Method 2
    #response = Response(content_type='application/jpg')
    #response.app_iter = img.thumbnail  

@view_config(route_name='user', renderer='templates/user_page.pt')
def user(request):
    uname = request.matchdict['user_name']
    try:
        user_rec = DBSession.query(
                            User
                        ).filter(
                            User.user_name==uname
                        ).first()
        person = DBSession.query(
                            Person
                        ).filter(
                            Person.person_id==user_rec.person_id
                        ).first()
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
    images = get_images(rec_id)
    if not images:
        return None
    print images
    return images

@view_config(route_name='get', renderer='json')
def get(request):
    get_type = request.matchdict['type']
    if get_type == 'users':
        return {
            'userid':[
                        58,
                        59,
                        60
                     ]
            }
    else:
        return HTTPNotFound()

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



