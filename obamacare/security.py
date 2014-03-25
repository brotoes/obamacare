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

# returns a dict of the logged in user's modules for use with templating
# such wow..
def getModules(request, keys=None):
	if not keys:
		keys = {}
	user = authenticated_userid(request)
	if not user:
		return keys
	keys['logged_in'] = user

	role = getRole(user, request)[0].split(':')[1].strip()   
	# Give admins acces to the user management module
	users = role == 'a'	
	# Give admins acces to the reports module
	reports = role == 'a'
	# Give everyone but patients access to the new module
	new = role!='p'

	keys['users'] = users
	keys['new'] = new
	keys['reports'] = reports

	return keys


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