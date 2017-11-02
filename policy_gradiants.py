# !/usr/bin/python

# Train the AI player using policy gradiants (PG)
# Reference http://karpathy.github.io/2016/05/31/rl/

from __future__ import division
from flappy_bird import flappy_bird_game, bird
from graphic_display import graphic_display
import time
import pygame

from matplotlib import pyplot as plt


import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('flappy_bird.policy_gradiants')

class policy_gradiants_trainer:
    '''
    Use policy gradiants directly acting on the pixels to train the AI player
    '''
    
    def run(self):
        '''
        Give user options to train, run the trained algorithm, etc
        '''
        print 'Running policy gradiants algorithm'
        self.train(delay_in_not_silent_mode=1)

    def train(self, delay_in_not_silent_mode=0.15):
        '''
        Train the AI player using the algorithm
        '''
        game = flappy_bird_game()
        display = graphic_display(game)

        while not game.is_game_over:
            action = False
            game.move(action)
            display.update_display()

            p = display.get_image_pixels()
            self.display_image(p)
            time.sleep(delay_in_not_silent_mode)

    def display_image(self, pixels):
        '''
        Display the image
        '''
        print pixels.shape
        plt.imshow(pixels)
        plt.show(block=False)
        time.sleep(5)
        plt.close()

if __name__ == '__main__':
    trainer = policy_gradiants_trainer()
    trainer.run()

