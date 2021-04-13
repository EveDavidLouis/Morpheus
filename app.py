from tornado import web, ioloop
from motor.motor_tornado import MotorClient

from server import config , pubsub

import os

import logging
logger = logging.getLogger('app')
logging.basicConfig(level=logging.info)

class Application(web.Application):

	def __init__(self):

		handlers = [
			(r"/images/(.*)"    ,web.StaticFileHandler, {"path": "docs/images"}),
			(r"/templates/(.*)" ,web.StaticFileHandler, {"path": "docs/templates"}),
			(r"/styles/(.*)"    ,web.StaticFileHandler, {"path": "docs/styles"}),
			(r"/scripts/(.*)"   ,web.StaticFileHandler, {"path": "docs/scripts"}),
			(r'/iss', pubsub.Subscription, dict(publisher=pubsub.ISS_Publisher(db))),
			(r'/copilot/(.*)', pubsub.Copilot_Subscriber),
			(r'/', MainHandler)]
		
		settings = dict(	
			cookie_secret=config.server['secret'],
			#template_path=os.path.join(os.path.dirname(__file__), "server/templates"),
			static_path=os.path.join(os.path.dirname(__file__), "docs"),
			static_url_prefix = "/static/",
			xsrf_cookies=False,
			debug=False,
			autoreload=True
		)
		
		super(Application, self).__init__(handlers, **settings)
		
		logger.warning(config.server['host'] + ':' + str(config.server['port']))
		
		self.listen(config.server['port'],config.server['host'])

class MainHandler(web.RequestHandler):
	def get(self):
		self.render('docs/index.html')

if __name__ == "__main__":

	#application
	db = MotorClient(config.mongodb['url'])[config.mongodb['db']]

	app = Application()
	app.settings['db'] = db

	#start IOloop
	ioloop.IOLoop.current().start()