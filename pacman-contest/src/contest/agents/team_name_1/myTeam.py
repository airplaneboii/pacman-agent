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
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)
    
    def choose_action(self, game_state):
        #print("------------------------------------------------")
        # Najprej pridobi seznam vseh legalnih potez
        actions = game_state.get_legal_actions(self.index)

        # Pridobi oceno za koristnost vsake poteze
        values = [self.evaluate(game_state, action) for action in actions]
        #if type(self) == LittleGhostie:
        #    print([(x, y) for x, y in zip(actions, values)])
        max_value = max(values)
        best_actions = [action for action, value in zip(actions, values) if value == max_value]
        #print(values)
        
        return random.choice(best_actions)
    
    def get_successor(self, game_state, action):
        successor = game_state.generate_successor(self.index, action)
        position = successor.get_agent_state(self.index).get_position()
        if position != nearestPoint(position):
            return successor.generate_successor(self.index, action)
        else:
            return successor

#    def evaluate(self, game_state, action):
#        features = self.get_features(game_state, action)
#        weights = self.get_weights(game_state, action)
#
#        if type(self) == LittleGhostie:
#            evaluation = evaluate(game_state, action)
#
#        #if type(self) == LittleGhostie:
#        #    #print(features)
#        #    #print(weights)
#        #    #print(features * weights)
#
#        # vrne vsoto produktov istoimenskih komponent
#        return features * weights

#class StarvingPaccy(DumbAgent):
#    def get_features(self, game_state, action):
#        features = util.Counter()
#
#        # postavi se na potencialno naslednjo pozicijo
#        successor = self.get_successor(game_state, action)
#
#        my_state = successor.get_agent_state(self.index)
#        my_pos = my_state.get_position()
#
#        # preveri, na kateri polovici si
#        if my_state.is_pacman:
#            # si na nasprotnikovi polovici
#            print("attack")
#            
#        elif my_state.scared_timer > 0:
#            # izogibaj se pacmanov
#            print("RUNNN")
#        
#        else:
#            # Pojdi na nasprotnikovo polovico, vmes pa isci, ce je kje kaksen pacman -> ce je, ga napadi
#            print("Go or eat")
#            
#
#        return features
#    
#    def get_weights(self, game_state, action):
#        return {}

class LittleGhostie(DumbAgent):
    def evaluate(self, game_state, action):
        score = 0

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

        # preveri, kaj bos delal
        if my_state.is_pacman:
            # si na nasprotnikovi polovici -> ce ti nihce nic ne je, poskusi ti pojest kaj, kar je blizu, a bodi previden
            agent = game_state.data.agent_states[self.index] # usefull
            numCarrying = agent.num_carrying

            # Preveri, ce ti kdo kaj jé
            if self.get_previous_observation() is not None:
                
                past_food = self.get_food_you_are_defending(self.get_previous_observation()).as_list()
                current_food = self.get_food_you_are_defending(game_state).as_list()
                missing_food = [food for food in past_food if food not in current_food]

                if len(missing_food) > 0:
                    # nekdo nekaj je, vrni se domov
                    missing_food_dist = [self.get_maze_distance(my_pos, food) for food in missing_food]
                    score -= min(missing_food_dist)
                    #features['missing_food_distance'] = min(missing_food_dist)
                
                enemy_food = self.get_food(game_state).as_list()
                if len(enemy_food) <= 2 and numCarrying > 0:
                    pass #it's probably better to solve this in choose_action()
                    
            #score += 0 # bigbrain (delete this)

            
        elif my_state.scared_timer > 0:
            # izogibaj se pacmanov in pojdi cim hitreje na nasprotnikovo polovico
            
            if len(pacmans) > 0:
                pacman_distances_future = [self.get_maze_distance(my_pos, pacman.get_position()) for pacman in pacmans]
                pacman_distances_current = [self.get_maze_distance(current_position, pacman.get_position()) for pacman in pacmans]

                if len(pacman_distances_future) > 0 and len(pacman_distances_current) > 0:
                    future_min = min(pacman_distances_future)
                    current_min = min(pacman_distances_current)
                    if future_min > current_min:
                        score += 100
                    #score += 0
                    #features['avoiding_pacman'] = 1 if future_min > current_min else 0
                    #print(features['avoiding_pacman'])

            else:
                food_list = self.get_food(successor).as_list()
                food_list_distances = [self.get_maze_distance(my_pos, food) for food in food_list]
                food_path = min(food_list_distances)
                score -= food_path

                # preveri, ce se premaknes blizje pacmanu -> TO SE NE ZGODI
        
        else:
            # poglej, ce ti kdo kaj je, pomakni se nekam v sredino, poskusi z blagim napadom
            if self.get_previous_observation() is not None:
                past_food = self.get_food_you_are_defending(self.get_previous_observation()).as_list()
                current_food = self.get_food_you_are_defending(game_state).as_list()
                missing_food = [food for food in past_food if food not in current_food]

                if len(missing_food) > 0:
                    # nekdo nekaj je, poisci ga
                    missing_food_dist = [self.get_maze_distance(my_pos, food) for food in missing_food]
                    score += 0
                    #features['missing_food_distance'] = min(missing_food_dist)
            
            # preveri, ce imas koga v blizini
            pacmans_distances = [self.get_maze_distance(my_pos, pacman.get_position()) for pacman in pacmans]
            if len(pacmans_distances) > 0:
                #print(pacmans_distances)
                minimal_pacman_distance = min(pacmans_distances)
                score -= 1000 * minimal_pacman_distance
            
            # Tu pride Tomazeva funkcija za iskanje hrane
            score += 0
            #features['resting_place'] = 1 # spremeni to glede na to ali te ta smer spravi blizje srediscu ali ne
            

        
        
        
          
        
        
#        features['on_defense'] = 1
#        if my_state.is_pacman or my_state.scared_timer > 0:
#            features['on_defense'] = 0
#        
#        # Pridobi razdaljo do nasprotnikov (ce jih vidis)
#        enemies = [successor.get_agent_state(opponent) for opponent in self.get_opponents(successor)]
#        invaders = [enemy for enemy in enemies if enemy.is_pacman and enemy.get_position() is not None]
#        features['num_invaders'] = len(invaders)
#        
#        # Preveri, ali je zmanjkalo kaj hrane
#        if self.get_previous_observation() is not None:
#            past_food = self.get_food_you_are_defending(self.get_previous_observation()).as_list()
#            current_food = self.get_food_you_are_defending(game_state).as_list()
#            missing_food = [food for food in past_food if food not in current_food]
#            
#            if len(missing_food) > 0:
#                missing_food_dist = [self.get_maze_distance(my_pos, food) for food in missing_food]
#                features['missing_food_distance'] = min(missing_food_dist)
#        
#        # preveri, kako dalec imas do najblizjega napadalca
#        if len(invaders) > 0:
#            distances = [self.get_maze_distance(my_pos, invader.get_position()) for invader in invaders]
#            features['invader_distance'] = min(distances)
#        
#        # Preveri, kje se ti najbolj splaca cakati, ce ni nobenega dogajanja oziroma naj poskusi z napadom
#        # TODO: uporabi Tomazeve funkcije in zgoraj ustvarjene vrednosti
        
        # Pojma nimam, kaj je to ...
        if action == Directions.STOP:
            score -= 100
            #features['stop'] = 1

        rev = Directions.REVERSE[game_state.get_agent_state(self.index).configuration.direction]
        if action == rev:
            score -= 2
            #features['reverse'] = 1
        
        # return
        return score

    def get_weights(self, game_state, action):
        return {'on_defense': 100, 'num_invaders': -1000, 'missing_food_distance': -500, 'invader_distance': -10, 'stop': -100, 'reverse': -2}
































class StarvingPaccy(DumbAgent):
    def get_features(self, game_state, action):
        features = util.Counter()
        successor = self.get_successor(game_state, action)
        food_list = self.get_food(successor).as_list()
        #print(food_list)
        features['successor_score'] = -len(food_list)  # self.getScore(successor)

        # compute distance to opponents ghosts (if they are close)
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        ghosts = [a for a in enemies if not a.is_pacman and a.get_position() is not None]
        features['num_ghosts'] = len(ghosts)
        #for i in ghosts:
        #    print(i.get_position())
        ghost_distances = [self.get_maze_distance(successor.get_agent_state(self.index).get_position(), a.get_position()) for a in ghosts]
        #print(features['num_ghosts'], ghost_distances)

        # Compute distance to the nearest food
        if len(food_list) > 0:  # This should always be True,  but better safe than sorry
            my_pos = successor.get_agent_state(self.index).get_position()
            min_distance = min([self.get_maze_distance(my_pos, food) for food in food_list])
            features['distance_to_food'] = min_distance
        return features

    def get_weights(self, game_state, action):
        return {'successor_score': 100, 'distance_to_food': -1}
    
    def evaluate(self, game_state, action):
        return 0

