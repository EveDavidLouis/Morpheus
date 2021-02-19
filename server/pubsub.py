from tornado import ioloop, gen, httpclient
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from tornado.queues import Queue

from motor.motor_tornado import MotorClient

import json

import logging
logger = logging.getLogger('pubsub')
logging.basicConfig(level=logging.INFO)

class Publisher(object):
	"""Handles new data to be passed on to subscribers."""
	def __init__(self,db):
		self.messages = Queue()
		self.subscribers = set()
		self.client = httpclient.AsyncHTTPClient()
		self.db = db

		ioloop.IOLoop.current().spawn_callback(self.produce)
		ioloop.IOLoop.current().spawn_callback(self.publish)

	def register(self, subscriber):
		self.subscribers.add(subscriber)

	def deregister(self, subscriber):
		self.subscribers.remove(subscriber)

	async def submit(self, message):
		self.messages.put(message)

	async def publish(self):
		async for message in self.messages :
			try:
				if len(self.subscribers) > 0:
					for subscriber in self.subscribers: 
						await subscriber.submit(message)
			finally:
				self.messages.task_done()

	async def asyncFetch(self,request):
		response = await self.client.fetch(request['url'],validate_cert=False,raise_error=False,**request['kwargs'])
		return response 

class Subscription(WebSocketHandler):
	"""Websocket for subscribers."""
	def initialize(self, publisher):
		self.publisher = publisher
		self.messages = Queue()
		self.finished = False

	async def open(self):
		#logger.warning("New subscriber.")
		self.publisher.register(self)
		await self.run()

	def on_close(self):
		self._close()        

	def _close(self):
		#logger.warning("Subscriber left.")
		self.publisher.deregister(self)
		self.finished = True

	async def submit(self, message):
		self.messages.put(message)

	async def run(self):
		while not self.finished:
			async for message in self.messages :
				try:
					self.send(message)
				finally:
					self.messages.task_done()
			
	def send(self, message):
		try:
			self.write_message(dict(response=message))
		except WebSocketClosedError:
			self._close()

class Copilot_Subscriber(WebSocketHandler):
	
	def __init__(self,db):
		self.db = db
		self.session = None

	async def open(self):
		payload = await self.process('open')
		await self.send(payload)

	async def on_message(self, message):
		if 'X-Session' in self.request.headers:
			self.session = self.request.headers['X-Session']
			payload = await self.process(message)
			await self.send(payload)			

	async def send(self, message):
		try:
			self.write_message(dict(response=message,session=self.session))
		except WebSocketClosedError:
			self._close()

	async def process(self,data):
		payload = data

		result = await self.db['message'].insert_one({'$set':data})

		return payload

	def on_close(self):
		logger.info("WebSocket closed")


class ISS_Publisher(Publisher):
	async def produce(self):
	
		#document = yield _db.pilots.find_one({'refresh_token':self.name},{'CharacterID':1,'CharacterName':1}) 	
		
		headers = {}
		url = 'http://api.open-notify.org/iss-now.json'
		request = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }

		while True:
			if len(self.subscribers) > 0:
				data = await self.asyncFetch(request)
				data = json.loads(data.body.decode())

				await self.submit(data)
			await gen.sleep(1)