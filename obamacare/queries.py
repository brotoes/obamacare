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
    RadiologyRecord,
    PacsImage,
)

def get_person(person_id):
    if not person_id:
        return None
    person = DBSession.query(Person).filter(Person.person_id==person_id).first()
    return person

# TODO: Possible permission check here
def get_images(record_id):
    if not record_id:
        return None
    images = DBSession.query(PacsImage.image_id).filter(PacsImage.record_id==record_id)

    return images.all()

