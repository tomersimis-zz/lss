from google.appengine.ext import db

import datetime


class User(db.Model):
	user_id = db.StringProperty(required=True)
	email = db.StringProperty(required=True)
	login = db.StringProperty(required=True)
	is_tutor = db.BooleanProperty()
	accepted = db.BooleanProperty()

class List(db.Model):
	name = db.StringProperty(required=True)
	start = db.DateTimeProperty()
	end = db.DateTimeProperty()
	questions = db.IntegerProperty()

	def __unicode__(self):
		return self.name

class Submission(db.Model):
	question = db.IntegerProperty(required=True)
	user = db.ReferenceProperty(User)
	list = db.ReferenceProperty(List)
	file = db.BlobProperty(required=True)
	date = db.DateTimeProperty(required=True)