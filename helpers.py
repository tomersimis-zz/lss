import os
from google.appengine.ext.webapp import template
from google.appengine.api import users

from models import *

import logging

def render(handler, template_name, context):
	path = os.path.join(os.path.join(os.path.dirname(__file__), 'templates'), template_name)
	handler.response.out.write(template.render(path, context))

def get_user(id):
	return User.all().filter('user_id = ', id).get()

def only_tutor(handler):
	def check_tutor(self, *args, **kwargs):
		guser = users.get_current_user()
		user = get_user(guser.user_id())

		if user and user.is_tutor:
			handler(self, *args, **kwargs)
		else:
			self.redirect('/')

	return check_tutor

def only_accepted(handler):
	def check_accepted(self, *args, **kwargs):
		guser = users.get_current_user()
		if guser:
			user = get_user(guser.user_id())

			if user and user.accepted:
				handler(self, *args, **kwargs)
			else:
				self.redirect('/erro')
		else:
			self.redirect('/erro')

	return check_accepted