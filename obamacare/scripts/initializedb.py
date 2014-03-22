import pdb
import ConfigParser, os
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


def gen_people():
    people =(
        ('john', 'fisher', 'p', 'john'), ('wilson', 'roberts', 'd', 'wilson'), 
        ('geroge', 'washington', 'r', 'admin'), ('lisa', 'brigs', 'pd', 'wilson'),
        ('newton', 'bitches!', 'pdr', 'admin'), ('frodo', 'baggins', 'dr', 'admin'), 
        ('Thomas', 'O\'Conner', 'p', 'thomas'), ('Kevin', 'Pain', 'd', 'kevin'),
        ('Devon', 'Milkman', 'p', 'r', 'devin'), ('Peter', 'Andrews', 'p', 'peter'),
        ('Amy', 'Smith', 'p', 'amy'), ('Jason' , 'Gerogegino', 'p', 'jason'),
        ('James', 'Davidson', 'p', 'james')
        )
    admin = ('Admin', 'Obamacare', 'a', 'admin')
    with transaction.manager:
        admin = DBSession.query(Person).filter(Person.first_name=='admin').first()
        if (not admin):
            admin = Person('admin', 'obamacare', 'land of the hungry', 'admin@obamacare.ca', '7702323548')
            DBSession.add(admin)
            transaction.manager.commit()
            
            admin = DBSession.query(Person).filter(Person.first_name=='admin').first()

            DBSession.add(User('admin', 'password', 'a', datetime.date(2014, 03, 06), admin.person_id))
            
            transaction.manager.commit()
            
        for per in people:
            new_person = Person(per[3], per[1], 'something happened', str(per[1]) + '@google.com', '7308291258')
            email = new_person.email
            DBSession.add(new_person)
            transaction.manager.commit()

            new_person= DBSession.query(Person).filter(Person.email==email).first() 

            new_user = User(per[0], 'password', per[2][0], datetime.date(2014, 03, 06), new_person.person_id)
            DBSession.add(new_user)
            transaction.manager.commit()
          

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    sqlalchemy_url = settings['sqlalchemy.url'].split(':')
    if(sqlalchemy_url[0].strip() == 'file'):
        print ('fixing')
        parser = ConfigParser.ConfigParser()
        parser.readfp(open(os.path.expanduser(sqlalchemy_url[1].strip()[2:])))
        settings['sqlalchemy.url'] = parser.get('main', 'db.url')

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    Base.metadata.drop_all(engine)  
    Base.metadata.create_all(engine)

    for i,j in (('a', 'administrator'), ('p', 'patient'), ('d', 'doctor'), ('r', 'radiologist')):
        with transaction.manager:
            DBSession.add(Role(i,j))
            try: 
                DBSession.flush()
            except IntegrityError:
                print("IntegrityError")
                DBSession.rollback()
    
    gen_people()
    """ with transaction.manager:
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
            """
   
