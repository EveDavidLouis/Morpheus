from tornado.websocket import WebSocketHandler, WebSocketClosedError
from tornado.queues import Queue

from tornado import ioloop , httpclient

import logging
logger = logging.getLogger('pubsub')
logging.basicConfig(level=logging.INFO)

class Publisher(object):
	"""Handles new data to be passed on to subscribers."""
	def __init__(self):
		self.messages = Queue()
		self.subscribers = set()
		self.client = httpclient.AsyncHTTPClient()

		ioloop.IOLoop.current().spawn_callback(self.produce)
		ioloop.IOLoop.current().spawn_callback(self.publish)

	def register(self, subscriber):
		"""Register a new subscriber."""
		#logger.warning('Register')
		self.subscribers.add(subscriber)

	def deregister(self, subscriber):
		"""Stop publishing to a subscriber."""
		#logger.warning('Deregister')
		self.subscribers.remove(subscriber)

	async def submit(self, message):
		"""Submit a new message to publish to subscribers."""
		self.messages.put(message)

	async def publish(self):

		#logger.warning('waiting for msg')

		#while True:		
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



class Copilot(WebSocketHandler):
	async def open(self):
		payload = await self.process('open')
		await self.send(payload)

	async def on_message(self, message):
		payload = await self.process(message)
		await self.send(payload)

	async def send(self, message):
		try:
			self.write_message(dict(response=message))
		except WebSocketClosedError:
			self._close()

	async def process(self,data):
		payload = {'data':data}
		return payload

	def on_close(self):
		logger.info("WebSocket closed")
