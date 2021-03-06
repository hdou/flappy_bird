# !/usr/bin/python

# Run the training sessions. It will load the Q-table, and update it with the training results

from __future__ import division
from flappy_bird import flappy_bird_game, bird
from graphic_display import graphic_display
from null_display import null_display
import random
import logging.config
import math
import pickle
import os
import time

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('flappy_bird.trainer')

class trainer:
    '''
    Run the training sessions
    '''
    def __init__(self):
        #self.n_state_x = 20
        #self.n_state_y = 20
        self.n_state_vy = 10
        
        self.dx_min = 0
        # bird initial location or after it clears a pillar, to the next pillar
        self.dx_max = max(flappy_bird_game.pillar_x0 + flappy_bird_game.pillar_width - flappy_bird_game.bird_x0, flappy_bird_game.pillar_x_interval)
        
        #self.dy_max = flappy_bird_game.height - flappy_bird_game.pillar_piece_min_length
        self.dy_max = 4.8
        self.dy_min = -self.dy_max 
        
        #self.step_dx = (self.dx_max - self.dx_min)/self.n_state_x
        #self.step_dy = (self.dy_max - self.dy_min)/self.n_state_y
        self.step_dx = 0.2  # same as the resolution of x in movement
        self.step_dy = 0.4  # same as the size of the bird
        
        self.vy_max = bird.yspeed_after_jump
        # time to fall from the top to bottom
        t_fall = math.sqrt(2 * self.dy_max / math.fabs(bird.yaccelation))
        self.vy_min = t_fall * bird.yaccelation
        self.step_dvy = (self.vy_max - self.vy_min) / self.n_state_vy  
        
        logging.info('x: ({:.2f}, {:.2f}), delta: {:.2f}'.format(self.dx_min, self.dx_max, self.step_dx))
        logging.info('y: ({:.2f}, {:.2f}), delta: {:.2f}'.format(self.dy_min, self.dy_max, self.step_dy))
        logging.info('vy: ({:.2f}, {:.2f}), delta: {:.2f}'.format(self.vy_min, self.vy_max, self.step_dvy))
        
        self.alpha = 0.1 # learning rate
        
        self.QTable_file = 'data/QTable_v1'
        self.QTable = dict()
        if os.path.isfile(self.QTable_file):
            self.QTable = pickle.load(open(self.QTable_file,'rb'))
            print 'Loaded Q-table from file. Total entries: ', len(self.QTable)
        
    def get_state(self, game, training):
        '''
        Returns state in (state_x, state_y, state_vy), where
        state_x is quantified horizontal distance of the bird to the pillar, and
        state_y is that of vertical distance, and
        state_vy is that of the vertical speed
        '''
        pillar_idx = 0
        if not training:
            # training always reference pillar 0
            for i in xrange(len(game.pillars)):
                p = game.pillars[i]
                _, p_x_max = p.get_x_range()
                if p_x_max > game.bird.x:
                    pillar_idx = i
                    break
        dx = game.pillars[pillar_idx].x + game.pillar_width - game.bird.x
        dy = game.bird.y - game.pillars[pillar_idx].bottom_rect[1][1]
        logging.debug('state dx={:.2f} dy={:.2f}, vy={:.2f}'.format(dx, dy, game.bird.yspeed))
        state_x = self._quantify_distance_x(dx)
        state_y = self._quantify_distance_y(dy)
        state_vy = self._quantify_speed_y(game.bird.yspeed)
        state = (state_x, state_y, state_vy)
        logging.debug('quantified state={}'.format(state))
        return state
    
    def _quantify_distance_x(self, dx):
        '''
        Evenly partition it from [min, max]
        '''
        return math.floor((dx - self.dx_min)/self.step_dx)
    
    def _quantify_distance_y(self, dy):
        '''
        Evenly partition it from [min, max]
        '''
        return math.floor((dy - self.dy_min)/self.step_dy)

    def _quantify_speed_y(self, vy):
        '''
        Evenly partition it from [min, max]
        '''
        return math.floor((vy - self.vy_min)/self.step_dvy)
    
    def _prompt(self):
        print 'Select from following options:'
        print ' x: quit'
        print ' p: play the game with learned Q-table'
        print ' q: show Q-table'
        print ' s: store Q-table'
        print ' f: dump Q-table to text file'
        print ' <n>: train n sessions'
        print ' <Return>: one interactive training session'
        user_input = raw_input('What do you want to do:')
        return user_input
    
    def play(self):
        '''
        Play the game using learned Q-table
        '''
        game = flappy_bird_game()
        display = graphic_display(game)
        while not game.is_game_over:
            state = self.get_state(game, training=False)
            bird_yspeed = game.bird.yspeed
            actions = game.get_legal_actions()
            scores = [self.get_action_value(game, act, training=False) for act in actions]
            action, max_score = self.select_action_with_max_score(actions, scores)
            game.move(action)
            if game.is_game_over:
            #if True:
                new_state = self.get_state(game, training=False)
                print 'state: ', state
                print 'bird y-speed: ', bird_yspeed
                print 'actions: ', actions
                print 'scores: ', scores
                if (state, action) in self.QTable.keys():
                    print '(state, action) is in the QTable'
                else:
                    print '(state, action) is not in the QTable'
                for i in xrange(len(actions)):
                    a = actions[i]
                    if a == action:
                        print 'action: {} (*), score: {}'.format(self.get_action_text(action), max_score)
                    else:
                        print 'action: {}, score: {}'.format(self.get_action_text(a), scores[i])
                print 'new state: ', new_state
                raw_input('press a key to continue...')
                
            time.sleep(0.15)
            display.update_display()
        
    def train(self):
        '''
        run the training sessions
        '''
        while True:
            user_input = self._prompt()
            if user_input == 'x':
                break
            if user_input == 'q':
                self.dump_q_table()
            elif user_input == 's':
                pickle.dump(self.QTable, open(self.QTable_file, 'wb'))
                print 'Stored Q-table'
            elif user_input == 'f':
                self.dump_q_table_to_file()
            elif user_input == 'p':
                # play the game using the learned Q-table
                self.play()
            elif user_input == '':
                self.train_one_session()
            else:
                n_sessions = eval(user_input)
                for i in xrange(n_sessions):
                    self.train_one_session(False)
                    if (i+1)%100 == 0:
                        print 'Finished {} sessions'.format(i+1)
                self.dump_q_table()

    def dump_q_table(self):
        print 'Q-table size: ', len(self.QTable)
        n_entries_value_0 = 0
        n_entries_greater_than_0 = 0
        n_entries_less_than_0 = 0
        for _, v in self.QTable.iteritems():
            if v == 0:
                n_entries_value_0 += 1
            elif v < 0:
                n_entries_less_than_0 += 1
            else:
                n_entries_greater_than_0 += 1
        print '{} entries == 0'.format(n_entries_value_0)
        print '{} entries < 0'.format(n_entries_less_than_0)
        print '{} entries > 0'.format(n_entries_greater_than_0) 
        #print 'Q-table: '
        #print self.QTable
    
    def dump_q_table_to_file(self):
        '''
        Dump Q-table to a text file, QTable.txt, sorted by the key
        '''
        with open('data/QTable.txt', 'w') as f:
            for k in sorted(self.QTable.keys()):
                f.write('{}: {}\n'.format(k, self.QTable[k]))
        
    def train_one_session(self, user_interactive = True):
        '''
        Run one training session
        '''
        game = flappy_bird_game()
        bird = game.bird
        bird.x = 2.0
        r = random.random()
        bird.y = r * flappy_bird_game.height
        dice = random.random()
        if dice < 0.2:
            bird.yspeed = 1.5       # 20% for the bird just jumped
        else:
            r = random.random()
            bird.yspeed = r * (self.vy_max - self.vy_min) + self.vy_min

        if user_interactive:
            display = graphic_display(game)
        else:
            display = null_display(game)
        
        game_over = game.is_game_over
        just_scored = game.just_scored

        while not game_over and not just_scored:
            state = self.get_state(game, training=True)
            #print 'state: ', state
            #raw_input('press key to continue...')
            game_over = game.is_game_over
            just_scored = game.just_scored
            if user_interactive:
                print 'state: ', state
                if just_scored:
                    print 'Just scored!'
                else:
                    print 'No score change'
            if game_over:
                self.update_q_value(state, 'x', -5 * state[0] - 10)  # The closer the less the negative score
                if state[0] == -1:
                    display = graphic_display(game)
                    print 'bird is at (x={}, y={})'.format(game.bird.x, game.bird.y)
                    print 'pillar[0] top {}, bottom'.format(game.pillars[0].top_rect, game.pillars[0].bottom_rect)
                    print 'state: {}'.format(state)
                    raw_input('Press a key to continue')
            elif just_scored:
                logging.debug('Found path to score!!!')
                self.update_q_value(state, 's', +100)
            else:
                actions = game.get_legal_actions()
                scores = [self.get_action_value(game, act, training=True) for act in actions]
                if user_interactive:
                    print 'actions: {}, scores: {}'.format(actions, scores)
                    for i in xrange(len(actions)):
                        if (state, actions[i]) in self.QTable.keys():
                            print '{} is in Q-table. Value={}'.format((state, actions[i]), self.QTable[(state, actions[i])])
                        else:
                            print '{} is not in Q-table'.format((state, actions[i]))
                dice = random.random()
                if dice < 0.5:
                    action, max_score = self.select_action_with_max_score(actions, scores)
                else:
                    action, max_score = self.select_action_for_training(actions, scores)
                if user_interactive:
                    action_text = self.get_action_text(action)             
                    print 'Take action {}, score {}'.format(action_text, max_score)
                self.update_q_value(state, action, max_score)
                if user_interactive:
                    if (state, action) in self.QTable.keys():
                        print '{} is in Q-table. Value={}'.format((state, action), self.QTable[(state, action)])
                    else:
                        print '{} is not in Q-table'.format((state, action))
                game.move(action)
            if user_interactive:
                print 'Take action: ', action
                print 'Just scored? : ', game.just_scored
                raw_input('Press any key to continue')
            display.update_display()
        
        #if user_interactive:
        #    raw_input('Press any key to continue')
    
    def select_action_with_max_score(self, actions, scores):
        '''
        Returns the action based on the scores
        '''
        max_score = max(scores)
        action_indices_with_max_scores = [i for i, x in enumerate(scores) if x == max_score]
        # randomly choose one with max score
        idx = int(math.floor(random.random()*len(action_indices_with_max_scores)))
        idx = action_indices_with_max_scores[idx]
        return actions[idx], max_score
    
    def select_action_for_training(self, actions, scores):
        '''
        Returns the action based on the scores
        '''
        action_indices_with_max_scores = [i for i, _ in enumerate(scores)]
        # randomly choose one with max score
        idx = int(math.floor(random.random()*len(action_indices_with_max_scores)))
        idx = action_indices_with_max_scores[idx]
        return actions[idx], scores[idx]

    def get_action_value(self, game, action, training):
        '''
        Returns the max Q-value of the state if the aciton is taken
        '''
        new_game = game.clone_game()
        new_game.move(action)
        state = self.get_state(new_game, training)
        if new_game.is_game_over:
            actions = ['x']
        elif new_game.just_scored:
            actions = ['s']
        else:            
            actions = new_game.get_legal_actions()
        #for act in actions:
        #    print 'Q(s\',a\') {}: {} '.format((state, self.get_action_text(act)), self.QTable.get((state, act), 0.0))
        max_score = max(self.QTable.get((state, act), 0.0) for act in actions)
        return max_score
        
    def update_q_value(self, state, action, score):
        key = (state, action)
        if key not in self.QTable.keys():
            self.QTable[key] = 0.0
            logging.debug('QTable: new size: {}'.format(len(self.QTable)))
        old_value = self.QTable[key]
        new_value = self.alpha * score + (1-self.alpha) * old_value
        self.QTable[key] = new_value
        logging.debug('New sample {} with score {}'.format((state, action), score))
        logging.debug('Value update {:.2f} -> {:.2f}'.format(old_value, new_value))
    
    def get_q_value(self, state, action):
        key = (state, action)
        if key not in self.QTable.keys():
            self.QTable[key] = 0.0
            logging.debug('QTable: new size: {}'.format(len(self.QTable)))
        return self.QTable[key]
    
    def get_action_text(self, action):
        if action == True:
            action_text = 'Jump'
        elif action == False:
            action_text = 'None'
        else:
            action_text = action
        return action_text
        
if __name__ == '__main__':
    trainer = trainer()
    trainer.train()
