"""
A simple Multi-User Dungeon (MUD) game. Players can talk to each other, examine
their surroundings and move between rooms.

author: Zhang Jianguo - 1401213887@pku.edu.cn
"""

import time
import random
# import the MUD server class
from Mudserver import MudServer

class MudManager(object):

    class _GameManager:
        def __init__(self):
            self.is_21gaming = False
            self.start_time_21game = 0
            self.answers_21game = {}
            self.random_nums_21game = []
            self.random_nums_str = ""

    def __init__(self):
        self.rooms = ["hall"]
        self.logPlayers = self._loadPlayersInformation('playerInfo.txt')
        self.mud = MudServer()
        self.mud.setLogedPlayers(self.logPlayers)
        self.connectPlayers = {}
        self.gameManager = self._GameManager()

    def _loadPlayersInformation(self, file_name):
        fp = open(file_name, 'r')
        log_players = {}
        while True:
            line = fp.readline()
            if not line:
                break
            user_name, pass_word, lasting_time = line.split(" ")
            user_name.strip()
            pass_word.strip()
            lasting_time.strip()
            log_players[user_name] = {
                "user_name": user_name,
                "pass_word": pass_word,
                "lasting_time": float(lasting_time),
                "is_online": False,
                "start_time": 0
            }
        return log_players

    def sendMessageToAll(self, message):
        for id, value in self.connectPlayers.items():
            self.mud.send_message(id, message)

    def sendMessageToRoom(self, rid, message):
        for id, value in self.connectPlayers.items():
            if value["room"] == rid:
                self.mud.send_message(id, message)

    def sendMessageToRoomExceptYourself(self, rid, message, eid):
        for id, value in self.connectPlayers.items():
            if value["room"] == rid and id != eid:
                self.mud.send_message(id, message)

    def sendMessageToSomeone(self, did, message):
        self.mud.send_message(did, message)

    def sendHelpMessage(self,id):
        # send the player back the list of possible commands
        self.mud.send_message(id, "Commands:")
        self.mud.send_message(id, "  chat     <message>  - said  in the room, e.g. 'chat Hello'")
        self.mud.send_message(id, "  hallchat <message>  - said in the hall ,e.g. 'hallchat hello'")
        self.mud.send_message(id, "  roomchat <message>  - said in the room ,e.g. 'roomchat hello'")
        self.mud.send_message(id, "  talkto   <username> <message>  - talk to  the user ,e.g. 'talkto zjg zjg'")
        self.mud.send_message(id, "  login    <username> <password> - login new user ,e.g. 'login zjg 123456")
        self.mud.send_message(id, "  land     <username> <password> - land the user ,e.g. 'land zjg 123456'")
        self.mud.send_message(id, "  21game   <expression>          -  take the 21game ,e.g. '21game 1+ 2 + 3 + 4'")
        self.mud.send_message(id, "  go       <room>                - get into the room , e.g 'go home'")
        self.mud.send_message(id, "  create   <room>                - create a room ,e.g. 'create home'")
        self.mud.send_message(id, "  rooms  - list the room information ,e.g. 'rooms'")
        self.mud.send_message(id, "  exit   - exit the room  ,e.g. 'exit' ")


    def work(self):
        while True:

            # pause for 1/5 of a second on each loop, so that we don't constantly
            # use 100% CPU time
            time.sleep(0.2)

            # 21 game
            if not self.gameManager.is_21gaming and int(time.strftime("%M"))  == 30:
                self.gameManager.is_21gaming = True
                self.gameManager.start_time_21game = time.time()
                for i in range(0, 4):
                    random_num = random.randint(1, 10)
                    self.gameManager.random_nums_21game.append(random_num)
                    self.gameManager.random_nums_str += str(random_num) + " "
                self.gameManager.random_nums_str.strip()
                message = "21 game time: %s" % self.gameManager.random_nums_str
                self.sendMessageToAll(message)

            if self.gameManager.is_21gaming:
                if time.time() - self.gameManager.start_time_21game >= 30.0:
                    self.gameManager.is_21gaming = False
                    self.gameManager.random_nums_21game = []
                    self.gameManager.random_nums_str = ""
                    self.gameManager.start_time_21game = 0
                    most_id = -1
                    opt_id = -1
                    if len(self.gameManager.answers_21game) == 0:
                        self.sendMessageToAll("It's the time. No one put an answer.")
                    else:
                        for pid, value in self.gameManager.answers_21game.items():
                            if value["value"] == 21:
                                if opt_id == -1:
                                    opt_id == pid
                                else:
                                    if value["time"] < self.gameManager.answers_21game[opt_id]["time"]:
                                        opt_id = pid
                            else:
                                if most_id == -1:
                                    most_id = pid
                                elif value["value"] > self.gameManager.answers_21game[most_id]["value"]:
                                    most_id = pid
                                elif value["value"] == self.gameManager.answers_21game[most_id]["value"]:
                                    if value["time"] < self.gameManager.answers_21game[most_id]["time"]:
                                        most_id = pid
                    last_id = -1
                    if opt_id != -1:
                        last_id = opt_id
                    else:
                        last_id = most_id
                    if last_id == -1:
                        self.sendMessageToAll("No one put the answer.")
                    else:
                        self.sendMessageToAll("21 game winner is: %s" % self.connectPlayers[last_id]["user_name"])
                    self.gameManager.answers_21game = {}

            # 'update' must be called in the loop to keep the game running and give
            # us up-to-date information
            self.mud.update()

            # go through any newly connected players
            for id in self.mud.get_new_players():
                # add the new player to the dictionary, noting that they've not been
                # named yet.
                # The dictionary key is the player's id number. Start them off in the
                # 'Tavern' room.
                # Try adding more player stats - level, gold, inventory, etc
                self.connectPlayers[id] = {
                    "user_name": None,
                    "room": "hall",
                    "lasting_time": 0,
                    "start_time": 0,
                    "is_logined": False,
                    "is_online": False,
                    "pass_word": "",
                }
                # send the new player a prompt for their name
                self.mud.send_connect_message(id)

            # go through any recently disconnected players
            for id in self.mud.get_disconnected_players():

                # if for any reason the player isn't in the player map, skip them and
                # move on to the next one
                if id not in self.connectPlayers: continue

                # go through all the players in the game
                self.sendMessageToAll("%s quit the game." % self.connectPlayers[id]["user_name"])

                # log user message
                self.mud.offLogedPlayer(self.connectPlayers[id]["user_name"])

                # remove the player's entry in the player dictionary
                del (self.connectPlayers[id])

            # go through any new commands sent from players
            for id, command, params in self.mud.get_commands():

                # if for any reason the player isn't in the player map, skip them and
                # move on to the next one
                if id not in self.connectPlayers: continue

                # if the player hasn't given their name yet, use this first command as their name
                # 'help' command
                if command == "help":
                    self.sendHelpMessage(id)

                # 'login' command
                elif command == "login":
                    # login new user
                    if params == "":
                        self.mud.send_message(id, "Unknown command")
                        continue
                    user_name, pass_word = params.split(" ")
                    if (self.mud.hasLoged(user_name)):
                        self.mud.send_message(id, "The user has been loged, please use another user name.")
                        continue
                    self.connectPlayers[id]["is_logined"] = True
                    self.connectPlayers[id]["user_name"] = user_name
                    self.connectPlayers[id]["pass_word"] = pass_word
                    new_log_player = {"user_name": user_name,
                                      "pass_word": pass_word,
                                      "lasting_time": 0,
                                      "is_online": False,
                                      "start_time": 0}
                    self.mud.addLogedPlayers(new_log_player)
                    self.mud.send_message(id, "you have logined successfully with name: %s and password: %s"
                                     % (self.connectPlayers[id]["user_name"], self.connectPlayers[id]["pass_word"]))
                # 'land' command
                elif command == "land":
                    # land user
                    if params == "":
                        self.mud.send_message(id, "Unknown command")
                        continue
                    if params.count(' ') == 0:
                        self.mud.send_message(id, "Wrong Input")
                        continue
                    user_name, pass_word = params.split(" ")[0:2]
                    if not self.mud.hasLoged(user_name):
                        self.mud.send_message(id, "There's not user: %s, please login the new user" % (user_name))
                    elif self.mud.getLogedPlayersInfo(user_name, "pass_word") != pass_word:
                        self.mud.send_message(id, "The password is wrong")
                    else:
                        current_time = time.time()
                        self.connectPlayers[id]["user_name"] = user_name
                        self.connectPlayers[id]["pass_word"] = pass_word
                        self.connectPlayers[id]["start_time"] = current_time
                        self.connectPlayers[id]["is_online"] = True
                        self.mud.setLogedPlayerInfo(self.connectPlayers[id]["user_name"], "is_online", True)
                        self.mud.setLogedPlayerInfo(self.connectPlayers[id]["user_name"], "start_time", current_time)

                        # send message to all players
                        message = "%s entered the game" % self.connectPlayers[id]["user_name"]
                        self.sendMessageToAll(message)

                        # send message to the new land players
                        self.mud.send_message(id, "Welcome to the hall, %s. Type 'help' for a list of commands."
                                         % self.connectPlayers[id]["user_name"])

                # 'rooms' command
                elif command == "rooms":
                    self.mud.send_message(id, "Room List: %s" % ((",").join(self.rooms)))
                    self.mud.send_message(id, "You are in '%s' room now" % (self.connectPlayers[id]["room"]))

                # 'create' command
                elif command == "create":
                    if self.connectPlayers[id]["is_online"] == False:
                        self.mud.send_message(id,"Please land in firstly.")
                        continue
                    if params == "":
                        self.mud.send_message(id, "Please input the room name.")
                    else:
                        params.lower()
                        if self.rooms.count(params) > 0:
                            self.mud.send_message(id, "The room name is used by other")
                            continue
                        self.rooms.append(params)
                        self.mud.send_message(id, "Room List: %s" % ((",").join(self.rooms)))
                        self.mud.send_message(id, "You are in '%s' room now" % (self.connectPlayers[id]["room"]))

                # 'go' command
                elif command == "go":
                    if self.connectPlayers[id]["is_online"] == False:
                        self.mud.send_message(id,"Please land in firstly.")
                        continue
                    if params == "":
                        self.mud.send_message(id, "Please input the room name.")
                    else:
                        params.lower()
                        if self.rooms.count(params) > 0:
                            self.connectPlayers[id]["room"] = params
                            self.mud.send_message(id, "You are in the '%s' room now." % params)
                            message = "%s enter the '%s' room" % (
                                self.connectPlayers[id]["user_name"], self.connectPlayers[id]["room"])
                            self.sendMessageToRoomExceptYourself(id, params, message)
                        else:
                            self.mud.send_message(id, "There's no the room named '%s'" % params)

                # 'exit' command
                elif command == "exit":
                    if self.connectPlayers[id]["is_online"] == False:
                        self.mud.send_message(id,"Please land in firstly.")
                        continue
                    if self.connectPlayers[id]["room"] == "hall":
                        self.mud.send_message(id, "Don't leave the 'hall' room")
                    else:
                        self.mud.send_message(id, "You have leave the '%s' room." % self.connectPlayers[id]["room"])
                        message = "%s left  the '%s' room" % (
                            self.connectPlayers[id]["user_name"], self.connectPlayers[id]["room"])
                        self.sendMessageToRoomExceptYourself(self.connectPlayers[id]["room"], message, id)
                        self.connectPlayers[id]["room"] = "hall"
                        self.mud.send_message(id, "You are in the 'hall' room")

                elif command == "roomchat":
                    if self.connectPlayers[id]["is_online"] == False:
                        self.mud.send_message(id,"Please land in firstly.")
                        continue
                    message = " %s said in the %s: %s" % (self.connectPlayers[id]["user_name"],
                                                                 self.connectPlayers[id]["room"],
                                                                 params)
                    self.sendMessageToRoom(self.connectPlayers[id]["room"], message)

                elif command == "hallchat" or command == "chat":
                    if self.connectPlayers[id]["is_online"] == False:
                        self.mud.send_message(id,"Please land in firstly.")
                        continue
                    message = "%s said in hall: %s" % (self.connectPlayers[id]["user_name"], params)
                    self.sendMessageToAll(message)

                elif command == "talkto":
                    if self.connectPlayers[id]["is_online"] == False:
                        self.mud.send_message(id,"Please land in firstly.")
                        continue
                    if params == "":
                        self.mud.send_message(id, "No message")
                    lisener, message = (params.split(' ', 1) + ["", ""])[0:2]
                    hasTalker = False
                    for pid, pl in self.connectPlayers.items():
                        # if player is in the same room and isn't the player sending the command
                        if self.connectPlayers[pid]["user_name"] == lisener and pid != id:
                            # send them a message telling them that the player left the room
                            message = " %s talk to you : %s" % (self.connectPlayers[id]["user_name"], message)
                            self.sendMessageToSomeone(pid, message)
                            hasTalker = True
                            break
                    if not hasTalker:
                        self.mud.send_message(id, "There's no the talker '%s'" % (lisenter))

                elif command == "21game":
                    if self.connectPlayers[id]["is_online"] == False:
                        self.mud.send_message(id,"Please land in firstly.")
                        continue
                    if not self.gameManager.is_21gaming:
                        self.mud.send_message(id,"Time out.")
                        continue
                    if self.gameManager.answers_21game.has_key(id):
                        self.mud.send_message(id, "You have answer the game, and you have only one chance.")
                        continue
                    self.gameManager.answers_21game[id] = {
                        "user_name": self.connectPlayers[id]["user_name"],
                        "value": None,
                        "time": time.time()
                    }
                    try:
                        val = eval(params)
                        self.gameManager.answers_21game[id]["value"] = val
                        self.mud.send_message(id, "The system has received your answer successfully.")
                    except Exception, e:
                        self.mud.send_message(id, "Input error")
                else:
                    # send back an 'unknown command' message
                    self.mud.send_message(id, "Unknown command: %s" % command)
