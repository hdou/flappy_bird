from __future__ import division

import logging.config
import spritesheet
import pygame
import time


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('flappy_bird.graphic_display')

class graphic_display:
    def __init__(self, game):
        self.game = game
        
        self.display_height = 300
        self.display_width = 600
        self.x_margin = 10.0
        self.y_margin = 0.0
        self.x_factor = (self.display_width - 2*self.x_margin)/self.game.dx_loaded
        self.y_factor = (self.display_height - 2*self.y_margin)/self.game.height
        
        pygame.init()
        pygame.mixer.music.load('Yesterday.wav')
        pygame.mixer.music.play(-1)
        
        self.screen = pygame.display.set_mode((self.display_width, self.display_height))
        pygame.display.set_caption('Flappy Bird')
        self.clock = pygame.time.Clock()
        
        # backgroud
        ss = spritesheet.spritesheet('res/atlas.png')
        self.bg_img = ss.image_at((0.0, 0.0, 0.28125*ss.imgsize[0], 0.5*ss.imgsize[1]))
        print 'background image size:', self.bg_img.get_rect().size
        
        # images for the bird
        bird_size = (36,36)
        bird_img1 = ss.image_at((0.0, 0.9472656*ss.imgsize[1], 0.046875*ss.imgsize[0], 0.046875*ss.imgsize[1]), -1)
        bird_img1 = pygame.transform.scale(bird_img1, bird_size)
        bird_img2 = ss.image_at((0.0546875*ss.imgsize[0], 0.9472656*ss.imgsize[1], 0.046875*ss.imgsize[0], 0.046875*ss.imgsize[1]), -1)
        bird_img2 = pygame.transform.scale(bird_img2, bird_size)
        bird_img3 = ss.image_at((0.109375*ss.imgsize[0], 0.9472656*ss.imgsize[1], 0.046875*ss.imgsize[0], 0.046875*ss.imgsize[1]), -1)
        bird_img3 = pygame.transform.scale(bird_img3, bird_size)
        self.bird_imgs = [bird_img1, bird_img2, bird_img3]
        self.bird_img_index = 0
        self.bird_img_time = time.time()
        
        # images for the pillars
        # use the pixel at (0,30) to remove the black borders
        self.pillar_bot_img = ss.image_at((0.0, 0.6308594*ss.imgsize[1], 52, 320), -1, (0,30))  
        pillar_img_size = self.pillar_bot_img.get_rect().size
        pillar_display_width = self.game.pillar_width * self.x_factor
        pillar_ima_scale = pillar_display_width / pillar_img_size[0]
        self.pillar_img_size = (int(pillar_display_width), int(pillar_img_size[1] * pillar_ima_scale))
        self.pillar_bot_img = pygame.transform.scale(self.pillar_bot_img, self.pillar_img_size)
        self.pillar_top_img = pygame.transform.flip(self.pillar_bot_img, False, True)
        
        self.update_display()
        
    def update_display(self):
        '''
        Update the game display
        Return QUIT, MOUSEBUTTONUP events 
        '''
        quit_game = False
        jump = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                quit_game = True
            if event.type == pygame.MOUSEBUTTONUP or event.type == pygame.KEYUP:
                jump = True
                
        self.screen.fill((255,255,255))
        
        self.display_background()
        
        self.display_bird()
        
        for pillar in self.game.pillars:
            self.display_rect(pillar.top_rect, True)
            self.display_rect(pillar.bottom_rect, False)
        
        pygame.display.flip()
        self.clock.tick(60)      # 60 frames-per-second
        
        return quit_game, jump
    
    def display_background(self):
        bg_img_size = self.bg_img.get_rect().size
        bg_img_width = bg_img_size[0]
        bg_img_height = bg_img_size[1]
        y_offset = self.display_height - self.y_margin - bg_img_height
        
        x = 0
        while x < self.display_width:
            self.screen.blit(self.bg_img, (x,y_offset))
            x += bg_img_width
                
    def display_bird(self):
        new_time = time.time()
        if new_time - self.bird_img_time > 0.3:
            self.bird_img_time = new_time
            self.bird_img_index = (self.bird_img_index + 1) % len(self.bird_imgs)
        bird_img = self.bird_imgs[self.bird_img_index]
        x, y = self.game_coordinate_to_display_coordinate(self.game.bird.x, self.game.bird.y)
        self.screen.blit(bird_img, (x, y))
    
    def display_rect(self, rect, isTop):
        x1, y1, x2, y2 = self._get_rect_display_coordinates(rect)
        if isTop:
            self.screen.blit(self.pillar_top_img, (x1, y1-self.pillar_img_size[1]))
        else:
            self.screen.blit(self.pillar_bot_img, (x1, y2))
        
    def _get_rect_display_coordinates(self, rect):
        '''
        Returns the coordinates of the rect's bottom left corner and top right corner
        '''
        x1 = rect[0][0]
        y1 = rect[0][1]
        x2 = rect[1][0]
        y2 = rect[1][1]
        x1, y1 = self.game_coordinate_to_display_coordinate(x1, y1)
        x2, y2 = self.game_coordinate_to_display_coordinate(x2, y2)
        return x1, y1, x2, y2
        
    def game_coordinate_to_display_coordinate(self, x_game, y_game):
        '''
        Convert from game coordinate to display coordinate
        '''
        x_display = (x_game - self.game.x) * self.x_factor + self.x_margin
        y_display = self.display_height - y_game * self.y_factor - self.y_margin
        return x_display, y_display
        
