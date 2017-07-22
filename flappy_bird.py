#!/usr/bin/python

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
    def __init__(self, x, y):
        pass


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
    
    def __str__(self):
        return 'pillar {} (x={:.2f}, gap {:.2f})'.format(self.pid, self.x, self.bottom_rect[1][1])
    
class flappy_bird_game:
    '''
    Maintain the state of the game
    
    The game has a logical coordinate system. At start, x=0. As the game proceeds, x increases with 
    a constant speed of 1 distance unit/1 time unit.
    
    '''
    def __init__(self, dx_loaded=10.0, presenter=None):
        '''
        dx_loaded: objects within [x, x+dx_loaded] will be kept in memory
        '''
        self.x = 0.0
        self.time_per_move = 0.5        # every consecutive moves are this time units apart
        self.dx_loaded=dx_loaded
        self.height = 5.0
        
        # parameters for the pillars
        self.pillar_width = 1.0
        self.pillar_x_interval = 4.0        # How far between consecutive pillars
        self.pillar_gap = 1.0               # Gap between two parts of a pillar that can go through
        self.pillar_piece_min_length = 0.2  # Each piece of a pillar is at least this long
        self.pillar_x0 = 5.0                # First pillar's x
        
        # parameters for the bird
        self.bird_x0 = 1.0
        self.bird_y0 = 2.5
        self.bird_vy0 = 0.0                 # start speed in y direction
        self.bird_ay = -2.0                 # accelaration in y direction, in distance unit/square(time unit)
        self.bird_vx = 1.0                  # bird in the x direction
        self.bird_dvy = 4.0                 # vy increment per tap

        # create the pillars
        self.pillars = []
        self.next_pillar_id = 0          # 0-based id of a pillar
        self.update_pillars()
    
    def move(self):
        self.x += self.time_per_move
        self.update_pillars()
        
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
    
    
if __name__=='__main__':
    parser = argparse.ArgumentParser('Flappy bird game with reinforcement learning')
    
    parser.add_argument('--p', '--player', choices=['h', 'human', 'a', 'AI'], default='human',
                        help = 'Specify the player. h=human or a=AI trained with reinforcement learning (default=%(default)s)')    
    
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    args = parser.parse_args()
    
    game = flappy_bird_game()
    presenter = graphic_display(game)
    begin_time = time.time()
    done = False
    while time.time() - begin_time < 10 and not done:
        time.sleep(game.time_per_move)
        game.move()
        done = not presenter.update_display()
    