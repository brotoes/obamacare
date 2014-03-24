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


"""
Function takes a string and cleans it by performing the following:
-First, it strips the string to remove excess whitespace
-next it removes all characters in 'remove' from the string
    except for those in 'exclude'
"""
#character lists
default_remove = [';', ')', '(']
digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

def clean(to_clean, remove=default_remove, exclude=[]):
    remove = [i for i in remove if i not in exclude]

    cleaned = to_clean.strip()
    for i in remove:
        cleaned = cleaned.replace(i, "")

    return cleaned

def format_phone(phone):
    phone = [x for x in phone if x in digits]

    if phone == '':
        return phone

    if len(phone) >= 7:
        return ''.join(phone)
    else:
        return 'BAD FORMAT'

def get_person(person_id):
    if not person_id:
        return None
    person = DBSession.query(Person).filter(Person.person_id==person_id).first()
    return person

