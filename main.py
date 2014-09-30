import webapp2
import logging

from routes import route_list

logging.getLogger().setLevel(logging.DEBUG)
application = webapp2.WSGIApplication(route_list, debug=True)