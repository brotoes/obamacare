from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    )

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from obamacare.security import getRole
import pdb
import ConfigParser, os

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    #print 'breaking'
    #pdb.set_trace()

    #if (settings['sqlalchemy.url'].split(':')[1]=='file'):
    sqlalchemy_url = settings['sqlalchemy.url'].split(':')
    if(sqlalchemy_url[0].strip() == 'file'):
        parser = ConfigParser.ConfigParser()
        parser.readfp(open(os.path.expanduser(sqlalchemy_url[1].strip()[2:])))
        settings['sqlalchemy.url'] = parser.get('main', 'db.url')

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine


    authn_policy = AuthTktAuthenticationPolicy(
        'sosecret', callback=getRole, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    
    config = Configurator(settings=settings, root_factory='obamacare.models.RootFactory')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
   
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('landing', '/')
    
    # Login Module: 
    config.add_route('user_profile', '/profile')
        # ---> HTML page with the logged in user's editable info displayed
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    # Search Module
    config.add_route('home', '/home')
        # ---> HTML page with the user's current records
    config.add_route('record', '/record/{id}')
        # ---> HTML page with the record and image info for rec_id=id
    #config.add_route('person_info', '/person/{id}')
        # ---> HTML page with the info with p_id=id

    config.add_route('image', '/i/{id}') 
        # ---> JPEG matching id and optionally ?s=[t,r,f] 

    config.add_route('get', '/get/{type}')
    config.add_route('user', '/user/{user_name}')
   

    config.add_route('help', '/help') #this is a fake page :P It's from the scaffold I just use it for reference 
    config.scan()
    return config.make_wsgi_app()
