from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    )

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from obamacare.security import getRole


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

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
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('home', '/help')
    config.scan()
    return config.make_wsgi_app()
