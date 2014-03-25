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
from json import loads
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

    if get.items() != []:
        search_filter = clean(get['filter'])
        start = clean(get['start'])
        end = clean(get['end'])

        try:
            # this query should be looked at..
            records = DBSession.query(RadiologyRecord).filter(
                RadiologyRecord.test_date >= start and
                RadiologyRecord.test_date <= end and
                (search_filter.upper in
                RadiologyRecord.diagnosis.upper or
                 search_filter.upper in
                 RadiologyRecord.description.upper))    
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain', status_int=500)

    # I added some more back end stuff that will show all records belonging to the signed in user
    # This is the type of thing that should probably be in the queuys oh i mean queries thing.
    if uid == 'admin':
        records = DBSession.query(RadiologyRecord).all()
    else:
        records = DBSession.query(RadiologyRecord).filter(or_(RadiologyRecord.patient_id==person.person_id,
            RadiologyRecord.doctor_id==person.person_id, RadiologyRecord.radiologist_id==person.person_id)).all()
    images = DBSession.query(PacsImage).all()    
    data = []
    for rec in records:
        pait = get_person(rec.patient_id)
        doc = get_person(rec.doctor_id)
        radi = get_person(rec.radiologist_id)
        data.append(
            (rec.record_id, images[random.randrange(len(images))].image_id, pait.last_name +", "+ pait.first_name, 
                doc.last_name +", "+doc.first_name,
                radi.first_name +", " + radi.last_name, rec.prescribing_date))
                        

    keys = dict(
        headers=('record id', 'image', 'patient', 'doctor', 'Radiologist','date'),
        data=data, name= person.first_name+' ' +person.last_name,
    )
    return getModules(request, keys)

    # When you add new return values we need to keep the old ones too or templates will break
"""    return {'headers':('record_id',
                       'image',
                       'patient',
                       'doctor',
                       'date'),
            'data':((10, 15, 'John', 'Wilson', '2014-03-16'),
                    (42, 33, 'John', 'Wilson', '2014-05-09'))}

    return {'new': new, 'users':users, 'reports':reports, 
    return {'headers': ('record id', 'image', 'patient', 'doctor', 'date'), 
    'data':((10, 15, 'john', 'wilson', '2014-03-16'),('42', 33, 'john', 'wilson', '2014-05-09')), 
    'new': new, 'users':users, 'reports':reports, 
    'project': 'obamacare', 'name': person.first_name+' ' +person.last_name, 
    'logged_in': authenticated_userid(request) }
"""

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
            img = DBSession.query(
                             PacsImage
                       ).filter(
                             PacsImage.record_id==rec_id
                       ).first()
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain', status_int=500)
            

        if img != None:
            imgurl = str(request.route_url('image', id=img.image_id))
        else:
            imgurl = 'No Image'


        #Until the template is finished, I'll return a string, not this.
        # I've returned the dict as a string so I can see the keys too.
        # TODO: these should be names not id's
        keys = dict(
            imgurl = imgurl,
            recid = record.record_id,
            pname = record.patient_id,
            dname = record.doctor_id,
            rname = record.radiologist_id,
            ttype = record.test_type,
            pdate = record.prescribing_date,
            tdate = record.test_date,
            diag = record.diagnosis,
            descr = record.description,)
        
        return  getModules(request, keys)
        #    'new': new, 'users':users, 'reports':reports, 'logged_in': authenticated_userid(request),)

        #return Response(keys.__str__())
        #return keys
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

    """
    img_id = request.matchdict['id']
    if (img_id == 'new'):
        return Response("Create new image")
   
    try:
        # TODO: no db stuff in views
        img = DBSession.query(PacsImage).filter(PacsImage.image_id==img_id).first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

    if img:
        if 'size' in request.GET:
            size = "r"
            size = request.GET['size']
            if size == 't':
                resp = img.thumbnail
            elif size == 'r':
                resp = img.regular_size
            elif size == 'f':
                resp = img.full_size
            else:
                resp = img.regular_size
        else:    
            resp = img.regular_size
            #resp = 'default: regular_size'
        return Response(resp)
    else:
        return Response('Image Not Found')
    """

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



