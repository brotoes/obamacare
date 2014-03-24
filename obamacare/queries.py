import pdb
import sys
import transaction
import datetime
import random

from sqlalchemy import engine_from_config

from sqlalchemy.exc import IntegrityError
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from .models import (
    DBSession,
    User,
    Person,
)

def get_person(person_id):
    if not person_id:
        return None
    person = DBSession.query(Person).filter(Person.person_id==person_id).first()
    return person

