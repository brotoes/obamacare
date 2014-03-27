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

from StringIO import StringIO
from PIL import Image
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )
from .security import(
    authenticate,
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

def mess_cat(cur_mess, new_mess, allow_duplicates=False):
    print "hello"
    if not cur_mess:
        return new_mess
    if cur_mess == '':
        return new_mess
    if new_mess in cur_mess and not allow_duplicates:
        return cur_mess

    return cur_mess + '</br>' + new_mess

def format_phone(phone):
    if phone == None:
        return None

    phone = [x for x in phone if x in digits]

    if phone == '':
        return phone

    if len(phone) >= 7:
        return ''.join(phone)
    else:
        return 'BAD FORMAT'

def format_email(email):
    if not email:
        return None
    parts = email.split('@')
    if len(parts) != 2:
        return 'BAD FORMAT'
    user = parts[0]
    domain = parts[1]
    if len(user.split('.')) != 1:
        return 'BAD FORMAT'
    if len(domain.split('.')) < 2:
        return 'BAD FORMAT'
    return email

def format_date(date):
    if date == None:
        return None

    date = [x for x in date if x in digits]

    if len(date) != 8:
        return None
    else:
        return ''.join(date[0:3]) + '-' + ''.join(date[4:5]) + \
        '-' + ''.join(date[6:7])

def format_name(first, last):
    if not first:
        first = "Unknown"
    else:
        first = first[0].upper() + first[1:]
    first.strip()
    if not last:
        last = "Unknown"
    else:
        last = last[0].upper() + last[1:]
    first.strip()

    return last + ", " + first
   
def get_standard_keys(request, keys = None):
    if not keys:
        keys = {}
    
    user = authenticated_userid(request)
    
    if not user:
        return keys

    keys['logged_in'] = user
    keys['displaysuccess'] = None
    keys['displayerror'] = None

    return keys


# jpeg  to convert what we read in from an image in binary for the db
def jpeg_toBinary(img):
    img_stream = StringIO()
    img_stream.seek(0)
    img.save(img_stream, format="JPEG")

    return img_stream.getvalue()
