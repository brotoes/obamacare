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
    )
from .security import(
    authenticate,
    getRole,

)

import pdb

@view_config(route_name='landing', renderer='templates/landing.pt', permission='view')
def landing_view(request):
    print("landing view")
    print ('auth user', authenticated_userid(request))
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

@view_config(route_name='user_profile', renderer='templates/user_profile.pt', permission='view')
def user_profile(request):
    print ('auth user', authenticated_userid(request))
    try:
        user = DBSession.query(User).filter(User.user_name==authenticated_userid(request)).first()
        person = DBSession.query(Person).filter(Person.person_id==user.person_id).first()

    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    role = getRole(user.user_name, request)[0].split(':')[1].strip()   
    users = role == 'a'
    reports = role == 'a'
    new = role!='p'
    pdb.set_trace()
    return {'new': new, 'users':users, 'reports':reports, 'logged_in': authenticated_userid(request)}

@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    print("login")
    print ('auth user', authenticated_userid(request))
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



