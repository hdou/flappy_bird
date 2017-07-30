# !/usr/bin/python

# Run the training sessions. It will load the Q-table, and update it with the training results

from __future__ import division
from flappy_bird import flappy_bird_game, bird
from graphic_display import graphic_display
import random
import logging.config
import math

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('flappy_bird.trainer')

class trainer:
    '''
    Run the training sessions
    '''
    def __init__(self):
        self.n_state_x = 20
        self.n_state_y = 20
        self.n_state_vy = 10
        
        self.dx_min = 0
        # bird initial location or after it clears a pillar, to the next pillar
        self.dx_max = max(flappy_bird_game.pillar_x0 + flappy_bird_game.pillar_width - flappy_bird_game.bird_x0, flappy_bird_game.pillar_x_interval)
        
        self.dy_max = flappy_bird_game.height - flappy_bird_game.pillar_piece_min_length
        self.dy_min = -self.dy_max 
        
        self.step_dx = (self.dx_max - self.dx_min)/self.n_state_x
        self.step_dy = (self.dy_max - self.dy_min)/self.n_state_y
        
        self.vy_max = bird.yspeed_after_jump
        # time to fall from the top to bottom
        t_fall = math.sqrt(2 * self.dy_max / math.fabs(bird.yaccelation))
        self.vy_min = t_fall * bird.yaccelation
        self.step_dvy = (self.vy_max - self.vy_min) / self.n_state_vy  
        
        logging.info('x: ({:.2f}, {:.2f}), delta: {:.2f}'.format(self.dx_min, self.dx_max, self.step_dx))
        logging.info('y: ({:.2f}, {:.2f}), delta: {:.2f}'.format(self.dy_min, self.dy_max, self.step_dy))
        logging.info('vy: ({:.2f}, {:.2f}, delta: {:.2f}'.format(self.vy_min, self.vy_max, self.step_dvy))
        
        self.alpha = 0.1 # learning rate
        
        self.QTable = dict()
        
    def get_state(self, game):
        '''
        Returns state in (state_x, state_y, state_vy), where
        state_x is quantified horizontal distance of the bird to the pillar, and
        state_y is that of vertical distance, and
        state_vy is that of the vertical speed
        '''
        dx = game.pillars[0].x + game.pillar_width - game.bird.x
        dy = game.bird.y - game.pillars[0].bottom_rect[1][1]
        logging.info('state dx={:.2f} dy={:.2f}, vy={:.2f}'.format(dx, dy, game.bird.yspeed))
        state_x = self._quantify_distance_x(dx)
        state_y = self._quantify_distance_y(dy)
        state_vy = self._quantify_speed_y(game.bird.yspeed)
        state = (state_x, state_y, state_vy)
        logging.info('quantified state={}'.format(state))
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
        print ' q: quit'
        print ' any other key: one more training session'
        user_input = raw_input('What do you want to do:')
        return user_input
    
    def train(self):
        '''
        run the training sessions
        '''
        user_input = self._prompt()
        while user_input != 'q':
            user_input = self.train_one_session()

    def train_one_session(self):
        '''
        Run one training session
        '''
        game = flappy_bird_game()
        bird = game.bird
        r = random.random()
        bird.yspeed = r * (self.vy_max - self.vy_min) + self.vy_min

        display = graphic_display(game)
        
        game_over = game.is_game_over
        just_scored = game.just_scored

        while not game_over and not just_scored:
            state = self.get_state(game)
            game_over = game.is_game_over
            just_scored = game.just_scored
            if game_over:
                self.update_q_value(state, 'x', -100)
            elif just_scored:
                logging.info('Found path to score!!!')
                self.update_q_value(state, 's', +100)
            else:
                actions = game.get_legal_actions()
                scores = [self.get_action_value(game, act) for act in actions]
                action, max_score = self.select_action_with_max_score(actions, scores)
                self.update_q_value(state, action, max_score)
                game.move(action)
            display.update_display()
        
        user_input = self._prompt()
        return user_input
    
    def select_action_with_max_score(self, actions, scores):
        '''
        Returns the action based on the scores
        '''
        max_score = max(scores)
        action_indices_with_max_scores = [i for i, x in enumerate(scores) if x == max_score]
        # randomly choose one with max score
        idx = int(math.floor(random.random()*len(action_indices_with_max_scores)))
        return actions[idx], max_score
    
    def get_action_value(self, game, action):
        '''
        Returns the max Q-value of the state if the aciton is taken
        '''
        new_game = game.clone_game()
        new_game.move(action)
        state = self.get_state(new_game)
        if new_game.is_game_over:
            actions = ['x']
        elif new_game.just_scored:
            actions = ['s']
        else:            
            actions = new_game.get_legal_actions()
        (_, max_score) = max((act, self.QTable.get((state, act), 0.0)) for act in actions)
        return max_score
        
    def update_q_value(self, state, action, score):
        key = (state, action)
        if key not in self.QTable.keys():
            self.QTable[key] = 0.0
            logging.info('QTable: new size: {}'.format(len(self.QTable)))
        old_value = self.QTable[key]
        new_value = self.alpha * score + (1-self.alpha) * old_value
        self.QTable[key] = new_value
        logging.info('New sample {} with score {}'.format((state, action), score))
        logging.info('Value update {:.2f} -> {:.2f}'.format(old_value, new_value))
    
    def get_q_value(self, state, action):
        key = (state, action)
        if key not in self.QTable.keys():
            self.QTable[key] = 0.0
            logging.info('QTable: new size: {}'.format(len(self.QTable)))
        return self.QTable[key]
    
if __name__ == '__main__':
    trainer = trainer()
    trainer.train()
