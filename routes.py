import webapp2

from handlers.core import *

route_list = [
	(r'^/', IndexHandler),
	(r'^/login', LoginHandler),
	(r'^/listas', ListsHandler),
	(r'^/alunos', UsersHandler),
	(r'^/submissoes', SubmissionsHandler),
	(r'^/submeter', SubmitHandler),
	(r'^/erro', ErrorHandler),
	(r'^/download', DownloadHandler),

]