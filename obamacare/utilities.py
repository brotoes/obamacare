import pdb
import sys
import transaction
import datetime
import random
import operator

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


"""
This function takes a string (from GET or POST requests) and removes
any superfluous, error prone, or potentially malicious characters from it
so as to prevent formatting problems, errors, or code injections.
"""
def clean(to_clean, remove=default_remove, exclude=[]):
    remove = [i for i in remove if i not in exclude]

    cleaned = to_clean.strip()
    for i in remove:
        cleaned = cleaned.replace(i, "")

    return cleaned


"""
This function takes a phone number (a string) and ensures that it is formatted
correctly for use with database information
"""
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

"""
This function takes an email address and ensures that it is formatted
correctly for use with database information
"""
def format_email(email):
    if not email:
        return None
    parts = email.split('@')
    if len(parts) != 2:
        return 'BAD FORMAT'
    user = parts[0]
    domain = parts[1]
    if len(domain.split('.')) < 2:
        return 'BAD FORMAT'
    return email

"""
this function takes a date and ensures that it is formatted correctly for use
with database information
"""
def format_date(date):
    if date == None:
        return None

    date = [x for x in date if x in digits]

    if len(date) != 8:
        return None
    else:
        return ''.join(date[0:3]) + '-' + ''.join(date[4:5]) + \
        '-' + ''.join(date[6:7])

"""
This function takes a first and last name and formats them into a single string,
'Last, First'
"""
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
   

"""
Simplifies work of what keys need to be passed from views to templates for
rendering
"""
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

"""
Takes a list of tuples, and applies filter to it

returns list with tuples ranked. rank is appended to end of tuple.
list is also sorted by rank. Keywords will be searched for in columns specified
by the cols list. Use 'None' to ignore a column

Ranking:
if method='freq', it will be ranked by 
    
    Rank(record_id) = 6*frequency(patient_name)
    + 3*frequency(diagnosis) + frequency(description)

for to identify columns, it will use col_names

if method='old', oldest records will be listed first
if method='new', newest records will be listed first
for the above, the column index in date_col will be removed from the tuple for
    purposes of searching and used for date-based sorting
"""
def apply_filter(filter_str, items, cols, method='freq', delimit=' '):
    terms = filter_str.split(delimit)
    result = []
    for item in items:
        name_count = 0
        diag_count = 0
        desc_count = 0
        for col_ind in range(len(cols)):
            title = cols[col_ind]
            if title != None and 'date' not in title:
                count = 0
                for term in terms:
                    count += item[col_ind].upper().count(term.upper())
                if 'name' in title:
                    name_count += count
                if 'diag' in title:
                    diag_count += count
                if 'desc' in title:
                    desc_count += count
        rank = 6*name_count + 3*diag_count + desc_count
        if rank > 0:
            if method == 'freq':
                result.append(item + (rank,))
            else:
                result.append(item)
    sort_col = 0
    for i in range(len(cols)):
        if cols[i] != None and 'date' in cols[i]:
            sort_col = i
            break

    if method == 'new':
        result.sort(key=operator.itemgetter(sort_col), reverse=True)
        final = []
        for i in range(len(result)):
            final.append(result[i] + (len(result) - i,))
        result = final
    elif method == 'old':
        result.sort(key=operator.itemgetter(sort_col))
        final = []
        for i in range(len(result)):
            final.append(result[i] + (len(result) - i,))
        result = final
    elif method == 'freq':
        result.sort(key=operator.itemgetter(-1), reverse=True)
    else:
        result = None

    return result

"""
takes a cube returned by get_cube and returns the count column corresponding to
arguments
"""
def cube_select(cube, pid=None, year=None, month=None, week=None, ttype=None):
    for row in cube:
        if (pid == row[0] and
            year == row[1] and
            month == row[2] and
            week == row[3] and
            ttype == row[4]):
            return row[5]

    return None
