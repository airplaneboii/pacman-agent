# baselineTeam.py
# ---------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

import random
import util

from captureAgents import CaptureAgent
from game import Directions
from util import nearestPoint
import time

#import os, sys
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import helper



#################
# Team creation #
#################

def create_team(first_index, second_index, is_red,
                first='StarvingPaccy', second='LittleGhostie', num_training=0):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """
    return [eval(first)(first_index), eval(second)(second_index)]


##########
# Agents #
##########

class DumbAgent(CaptureAgent):
    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None

    def register_initial_state(self, game_state):
        # dodaj graf labirinata (za potrebe pasti) - potrebno dobiti samo enkrat
        layout = str(game_state).split("\n")
        self.graph = helper.generate_graph_from_layout(layout)

        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)
    
    def choose_action(self, game_state):
        # print("------------------------------------------------")
        # Najprej pridobi seznam vseh legalnih potez
        actions = game_state.get_legal_actions(self.index)

        # Pridobi oceno za koristnost vsake poteze
        values = [self.evaluate(game_state, action) for action in actions]

        # Pridobi vse najboljse poteze
        max_value = max(values)
        best_actions = [action for action, value in zip(actions, values) if value == max_value]

        #if type(self) == StarvingPaccy:
        #    print([(x, y) for x, y in zip(actions, values)])
        #    print("[" + str(max_value) + "]")

        return random.choice(best_actions)
    
    def get_successor(self, game_state, action):
        successor = game_state.generate_successor(self.index, action)
        position = successor.get_agent_state(self.index).get_position()
        if position != nearestPoint(position):
            return successor.generate_successor(self.index, action)
        else:
            return successor

    def evaluate(self, game_state, action):
        features = self.get_features(game_state, action)
        weights = self.get_weights(game_state, action)

        #print(action)
        #print(features)
        #print(weights)

        return features * weights

class StarvingPaccy(DumbAgent):
    def get_features(self, game_state, action):
        features = util.Counter()

        # da ve koliko hrane nosi
        agent = game_state.data.agent_states[self.index] # usefull
        numCarrying = agent.num_carrying

        # postavi se na potencialno naslednjo pozicijo
        successor = self.get_successor(game_state, action)
        my_state = successor.get_agent_state(self.index)
        my_current_state = game_state.get_agent_state(self.index)

        # pridobi pozicije
        past_position = None
        current_position = game_state.get_agent_position(self.index)
        my_pos = my_state.get_position()

        if self.get_previous_observation() is not None:
            past_position = self.get_previous_observation().get_agent_position(self.index)

        # preveri ce je ujet
        #is_trapped = helper.is_trap(self.graph, current_position, my_pos)

        # pridobi informacije o nasprotniku
        enemies = [successor.get_agent_state(opponent) for opponent in self.get_opponents(successor)]
        pacmans = [enemy for enemy in enemies if enemy.is_pacman and enemy.get_position() is not None]
        ghosts = [enemy for enemy in enemies if not enemy.is_pacman and enemy.get_position() is not None]
        ghosts_scared_times = [ghost.scared_timer for ghost in ghosts]

        # univerzalna meja na enem mestu
        scared_time_limit = 5

        capsules = game_state.get_blue_capsules() if self.red else game_state.get_red_capsules()
        distance_capsule = min([self.get_maze_distance(my_pos, capsule) for capsule in capsules]) if capsules != [] else 0
        distance_capsule_limit = 5

        food_list = self.get_food(successor).as_list()
        food_list_current = self.get_food(game_state).as_list()
        food_left = len(food_list_current)
        food_list_distances = [self.get_maze_distance(my_pos, food) for food in food_list]
        food_path = min(food_list_distances)

        layout = game_state.data.layout
        my_bases = [layout.agentPositions[i][1] for i in self.get_team(successor)]
        enemy_bases = [layout.agentPositions[i][1] for i in self.get_opponents(successor)]

        # za poiskat pot domov: ugotovis, o kateri koordinati govoris (vzhod-zahod [layout.width] ali sever-jug[layout.height]), 
        # potem pa isces min distance med sabo in tokami po liniji ob srediscu (width oziroma height) - 1
    
        home_base_position = (my_bases[0][0], 0) if my_bases[0][0] == my_bases[1][0] else (0, my_bases[0][1])
        enemy_base_position = (enemy_bases[0][0], 0) if enemy_bases[0][0] == enemy_bases[1][0] else (0, enemy_bases[0][1])
        #print(enemy_base_position, layout.height, layout.width)

        
        # preveri, na kateri polovici si
        # PAZI: GLEJ GLEDE NA TO, KAJ SI TRENUTNO, NE PA KAJ BOS V NASLEDNJEM KORAKU
        # preveri, ce sploh se imas dovolj casa
        if my_state.is_pacman:
            time_left = game_state.data.timeleft
            if home_base_position[0] > 0:
                dir = 0 if (layout.width - home_base_position[0]) < layout.width/2 else -1
                distances = [self.get_maze_distance(my_pos, (dir + layout.width/2, i)) for i in range(1, layout.height - 1) if not layout.walls[int(dir + layout.width/2)][i]]
            else:
                dir = 0 if (layout.height - home_base_position[1]) < layout.height/2 else -1
                distances = [self.get_maze_distance((i, dir + layout.width/2), my_pos) for i in range(1, layout.width - 1) if not layout.walls[i][int(dir + layout.width/2)]]
            dist = min(distances)

            retreat = False if ((time_left / 4 - 20) > dist) else True


            # najprej preveri, ce je nujno domov
            if food_left <= 2 or retreat:
                #dist = self.get_maze_distance(self.start, my_pos)
                features['going_home'] = dist
                if len(ghosts) > 0:

                    features['ghosts_nearby_distance'] = min([self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]) # check this

                    ghosts_dist = [self.get_maze_distance(current_position, ghost.get_position()) for ghost in ghosts]
                    ghosts_current_dist = [self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]
                    ghost_approaching = min(ghosts_dist) - min(ghosts_current_dist)
                    features['going_home_ghost_danger'] = ghost_approaching

                    is_trapped = helper.is_trap(self.graph, current_position, my_pos, ghosts_current_dist)
                    if is_trapped:
                        features['is_trapped'] = 1
                #return features # preveri ce je smiselno

            features['food_path'] = food_path
            features['food_eat'] = abs(len(food_list) - len(food_list_current))
            
            # fix this
            if numCarrying - len(food_list_current) > 0:
                features['going_home'] = dist# * 10
                if len(ghosts) > 0 and ghosts_scared_times != [] and max(ghosts_scared_times) > scared_time_limit:

                    features['ghosts_nearby_distance'] = min([self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]) # check this

                    ghosts_dist = [self.get_maze_distance(current_position, ghost.get_position()) for ghost in ghosts]
                    ghosts_current_dist = [self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]
                    ghost_approaching = min(ghosts_dist) - min(ghosts_current_dist)
                    features['going_home_ghost_danger'] = ghost_approaching# * 10

            if len(ghosts) > 0:
                # BODI PREVIDEN TU ----------------------------------------------------------------------------------------------------------------
                # lahko bi bila situacija P..OG -> P.G -> stestiraj

                # ce ghost blizu (trenutna pozicija), mi pa blizje kapsuli: gremo jo pobrat
                # predpostavka, da niso blizu kapsule in nih ne vidimo
                if (capsules != []):
                    distance_ghosts_capsule = min([self.get_maze_distance(capsules[0], ghost.get_position()) for ghost in ghosts])
                    if (distance_capsule < distance_capsule_limit and distance_capsule < distance_ghosts_capsule):
                        features['eat_capsule'] = distance_capsule                

                if (ghosts_scared_times != [] and max(ghosts_scared_times) > scared_time_limit):
                    pass
                else:
                    # Tu se izogiba duhcom

                    features['ghosts_nearby_distance'] = min([self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]) # check this

                    features['going_home'] = dist

                    ghosts_dist = [self.get_maze_distance(current_position, ghost.get_position()) for ghost in ghosts]

                    # ce ghost preblizu: ne pobirat - pomembno!!
                    if (min(ghosts_dist) <= 2):
                        features.pop('food_eat', None)

                    ghosts_current_dist = [self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]
                    ghost_approaching = min(ghosts_dist) - min(ghosts_current_dist)
                    features['going_home_ghost_danger'] = ghost_approaching

                    # prioriteta: ozogni se pasti
                    # ali gre v past (relevantno, če duhci v bližini)
                    is_trapped = helper.is_trap(self.graph, current_position, my_pos, ghosts_current_dist)
                    if is_trapped:
                        print("trap")
                        features.pop('going_home_ghost_danger', None)
                        features['is_trapped'] = 1
            
            if 2*numCarrying >= len(food_list_current):
                features['going_home'] = dist   
            
            if len(pacmans)> 0:
                pacmans_distances = [self.get_maze_distance(my_pos, pacman.get_position()) for pacman in pacmans]
                minimal_pacman_distance = min(pacmans_distances)
                features['pacman_nearby_distance'] = minimal_pacman_distance

            
        elif my_state.scared_timer > 0 and not my_state.is_pacman:
            # izogibaj se pacmanov
            if len(pacmans) > 0:
                pacman_distances_future = [self.get_maze_distance(my_pos, pacman.get_position()) for pacman in pacmans]
                pacman_distances_current = [self.get_maze_distance(current_position, pacman.get_position()) for pacman in pacmans]

                if len(pacman_distances_future) > 0 and len(pacman_distances_current) > 0:
                    future_min = min(pacman_distances_future)
                    current_min = min(pacman_distances_current)
                    diff = future_min - current_min
                    features['pacman_danger_close'] = diff

                else:
                    food_list = self.get_food(successor).as_list()
                    food_list_distances = [self.get_maze_distance(my_pos, food) for food in food_list]
                    food_path = min(food_list_distances)
                    features['food_path_scared'] = food_path
        
        else:
            pacmanDanger = False if len(ghosts) == 0 else True

            # ce v moji polovici: izogni se duhcu, mogoce najde drugo pot
            if not my_current_state.is_pacman and pacmanDanger > 0:
                ghosts_dist = [self.get_maze_distance(current_position, ghost.get_position()) for ghost in ghosts]
                ghosts_current_dist = [self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]
                ghost_approaching = min(ghosts_dist) - min(ghosts_current_dist)
                features['going_home_ghost_danger'] = ghost_approaching
            
            # Edge case - ce si trenutno pacman in nosis hrano / je v blizini duhec, se umakni na svojo polovico
            if my_current_state.is_pacman and (numCarrying or pacmanDanger) > 0: 
                features["drop_food"] = 1
            
            # Pojdi na nasprotnikovo polovico, vmes pa isci, ce je kje kaksen pacman -> ce je, ga napadi
            pacmans_distances = [self.get_maze_distance(my_pos, pacman.get_position()) for pacman in pacmans]
            if len(pacmans_distances) > 0:
                minimal_pacman_distance = min(pacmans_distances)
                features['pacman_nearby_distance'] = minimal_pacman_distance
            
            features['food_path'] = food_path
        
        # ni dobro ce stojis na mestu
        if action == Directions.STOP:
            features['stop_move'] = 1

        # ni ravno dobro ce se vracas
        rev = Directions.REVERSE[game_state.get_agent_state(self.index).configuration.direction]
        if action == rev:
            features['reverse_move'] = 1

        return features
    
    def get_weights(self, game_state, action):
        weights = util.Counter()
        weights['food_path'] = -2                  # 0, 1, 2, 3, 4 ........... | vecje je, dlje je hrana (vecje = slabse)
        weights['food_eat'] = 100                  # 0, 1 .................... | ali poje hrano s to potezo
        weights['ghosts_nearby_distance'] = 10     # 0, 1, 2, 3, 4 ........... | vecje je, dlje je duhec (vecje = boljse)
        weights['pacman_danger_close'] = 40        # naceloma 0 ali 1, maybe 2 | vecje je, boljse je
        weights['pacman_nearby_distance'] = -800   # 0, 1, 2, 3, 4 ........... | vecje je, dlje je pacman (vecje = slabse)
        weights['stop_move'] = -500                # 0, 1 .................... | zavraca neaktivnost
        weights['reverse_move'] = -1               # 0, 1 .................... | zavraca vracanje nazaj
        weights['going_home'] = -8                 # 0, 1, 2, 3, 4 ........... | vecje je, dlje je dom (vecje = slabse)    # preveri ce *10
        weights['going_home_ghost_danger'] = -120  # naceloma 0 ali 1, maybe 2 | vecje je, slabse je                       # preveri ce *10
        weights['drop_food'] = 10000
        weights['is_trapped'] = -200               # 0, 1 .................... | ali je ujet                               # ali se premika v past
        weights['eat_capsule'] = -100              # 0, 1, 2, 3, 4 ........... | vecje je, slabse je                       # treba testirati, koliko potrebno
        weights['food_path_scared'] = -10          # 0, 1, 2, 3, 4 ........... | vecje je, slabse je
        
        
        # backup
#        weights = util.Counter()
#        weights['food_path'] = -1                  # 0, 1, 2, 3, 4 ........... | vecje je, dlje je hrana (vecje = slabse)
#        weights['food_eat'] = 100                  # 0, 1 .................... | ali poje hrano s to potezo
#        weights['ghosts_nearby_distance'] = 10     # 0, 1, 2, 3, 4 ........... | vecje je, dlje je duhec (vecje = boljse)
#        weights['pacman_danger_close'] = 40        # naceloma 0 ali 1, maybe 2 | vecje je, boljse je
#        weights['pacman_nearby_distance'] = -1000  # 0, 1, 2, 3, 4 ........... | vecje je, dlje je pacman (vecje = slabse)
#        weights['stop_move'] = -100                # 0, 1 .................... | zavraca neaktivnost
#        weights['reverse_move'] = -2               # 0, 1 .................... | zavraca vracanje nazaj
#        weights['going_home'] = -5                 # 0, 1, 2, 3, 4 ........... | vecje je, dlje je dom (vecje = slabse)    # preveri ce *10
#        weights['going_home_ghost_danger'] = -100  # naceloma 0 ali 1, maybe 2 | vecje je, slabse je                       # preveri ce *10
#        weights['drop_food'] = 10000
#        weights['is_trapped'] = -200               # 0, 1 .................... | ali je ujet                               # ali se premika v past
#        weights['eat_capsule'] = -100              # 0, 1, 2, 3, 4 ........... | vecje je, slabse je                       # treba testirati, koliko potrebno
#        weights['food_path_scared'] = -10          # 0, 1, 2, 3, 4 ........... | vecje je, slabse je
        return weights


# tale se naj tudi ves cas premika proti najvecji gostoti svoje hrane -> utezi naj bodo majhne
class LittleGhostie(DumbAgent):
    def get_features(self, game_state, action):
        features = util.Counter()

        # da ve koliko hrane nosi
        agent = game_state.data.agent_states[self.index] # usefull
        numCarrying = agent.num_carrying

        # postavi se na potencialno naslednjo pozicijo
        successor = self.get_successor(game_state, action)
        my_state = successor.get_agent_state(self.index)

        # pridobi pozicije
        past_position = None
        current_position = game_state.get_agent_position(self.index)
        my_pos = my_state.get_position()

        if self.get_previous_observation() is not None:
            past_position = self.get_previous_observation().get_agent_position(self.index)

        # pridobi informacije o nasprotniku
        enemies = [successor.get_agent_state(opponent) for opponent in self.get_opponents(successor)]
        pacmans = [enemy for enemy in enemies if enemy.is_pacman and enemy.get_position() is not None]
        ghosts = [enemy for enemy in enemies if not enemy.is_pacman and enemy.get_position() is not None]
        ghosts_scared_times = [ghost.scared_timer for ghost in ghosts]

        # univerzalna meja na enem mestu
        scared_time_limit = 5

        capsules = game_state.get_blue_capsules() if self.red else game_state.get_red_capsules()
        distance_capsule = min([self.get_maze_distance(my_pos, capsule) for capsule in capsules]) if capsules != [] else 0
        distance_capsule_limit = 5

        my_food = [food for food in self.get_food_you_are_defending(game_state).as_list()]

        food_list = self.get_food(successor).as_list()
        food_list_current = self.get_food(game_state).as_list()
        food_left = len(food_list_current)
        food_list_distances = [self.get_maze_distance(my_pos, food) for food in food_list]
        food_path = min(food_list_distances)

        layout = game_state.data.layout
        my_bases = [layout.agentPositions[i][1] for i in self.get_team(successor)]
        enemy_bases = [layout.agentPositions[i][1] for i in self.get_opponents(successor)]

        # za poiskat pot domov: ugotovis, o kateri koordinati govoris (vzhod-zahod [layout.width] ali sever-jug[layout.height]), 
        # potem pa isces min distance med sabo in tokami po liniji ob srediscu (width oziroma height) - 1
    
        home_base_position = (my_bases[0][0], 0) if my_bases[0][0] == my_bases[1][0] else (0, my_bases[0][1])
        enemy_base_position = (enemy_bases[0][0], 0) if enemy_bases[0][0] == enemy_bases[1][0] else (0, enemy_bases[0][1])

        # preveri, kaj bos delal
        if my_state.is_pacman:
            # si na nasprotnikovi polovici -> ce ti nihce nic ne je, poskusi ti pojest kaj, kar je blizu, a bodi previden
            # Popravi ta del, ker se ni v redu (uporabi tudi Tomazevo funkcijo)
            agent = game_state.data.agent_states[self.index] # usefull
            numCarrying = agent.num_carrying

            time_left = game_state.data.timeleft
            if home_base_position[0] > 0:
                dir = 0 if (layout.width - home_base_position[0]) < layout.width/2 else -1
                distances = [self.get_maze_distance(my_pos, (dir + layout.width/2, i)) for i in range(1, layout.height - 1) if not layout.walls[int(dir + layout.width/2)][i]]
            else:
                dir = 0 if (layout.height - home_base_position[1]) < layout.height/2 else -1
                distances = [self.get_maze_distance((i, dir + layout.width/2), my_pos) for i in range(1, layout.width - 1) if not layout.walls[i][int(dir + layout.width/2)]]
            dist = min(distances)

            retreat = False if ((time_left / 4 - 20) > dist) else True

            
#            if len(enemy_food) <= 2 and numCarrying > 0:
#                pass # TODO
            # najprej preveri, ce je nujno domov
            if food_left <= 2 or retreat:
                features['going_home'] = dist
                if len(ghosts) > 0:
                    ghosts_dist = [self.get_maze_distance(current_position, ghost.get_position()) for ghost in ghosts]
                    ghosts_current_dist = [self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]
                    ghost_approaching = min(ghosts_dist) - min(ghosts_current_dist)
                    features['going_home_ghost_danger'] = ghost_approaching

                    is_trapped = helper.is_trap(self.graph, current_position, my_pos, ghosts_current_dist)
                    if is_trapped:
                        features['is_trapped'] = 1
            
            features['food_path'] = food_path
            features['food_eat'] = abs(len(food_list) - len(food_list_current))

            if my_state.scared_timer > 5:
                if numCarrying - len(food_list_current) > 0:
                    features['going_home'] = dist# * 10
                    
                if len(ghosts) > 0:
                    if (capsules != []):
                        distance_ghosts_capsule = min([self.get_maze_distance(capsules[0], ghost.get_position()) for ghost in ghosts])
                        if (distance_capsule < distance_capsule_limit and distance_capsule < distance_ghosts_capsule):
                            features['eat_capsule'] = distance_capsule  
                    
                    if not (ghosts_scared_times != [] and max(ghosts_scared_times) > scared_time_limit):
                        features['going_home'] = dist

                        ghosts_dist = [self.get_maze_distance(current_position, ghost.get_position()) for ghost in ghosts]

                            # ce ghost preblizu: ne pobirat - pomembno!!
                        if (min(ghosts_dist) <= 2):
                            features.pop('food_eat', None)

                        ghosts_current_dist = [self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]
                        ghost_approaching = min(ghosts_dist) - min(ghosts_current_dist)
                        features['going_home_ghost_danger'] = ghost_approaching

                        # prioriteta: ozogni se pasti
                            # ali gre v past (relevantno, če duhci v bližini)
                        is_trapped = helper.is_trap(self.graph, current_position, my_pos, ghosts_current_dist)
                        if is_trapped:
                            features['is_trapped'] = 1

                if 2.5*numCarrying > len(food_list_current):
                    features['going_home'] = dist   

                if len(pacmans)> 0:
                    pacmans_distances = [self.get_maze_distance(my_pos, pacman.get_position()) for pacman in pacmans]
                    minimal_pacman_distance = min(pacmans_distances)
                    features['pacman_nearby_distance'] = minimal_pacman_distance

            else:
                # vrni se domov
                features['going_home'] = dist
                if len(ghosts) > 0:
                    ghosts_dist = [self.get_maze_distance(current_position, ghost.get_position()) for ghost in ghosts]
                    ghosts_current_dist = [self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]
                    ghost_approaching = min(ghosts_dist) - min(ghosts_current_dist)
                    features['going_home_ghost_danger'] = ghost_approaching


        elif my_state.scared_timer > 0: # 10
            # izogibaj se pacmanov in pojdi cim hitreje na nasprotnikovo polovico
            
            if len(pacmans) > 0:
                pacman_distances_future = [self.get_maze_distance(my_pos, pacman.get_position()) for pacman in pacmans]
                pacman_distances_current = [self.get_maze_distance(current_position, pacman.get_position()) for pacman in pacmans]

                if len(pacman_distances_future) > 0 and len(pacman_distances_current) > 0:
                    future_min = min(pacman_distances_future)
                    current_min = min(pacman_distances_current)
                    if future_min > current_min:
                        features['scared_avoiding_pacman'] = 1

            else:
                food_list = self.get_food(successor).as_list()
                food_list_distances = [self.get_maze_distance(my_pos, food) for food in food_list]
                food_path = min(food_list_distances)
                features['food_path_scared'] = food_path
        
        else:
            # poglej, ce ti kdo kaj je, pomakni se nekam v sredino, poskusi z blagim napadom
            if self.get_previous_observation() is not None:
                past_food = self.get_food_you_are_defending(self.get_previous_observation()).as_list()
                current_food = self.get_food_you_are_defending(game_state).as_list()
                missing_food = [food for food in past_food if food not in current_food]

                if len(missing_food) > 0:
                    # nekdo nekaj je, poisci ga
                    missing_food_dist = [self.get_maze_distance(my_pos, food) for food in missing_food]
                    features['missing_food'] = min(missing_food_dist)
            
            # preveri, ce imas koga v blizini
            pacmans_distances = [self.get_maze_distance(my_pos, pacman.get_position()) for pacman in pacmans]
            if len(pacmans_distances) > 0:
                minimal_pacman_distance = min(pacmans_distances)
                features['minimal_pacman_distance'] = minimal_pacman_distance
            
            # Tu pride Tomazeva funkcija za iskanje hrane (TODO) (preveri, kaj se zgodi, ce das to izven if stavka)
            my_food_distance = [self.get_maze_distance(my_pos, food) for food in my_food]
            resting_place_distance = int(sum(my_food_distance)/len(my_food_distance))
            features['resting_place_distance'] = resting_place_distance # spremeni to glede na to ali te ta smer spravi blizje srediscu ali ne

            #base_dist_random = random.randint(1, 3)
            #if home_base_position[0] > 0:
            #    middle_dir = 0 if (layout.width - home_base_position[0]) < layout.width/2 else -1
            #    middle_distances = [self.get_maze_distance(my_pos, (middle_dir + layout.width/2, i)) for i in range(1, layout.height - base_dist_random) if not layout.walls[int(middle_dir + layout.width/2)][i]]
            #else:
            #    middle_dir = 0 if (layout.height - home_base_position[1]) < layout.height/2 else -1
            #    middle_distances = [self.get_maze_distance((i, middle_dir + layout.width/2), my_pos) for i in range(1, layout.width - base_dist_random) if not layout.walls[i][int(middle_dir + layout.width/2)]]
            #min_middle_dir = min(middle_distances)
            #features['resting_place_distance_random'] = min_middle_dir

     
        # ni dobro ce stojis na mestu
        if action == Directions.STOP:
            features['stop'] = 1

        # ni ravno dobro ce se vracas
        rev = Directions.REVERSE[game_state.get_agent_state(self.index).configuration.direction]
        if action == rev:
            features['reverse'] = 1
        
        # return
        return features

    def get_weights(self, game_state, action):
        weights = util.Counter()
        weights['scared_avoiding_pacman'] = 120          # 0, 1 ............ | 1 if scared in v blizini pacmana else 0 (vecje = boljse)
        weights['food_path'] = -2                        # 0, 1, 2, 3, 4 ... | vecje je, dlje je hrana (vecje = slabse)
        weights['missing_food'] = -100                   # 0, 1, 2, 3, 4 ... | vecje je, dlje se slabo dogaja (vecje = slabse)
        weights['minimal_pacman_distance'] = -1000       # 0, 1, 2, 3, 4 ... | vecje je, slabse je
        weights['resting_place_distance'] = -2           # 0, 1, 2, 3, 4 ... | vecje je, slabse je
        weights['stop'] = -210                           # 0, 1 ............ | zavraca neaktivnost
        weights['reverse'] = -1                          # 0, 1 ............ | zavraca vracanje nazaj

        weights['going_home'] = -10                      # 0, 1, 2, 3, 4 ........... | vecje je, dlje je dom (vecje = slabse)    # preveri ce *10
        weights['going_home_ghost_danger'] = -120        # naceloma 0 ali 1, maybe 2 | vecje je, slabse je                       # preveri ce *10
        weights['food_eat'] = 100                        # 0, 1 .................... | ali poje hrano s to potezo
        weights['pacman_nearby_distance'] = -1010        # 0, 1, 2, 3, 4 ........... | vecje je, dlje je pacman (vecje = slabse)
        weights['food_path_scared'] = -20                # 0, 1, 2, 3, 4 ........... | vecje je, dlje je hrana (vecje = slabse)
        weights['is_trapped'] = -200                     # 0, 1 .................... | ali je ujet
        weights['eat_capsule'] = -100                    # 0, 1, 2, 3, 4 ........... | vecje je, slabse je

        #weights['resting_place_distance_random'] = -1    # 0, 1, 2, 3, 4 ........... | vecje je, slabse je


        # backup
#        weights['missing_food_distance'] = -1        # 0, 1, 2, 3, 4 ... | vecje je, dlje se slabo dogaja (vecje = slabse) (ko je pacman)
#        weights['scared_avoiding_pacman'] = 100      # 0, 1 ............ | 1 if scared in v blizini pacmana else 0
#        weights['food_path'] = -1                    # 0, 1, 2, 3, 4 ... | vecje je, dlje je hrana (vecje = slabse)
#        weights['missing_food'] = -100               # 0, 1, 2, 3, 4 ... | vecje je, dlje se slabo dogaja (vecje = slabse) (isto kot missing_food_distance, samo da je tokrat kot ghost)
#        weights['minimal_pacman_distance'] = -1000   # 0, 1, 2, 3, 4 ... | vecje je, slabse je
#        weights['resting_place_distance'] = -1       # 0, 1, 2, 3, 4 ... | vecje je, slabse je
#        weights['stop'] = -100                       # 0, 1 ............ | zavraca neaktivnost
#        weights['reverse'] = -2                      # 0, 1 ............ | zavraca vracanje nazaj
#
#        weights['going_home'] = -5                   # 0, 1, 2, 3, 4 ........... | vecje je, dlje je dom (vecje = slabse)    # preveri ce *10
#        weights['going_home_ghost_danger'] = -100    # naceloma 0 ali 1, maybe 2 | vecje je, slabse je                       # preveri ce *10
#        weights['food_eat'] = 100                    # 0, 1 .................... | ali poje hrano s to potezo
#        weights['pacman_nearby_distance'] = -1000    # 0, 1, 2, 3, 4 ........... | vecje je, dlje je pacman (vecje = slabse)
#        weights['food_path_scared'] = -10            # 0, 1, 2, 3, 4 ... | vecje je, dlje je hrana (vecje = slabse)
        return weights