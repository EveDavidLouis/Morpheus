from tornado import web , gen , ioloop

from server import config , pubsub

import os , random , json

import logging
logger = logging.getLogger('app')
logging.basicConfig(level=logging.INFO)

class Application(web.Application):

	def __init__(self):

		self.iss = ISS()

		handlers = [
			(r"/images/(.*)"    ,web.StaticFileHandler, {"path": "docs/images"}),
			(r"/templates/(.*)" ,web.StaticFileHandler, {"path": "docs/templates"}),
			(r"/styles/(.*)"    ,web.StaticFileHandler, {"path": "docs/styles"}),
			(r"/scripts/(.*)"   ,web.StaticFileHandler, {"path": "docs/scripts"}),
			(r'/iss', pubsub.Subscription, dict(publisher=self.iss)),
			(r'/copilot', pubsub.Copilot, dict()),
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

class ISS(pubsub.Publisher):
	async def produce(self):
		while True:
			#data =[random.randint(0, 9),random.randint(0, 9)] 
			headers = {}
			url = 'http://api.open-notify.org/iss-now.json'
			request = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }
			if len(self.subscribers) > 0:
				data = await self.asyncFetch(request)
				data = json.loads(data.body.decode())
				await self.submit(data)
			await gen.sleep(1)
	
if __name__ == "__main__":
	

	#application
	app = Application()

	#start IOloop
	ioloop.IOLoop.current().start()
