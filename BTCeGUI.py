#! python3
import tkinter
import tkinter.ttk as ttk
import threading
import operator
import time
import copy
import os.path
import datetime
import queue
import BTCe

api = BTCe.API('BTCe.ini')
console = None

def format_float(value):
	return ('{:0.8f}'.format(float(value)).rstrip('0').rstrip('.'))

def validate_float(value):
	if not value:
		return True
	try:
		v = float(value)
		return True
	except ValueError:
		return False

class CurrencyBox(ttk.Combobox):
	"""Currency pair selection combo box."""
	def __init__(self, parent):
		ttk.Combobox.__init__(self, parent, state='readonly', justify='left', width=12)
		self.set('Currency Pair')

	def update(self, pairs):
		"""Update available pairs."""
		if not pairs:
			return
		values = [pair.upper().replace('_', '/') for pair in pairs]
		values.sort()
		self.config(values=values)

class TradeFrame(ttk.Frame):
	"""Buy/sell box."""
	def __init__(self, parent, type):
		"""type: Buy | Sell"""
		ttk.Frame.__init__(self, parent, borderwidth=10, relief='groove')
		self.type = type
		self.funds = {}
		self.fee = 0
		self.allchecked = tkinter.IntVar()
		self.focus = 0
		self.currvars = [tkinter.StringVar(value='0') for i in range(2)]
		self.ratevar = tkinter.StringVar(value='0')
		self.feevar = tkinter.StringVar(value='0')
		self.ignoretrace = False

		# init widgets
		validatecommand = (self.register(validate_float), '%P')
		self.currentries = [ttk.Entry(self, justify='right', validate='key', validatecommand=validatecommand, textvariable=self.currvars[i]) for i in range(2)]
		self.currlabels = [ttk.Label(self, text='') for i in range(2)]
		self.rateentry = ttk.Entry(self, justify='right', validate='key', validatecommand=validatecommand, textvariable=self.ratevar)
		self.feeentry = ttk.Entry(self, justify='right', state='readonly', validate='key', validatecommand=validatecommand, textvariable=self.feevar)
		self.feelabel = ttk.Label(self, text='')
		self.orderbutton = ttk.Button(self, text='Place Order', state='disabled', command=self.placeorder)

		# frame layout
		ttk.Label(self, text=type).grid(column=0, row=0, sticky='w')

		ttk.Label(self, text='Amount:').grid(column=0, row=1, sticky='w')
		self.currentries[0].grid(column=1, row=1, sticky='nsew')
		self.currlabels[0].grid(column=2, row=1, sticky='w')

		ttk.Label(self, text='Value:').grid(column=0, row=2, sticky='w')
		self.currentries[1].grid(column=1, row=2, sticky='nsew')
		self.currlabels[1].grid(column=2, row=2, sticky='w')

		ttk.Label(self, text='Rate:').grid(column=0, row=3, sticky='w')
		self.rateentry.grid(column=1, row=3, sticky='nsew')

		ttk.Label(self, text='Fee:').grid(column=0, row=4, sticky='w')
		self.feelabel.grid(column=2, row=4, sticky='w')
		self.feeentry.grid(column=1, row=4, sticky='nsew')

		ttk.Checkbutton(self, text='All', variable=self.allchecked, command=self.update_amounts).grid(column=1, row=5, sticky='nw')
		self.orderbutton.grid(column=1, row=5, sticky='ne')

		self.grid_columnconfigure(0, weight=0, minsize=50)
		self.grid_columnconfigure(1, weight=1)
		self.grid_columnconfigure(2, weight=0, minsize=50)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1, pad=5)
		self.grid_rowconfigure(2, weight=1, pad=5)
		self.grid_rowconfigure(3, weight=1, pad=5)
		self.grid_rowconfigure(4, weight=1, pad=5)
		self.grid_rowconfigure(5, weight=1)

		# events
		self.ratevar.trace('w', self.update_amounts)
		for i in range(2):
			self.currvars[i].trace('w', lambda name, index, op, focus=i: self.setfocus(focus))

	def setfocus(self, focus, *args):
		"""Change focus due to currency entry edit (using trace)."""
		if not self.ignoretrace:
			self.focus = focus
			self.update_amounts(args)

	def setrate(self, rate):
		self.ratevar.set(format_float(rate))

	def placeorder(self):
		self.orderbutton.config(state='disabled', text='Placing Order...')
		# get all trade data from current entries and labels
		pair = '_'.join(self.currlabels[i].cget('text') for i in range(2)).lower()
		type = self.type.lower()
		rate = float(self.rateentry.get())
		amount = float(self.currentries[0].get())
		threading.Thread(target=self.master.placeorder, args=[pair, type, rate, amount]).start()

	def update(self, pair, funds, fee, cantrade, ordering):
		"""Update currency labels and amounts."""
		if len(pair) == 2:
			for i in range(2):
				self.currlabels[i].config(text=pair[i])
			self.feelabel.config(text=(pair[0] if self.type == 'Buy' else pair[1]))

		# enable/disable order button
		amount = self.currvars[0].get()
		amount = float(0.0 if amount == '' else amount)
		rate = self.ratevar.get()
		rate = float(0.0 if rate == '' else rate)
		if cantrade and len(pair) == 2 and amount > 0.0 and rate > 0.0 and not ordering:
			self.orderbutton.config(state='normal', text='Place Order')
		elif ordering:
			self.orderbutton.config(state='disabled', text='Placing Order...')
		else:
			self.orderbutton.config(state='disabled', text='Place Order')

		self.funds = funds
		self.fee = float(fee) / 100.0
		self.update_amounts()

	def update_amounts(self, *args):
		"""Update currency amounts."""
		self.ignoretrace = True
		# auto-fill focus in case of a checked All button
		pair = [self.currlabels[i].cget('text') for i in range(2)]
		if self.funds and self.allchecked.get() and pair[0] and pair[1]:
			self.focus = 1 if self.type == 'Buy' else 0
			balance = self.funds[pair[self.focus].lower()]
			self.currvars[self.focus].set(format_float(balance))

		# calculate non-focused entry
		rate = self.ratevar.get()
		rate = float(0.0 if rate == '' else rate)
		op = operator.mul if self.focus == 0 else operator.truediv
		nonfocus = 1 - self.focus
		focus = self.currvars[self.focus].get()
		focus = float(focus) if focus else 0.0
		self.currvars[nonfocus].set(format_float(op(focus, rate) if rate != 0.0 else 0.0))

		# calculate fee
		feedval = self.currvars[0].get() if self.type == 'Buy' else self.currvars[1].get()
		feedval = float(feedval) if feedval else 0.0
		self.feevar.set(format_float(self.fee * feedval))

		# (re)set readonly/normal entry states
		state = 'readonly' if self.allchecked.get() else 'normal'
		for currentry in self.currentries:
			currentry.config(state=state)

		self.ignoretrace = False

class ConsoleFrame(ttk.Frame):
	"""Console."""
	def __init__(self, parent):
		ttk.Frame.__init__(self, parent, borderwidth=10, relief='groove')
		self.queue = queue.Queue()

		# init widgets
		self.text = tkinter.Text(self, height=4, state='disabled')
		vsb = ttk.Scrollbar(self, orient='vertical', command=self.text.yview)
		self.text.config(yscrollcommand=vsb.set)

		# frame layout
		ttk.Label(self, text='Console').grid(column=0, row=0, sticky='w', columnspan=2)
		self.text.grid(column=0, row=1, sticky='nsew')
		vsb.grid(column=1, row=1, sticky='nse')

		self.grid_columnconfigure(0, weight=1)
		self.grid_columnconfigure(1, weight=0)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1, pad=5)

	def print(self, text):
		self.queue.put(text)

	def update(self):
		atend = self.text.yview()[1] == 1.0
		self.text.config(state='normal')
		while not self.queue.empty():
			self.text.insert('end', '{}: {}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), self.queue.get()))
		self.text.config(state='disabled')
		if atend:
			self.text.see('end')

class Console:
	def print(self, text):
		print(text)

class OrderFrame(ttk.Frame):
	"""Frame for showing open orders."""
	status = ['Active', 'Filled', 'Partially Filled', 'Cancelled']

	def __init__(self, parent):
		ttk.Frame.__init__(self, parent, borderwidth=10, relief='groove')

		# init widgets
		self.table = ttk.Treeview(self, columns=['id', 'time', 'pair', 'type', 'rate', 'amount', 'value', 'status'], show='headings', height=3)
		vsb = ttk.Scrollbar(self, orient='vertical', command=self.table.yview)
		self.table.config(yscrollcommand=vsb.set)
		self.orderbutton = ttk.Button(self, text='Cancel Order(s)', state='disabled', command=self.cancelorders)

		# frame layout
		ttk.Label(self, text='Open Orders').grid(column=0, row=0, sticky='w')
		self.table.grid(column=0, row=1, sticky='nsew')
		vsb.grid(column=1, row=1, sticky='ns')
		self.orderbutton.grid(column=0, row=2, sticky='nse')
		self.grid_columnconfigure(0, weight=1, pad=5)
		self.grid_columnconfigure(1, weight=0, pad=5)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1, pad=5)

		# table layout
		self.table.heading('id', text='ID', anchor='w')
		self.table.heading('time', text='Placed on', anchor='w')
		self.table.heading('pair', text='Pair', anchor='w')
		self.table.heading('type', text='Type', anchor='w')
		self.table.heading('rate', text='Rate', anchor='w')
		self.table.heading('amount', text='Amount', anchor='w')
		self.table.heading('value', text='Value', anchor='w')
		self.table.heading('status', text='Status', anchor='w')

		self.table.column('id', width=15)
		self.table.column('time', width=60)
		self.table.column('pair', width=10)
		self.table.column('type', width=20)
		self.table.column('rate', width=30)
		self.table.column('amount', width=60)
		self.table.column('value', width=60)
		self.table.column('status', width=40)

	def cancelorders(self):
		"""Cancel all selected orders."""
		self.orderbutton.config(state='disabled', text='Cancelling...')
		selects = self.table.selection()
		selectids = []
		for select in selects:
			selectids.append(int(self.table.item(select)['values'][0]))
		threading.Thread(target=self.master.cancelorders, args=[selectids]).start()

	def update(self, orders, cantrade, cancelling):
		"""Build order list and update table."""
		# enable/disable order button
		if cantrade and orders and not cancelling:
			self.orderbutton.config(state='normal', text='Cancel Order(s)')
		elif cancelling:
			self.orderbutton.config(state='disabled', text='Cancelling...')
		else:
			self.orderbutton.config(state='disabled', text='Cancel Order(s)')

		# store old selection keys
		selects = self.table.selection()
		selectids = []
		for select in selects:
			selectids.append(int(self.table.item(select)['values'][0]))

		# delete old entries
		self.table.delete(*self.table.get_children())

		if not orders:
			return
		# insert new entries and select old keys
		for id in orders:
			order = orders[id]
			time = datetime.datetime.utcfromtimestamp(order['timestamp_created'])
			pair = order['pair'].upper().split('_')
			rate = float(order['rate'])
			amount = float(order['amount'])
			value = format_float(rate * amount) + ' ' + pair[1]
			amount = format_float(amount) + ' ' + pair[0]
			status = OrderFrame.status[order['status']]

			values = [id, time, '/'.join(pair), order['type'].capitalize(), rate, amount, value, status]
			item = self.table.insert('', 'end', values=values)
			if int(id) in selectids:
				self.table.selection_add(item)


class DepthFrame(ttk.Frame):
	"""Treeview and components for a list of offers."""
	def __init__(self, parent, type):
		"""type: Ask | Bid"""
		ttk.Frame.__init__(self, parent, borderwidth=10, relief='groove')
		self.type = type

		# init widgets
		self.table = ttk.Treeview(self, columns=['rate', 'curr0', 'curr1'], show='headings')
		vsb = ttk.Scrollbar(self, orient='vertical', command=self.table.yview)
		self.table.configure(yscrollcommand = vsb.set)

		# frame layout
		ttk.Label(self, text=type).grid(column=0, row=0, sticky='w')
		self.table.grid(column=0, row=1, sticky='nsew')
		vsb.grid(column=1, row=1, sticky='ns')
		self.grid_columnconfigure(0, weight=1, pad=5)
		self.grid_columnconfigure(1, weight=0, pad=5)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1, pad=5)

		# table layout
		self.table.column('rate', width=60)
		self.table.column('curr0', width=80)
		self.table.column('curr1', width=80)

	def update(self, depth, pair):
		"""Clear and rebuild the depth table."""
		if not depth or len(pair) != 2:
			return

		# update headings
		self.table.heading('rate', text='Rate', anchor='w')
		self.table.heading('curr0', text=pair[0], anchor='w')
		self.table.heading('curr1', text=pair[1], anchor='w')

		# store old selection keys
		selects = self.table.selection()
		selectrates = []
		for select in selects:
			selectrates.append(float(self.table.item(select)['values'][0]))

		# delete old entries
		self.table.delete(*self.table.get_children())

		# insert new entries and select old keys
		orders = depth[self.type.lower() + 's']
		for order in orders:
			values = [float(order[0]), float(order[1]), format_float(float(order[0]) * float(order[1]))]
			item = self.table.insert('', 'end', values=values)
			if values[0] in selectrates:
				self.table.selection_add(item)


class BalanceFrame(ttk.Frame):
	"""Tree view for personal balances."""
	def __init__(self, parent):
		ttk.Frame.__init__(self, parent, borderwidth=10, relief='groove')

		# init widgets
		self.table = ttk.Treeview(self, columns = ['curr', 'funds'], show='headings')
		vsb = ttk.Scrollbar(self, orient='vertical', command=self.table.yview)
		self.table.configure(yscrollcommand = vsb.set)

		# frame layout
		ttk.Label(self, text='Funds').grid(column=0, row=0, columnspan=2, sticky='w')
		self.table.grid(column=0, row=1, sticky='nsew')
		vsb.grid(column=1, row=1, sticky='ns')
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1)

		# table layout
		self.table.column('curr', width=60)
		self.table.column('funds', width=100)
		self.table.heading('curr', text='Currency', anchor='w')
		self.table.heading('funds', text='Balance', anchor='w')

	def update(self, funds):
		"""Clear and rebuild the balance table."""
		if not funds:
			return

		# store old selection keys
		selects = self.table.selection()
		selectcurrs = []
		for select in selects:
			selectcurrs.append(self.table.item(select)['values'][0])

		# delete old entries
		for entry in self.table.get_children():
			self.table.delete(entry)

		# insert new sorted entries and select old keys
		funds = list(funds.items())
		funds.sort()
		for fund in funds:
			curr = fund[0].upper()
			item = self.table.insert('', 'end', values=[curr, format_float(fund[1])])
			if curr in selectcurrs:
				self.table.selection_add(item)

class Main(tkinter.Tk):
	"""Main frame."""
	def __init__(self):
		tkinter.Tk.__init__(self)
		self.title('BTCeGUI')
		self.lockdata = threading.Lock()
		self.locknonce = threading.Lock()
		self.info = {}
		self.depth = {}
		self.userinfo = {}
		self.orders={}
		self.pair = {}
		self.run = True
		self.buying = False
		self.selling = False
		self.cancelling = False

		# layout
		self.geometry('800x800+100+100')
		self.currencybox = CurrencyBox(self)
		self.currencybox.grid(column=0, row=0, stick='nw')

		self.buybox = TradeFrame(self, 'Buy')
		self.buybox.grid(column=0, row=1, sticky='nsew', padx=20, pady=5)
		self.sellbox = TradeFrame(self, 'Sell')
		self.sellbox.grid(column=1, row=1, sticky='nsew', padx=20, pady=5)

		self.askframe = DepthFrame(self, 'Ask')
		self.askframe.grid(column=0, row=2, sticky='nsew', padx=5, pady=5)
		self.bidframe = DepthFrame(self, 'Bid')
		self.bidframe.grid(column=1, row=2, sticky='nsew', padx=5, pady=5)
		self.balanceframe = BalanceFrame(self)
		self.balanceframe.grid(column=2, row=2, sticky='nsew', padx=5, pady=5)

		self.orderframe = OrderFrame(self)
		self.orderframe.grid(column=0, row=3, sticky='nsew', padx=5, pady=5, columnspan=3)

		self.console = ConsoleFrame(self)
		self.console.grid(column=0, row=4, sticky='nsew', padx=5, pady=5, columnspan=3)
		global console
		console = self.console

		self.grid_columnconfigure(0, weight=1)
		self.grid_columnconfigure(1, weight=1)
		self.grid_columnconfigure(2, weight=0)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=0)
		self.grid_rowconfigure(2, weight=1)
		self.grid_rowconfigure(3, weight=0)
		self.grid_rowconfigure(4, weight=0)

		# events
		self.askframe.table.bind('<Double-1>', lambda event: self.ondouble_depth(self.askframe.table, self.buybox, event))
		self.bidframe.table.bind('<Double-1>', lambda event: self.ondouble_depth(self.bidframe.table, self.sellbox, event))

		# api threads
		if api.secret == b'copy API secret here' or api.key == b'copy API key here':
			console.print('No API secret/key found. Only public data available.')
		else:
			threading.Thread(target=self.update_userinfo_loop).start()
			threading.Thread(target=self.update_orders_loop).start()
		threading.Thread(target=self.update_depth_loop).start()
		threading.Thread(target=self.update_info_loop).start()

		self.sync()

	def exit(self):
		"""Stop running threads."""
		self.run = False
		# redirect console prints to the normal console
		global console
		console = Console()

	def ondouble_depth(self, table, box, event):
		"""Send double-clicked rate to trade box."""
		item = table.identify('item', event.x, event.y)
		if (item):
			box.setrate(table.item(item, 'values')[0])

	def sync(self):
		"""Sync GUI to states."""
		self.lockdata.acquire()
		userinfo = copy.copy(self.userinfo)
		orders = copy.copy(self.orders)
		info = copy.copy(self.info)
		depth = copy.copy(self.depth)
		self.pair = copy.copy(self.currencybox.get().split('/'))
		self.lockdata.release()

		pairs = None
		if info:
			pairs = info.get('pairs')
		self.currencybox.update(pairs)

		funds = None
		if userinfo:
			funds = userinfo.get('funds')

		# update depth tables
		fee = 0
		pair = []
		if (depth):
			pair = next(iter(depth))
			if pairs:
				fee = pairs[pair]['fee']
			depth = depth[pair]
			pair = pair.upper().split('_')

		cantrade = True if userinfo and userinfo['rights']['trade'] == 1 else False

		self.askframe.update(depth, pair)
		self.bidframe.update(depth, pair)
		self.balanceframe.update(funds)
		self.buybox.update(pair, funds, fee, cantrade, self.buying)
		self.sellbox.update(pair, funds, fee, cantrade, self.selling)
		self.orderframe.update(orders, cantrade, self.cancelling)
		self.console.update()

		self.after(100, self.sync)

	def update_depth_loop(self):
		while self.run:
			self.update_depth()
			time.sleep(1.0)

	def update_depth(self):
		# if currency pair is valid get depth table
		self.lockdata.acquire()
		pair = copy.copy(self.pair)
		self.lockdata.release()
		depth = {}
		if len(pair) == 2:
			depth = BTCe.API.depth('_'.join(pair).lower())
			if depth and 'success' in depth.keys():
				if depth['success'] == 1:
					depth = depth['return']
				else:
					console.print('[WARNING] Error requesting depth: {}'.format(depth['error']))
					depth = None
			self.lockdata.acquire()
			self.depth = depth
			self.lockdata.release()

	def update_userinfo_loop(self):
		acc = 0.0
		while self.run:
			self.update_userinfo()
			while acc < 5.0 and self.run:
				time.sleep(0.5)
				acc += 0.5
			acc = 0.0

	def update_userinfo(self):
			self.locknonce.acquire()
			userinfo = api.getinfo()
			self.locknonce.release()
			if userinfo and 'success' in userinfo.keys():
				if userinfo['success'] == 1:
					userinfo = userinfo['return']
				else:
					console.print('[WARNING] Error requesting user info: {}'.format(userinfo['error']))
					userinfo = None
			self.lockdata.acquire()
			self.userinfo = userinfo
			self.lockdata.release()

	def update_orders_loop(self):
		acc = 0.0
		while self.run:
			self.update_orders()
			while acc < 10.0 and self.run:
				time.sleep(0.5)
				acc += 0.5
			acc = 0.0

	def update_orders(self):
		self.locknonce.acquire()
		orders = api.activeorders()
		self.locknonce.release()
		if orders and 'success' in orders.keys():
			if orders['success'] == 1:
				orders = orders['return']
			else:
				if orders['error'] != 'no orders':
					console.print('[WARNING] Error requesting open orders: {}'.format(orders['error']))
				orders = None
		self.lockdata.acquire()
		self.orders = orders
		self.lockdata.release()

	def update_info_loop(self):
		acc = 0.0
		while self.run:
			self.update_info()
			while acc < 7.0 and self.run:
				time.sleep(0.5)
				acc += 0.5
			acc = 0.0

	def update_info(self):
		acc = 0.0
		while self.run:
			info = BTCe.API.info()
			if info and 'success' in info.keys():
				if info['success'] == 1:
					info = info['return']
				else:
					console.print('[WARNING] Error requesting public info: {}'.format(info['error']))
					info = None
			self.lockdata.acquire()
			self.info = info
			self.lockdata.release()
			while acc < 30.0 and self.run:
				time.sleep(0.5)
				acc += 0.5
			acc = 0.0

	def placeorder(self, pair, type, rate, amount):
		console.print('Placing order {}.'.format([pair, type, rate, amount]))
		if type == 'buy':
			self.buying = True
		elif type == 'sell':
			self.selling = True
		else:
			return

		self.locknonce.acquire()
		response = api.trade(pair, type, rate, amount)
		self.locknonce.release()

		if response and 'success' in response.keys():
			if response['success'] == 1:
				console.print('Order placed successfully.')
			else:
				console.print('[WARNING] Error placing order: {}'.format(response['error']))

		self.update_orders()
		self.update_userinfo()
		
		if type == 'buy':
			self.buying = False
		elif type == 'sell':
			self.selling = False

	def cancelorders(self, ids):
		self.cancelling = True
		for id in ids:
			console.print('Cancel order {}.'.format(id))
			self.locknonce.acquire()
			response = api.cancelorder(id)
			self.locknonce.release()
			if response and 'success' in response.keys():
				if response['success'] == 1:
					console.print('Order cancelled successfully.')
				else:
					console.print('[WARNING] Error cancelling order: {}'.format(response['error']))
		self.update_orders()
		self.update_userinfo()
		self.cancelling = False

root = Main()
root.mainloop()
root.exit()