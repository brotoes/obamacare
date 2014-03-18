import os
import sys
import transaction
import datetime

from sqlalchemy import engine_from_config

from sqlalchemy.exc import IntegrityError
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    MyModel,
    Person,
    User,
    FamilyDoctor,
    Role,
    Base,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
  #  with transaction.manager:
        #model = MyModel(name='one', value=1)

    for i,j in (('a', 'administrator'), ('p', 'patient'), ('d', 'doctor'), ('r', 'radiologist')):
        with transaction.manager:
            DBSession.add(Role(i,j))
            try: 
                DBSession.flush()
            except IntegrityError:
                print("IntegrityError")
                DBSession.rollback()
    with transaction.manager:
        DBSession.add(Person('admin', 'obamacare', 'not reall an address', 'admin@obamacare.com', '7804929400', 0))            
        try:  
            DBSession.flush()
        except IntegrityError:
            DBSession.rollback()
        
    with transaction.manager:

        admin = DBSession.query(Person).filter_by(email='admin@obamacare.com').first()
        DBSession.add(User('admin', 'password', 'a', datetime.date(2014, 03, 06), admin.person_id))
        try:
            DBSession.flush()
        except IntegrityError:
            DBSession.rollback()

   
