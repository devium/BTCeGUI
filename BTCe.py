#! python3
import configparser
import http.client
import urllib
import urllib.request
import json
import hashlib
import hmac
import code
import sys
import threading
import os.path

class API:
	"""Wrapper class for BTC-e API methods."""

	def __init__(self, inipath):
		"""Initialize an API object with a path to the config file and connect to btc-e.com."""
		self.inipath = inipath

		config = configparser.ConfigParser()
		config.read(inipath)
		if not 'API' in config:
			config.add_section('API')

		self.nonce = config.getint('API', 'nonce', fallback=0) + 1
		self.secret = config.get('API', 'secret', fallback='copy API secret here').encode('ascii')
		self.key = config.get('API', 'key', fallback='copy API secret here').encode('ascii')

	def save(self):
		config = configparser.ConfigParser()
		config.read(self.inipath)
		if not 'API' in config:
			config.add_section('API')

		config.set('API', 'nonce', str(self.nonce))
		if not 'secret' in config['API']:
			config.set('API', 'secret', 'copy API secret here')
		if not 'key' in config['API']:
			config.set('API', 'key', 'copy API key here')
		with open(self.inipath, 'w+') as file:
			config.write(file)
		print('Saved API settings to {}.'.format(self.inipath))

	def request(self, method, extraparams = {}):
		"""Send an API request for method to BTC-e and return a dictionary of the return object."""
		self.nonce += 1
		params = {'method' : method, 'nonce' : self.nonce}
		params.update(extraparams)
		params = urllib.parse.urlencode(params).encode('ascii')
		mac = hmac.new(self.secret, digestmod=hashlib.sha512)
		mac.update(params)
		sign = mac.hexdigest()

		conn = http.client.HTTPSConnection('btc-e.com')
		headers = {'Content-type' : 'application/x-www-form-urlencoded', 'Key' : self.key, 'Sign' : sign}
		conn.request('POST', '/tapi', params, headers)
		response = json.loads(conn.getresponse().read().decode('utf-8'))

		return response

	def getinfo(self):
		"""Request account balance info."""
		return self.request('getInfo')

	def transhistory(self, from_ = 0, count = 1000, fromid = 0, endid = sys.maxsize, order = 'DESC', since = 0, end = sys.maxsize):
		"""Request transaction history."""
		return self.request('TransHistory', {'from' : from_, 'count' : count, 'from_id' : fromid, 'end_id' : endid, 'order' : order, 'since' : since, 'end' : end})

	def tradehistory(self, from_ = 0, count = 1000, fromid = 0, endid = sys.maxsize, order = 'DESC', since = 0, end = sys.maxsize, pair = '', active = 1):
		"""Request trade history."""
		return self.request('TradeHistory', {'from' : from_, 'count' : count, 'from_id' : fromid, 'end_id' : endid, 'order' : order, 'since' : since, 'end' : end, 'pair' : pair, 'active' : active})

	def activeorders(self, pair = ''):
		"""Request active orders."""
		return self.request('ActiveOrders')

	def trade(self, pair, type, rate, amount):
		"""Place buy/sell (type) order for amount of given currency pair at rate."""
		return self.request('Trade', {'pair' : pair, 'type' : type, 'rate' : rate, 'amount' : amount})

	def cancelorder(self, orderid):
		"""Cancel order with id orderid."""
		return self.request('CancelOrder', {'order_id' : orderid})

	@staticmethod
	def query(method, pair=''):
		"""Query a method of the public BTC-e API."""
		response = json.loads(urllib.request.urlopen('http://btc-e.com/api/3/{method}/{pair}'.format(method=method, pair=pair)).read().decode('utf-8'))
		return response

	@staticmethod
	def info():
		"""Query public info method."""
		return API.query('info')

	@staticmethod
	def ticker(pair):
		"""Query public ticker method for given currency pair."""
		return API.query('ticker', pair)

	@staticmethod
	def depth(pair):
		"""Query public depth method for given currency pair."""
		return API.query('depth', pair)

	@staticmethod
	def trades(pair):
		"""Query public trades method for given currency pair."""
		return API.query('trades', pair)