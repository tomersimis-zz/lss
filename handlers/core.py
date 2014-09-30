#encoding: utf-8
import webapp2

from google.appengine.api import users

from helpers import *

from google.appengine.ext import db

from models import *

import re

import logging

import json

from datetime import datetime

class IndexHandler(webapp2.RequestHandler):

    def get(self):

        user = users.get_current_user()

        if user:

            user_query = User.all().filter('user_id = ', user.user_id()).fetch(10)

            login, domain = users.get_current_user().email().split('@')

            # Register a new user to the database (checking its email domain)
            if len(user_query) == 0 and domain == "cin.ufpe.br":
                new_user = User(user_id=str(user.user_id()), login=login, email=users.get_current_user().email(), 
                    accepted = False, is_tutor = False)
                new_user.save()

            self.redirect('/submeter')


        render(self, 'login.html', {})


class LoginHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect(users.create_login_url("/"))


class ListsHandler(webapp2.RequestHandler):

    @only_tutor
    def get(self):

        user = users.get_current_user()

        lists = List.all().order('-name').fetch(100)

        now = datetime.now()
        for list in lists:
            if list.start > now:
                list.status = 0
            elif now > list.start and now < list.end:
                list.status = 1
            else:
                list.status = 2


        context = {
            'logout_url' :  users.create_logout_url('/'),
            'user' : user,
            'lists' : lists
        }
        render(self, 'lists.html', context)

    @only_tutor    
    def post(self):
        user = get_user(users.get_current_user().user_id())

        if not user.is_tutor:
            self.redirect("/listas")

        if self.request.get('id') == '-1': #creating
            start = datetime.strptime(self.request.get('start'), "%d %B %Y - %H:%M")
            end = datetime.strptime(self.request.get('end'), "%d %B %Y - %H:%M")
            new_list = List(name=self.request.get('name'), questions=int(self.request.get('questions')), 
                start=start, end=end)
            new_list.put()
            
        else:
            list = List.get_by_id(int(self.request.get('id')))
            if list:
                if self.request.get('name'):
                    list.name = self.request.get('name')
                if self.request.get('start'):
                    list.start = datetime.strptime(self.request.get('start'), "%d %B %Y - %H:%M")
                if self.request.get('end'):
                    list.end =  datetime.strptime(self.request.get('end'), "%d %B %Y - %H:%M")
                if self.request.get('questions'):
                    list.questions = int(self.request.get('questions'))
                list.save()

        self.redirect('/listas')


class UsersHandler(webapp2.RequestHandler):
    @only_tutor
    def get(self):

        user = users.get_current_user()

        users_list = User.all().fetch(300)

        context = {
            'logout_url' :  users.create_logout_url('/'),
            'user' : user,
            'users' : users_list
        }
        render(self, 'users.html', context)

    @only_tutor
    def post(self):

        guser = users.get_current_user()

        user = get_user(guser.user_id())

        self.response.headers['Content-Type'] = 'application/json'

        success = False
        if user and user.is_tutor:
            student = get_user(self.request.get('user_id'))
            student.accepted = not student.accepted
            student.put()
            success = True
            
        response = {
            'success': success, 
            'accepted' : student.accepted
        } 
        self.response.out.write(json.dumps(response))



class SubmissionsHandler(webapp2.RequestHandler):
    @only_tutor
    def get(self):

        list = List.get_by_id(int(self.request.get('id')))

        subs = Submission.all().filter('list = ', list).order('-date').order('question').fetch(10000)

        students = User.all().filter('is_tutor = ', False).fetch(10000)

        for student in students:
            added = []
            student.submissions = []
            for sub in subs:
                if sub.user.login == student.login:
                    if not sub.question in added:
                        student.submissions.append(sub)
                        added.append(sub.question)

        context = {
            'list' : list,
            'students' : students,
            'logout_url' :  users.create_logout_url('/'),
        }
        render(self, 'submissions.html', context)


class SubmitHandler(webapp2.RequestHandler):

    def get_open_lists(self):
        lists_gt = List.all().filter('start <= ', datetime.now()).fetch(100)
        lists_lt = List.all().filter('end > ', datetime.now()).fetch(100)

        lists = []
        for list_gt in lists_gt:
            for list_lt in lists_lt:
                if list_gt.key().id == list_lt.key().id:
                    lists.append(list_lt)

        return lists

    @only_accepted
    def get(self):

        guser = users.get_current_user()

        user = get_user(guser.user_id())

        if user.is_tutor:
            self.redirect("/listas")

        lists = self.get_open_lists()

        for l in lists:

            subs = Submission.all().filter('list = ', l).order('-date').order('question').fetch(10000)

            added = []
            last_submissions = [None]*(l.questions+1)
            for sub in subs:
                if sub.user.login == user.login:
                    if not sub.question in added:
                        added.append(sub.question)
                        last_submissions[sub.question] = sub

            l.questions_set = []
            for q in range(1, l.questions+1):
                l.questions_set.append({
                    'n' : q,
                    'last': last_submissions[q]
            })


        context = {
            'lists' : lists,
        }
        render(self, 'submit.html', context)

    @only_accepted
    def post(self):

        guser = users.get_current_user()

        user = get_user(guser.user_id())

        lists = self.get_open_lists()

        if not user.accepted:
            self.redirect('/')

        list = List.get_by_id(int(self.request.get('id')))

        if list.start <= datetime.now() and list.end > datetime.now():

            for q in range(1, list.questions + 1):
                if self.request.get("question_"+str(q)):
                    question = Submission(question=q, user=user, list=list, file=db.Blob(self.request.get("question_"+str(q))), 
                        date=datetime.now())
                    question.put()

        self.redirect('/')

class ErrorHandler(webapp2.RequestHandler):
    def get(self):
        render(self, 'error.html', {})

class DownloadHandler(webapp2.RequestHandler):
    @only_tutor
    def get(self):
        id = self.request.get('id')
        submission = Submission.get_by_id(int(id))
        if submission:
            self.response.headers['Content-Disposition'] = 'attachment; filename=' + str(submission.user.login) + "_Q" + str(submission.question) + ".rar"
            self.response.headers['Content-Type'] = 'application/zip'
            self.response.out.write(submission.file)