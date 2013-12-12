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
import re

class API:
	"""Wrapper class for BTC-e API methods."""

	def __init__(self, inipath):
		"""Initialize an API object with a path to the config file and connect to btc-e.com."""
		self.inipath = inipath
		self.nonce = 0

		config = configparser.ConfigParser()
		config.read(inipath)
		if not 'API' in config:
			config.add_section('API')

		self.secret = config.get('API', 'secret', fallback='copy API secret here').encode('ascii')
		self.key = config.get('API', 'key', fallback='copy API secret here').encode('ascii')

	def request(self, method, extraparams = {}):
		"""Send an API request for method to BTC-e and return a dictionary of the return object."""
		self.nonce += 1
		params = {'method' : method, 'nonce' : self.nonce}
		params.update(extraparams)
		params = urllib.parse.urlencode(params).encode('ascii')
		mac = hmac.new(self.secret, digestmod=hashlib.sha512)
		mac.update(params)
		sign = mac.hexdigest()

		response = ''
		try:
			conn = http.client.HTTPSConnection('btc-e.com', timeout=5)
			headers = {'Content-type' : 'application/x-www-form-urlencoded', 'Key' : self.key, 'Sign' : sign}
			conn.request('POST', '/tapi', params, headers)
			response = conn.getresponse().read().decode('utf-8')
		except Exception as err:
			response = '{{"success" : 0, "error" : "{}"}}'.format(err)
		j = {}
		try:
			j = json.loads(response)
			if j['success'] == 0:
				matchnonce = re.match(r'invalid nonce parameter; on key:(\d+)', j['error'])
				if matchnonce:
					self.nonce = int(matchnonce.group(1))
					return self.request(method, extraparams)
		except ValueError:
			j = {'success': 0, 'error': 'No valid JSON document received.'}
		return j

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
		response = ''
		try:
			response = urllib.request.urlopen('http://btc-e.com/api/3/{method}/{pair}'.format(method=method, pair=pair), timeout=5).read().decode('utf-8')
		except Exception as err:
			response = '{{"success" : 0, "error" : "{}"}}'.format(err)
		j = {}
		try:
			j = json.loads(response)
		except ValueError:
			j = {'success': 0, 'error': 'No valid JSON document received.'}
		return j

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