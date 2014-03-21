from pyramid.response import Response

from sqlalchemy.exc import DBAPIError

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
from .models import (
    DBSession,
    MyModel,
    Person,
    User,
    RadiologyRecord
    )
from .security import(
    authenticate,
    getRole,

)

import pdb
from utilities import *
from json import loads

@view_config(route_name='landing', renderer='templates/landing.pt', permission='view')
def landing_view(request):
    #print("landing view")
    #print ('auth user', authenticated_userid(request))
    try:
        user = DBSession.query(User).filter(User.user_name==authenticated_userid(request)).first()
        person = DBSession.query(Person).filter(Person.person_id==user.person_id).first()

    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    role = getRole(user.user_name, request)[0].split(':')[1].strip()   
    users = role == 'a'
    reports = role == 'a'
    new = role!='p'

    return {'new': new, 'users':users, 'reports':reports, 
    'project': 'obamacare', 'name': person.first_name+' ' +person.last_name, 
    'logged_in': authenticated_userid(request) }

@view_config(route_name='home', renderer='templates/user_home.pt', permission='view')
def home_view(request):
    #print("home view")
    return Response("empty")
    

@view_config(route_name='user_profile', renderer='templates/user_profile.pt', permission='view')
def user_profile(request):
    #print ('auth user', authenticated_userid(request))
    try:
        user = DBSession.query(User).filter(User.user_name==authenticated_userid(request)).first()
        person = DBSession.query(Person).filter(Person.person_id==user.person_id).first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    role = getRole(user.user_name, request)[0].split(':')[1].strip()   
    users = role == 'a'
    reports = role == 'a'
    new = role!='p'

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
            password.append(post['existing'])
            password.append(post['newpass'])
            password.append(post['newconfirm'])
            
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

    return {'new': new, 'users':users, 'reports':reports, 'logged_in': authenticated_userid(request)}

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
        return Response("Create new record")
    else:
        resp = ''
        record = DBSession.query(
                         RadiologyRecord
                   ).filter(
                         RadiologyRecord.record_id==rec_id
                   ).first()

        resp += 'TODO: thumb url'
        resp += '</br>'
        resp += 'TODO: reg url'
        resp += '</br>'
        resp += 'TODO: full url'
        resp += '</br>'
        resp += str(record.record_id)
        resp += '</br>'
        resp += str(record.patient_id)
        resp += '</br>'
        resp += str(record.doctor_id)
        resp += '</br>'
        resp += str(record.radiologist_id)
        resp += '</br>'
        resp += record.test_type
        resp += '</br>'
        resp += str(record.prescribing_date)
        resp += '</br>'
        resp += str(record.test_date)
        resp += '</br>'
        resp += record.diagnosis
        resp += '</br>'
        resp += record.description
        resp += '</br>'

        #Until the template is finished, I'll return a string, not this.
        keys = dict(
            thumburl = None,
            regurl = None,
            fullurl = None,
            recid = record.record_id,
            pid = record.patient_id,
            did = record.doctor_id,
            rid = record.radiologist_id,
            ttype = record.test_type,
            pdate = record.prescribing_date,
            tdate = record.test_date,
            diag = record.diagnosis,
            descr = record.description,
            )

        return Response(resp)

@view_config(route_name='image')
def image(request):
    rec_id = request.matchdict['id']
    if (rec_id == 'new'):
        return Response("Create new image")
    else:
        return Response("Image ID: " + rec_id)

@view_config(route_name='user', renderer='templates/user_page.pt')
def user(request):
    uname = request.matchdict['user_name']
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
    resp  = 'fname: ' + person.first_name + '</br>'
    resp += 'lname: ' + person.last_name + '</br>'
    resp += 'email: ' + person.email + '</br>'

    keys = dict(
        fname = person.first_name,
        lname = person.last_name,
        email = person.email
    )

    return Response(resp)

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



