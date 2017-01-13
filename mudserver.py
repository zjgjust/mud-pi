# -*- coding: utf-8 -*-
"""
author: Zhang Jianguo - 1401213887@pku.edu.cn
"""


import socket
import select
import time
import sys


class MudServer(object):    
    """
    一个Mud服务器类，实例化之后可以监听Telnet连接，并向客户端发送消息和处理从客户端发送过来的指令
    update方法是在主循环里要调用的，然后，就开始工作了
    """

    #嵌套类，存储连接的用户的信息
    
    class _Client(object):
        """
        存储连接的用户的信息
        """
        
        socket = None   # 连接套接字
        address = ""    # IP address
        buffer = ""     # 用户发来的信息
        lastcheck = 0   # 检查用户是否连接的标记，记录最后一次检查通过的时间
        
        def __init__(self,socket,address,buffer,lastcheck):

            self.socket = socket
            self.address = address
            self.buffer = buffer
            self.lastcheck = lastcheck
            

    #消息状态
    _EVENT_NEW_PLAYER = 1   #新用户连接
    _EVENT_PLAYER_LEFT = 2  #用户离开
    _EVENT_COMMAND = 3      #用户指令
    
    # Different states we can be in while reading data from client
    # See _process_sent_data function
    _READ_STATE_NORMAL = 1
    _READ_STATE_COMMAND = 2
    _READ_STATE_SUBNEG = 3
    
    # Telnet使用的特殊指令字符
    _TN_INTERPRET_AS_COMMAND = 255
    _TN_ARE_YOU_THERE = 246
    _TN_WILL = 251
    _TN_WONT = 252
    _TN_DO = 253
    _TN_DONT = 254
    _TN_SUBNEGOTIATION_START = 250
    _TN_SUBNEGOTIATION_END = 240

    _listen_socket = None  # 监听套接字
    _clients = {}          # 连接用户字典 key: id , value : _Client实例
    _nextid = 0            # 用户id,新用户来加一
    _events = []           # 事件列表
    _new_events = []       # swap buffer
    _loged_player = {}     # { “zjg" : {"user_name" : "zjg", "pass_word":123, "lasting_time" : 3000}}, key : str, value : {}
    
    def __init__(self):
        """    
        创建Mud服务器，监听连接
        """
        
        self._clients = {}
        self._nextid = 0
        self._events = []
        self._new_events = []
        self._loged_player = {}

        # 监听套接字创建
        self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._listen_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)

        # 监听套接字bind,监听任意IP，端口23
        self._listen_socket.bind(("0.0.0.0",23))

        # 非阻塞
        self._listen_socket.setblocking(False)
        
        # listen，最大监听数1
        self._listen_socket.listen(1)

    def setLogedPlayers(self,players):
        """
        当server启动的时候，调用一次该方法，记录从存盘读取的注册过的用户信息
        """
        self._loged_player = players

    def getLogedPlayersInfo(self,key,kkey):
        """
        获取注册过的用户的信息，包括用户名，密码，在线时间（秒）
        """
        return self._loged_player[key][kkey]

    def addLogedPlayers(self,player):
        """
        新的用户注册时调用，记录到server中
        """
        if self._loged_player.has_key(player["user_name"]):
            return
        self._loged_player[player["user_name"]] = player

    def setLogedPlayerInfo(self,key,kkey,value):
        """
        设置注册过的用户的值,这个主要在用户登录的时候设置"is_online"位
        """
        if not self._loged_player.has_key(key):
            return

        self._loged_player[key][kkey] = value
        if kkey == "is_online":
            if value == False:
               self.offLogedPlayer(self._loged_player[key]["user_name"])

    def offLogedPlayer(self,user_name):
        """
        登陆过用户下线时使用，记录在线时长
        """
        if self._loged_player.has_key(user_name):
            self._loged_player[user_name]["is_online"] = False
            self._loged_player[user_name]["lasting_time"] = self._loged_player[user_name]["lasting_time"] +\
                                                            time.time() - self._loged_player[user_name]["start_time"]
            self.savePlayers()

    def savePlayers(self):
        """
        保存所有注册过的用户信息,主要包括用户名,密码,在线时间
        """
        try:
            fp = open('playerInfo.txt','w')
        except IOError, e:
            print 'could not open file:', e
        for key,value in self._loged_player.items():
            if value["is_online"] == True:
                value["lasting_time"] = time.time() - value["start_time"] + value["lasting_time"]
            line_info = value["user_name"] + " " + value["pass_word"] + " " + str(value["lasting_time"]) + "\n"
            fp.write(line_info)

    def hasLoged(self,user_name):
        """
        判断用户名为user_name的用户是否注册过
        """
        return self._loged_player.has_key(user_name)

    def __delete__(self, instance):
        """
        析构函数，析构时，保存用户信息
        """
        self.savePlayers()

    def update(self):
        """
        监听新用户连接，用户断开连接和用户消息。
        这个方法必须在'get_new_players', 'get_disconnected_players' and 'get_commands'方法之前调用
        请将该方法放在一个循环里
        """

        self._check_for_new_connections()
        self._check_for_disconnected()
        self._check_for_messages()
        
        #保存消息，swap buffer
        self._events = list(self._new_events)
        self._new_events = []

        
    def get_new_players(self):
        """    
        获得新用户连接消息
        """
        retval = []

        for ev in self._events:
            if ev[0] == self._EVENT_NEW_PLAYER: retval.append(ev[1])

        return retval

        
    def get_disconnected_players(self):
        """    
        获得用户断开连接的消息
        """
        retval = []
        for ev in self._events:
            if ev[0] == self._EVENT_PLAYER_LEFT:
                retval.append(ev[1])

        return retval

    
    def get_commands(self):
        """    
        获取用户指令消息，ev[1] : 用户ID， ev[2] ：用户指令command, ev[3] : 指令参数parameters
        """
        retval = []

        for ev in self._events:
            if ev[0] == self._EVENT_COMMAND:
                retval.append((ev[1],ev[2],ev[3]))

        return retval


    def send_message(self,to,message):
        """    
        向ID为to的用户发送消息
        """
        self._attempt_send(to,message+"\n\r")

    def send_connect_message(self,to):
        """
        新用户连接成功时，发送提示信息
        """
        self.send_message(to, "You can login , land and help:")
        self.send_message(to, "  login <username> <password> - login new user ,e.g. 'login zjg 123456")
        self.send_message(to, "  land <username> <password> - land the user ,e.g. 'land zjg 123456'")
        self.send_message(to, "  help - get the help message ,e.g. 'help'")

    def shutdown(self):
        """    
        关闭服务器
        """
        self.savePlayers();
        for cl in self._clients.values():
            cl.socket.shutdown()
            cl.socket.close()
        self._listen_socket.close()

    
    def _attempt_send(self,clid,data):
        """
        发送消息，Unicode转码操作，保证兼容性
        """
        if sys.version < '3' and type(data)!=unicode: data = unicode(data,"latin1")
        try:
            self._clients[clid].socket.sendall(bytearray(data,"latin1"))

        except KeyError: pass

        except socket.error:
            self._handle_disconnect(clid)

    
    def _check_for_new_connections(self):
        """
        检测新用户连接，使用select
        """
        rlist,wlist,xlist = select.select([self._listen_socket],[],[],0)

        if self._listen_socket not in rlist: return

        joined_socket,addr = self._listen_socket.accept()

        joined_socket.setblocking(False)

        self._clients[self._nextid] = MudServer._Client(joined_socket,addr[0],"",time.time())

        self._new_events.append((self._EVENT_NEW_PLAYER,self._nextid))

        self._nextid += 1


    def _check_for_disconnected(self):
    
        """
        检测断开连接的用户
        """
        for id,cl in list(self._clients.items()):

            if time.time() - cl.lastcheck < 5.0: continue

            self._attempt_send(id,"\x00")

            cl.lastcheck = time.time()
        
                
    def _check_for_messages(self):
    
        """
        检测用户发来的消息
        """
        for id,cl in list(self._clients.items()):

            rlist,wlist,xlist = select.select([cl.socket],[],[],0)

            if cl.socket not in rlist: continue
                        
            try:
                data = cl.socket.recv(4096).decode("latin1")             

                message = self._process_sent_data(cl,data)

                if message:

                    message = message.strip()

                    command,params = (message.split(" ",1)+["",""])[:2]

                    self._new_events.append((self._EVENT_COMMAND,id,command.lower(),params))

            except socket.error:
                self._handle_disconnect(id)
        
                
    def _handle_disconnect(self,clid):
        """
        处理连接错误的用户，即断开连接用户
        """

        del(self._clients[clid])

        self._new_events.append((self._EVENT_PLAYER_LEFT,clid))
        
                
    def _process_sent_data(self,client,data):
    
        """
        处理接受到的消息，主要是干掉Telnet协议的特殊指令
        """
    
        # start with no message and in the normal state
        message = None
        state = self._READ_STATE_NORMAL
        
        # go through the data a character at a time
        for c in data:
        
            # handle the character differently depending on the state we're in:
        
            # normal state
            if state == self._READ_STATE_NORMAL:
            
                # if we received the special 'interpret as command' code, switch
                # to 'command' state so that we handle the next character as a 
                # command code and not as regular text data
                if ord(c) == self._TN_INTERPRET_AS_COMMAND:
                    state = self._READ_STATE_COMMAND
                    
                # if we get a newline character, this is the end of the message.
                # Set 'message' to the contents of the buffer and clear the buffer
                elif c == "\n":
                    message = client.buffer
                    client.buffer = ""
                
                # some telnet clients send the characters as soon as the user types 
                # them. So if we get a backspace character, this is where the user has 
                # deleted a character and we should delete the last character from
                # the buffer.
                elif c == "\x08":
                    client.buffer = client.buffer[:-1]
                    
                # otherwise it's just a regular character - add it to the buffer
                # where we're building up the received message
                else:
                    client.buffer += c
                    
            # command state
            elif state == self._READ_STATE_COMMAND:
            
                # the special 'start of subnegotiation' command code indicates that
                # the following characters are a list of options until we're told
                # otherwise. We switch into 'subnegotiation' state to handle this
                if ord(c) == self._TN_SUBNEGOTIATION_START:
                    state = self._READ_STATE_SUBNEG
                    
                # if the command code is one of the 'will', 'wont', 'do' or 'dont'
                # commands, the following character will be an option code so we 
                # must remain in the 'command' state
                elif ord(c) in (self._TN_WILL,self._TN_WONT,self._TN_DO,self._TN_DONT):
                    state = self._READ_STATE_COMMAND
                    
                # for all other command codes, there is no accompanying data so 
                # we can return to 'normal' state.
                else:
                    state = self._READ_STATE_NORMAL
                    
            # subnegotiation state
            elif state == self._READ_STATE_SUBNEG:
                
                # if we reach an 'end of subnegotiation' command, this ends the
                # list of options and we can return to 'normal' state. Otherwise
                # we must remain in this state
                if ord(c) == self._TN_SUBNEGOTIATION_END:
                    state = self._READ_STATE_NORMAL
                    
        # return the contents of 'message' which is either a string or None
        return message

