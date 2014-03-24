from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    String,
    CHAR,
    Date,
    BLOB,
    ForeignKey,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.security import (
    Allow,
    Everyone,
)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class RootFactory(object):
    __acl__ = [ (Allow, 'group:a', 'view'),
		(Allow, 'group:d', 'view'),
        (Allow, 'group:a', 'admin'),
        (Allow, 'group:p', 'view'),
        (Allow, 'group:r', 'view') ]
    def __init__(self, request):
        #print ('root fac', self.__acl__)
        pass

class MyModel(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    value = Column(Integer)

    def __init__(self, name, value):
        self.name = name
        self.value = value

class Role(Base):
    __tablename__ = 'roles'
    role = Column(CHAR(1), primary_key=True, nullable=False)
    name = Column(String(128), nullable=False)

    def __init__(self, role, name):
        self.role = role
        self.name = name
        
    def __repr__(self):
        return str(('role:', self.role, 'name:', self.name))

class Person(Base):
    __tablename__ = 'persons'
    person_id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String(24), nullable=False)
    last_name = Column(String(24), nullable=False)
    address = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    phone = Column(CHAR(10), nullable=False)

    def __init__(self, f_name, l_name, addr, email, phone, id=None ):
        self.first_name = f_name
        self.last_name = l_name
        self.address = addr
        self.email = email
        self.phone = phone
        if (id!=None):
            self.person_id=id

    def __repr__ (self):
        return str(('id: ', self.person_id, ', f_name: ', self.first_name, 
            ', l_name: ', self.last_name, ', addr: ', self.address, 
            ', email: ', self.email, ', phone: ', self.phone)) 

class User(Base):
    __tablename__= 'users'
    user_name = Column(String(24), nullable=False, primary_key=True)
    password = Column(String(24), nullable=False)
    role = Column(CHAR(1), ForeignKey('roles.role'), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=False, autoincrement=False)
    date_registered = Column(Date(), nullable=False)

    def __init__(self, user, pwd,role, registered, id=None):
        self.user_name = user
        self.password = pwd
        self.role = role
        self.date_registered = registered

        if (id != None):
            self.person_id = id

    def __repr__(self):
        return str(('id: ', self.person_id, ', user: ', self.user_name, 
            ', password: ', self.password, ', role: ', self.role, 
            ', registered: ', self.date_registered))

class FamilyDoctor(Base):
    __tablename__ = 'family_doctor'
    doctor_id = Column(Integer, ForeignKey("persons.person_id"), primary_key=True)
    patient_id = Column(Integer, ForeignKey("persons.person_id"), primary_key=True)

    def __init__(self, doc, pat):
        self.doctor_id = doc
        self.patient_id = pat

    def __repr__(self):
        return str(('doc: ', self.doctor_id, ', patient_id: ', self.patient_id))

class RadiologyRecord(Base):
    __tablename__ = 'radiology_records'
    record_id  = Column(Integer, primary_key=True, nullable=False)
    patient_id = Column(Integer, ForeignKey('persons.person_id'), nullable=False)
    doctor_id  = Column(Integer, ForeignKey('persons.person_id'), nullable=False)
    radiologist_id = Column(Integer, ForeignKey('persons.person_id'), nullable=False)
    test_type  = Column (String(24), nullable = False)
    prescribing_date = Column(Date, nullable=False)
    test_date  = Column(Date, nullable=False)
    diagnosis  = Column(String (128))
    description  = Column (String(1024))

    def __init__(self, pat, doc, radi, ttype, p_date, t_date, diag, descr, record_id=None):
        if record_id != None:
            self.record_id = record_id
        self.patient_id = pat
        self.doctor_id = doc
        self.radiologist_id = radi
        self.test_type = ttype
        self.prescribing_date = p_date
        self.test_date = t_date
        self.diagnosis = diag
        self.description = descr


class PacsImage(Base):
    __tablename__ = 'pacs_images'
    # image_id NEEDS to be the first column as then sqlalchemy will set autoinc on it
    image_id = Column(Integer, primary_key=True)
    record_id = Column(Integer, primary_key=True, nullable=False)
    
    thumbnail = Column(BLOB)
    regular_size = Column(BLOB)
    full_size = Column(BLOB)

    def __init__(self, rec_id, thumb, reg, full, img_id=None):
        self.record_id = rec_id
        self.image_id = img_id
        self.thumbnail = thumb
        self.regular_size = reg
        self.full_size=full



Index('my_index', MyModel.name, unique=True, mysql_length=255)
