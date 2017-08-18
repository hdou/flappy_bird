# !/usr/bin/python

# Train the AI player with features, or approximate Q-table

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
logger = logging.getLogger('flappy_bird.feature_trainer')

class feature_trainer:
    '''
    Instead of representing the game state with low level states,
    Represent it with linear combination of high level features:
      * distance to the center of the scene
      * distance to the baseline of the gap (the baseline is chosen to be 20% towards the bottom of the gap)
      * distance to the baseline of the gap when the bird is in the gap (not sure this is necessary, but keep it anyway)
    '''
    weight_file = 'data/feature_weights'
    def __init__(self):
        self.alpha = 0.1    # learning rate
        self.load_weights()
        
        # compute some parameters for convenience later
        self.vy_max = bird.yspeed_after_jump
        # time to fall from the top to bottom
        t_fall = math.sqrt(2 * flappy_bird_game.height / math.fabs(bird.yaccelation))
        self.vy_min = t_fall * bird.yaccelation
            
    def load_weights(self):
        if os.path.isfile(feature_trainer.weight_file):
            with open(feature_trainer.weight_file) as f:
                self.w_dy_to_center = pickle.load(f)
                self.w_dy_to_gap_baseline = pickle.load(f)
                self.w_dy_to_gap_baseline_in_gap = pickle.load(f)
            print 'Loaded weights'
            self.show_weights()
        else:
            print 'No weight file available. Initialize weights to ones'
            self.w_dy_to_center = 1.0
            self.w_dy_to_gap_baseline = 1.0
            self.w_dy_to_gap_baseline_in_gap = 1.0

    def store_weights(self):
        with open(feature_trainer.weight_file, 'wb') as f:
            pickle.dump(self.w_dy_to_center, f)
            pickle.dump(self.w_dy_to_gap_baseline, f)
            pickle.dump(self.w_dy_to_gap_baseline_in_gap, f)
    
    def show_weights(self):
        print 'weight for dy_to_center:            ', self.w_dy_to_center
        print 'weight for dy_to_gap_baseline:        ', self.w_dy_to_gap_baseline
        print 'weight for dy_to_gap_baseline_in_gap: ', self.w_dy_to_gap_baseline_in_gap
    
    def train_one_session(self, user_interactive = True):
        '''
        Run one interactive training session
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
            actions = game.get_legal_actions()
            dice = random.random()
            if dice < 0:
                action = random.choice(actions)
                if user_interactive:
                    print 'randomly choose action: ', self.get_action_text(action)     
            else:
                action, values = self.selection_action_with_max_value(game, actions, user_interactive)
                if user_interactive:
                    print 'selecting actions based on values'
                    for i in xrange(len(actions)):
                        print 'action {} value {:.2f}: '.format(self.get_action_text(actions[i]), values[i])
                    print 'choose action: ', self.get_action_text(action)
            
            game.move(action)
            
            game_over = game.is_game_over
            just_scored = game.just_scored

            if game_over or just_scored:
                self.update_weights(game, user_interactive)
            
            display.update_display()
            
            if user_interactive:
                raw_input('press any key to continue ...')
    
    def selection_action_with_max_value(self, game, actions, user_interactive):
        '''
        returns the action that resules in the max value, and all values.
        if multiple actions has the same value, randomly choose one
        '''
        if len(actions) == 0:
            raise Exception('Actions can not be empty')
        
        values = []
        
        max_value = None
        actions_with_max_value = []
        
        for a in actions:
            copied_game = game.clone_game()
            copied_game.move(a)
            value = self.get_value(copied_game)
            values.append(value)
            if max_value is None:
                max_value = value
                actions_with_max_value = [a]
            elif value == max_value:
                actions_with_max_value.append(a)
            elif value > max_value:
                max_value = value
                actions_with_max_value = [a]
            else:
                pass
            
            if user_interactive:
                print 'action {} has value {:.2f}'.format(self.get_action_text(a), value)
            
        action = random.choice(actions_with_max_value)
        return action, values
    
    def get_value(self, game):
        '''
        returns the value (weighted sum of feature values) of the game
        '''
        dy, dy_gap, dy_gap_in_gap = self.get_feature_values(game, False)
        return self.w_dy_to_center * dy + self.w_dy_to_gap_baseline * dy_gap + self.w_dy_to_gap_baseline_in_gap * dy_gap_in_gap
        
    def update_weights(self, game, user_interactive):
        '''
        update the weights based on the rewards
        '''
        if game.is_game_over:
            score = -100.0
        #elif game.just_scored:
        #    score = 100.0
        else:
            # if there is no score change, we don't update weights
            return
        
        dy, dy_gap, dy_gap_in_gap = self.get_feature_values(game, user_interactive)
        
        # expected value verse acture value (score)
        expected_value = self.w_dy_to_center * dy + self.w_dy_to_gap_baseline * dy_gap + self.w_dy_to_gap_baseline_in_gap * dy_gap_in_gap
        diff = score - expected_value
        w_dy = self.w_dy_to_center + self.alpha * diff * dy
        w_dy_gap = self.w_dy_to_gap_baseline + self.alpha * diff * dy_gap
        w_dy_gap_in_gap = self.w_dy_to_gap_baseline_in_gap + self.alpha * diff * dy_gap_in_gap
        if user_interactive:
            print 'updating weights...'
            print 'expected value: {:.2f}, and actual: {}'.format(expected_value, score)
            print 'w_dy:            {:.2f} -> {:.2f}'.format(self.w_dy_to_center, w_dy)
            print 'w_dy_gap:        {:.2f} -> {:.2f}'.format(self.w_dy_to_gap_baseline, w_dy_gap)
            print 'w_dy_gap_in_gap: {:.2f} -> {:.2f}'.format(self.w_dy_to_gap_baseline_in_gap, w_dy_gap_in_gap)
        self.w_dy_to_center = w_dy
        self.w_dy_to_gap_baseline = w_dy_gap
        self.w_dy_to_gap_baseline_in_gap = w_dy_gap_in_gap
        
        
    def get_feature_values(self, game, user_interactive):
        '''
        returns values of each feature if activated.
        if not activated, returns 0
        '''
        bird = game.bird
        
        # find the target pillar
        for i in xrange(len(game.pillars)):
            p = game.pillars[i]
            p_x_min, p_x_max = p.get_x_range()
            if p_x_max > game.bird.x:
                pillar = game.pillars[i]
                break
        
        gap_y_min, gap_y_max = pillar.get_gap_y_range()
        #gap_y_center = (gap_y_min + gap_y_max) / 2.0
        gap_y_center = 0.8 * gap_y_min + 0.2 * gap_y_max    # aim toward the bottom of the gap

        bird_y = game.bird.y
        
        if bird.x < p_x_min:
            # not in the gap
            y_center = game.height/2.0
            dy = abs(bird_y - y_center)
            dy_gap = abs(bird_y - gap_y_center)
            dy_gap_in_gap = 0.0     # not activated
        else:
            # in the gap
            dy = 0.0                # not activated
            dy_gap = 0.0            # not activated
            dy_gap_in_gap = abs(bird_y - gap_y_center)
            
        if user_interactive:
            print 'feature values...'
            print 'dy: ', dy
            print 'dy_gap', dy_gap
            print 'dy_gap_in_gap', dy_gap_in_gap
        
        return dy, dy_gap, dy_gap_in_gap
    
    def play(self):
        '''
        play the game based on learned weights
        '''
        game = flappy_bird_game()
        display = graphic_display(game)
        while not game.is_game_over:
            actions = game.get_legal_actions()
            action, _ = self.selection_action_with_max_value(game, actions, False)
            game.move(action)
            
            time.sleep(0.15)
            display.update_display()

    def _prompt(self):
        print 'Select from following options:'
        print ' x: quit'
        print ' p: play the game with learned weights'
        print ' w: show the weights'
        print ' s: store the weights'
        print ' <Return>: one interactive training session'
        user_input = raw_input('What do you want to do:')
        return user_input

    def run(self):
        '''
        run the trainer functions
        '''
        user_input = self._prompt()
        while user_input != 'x':
            if user_input == 'w':
                self.show_weights()
            elif user_input == 's':
                self.store_weights()
            elif user_input == '':
                self.train_one_session()
            elif user_input == 'p':
                self.play()
            user_input = self._prompt()
            
    def get_action_text(self, action):
        if action == True:
            action_text = 'Jump'
        elif action == False:
            action_text = 'None'
        else:
            action_text = action
        return action_text
        

if __name__ == '__main__':
    trainer = feature_trainer()
    trainer.run()