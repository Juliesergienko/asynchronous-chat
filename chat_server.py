import tornado.ioloop
import tornado.web
import tornado.websocket
import psycopg2
import sys
import MySQLdb
import json
import time
from db_config import *

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("chat.html")


class EchoWebSocket(tornado.websocket.WebSocketHandler):
	def authorisation_check(self,name, password):	
		db.execute("select * from users where name='"+name+ "' and password = '"+password+"';")
		user = db.fetchall()
		if user:
			user_tuple = user[0]

			user = {"id":user_tuple[0], "name":user_tuple[1], "password":user_tuple[2], "avatar":user_tuple[3],
			"status":user_tuple[4]}
			db.execute("UPDATE users SET status = 'online' WHERE id = %s" %user["id"]) 
			connection.commit()
		
		try:
			if user:
				clients_list[self] = user
				response = {"type":"status", "id":user["id"], "status":"online"}
				for i in list(clients_list.keys()):
					if not i==self:
						i.write_message(response)

				return True, user
		except:
			return False, None
		return False, None

	def register_new_user(self, name, password):
		try:
			db.execute("select * from users where name='"+name+"';")
			user_exists = db.fetchall()
		except:
			print ("failed to get from db")
			return False, None
		if user_exists:
			return False, None
		else:
			
			try:
				db.execute("INSERT INTO users (name, password, avatar, status) VALUES ('%s', '%s', '%s', '%s')" %( name,
				 password, '', 'online'))
				connection.commit()
			except:
				print ("failed to write into db")
				return False, None
			db.execute("select * from users where name='"+name+"' and password = '"+password+"';")
			user = db.fetchall()
			user_tuple = user[0]
			user = {"id":user_tuple[0], "name":user_tuple[1], "password":user_tuple[2], "avatar":user_tuple[3],
			"status":user_tuple[4]}
			clients_list[self] = user
			return True, user

	def form_history(self, user, other):
		db.execute("select * from messages where (sender_id= '%s' AND receiver_id = '%s' ) OR (sender_id= '%s' AND receiver_id = '%s') order by time" %( user, other, other, user))
		messages_list_from_db = db.fetchall()
		messages_list =[]
		for i in messages_list_from_db:
			row =  {"id":i[0], "sender_id":i[1], "receiver_id":i[2], "message":i[3], "time":i[4]}
			messages_list.append(row)
		return messages_list

	def open(self):
		clients_list[self] = None 
		print("WebSocket opened")
		
	def on_message(self, message):
		js = json.loads(message)
		global user

		if js['type'] == "authorisation":
			authorised, user = self.authorisation_check(js['user_name'], js['user_password'])
			response = ({"type":"authorisation", "authorised":authorised, "user":user})
			self.write_message(response)

		elif js["type"] == "registration":
			registered, user = self.register_new_user(js['user_name'], js['user_password'])
			response = ({"type":"registration", "registered":registered, "user":user})
			self.write_message(response)

		elif js['type']=='get_online_user_list':
			db.execute("SELECT * FROM users WHERE status = 'online' order by name;")
			users = db.fetchall()
			for i in range(len(users)):
				users[i] = {"name":users[i][1], "id":users[i][0], "avatar":users[i][3], "status":users[i][4]}
			response = {"type":"get_online_user_list", "user_list":users}
			self.write_message(response)

		elif js['type']=='get_user_list':
			db.execute("SELECT * FROM users order by name;")
			users = db.fetchall()
			for i in range(len(users)):
				users[i] = {"name":users[i][1], "id":users[i][0], "avatar":users[i][3], "status":users[i][4]}
			response = {"type":"get_online_user_list", "user_list":users}
			self.write_message(response)

		elif js['type'] == "message":
			db.execute("INSERT INTO messages (sender_id, receiver_id, message, time) VALUES ('%s', '%s', '%s', '%s' )" % (clients_list[self]["id"],
				js["to"], js["message"], str(js["time"])))
			connection.commit()
			response = {"type":"message", "message":js["message"], "from":clients_list[self]["id"]}
			for i in list(clients_list.keys()):
				if clients_list[i]:
					if int(clients_list[i]["id"]) == int(js["to"]):
						i.write_message(response)

		elif js['type'] == "history":
			message_list = self.form_history(clients_list[self]["id"],js['user_id'])
			response = {"type":"history", "message_list":message_list, "other_id":js["user_id"]}
			self.write_message(response)

		else:
			response = {"type": "Error", "except":"type was not mentioned!!!"}
			self. write_message(response)

	def on_close(self):
		response = {"type":"status"}
		try:
			db.execute("UPDATE users SET status = 'ofline' WHERE id = '%s'" %clients_list[self]["id"])
			connection.commit()
			response = {"type":"status", "id":clients_list[self]["id"], "status":"ofline"}
		except:
			pass
		to_delete = []
		for i in list(clients_list.keys()):
			if i==self:
				to_delete.append(i)
				
		for i in to_delete:
			clients_list.pop(i, 0)
		
		for i in list(clients_list.keys()):
			if not i==self:
				i.write_message(response)
		print("WebSocket closed")

static_path = 'ball'
user = ""

connection = psycopg2.connect(conn_string)
db = connection.cursor()

clients_list = {}

application = tornado.web.Application([
	(r"/", MainHandler),
	(r'/ball/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
	(r'/ws', EchoWebSocket)
], autoreload = True, compiled_template_cache = False)

if __name__ == "__main__":
	application.listen(8080)
	tornado.ioloop.IOLoop.instance().start()