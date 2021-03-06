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
    HelpFile,
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
    NUM_PEOPLE = 30
    people =[
        ('john', 'fisher','p'), ('wilson', 'roberts','d'), 
        ('george', 'washington', 'd'), ('lisa', 'brigs','r'),
        ('newton', 'bitches!', 'd'), ('frodo', 'baggins','p'), 
        ('Thomas', 'O\'Conner','d'), ('Kevin', 'Pain','d'),
        ('Devon', 'Milkman','r'), ('Peter', 'Andrews','d'),
        ('Amy', 'Smith','p'), ('Jason' , 'Georgegino','p' ),
        ('James', 'Davidson', 'p' )
        ]
    names = list(set(random.sample(get_names(), NUM_PEOPLE)))
    users = list(set(random.sample(get_usernames(), len(names)*5)))

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

        for i in range(0, len(names)):
            name = names.pop()
            person = Person(name[0], name[1], 'randomly genereated...', name[0] +"."+name[1]+"@gmail.com" ,'7308291258')
            email = person.email
            DBSession.add(person)
            transaction.manager.commit()
            
            new_person= DBSession.query(Person).filter(Person.email==email).first() 

            sample = random.sample(users, random.randint(1,2))
            for username in sample:
                new_user = User(username, "password", "p", gen_randDate(), new_person.person_id)
                # Since all the randoms are patients I'll them all up with family doctors :O
                DBSession.add(new_user)
                users.remove(username)
            transaction.manager.commit()
        docs = DBSession.query(Person).filter(Person.person_id==User.person_id, User.role=='d').all()
        
        for patient in DBSession.query(Person).filter(Person.person_id==User.person_id, User.role=='p'):
            for doc in random.sample(docs, random.randint(1,5)):
                DBSession.add(FamilyDoctor(doc.person_id, patient.person_id))
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

def gen_helpfiles():
    helpdocs = { "Install Instructions" : """Install pyramid version 1.4.5. It works on various platforms and the specific instructions can be found here: http://docs.pylonsproject.org/projects/pyramid/en/1.4-branch/narr/install.html\n\n
Setup a mysql database obamacare with the user obamacare.  The password can be found in the connection string. 
Using pip in the virtual env created during the install issue pip install pillow mysql-python
Extract the project source in the virtual env created during the pyramid install
run bin/python setup.py develop to setup the project dependencies
run bin/initialize_obamacare_db development.ini to set up the tables and fill the database with images
run bin/pserve development.ini to start up the webapp
Navigate to 0.0.0.0:5656/home in your browser to get started
""",
    "Search Module" : """Upon logging in, you will be taken to this page. Here you will see all records that you have permission to access. These results may be filtered using the forms at the top.-The 'filter' form will yield only results containing all provided keyworks-The 'fter' form will yield only records where the test date is after this date-Similarly, the 'before' form will yield only records where the test date is before this date.-Finally, the dropdown menu will allow you to choose how the results are sorted. Newest and         Oldest sort by the test date, and 'Rank' will sort by the frequency of the keywordsTo view the entire record, simply click on the row and you will be taken to that record's page.""",
    "Login Module" : """After logging in, you may click on the 'Profile' tab to see all of your information as a user. This information is all editable. At the top of the page, you will see your personal information, such as your name and address. Below this, you may update your password. Next, you'll see a list of users you can log in as. Finally, you can see a list of your family doctors or patients. The'plus' button will bring up a list of doctors you can add.""",
    "Reports Module" : """The 'Reports' tab, by default, will show you all patients along with a selection of their information. If you wish to view the patient's page and information, you may click on their respective rows.This list of users can be narrowed down with the fields at the top, by diagnosis and date.""",
    "Olap Module" : """The 'OLAP' tab shows you a list of patients and every type of test they have undergone in each year, and how many images there are under each of these entries. The results of this page may be fine-tuned using the fields at the top.If you wish to only see the results for one particular user, use the people picker (the button with an ellipsis). If you wish to not have results grouped by user, and instead see totals, remove the asterisk from the search field. To see results for a single test type, enter it into the test type field. To not group by any test type, remove the asterisk from the field. Finally, to group counts by year, month, or week, select the corresponding option from the dropdown menu. If 'None' is selected, it will not group by any time period.For example, leaving all fields blank will give the total count of images in the entire database. Leaving all fields blank, save for patient ID with an asterisk, you will see the number of images each patient has.""",
    "User Module" : """This shows a list of all users who may access the database, sorted by the ids of the person they are attached to.  To filter this list down, by name, enter a name into the filter field.If you wish to edit a user, simply click on a row in that list, and you are brought to a page allowing you to edit their information.""",


    }
    with transaction.manager:
        for topic in helpdocs:
            DBSession.add(HelpFile(topic, helpdocs[topic]))
        transaction.manager.commit()

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

    numdocs = len(doctors)-1
    numradis = len(radis)-1
    numpaits = len(patients)-1

    num_records = 10
    with transaction.manager:
        for patient in patients:
            for i in range(0,random.randint(1,num_records)):
                DBSession.add(RadiologyRecord(
                    patient[0].person_id, 
                    doctors[random.randint(0,numdocs)][0].person_id, 
                    radis[random.randint(0,numradis)][0].person_id,
                    test_types[random.randint(0,len(test_types)-1)],
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

    DBSession.execute("DROP TABLE IF EXISTS helpfiles")
    Base.metadata.create_all(engine)
    gen_helpfiles()

    """ DBSession.execute("DROP TABLE IF EXISTS users")
    DBSession.execute("DROP TABLE IF EXISTS family_doctor")
    DBSession.execute("DROP TABLE IF EXISTS roles")
    DBSession.execute("DROP TABLE IF EXISTS radiology_records")
    DBSession.execute("DROP TABLE IF EXISTS persons")
    DBSession.execute("DROP TABLE IF EXISTS pacs_images")
    
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
    """