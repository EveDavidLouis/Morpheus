from tornado import ioloop, gen, httpclient
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from tornado.queues import Queue

from motor.motor_tornado import MotorClient

import json, yaml

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
	def check_origin(self, origin):
		return True
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
	
	async def open(self,session):
		logger.info('a wild pilot logged in')
		self.session = session
		self.mongodb =  self.settings['db']
		self.airplane = 'PA28'
		self.checklist = ''
		self.waitWord = None
		self.q = dict(status='OPEN',data='')
		#self.close()
	
	def check_origin(self, origin):
		return True

	async def on_message(self, message):
		logger.info('somebody says:' + message)
		payload = await self.process(message)
		await self.send(payload)			

	async def send(self, message):
		logger.info('copilot says:' + message)
		try:
			self.write_message(dict(response=message,session=self.session))
		except WebSocketClosedError:
			self.close()

	async def process(self,data):
		result = await self.settings['db']['message'].update_one({'message':data},{'$inc': {'count': 1}},upsert=True)
		payload = ''
		if 'checklist' in data:
			self.checklist = data.replace(' checklist', '').upper()
			self.q = self.loadchecklist(self.airplane,self.checklist)
			if self.q['status'] == 'OK':
				payload = 'Loading the ' + data
			else:
				payload = self.q['data']

		elif self.q['status'] == 'OK' and len(self.q['data']) > 0 :
			
			if 'ANNOUNCE' in self.q['data'][0] :
				payload +=  self.q['data'][0]['ANNOUNCE']

			elif 'NEXT' in self.q['data'][0] :
				payload += self.checklist + ' checklist complete, next checklist will be ' + self.q['data'][0]['NEXT']
				waitingFor = ''
			else:
				logger.warning(self.q['data'][0])
				for k,v in self.q['data'][0].items():
					self.waitWord = v
					payload += k + '............' + v

			self.q['data'].pop(0)
		elif 'help' in data:
			payload = 'You could ask me to load a specific checklist. For example say "STARTING ENGINE CHECKLIST"'
		elif any(x in data for x in ['hello','hi']):
			payload = 'Hello, how are you doing today?'
		else:
			payload = 'you said:' + data + '. But i am not sure how to respond to that yet.'
		return payload
	
	def loadchecklist(self,airplane,checklist):
		with open('./docs/checklists.yaml') as file:
			data = yaml.load(file)
		if airplane.upper() in data:
			if checklist.upper() in data[airplane.upper()]['CHECKLISTS']:
				return dict(status='OK',data=[d for d in data[airplane]['CHECKLISTS'][checklist.upper()]])
			else:
				return dict(status='ERROR',data='I can not find the '+checklist+' checklist for ' + airplane + ' aircraft')
		else:
			return dict(status='ERROR',data='I have no checklist for ' + airplane + ' aircraft')

	def on_close(self):
		logger.info("WebSocket closed")

class ISS_Publisher(Publisher):
	
	def __init(self):
		super().__init()
		self.session = None
		
	async def produce(self):
	
		headers = {}
		url = 'http://api.open-notify.org/iss-now.json'
		request = { 'kwargs':{'method':'GET','headers':headers} , 'url':url }

		while True:
			if len(self.subscribers) > 0:
				data = await self.asyncFetch(request)
				data = json.loads(data.body.decode())

				await self.submit(data)
			await gen.sleep(1)
