#!/usr/bin/python
from __future__ import division
import argparse
import random
from graphic_display import graphic_display
import time

import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('flappy_bird.game')


class bird:
    '''
    Represent the bird
    '''
    # Some constant parameters
    xspeed = 1
    yaccelation = -2        # accelaration in y-direction
    yspeed_after_jump = 1.5   # everytime the bird jumps, vy is set to this value
    #yspeed_inc_per_jump = 1
    
    def __init__(self, size, x, y):
        self.size = size
        self.x = x
        self.y = y
        self.yspeed = 0

    def clone(self):
        '''
        clone a bird
        '''
        bird_copy = bird(self.size, self.x, self.y)
        bird_copy.yspeed = self.yspeed
        return bird_copy
        
    def move(self, dt, jumped=False):
        '''
        Move the bird with the current speeds of x and y
        '''
        self.x += bird.xspeed * dt
        y_old_speed = self.yspeed
        self.yspeed += bird.yaccelation * dt
        if jumped:
            logger.debug('bird jumped')
            #self.yspeed += self.yspeed_inc_per_jump
            self.yspeed = bird.yspeed_after_jump
        self.y += (y_old_speed + self.yspeed) / 2.0 * dt

        logger.debug('bird vy={}, y={}'.format(self.yspeed, self.y))

    def get_rect(self):
        '''
        return the rect area that the bird occupies, in ((x, y), (x+width, x+height))
        '''
        return ((self.x, self.y), (self.x+self.size, self.y+self.size))
    
class pillar:
    '''
    Represent a pillar
    Each pillar has two pieces: the top and the bottom. The gap in between is for the bird to fly through
    For display, pillars may be added with trims, but they are not included in the collission computation.
    '''
    def __init__(self, pid, x, top_length, bottom_length, width, height):
        self.pid = pid
        self.x = x
        self.bottom_rect = ((x, 0), (x+width, bottom_length))        # (bottom_left point, top_righ_point)
        self.top_rect = ((x, height-top_length), (x+width, height))  # (bottom_left point, top_righ_point)
        self.width = width

    def get_x_range(self):
        return self.x, self.x+self.width
    
    def get_gap_y_range(self):
        '''
        returns the vertical range of the gap: y_min, y_max
        '''
        y_min = self.bottom_rect[1][1]
        y_max = self.top_rect[0][1]
        return y_min, y_max
    
    def __str__(self):
        return 'pillar {} (x={:.2f}, gap {:.2f})'.format(self.pid, self.x, self.bottom_rect[1][1])
    
    def collide_with(self, rect):
        '''
        Check whether the pillar collides with the rectangle
        '''
        collided = collission_detector.collide(self.top_rect, rect) or collission_detector.collide(self.bottom_rect, rect)
        if collided:
            logging.debug('{} collides with bird'.format(self))
        return collided
        
class collission_detector:
    @staticmethod
    def collide(rect1, rect2):
        '''
        Check whether the two rectangulars overlap
        The rectangulars are in ((x and y of one corner), (x and y of the opposite corner))
        '''
        rect1_x_min, rect1_x_max = collission_detector._get_x_min_max(rect1)
        rect1_y_min, rect1_y_max = collission_detector._get_y_min_max(rect1)
        rect2_x_min, rect2_x_max = collission_detector._get_x_min_max(rect2)
        rect2_y_min, rect2_y_max = collission_detector._get_y_min_max(rect2)
        
        if (rect2_x_min <= rect1_x_min <= rect2_x_max or rect2_x_min <= rect1_x_max <= rect2_x_max) and \
            (rect2_y_min <= rect1_y_min <= rect2_y_max or rect2_y_min <= rect1_y_max <= rect2_y_max):
            return True
        
        if (rect1_x_min <= rect2_x_min <= rect1_x_max or rect1_x_min <= rect2_x_max <= rect1_x_max) and \
            (rect1_y_min <= rect2_y_min <= rect1_y_max or rect1_y_min <= rect2_y_max <= rect1_y_max):
            return True
               
        return False
    
    @staticmethod
    def _get_x_min_max(rect):
        if rect[0][0] < rect[1][0]:
            return rect[0][0], rect[1][0]
        return rect[1][0], rect[0][0]
    
    @staticmethod
    def _get_y_min_max(rect):
        if rect[0][1] < rect[1][1]:
            return rect[0][1], rect[1][1]
        return rect[1][1], rect[0][1]
        
class flappy_bird_game:
    '''
    Maintain the state of the game
    
    The game has a logical coordinate system. At start, x=0. As the game proceeds, x increases with 
    a constant speed of 1 distance unit/1 time unit.
    
    '''
    
    # Constant parameters
    time_per_move = 0.2        # every consecutive moves are this time units apart
    height = 5.0
    
    # parameters for the pillars
    pillar_width = 1.0
    pillar_x_interval = 4.0        # How far between consecutive pillars
    pillar_gap = 2.0               # Gap between two parts of a pillar that can go through
    pillar_piece_min_length = 0.6  # Each piece of a pillar is at least this long
    pillar_x0 = 5.0                # First pillar's x

    # parameters for the bird
    bird_size = 0.4
    bird_x0 = 1.0
    bird_y0 = 2.5

    def __init__(self, dx_loaded=10.0, presenter=None):
        '''
        dx_loaded: objects within [x, x+dx_loaded] will be kept in memory
        '''
        self.x = 0.0
        self.dx_loaded=dx_loaded
                
        self.bird = bird(self.bird_size, self.bird_x0, self.bird_y0)

        # create the pillars
        self.pillars = []
        self.next_pillar_id = 0          # 0-based id of a pillar
        self.update_pillars()
        
        self.is_game_over = not self.is_bird_alive()
        self.just_scored = False
        self.score = 0
        self.last_pillar_bird_passed = -1
    
    def clone_game(self):
        '''
        Make a clone of the game
        '''
        game = flappy_bird_game()
        game.x = self.x
        game.dx_loaded = self.dx_loaded
        game.bird = self.bird.clone()
        game.pillars = self.pillars[:]      # pillars are immutable, thus no need to deep copy
        game.next_pillar_id = self.next_pillar_id
        game.is_game_over = self.is_game_over
        game.score = self.score
        game.just_scored = self.just_scored
        game.last_pillar_bird_passed = self.last_pillar_bird_passed
        
        return game
        
    def score_update(self):
        '''
        Update the score
        '''
        bird_rect = self.bird.get_rect()
        bird_xmin = min(bird_rect[0][0], bird_rect[1][0])
        for p in self.pillars:
            _, pxmax = p.get_x_range()
            if bird_xmin >= pxmax and p.pid > self.last_pillar_bird_passed:
                self.just_scored = True
                self.score += 1
                self.last_pillar_bird_passed = p.pid
                
    def is_bird_alive(self):
        '''
        Check whether the game is over
        '''
        if self.is_bird_out_of_bound():
            return False
        bird_rect = self.bird.get_rect()
        for p in self.pillars:
            if p.collide_with(bird_rect):
                return False
        return True
    
    def is_bird_out_of_bound(self):
        rect = self.bird.get_rect()
        min_y = min(rect[0][1], rect[1][1])
        max_y = max(rect[0][1], rect[1][1])
        return min_y <= 0 or max_y >= self.height
    
    def move(self, jump=False):
        self.just_scored = False
        if not self.is_game_over:
            self.x += self.time_per_move
            self.update_pillars()
            self.bird.move(self.time_per_move, jump)
            self.score_update()
            self.is_game_over = not self.is_bird_alive()
            if self.is_game_over:
                logging.debug('game is over. Bird is at {}. Score: {}'.format(self.bird.get_rect(), self.score))
        
    def update_pillars(self):
        '''
        Remove the pillars that are no longer in view, and create ones that come in view
        '''
        for p in self.pillars:
            xmin, xmax = p.get_x_range()
            if not self.should_be_loaded(xmax) and not self.should_be_loaded(xmin):
                self.pillars.remove(p)
            
        xmin = self.get_pillar_x(self.next_pillar_id)
                
        while self.should_be_loaded(xmin):
            p = self.create_pillar(self.next_pillar_id)
            self.pillars.append(p)
            self.next_pillar_id += 1
            xmin = self.get_pillar_x(self.next_pillar_id)

    def should_be_loaded(self, x):
        '''
        Returns whether the object at x should be loaded in memory
        '''
        return x >= self.x and x < self.x+self.dx_loaded
    
    def get_pillar_x(self, pid):
        '''
        Returns the starting x of the pillar
        '''
        return self.pillar_x0 + pid * self.pillar_x_interval

    def create_pillar(self, pid):
        '''
        Create a pillar with pid
        '''
        x = self.get_pillar_x(pid)
        r = random.random()
        bottom_length = r * (self.height - 2 * self.pillar_piece_min_length - self.pillar_gap) + self.pillar_piece_min_length
        top_length = self.height - bottom_length - self.pillar_gap
        return pillar(pid, x, top_length, bottom_length, self.pillar_width, self.height)
    
    def get_legal_actions(self):
        '''
        Return the legal moves at the current state of the game:
        x: game over
        j: jump
        n: no jump
        '''
        if self.is_game_over:
            return []
        return [True, False]
    
if __name__=='__main__':
    parser = argparse.ArgumentParser('Flappy bird game with reinforcement learning')
    
    parser.add_argument('--p', '--player', choices=['h', 'human', 'a', 'AI'], default='human',
                        help = 'Specify the player. h=human or a=AI trained with reinforcement learning (default=%(default)s)')    
    
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    args = parser.parse_args()

    new_game = True
    while new_game:
        new_game = False
        game = flappy_bird_game()
        presenter = graphic_display(game)
        done = False
        jump = False
        while not done and not new_game:
            time.sleep(0.15)
            game.move(jump)
            done, jump, new_game = presenter.update_display()
        if done:
            break
        

    