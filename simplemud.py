"""    
A simple Multi-User Dungeon (MUD) game. Players can talk to each other, examine
their surroundings and move between rooms.

Some ideas for things to try adding:
    * More rooms to explore
    * An 'emote' command e.g. 'emote laughs out loud' -> 'Mark laughs out loud'
    * A 'whisper' command for talking to individual players
    * A 'shout' command for yelling to players in all rooms
    * Items to look at in rooms e.g. 'look fireplace' -> 'You see a roaring, glowing fire'
    * Items to pick up e.g. 'take rock' -> 'You pick up the rock'
    * Monsters to fight
    * Loot to collect
    * Saving players accounts between sessions
    * A password login
    * A shop from which to buy items

author: Mark Frimston - mfrimston@gmail.com
"""

import time

# import the MUD server class
from mudserver import MudServer

# structure defining the rooms in the game. Try adding more rooms to the game!
rooms = ["hall"]

# read players file
def loadPlayersInformation(file_name):
    fp = open(file_name, 'r')
    log_players = {}
    while 1:
        line = fp.readline()
        if not line:
            break
        user_name,pass_word,lasting_time = line.split(" ")
        user_name.strip()
        pass_word.strip()
        lasting_time.strip()
        log_players[user_name] = {
            "user_name":user_name,
            "pass_word":pass_word,
            "lasting_time":float(lasting_time),
            "is_online":False,
            "start_time":0
        }
    return log_players

# stores the logined players in the game
logPlayers = {}
logPlayers = loadPlayersInformation('playerInfo.txt')

# start the server
mud = MudServer()
mud.setLogedPlayers(logPlayers)

# stores the players in the game
connectPlayers = {}

# 21gaming
is_21gaming = False
start_time_21game = 0
answers_21game = {}

# main game loop. We loop forever (i.e. until the program is terminated)
while True:

	# pause for 1/5 of a second on each loop, so that we don't constantly 
	# use 100% CPU time
    time.sleep(0.2)

    # 21 game
    if not is_21gaming and int(time.strftime("%M")) == 30:
        is_21gaming = True
        start_time_21game = time.time()
        #产生4个10以内的随机数,发送给每一个玩家

    if is_21gaming:
        if time.time() - start_time_21game >= 30.0:
            is_21gaming = False
            #发布结果


    # 'update' must be called in the loop to keep the game running and give
    # us up-to-date information
    mud.update()

    # go through any newly connected players
    for id in mud.get_new_players():
    
        # add the new player to the dictionary, noting that they've not been
        # named yet.
        # The dictionary key is the player's id number. Start them off in the 
        # 'Tavern' room.
        # Try adding more player stats - level, gold, inventory, etc
        connectPlayers[id] = {
            "user_name": None,
            "room": "hall",
            "lasting_time":0,
            "start_time":0,
            "is_logined":False,
            "pass_word":"",
        }
        # send the new player a prompt for their name
        mud.send_connect_message(id)
    
    # go through any recently disconnected players    
    for id in mud.get_disconnected_players():
    
        # if for any reason the player isn't in the player map, skip them and 
        # move on to the next one
        if id not in connectPlayers: continue
        
        # go through all the players in the game
        for pid,pl in connectPlayers.items():
            # send each player a message to tell them about the diconnected player
            mud.send_message(pid,"%s quit the game" % connectPlayers[id]["user_name"])

        # log user message
        mud.offLogedPlayer(connectPlayers[id]["user_name"])

        # remove the player's entry in the player dictionary
        del(connectPlayers[id])

    # go through any new commands sent from players
    for id,command,params in mud.get_commands():
    
        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in connectPlayers: continue
    
        # if the player hasn't given their name yet, use this first command as their name
        # 'help' command
        if command == "help":
            # send the player back the list of possible commands
            mud.send_message(id, "Commands:")
            mud.send_message(id, "  say <message>  - Says something out loud, e.g. 'say Hello'")
            # mud.send_message(id,"  look           - Examines the surroundings, e.g. 'look'")
            # mud.send_message(id,"  go <exit>      - Moves through the exit specified, e.g. 'go outside'")
            mud.send_message(id, "  login <username> <password> - login new user ,e.g. 'login zjg 123456")
            mud.send_message(id, "  land <username> <password> - land the user ,e.g. 'land zjg 123456'")

        # 'login' command
        elif command == "login":
            # login new user
            if params == "":
                mud.send_message(id, "Unknown command")
                continue
            user_name,pass_word = params.split(" ")
            if(mud.hasLoged(user_name)):
                mud.send_message(id,"The user has been loged, please use another user name.")
                continue
            connectPlayers[id]["is_logined"] = True
            connectPlayers[id]["user_name"] = user_name
            connectPlayers[id]["pass_word"] = pass_word
            new_log_player = {"user_name":user_name,
                      "pass_word":pass_word,
                      "lasting_time":0,
                      "is_online":False,
                      "start_time":0}
            mud.addLogedPlayers(new_log_player)
            mud.send_message(id,"you have logined successfully with name: %s and password: %s"
                             % (connectPlayers[id]["user_name"],connectPlayers[id]["pass_word"]))
        # 'land' command
        elif command == "land":
            # land user
            if params == "":
                mud.send_message(id, "Unknown command")
                continue
            if params.count(' ') == 0:
                mud.send_message(id, "Wrong Input")
                continue
            user_name,pass_word = params.split(" ")[0:2]
            if not mud.hasLoged(user_name):
                mud.send_message(id, "There's not user: %s, please login the new user" % (user_name))
            elif mud.getLogedPlayersInfo(user_name,"pass_word") != pass_word:
                mud.send_message(id,"The password is wrong")
            else:
                current_time = time.time()
                connectPlayers[id]["user_name"] = user_name
                connectPlayers[id]["pass_word"] = pass_word
                connectPlayers[id]["start_time"] = current_time
                mud.setLogedPlayerInfo(connectPlayers[id]["user_name"],"is_online",True)
                mud.setLogedPlayerInfo(connectPlayers[id]["user_name"],"start_time",current_time)
                # send message to all players
                for pid, pl in connectPlayers.items():
                    # send each player a message to tell them about the new player
                    mud.send_message(pid, "%s entered the game" % connectPlayers[id]["user_name"])
                # send message to the new land players
                mud.send_message(id,"""Welcome to the hall, %s. Type 'help' for a list of commands.""" % connectPlayers[id]["user_name"])

        # 'say' command
        elif command == "chat":
            # go through every player in the game
            for pid,pl in connectPlayers.items():
                # if they're in the same room as the player
                if connectPlayers[pid]["room"] == connectPlayers[id]["room"]:
                    # send them a message telling them what the player said
                    mud.send_message(pid,"%s says: %s" % (connectPlayers[id]["user_name"],params) )
                    # some other, unrecognised command
        # 'save' command
        elif command == "save":
            mud.savePlayers()

        # 'rooms' command
        elif command == "rooms":
            mud.send_message(id,"Room List: %s" %((",").join(rooms)))
            mud.send_message(id,"You are in '%s' room now" %(connectPlayers[id]["room"]))

        # 'create' command
        elif command == "create":
            if params == "":
                mud.send_message(id, "Please input the room name.")
            else:
                params.lower()
                if rooms.count(params) > 0:
                    mud.send_message(id, "The room name is used by other")
                    continue
                rooms.append(params)
                mud.send_message(id, "Room List: %s" % ((",").join(rooms)))
                mud.send_message(id, "You are in '%s' room now" % (connectPlayers[id]["room"]))

        # 'go' command
        elif command == "go":
            if params == "":
                mud.send_message(id, "Please input the room name.")
            else:
                params.lower()
                if rooms.count(params) > 0:
                    connectPlayers[id]["room"] = params
                    mud.send_message(id,"You are in the '%s' room" %(params))

                    for pid, pl in connectPlayers.items():
                        # if player is in the same room and isn't the player sending the command
                        if connectPlayers[pid]["room"] == connectPlayers[id]["room"] and pid != id:
                            # send them a message telling them that the player left the room
                            mud.send_message(pid, "%s enter the '%s' room" % (connectPlayers[id]["user_name"],
                                                                                   connectPlayers[id]["room"]))
                else:
                    mud.send_message(id, "There's no the room named '%s'" %(params))

        # 'exit' command
        elif command == "exit":
            if connectPlayers[id]["room"] == "hall":
                mud.send_message(id, "Don't leave the 'hall' room")
            else:
                mud.send_message(id,"You have leave the '%s' room." %(connectPlayers[id]["room"]))
                for pid, pl in connectPlayers.items():
                    # if player is in the same room and isn't the player sending the command
                    if connectPlayers[pid]["room"] == connectPlayers[id]["room"] and pid != id:
                        # send them a message telling them that the player left the room
                        mud.send_message(pid, "%s left  the '%s' room" % (connectPlayers[id]["user_name"],
                                                                          connectPlayers[id]["room"]))
                connectPlayers[id]["room"] = "hall"
                mud.send_message(id,"You are in the 'hall' room")

        elif command == "roomchat":
            for pid, pl in connectPlayers.items():
                # if player is in the same room and isn't the player sending the command
                if connectPlayers[pid]["room"] == connectPlayers[id]["room"] and pid != id:
                    # send them a message telling them that the player left the room
                    mud.send_message(pid, " %s said in the room: %s" %(connectPlayers[id]["user_name"],params))

        elif command == "hallchat":
            for pid, pl in connectPlayers.items():
                mud.send_message(pid,"%s said in hall: %s" %(connectPlayers[id]["user_name"],params))

        elif command == "talkto":
            if params == "":
                mud.send_message(id,"No message")
            lisener,message = (params.split(' ',1) + ["",""])[0:2]
            hasTalker = False
            for pid, pl in connectPlayers.items():
                # if player is in the same room and isn't the player sending the command
                if connectPlayers[pid]["user_name"] == lisener and pid != id:
                    # send them a message telling them that the player left the room
                    mud.send_message(pid, " %s talk to you : %s" %(connectPlayers[id]["user_name"],message))
                    hasTalker = True
                    break
            if not hasTalker:
                mud.send_message(id,"There's no the talker '%s'" %(lisenter))

        elif command == "21game":
            pass
        else:
            # send back an 'unknown command' message
            mud.send_message(id, "Unknown command: %s" % command)
    """
        # 'look' command
        elif command == "look":
        
            # store the player's current room
            rm = rooms[players[id]["room"]]
            
            # send the player back the description of their current room
            mud.send_message(id, rm["description"])
            
            playershere = []
            # go through every player in the game
            for pid,pl in players.items():
                # if they're in the same room as the player
                if players[pid]["room"] == players[id]["room"]:
                    # add their name to the list
                    playershere.append(players[pid]["name"])
                    
            # send player a message containing the list of players in the room
            mud.send_message(id, "Players here: %s" % ", ".join(playershere))
            
            # send player a message containing the list of exits from this room
            mud.send_message(id, "Exits are: %s" % ", ".join(rm["exits"]))

        # 'go' command
        elif command == "go":
            
            # store the exit name
            ex = params.lower()
            
            # store the player's current room
            rm = rooms[players[id]["room"]]
            
            # if the specified exit is found in the room's exits list
            if ex in rm["exits"]:
            
                # go through all the players in the game
                for pid,pl in players.items():
                    # if player is in the same room and isn't the player sending the command
                    if players[pid]["room"] == players[id]["room"] and pid!=id:
                        # send them a message telling them that the player left the room
                        mud.send_message(pid,"%s left via exit '%s'" % (players[id]["name"],ex))
                        
                # update the player's current room to the one the exit leads to
                players[id]["room"] = rm["exits"][ex]
                rm = rooms[players[id]["room"]]
                
                # go through all the players in the game
                for pid,pl in players.items():
                    # if player is in the same (new) room and isn't the player sending the command
                    if players[pid]["room"] == players[id]["room"] and pid!=id:
                        # send them a message telling them that the player entered the room
                        mud.send_message(pid,"%s arrived via exit '%s'" % (players[id]["name"],ex))
                        
                # send the player a message telling them where they are now
                mud.send_message(id,"You arrive at '%s'" % players[id]["room"])
                
            # the specified exit wasn't found in the current room
            else:
                # send back an 'unknown exit' message
                mud.send_message(id, "Unknown exit '%s'" % ex)
    """


