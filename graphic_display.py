from __future__ import division

import logging.config
import spritesheet
import pygame


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('flappy_bird.graphic_display')

class graphic_display:
    def __init__(self, game):
        self.game = game
        
        self.display_height = 300
        self.display_width = 600
        self.x_margin = 10.0
        self.y_margin = 10.0
        self.x_factor = (self.display_width - 2*self.x_margin)/self.game.dx_loaded
        self.y_factor = (self.display_height - 2*self.y_margin)/self.game.height
        
        # maintain a map from pillar id to the display objects, so that when a pillar is moved
        # out of the display, it can be deleted. pid -> (top_rect_id, bottom_rect_id)
        self.pillar_id_dict = {}
        
        pygame.init()
        self.screen = pygame.display.set_mode((self.display_width, self.display_height))
        pygame.display.set_caption('Flappy Bird')
        self.clock = pygame.time.Clock()
        
        self.update_display()
        
    def update_display(self):
        '''
        Update the game display
        Return False if it has received the QUIT event; True Otherwise
        '''
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
        self.screen.fill((255,255,255))
        
        for pillar in self.game.pillars:
            self.display_rect(pillar.top_rect)
            self.display_rect(pillar.bottom_rect)
        
        pygame.display.flip()
        self.clock.tick(60)      # 60 frames-per-second
        
        return True
    
    def display_rect(self, rect):
        x1, y1, x2, y2 = self._get_rect_display_coordinates(rect)
        pygame.draw.rect(self.screen, (200, 200, 200), pygame.Rect(x1, y1, x2-x1, y2-y1))
        
    def _get_rect_display_coordinates(self, rect):
        '''
        Returns the coordinates of the rect's bottom left corner and top right corner
        '''
        x1 = rect[0][0]
        y1 = rect[0][1]
        x2 = rect[1][0]
        y2 = rect[1][1]
        x1, y1 = self.game_coordinate_to_display_coordinate(x1, y1, self.game.x)
        x2, y2 = self.game_coordinate_to_display_coordinate(x2, y2, self.game.x)
        return x1, y1, x2, y2
        
    def game_coordinate_to_display_coordinate(self, x_game, y_game, x0_game):
        '''
        Convert from game coordinate to display coordinate
        '''
        x_display = (x_game - x0_game) * self.x_factor + self.x_margin
        y_display = self.display_height - y_game * self.y_factor - self.y_margin
        return x_display, y_display
        
