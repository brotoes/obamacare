import pdb
import ConfigParser, os
import sys
import transaction
import datetime
import random
import urllib
import re
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
    RadiologyRecord,
    PacsImage,
    )

from PIL import Image

from ..utilities import jpeg_toBinary

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def get_names():
    names = []
    role = ['p', 'd', 'r']
    fd = open("temp-names.txt", "r")
    for line in fd:
        parts = line.strip().split(" ")
        if len(parts) >= 2:
            names.append((parts[0], parts[1]))
    fd.close()

    return names    

def get_usernames():
    
    urllib.urlretrieve("http://socialblade.com/digg/top1000users.html","tmp-users.html")
    f = open ("tmp-users.html", 'r')
    data = f.read()
    f.close()

    names =re.findall(r'user=[^"]+">([^<]+)',data,re.I)

    return names

def gen_people():
    NUM_PEOPLE = 70
    people =[
        ('john', 'fisher', 'p', 'john'), ('wilson', 'roberts', 'd', 'wilson'), 
        ('george', 'washington', 'r', 'admin'), ('lisa', 'brigs', 'pd', 'wilson'),
        ('newton', 'bitches!', 'pdr', 'admin'), ('frodo', 'baggins', 'dr', 'admin'), 
        ('Thomas', 'O\'Conner', 'p', 'thomas'), ('Kevin', 'Pain', 'd', 'kevin'),
        ('Devon', 'Milkman', 'r', 'devin'), ('Peter', 'Andrews', 'p', 'peter'),
        ('Amy', 'Smith', 'p', 'amy'), ('Jason' , 'Georgegino', 'p', 'jason'),
        ('James', 'Davidson', 'p', 'james')
        ]

    names = random.sample(get_names(), NUM_PEOPLE)
    users = random.sample(get_usernames(), NUM_PEOPLE*5)
   

    for i in range(0, len(names)):
        name = names.pop()
        sample = random.sample(users, random.randint(1,5))
        for username in sample:
            people.append((name[0], name[1], 'p', username))
            users.remove(username)
    print people

    pdb.set_trace()


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
            new_person = Person(per[0], per[1], 'something happened', str(per[1]) + '@google.com', '7308291258')
            email = new_person.email
            DBSession.add(new_person)
            transaction.manager.commit()

            new_person= DBSession.query(Person).filter(Person.email==email).first() 

            new_user = User(per[0].lower(), 'password', per[2][0], datetime.date(2014, 03, 06), new_person.person_id)
            DBSession.add(new_user)
            transaction.manager.commit()

def gen_images():
    #pdb.set_trace()
    path = os.path.expanduser("initimages/")
    files = os.listdir(path)
    for f in files:
        try:
            fd = open(path+f, "r")
            img = Image.open(fd)
            thumb = img.copy()
            reg = img.copy()

            thumb.thumbnail((60,60), Image.ANTIALIAS)
            reg.thumbnail((200,200), Image.ANTIALIAS)

            img.thumbnail = jpeg_toBinary(thumb)
            img.regular_size = jpeg_toBinary(reg)
            img.full_size = jpeg_toBinary(img)

        except:
            print 'failed to load image from \'%s\'' % (path+f)
            continue
        with transaction.manager:
            records = DBSession.query(RadiologyRecord).all()
            img.seek(0)
            DBSession.add(PacsImage(records[random.randrange(len(records))].record_id, 
                img.thumbnail, img.regular_size, img.full_size))

    print path


def gen_randDate(start=datetime.datetime(1962,1,1,0,0,0)):
    end = datetime.datetime(2014,12,26,23,59,59)
    
    year = start.year + random.randint(1, end.year-start.year+1)-1
    month = start.month + random.randint(1, end.month-start.month+1)-1
    day = start.day + random.randint(1, end.day-start.day+1)-1
    
    hour = start.hour + random.randint(1, end.hour-start.hour+1)-1
    minute = start.minute + random.randint(1, end.minute-start.minute+1)-1
    second = start.second + random.randint(1, end.second-start.second+1)-1
    
    ret = datetime.datetime(year,month,day,hour,minute,second)
    return ret.date().isoformat()

def gen_records():
    test_types = ['invasive', 'scary', 'painful', 'harmles...really', 'smelly', 'chronic', 'geo physical',
                'exothemeric', 'deadly', 'doctor gibberish']
    diags = ['death', 'mild stench', 'chronic fever', 'successful', 'ordinary', 'normal' ,'typical', 'usual',
            'unhealthy', 'too tall for tests', 'too short for tests', 'too FAT!', 'IT\'s an ALIEN!!']
    descr = ["""It sportsman earnestly ye preserved an on. Moment led family sooner cannot her window pulled any. Or raillery if improved landlord to speaking hastened differed he. Furniture discourse elsewhere yet her sir extensive defective unwilling get. Why resolution one motionless you him thoroughly. Noise is round to in it quick timed doors. Written address greatly get attacks inhabit pursuit our but. Lasted hunted enough an up seeing in lively letter. Had judgment out opinions property the supplied.""",
            """Repulsive questions contented him few extensive supported. Of remarkably thoroughly he appearance in. Supposing tolerably applauded or of be. Suffering unfeeling so objection agreeable allowance me of. Ask within entire season sex common far who family. As be valley warmth assure on. Park girl they rich hour new well way you. Face ye be me been room we sons fond.""",
            """Oh acceptance apartments up sympathize astonished delightful. Waiting him new lasting towards. Continuing melancholy especially so to. Me unpleasing impossible in attachment announcing so astonished. What ask leaf may nor upon door. Tended remain my do stairs. Oh smiling amiable am so visited cordial in offices hearted.""",
            """Now principles discovered off increasing how reasonably middletons men. Add seems out man met plate court sense. His joy she worth truth given. All year feet led view went sake. You agreeable breakfast his set perceived immediate. Stimulated man are projecting favourable middletons can cultivated.""",
            """Frankness applauded by supported ye household. Collected favourite now for for and rapturous repulsive consulted. An seems green be wrote again. She add what own only like. Tolerably we as extremity exquisite do commanded. Doubtful offended do entrance of landlord moreover is mistress in. Nay was appear entire ladies. Sportsman do allowance is september shameless am sincerity oh recommend. Gate tell man day that who.""",
            """In friendship diminution instrument so. Son sure paid door with say them. Two among sir sorry men court. Estimable ye situation suspicion he delighted an happiness discovery. Fact are size cold why had part. If believing or sweetness otherwise in we forfeited. Tolerably an unwilling arranging of determine. Beyond rather sooner so if up wishes or.""",
            """Bringing so sociable felicity supplied mr. September suspicion far him two acuteness perfectly. Covered as an examine so regular of. Ye astonished friendship remarkably no. Window admire matter praise you bed whence. Delivered ye sportsmen zealously arranging frankness estimable as. Nay any article enabled musical shyness yet sixteen yet blushes. Entire its the did figure wonder off.""",
            """An so vulgar to on points wanted. Not rapturous resolving continued household northward gay. He it otherwise supported instantly. Unfeeling agreeable suffering it on smallness newspaper be. So come must time no as. Do on unpleasing possession as of unreserved. Yet joy exquisite put sometimes enjoyment perpetual now. Behind lovers eat having length horses vanity say had its.""",
            ]

    doctors = DBSession.query(Person, User).filter(Person.person_id==User.person_id).filter(User.role=='d').all()
    radis = DBSession.query(Person, User).filter(Person.person_id==User.person_id).filter(User.role=='r').all()
    patients  = DBSession.query(Person, User).filter(Person.person_id==User.person_id).filter(User.role=='p').all()

    num_records = 100
    with transaction.manager:
        for i in range(0,num_records):
            # pat, doc, radi, ttype, p_date, t_date, diag, descr, record_id=None):
            DBSession.add(RadiologyRecord(
                patients[random.randrange(len(patients))][0].person_id, 
                doctors[random.randrange(len(doctors))][0].person_id, 
                radis[random.randrange(len(radis))][0].person_id,
                test_types[random.randrange(len(test_types))],
                gen_randDate(),
                gen_randDate(),
                diags[random.randrange(len(diags))],  
                descr[random.randrange(len(descr))]))
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

    engine = engine_from_config(settings, 'sqlalchemy.',)
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
    gen_records()
    gen_images()
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
   
