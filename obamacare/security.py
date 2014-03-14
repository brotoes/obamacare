from .models import (
	 DBSession,
	Role,
	Base,
	User,
	Person,
)
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )

from sqlalchemy.exc import DBAPIError

def getRole(username, request):
	print ("getRole called: ", username)	
	try:
		user = DBSession.query(User).filter_by(user_name=username).first()
	except DBAPIError:
		return none
	print ('user: ', user)
	print ['group:'+user.role]

	return ['group:'+user.role]


def authenticate(user_name, password):
	try:
		user = DBSession.query(User).filter_by(user_name=user_name).first()
	except DBAPIError:
		return False
	finally:
		if user == None:
			return None;
	print (user)

	if (str(user.password) == password):
		return True
	else:
		return False