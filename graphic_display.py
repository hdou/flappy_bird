
from Tkinter import Tk, Canvas
import logging.config
import spritesheet
import pygame
from PIL import ImageTk


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('flappy_bird.graphic_display')

class graphic_display:
    def __init__(self, game):
        self.root = Tk()
        self.root.title('Flappy Bird')
        self.root.resizable(0,0)
        self.game = game
        
        self.display_height = 300.0
        self.display_width = 600.0
        self.x_margin = 10.0
        self.y_margin = 10.0
        self.x_factor = (self.display_width - 2*self.x_margin)/self.game.dx_loaded
        self.y_factor = (self.display_height - 2*self.y_margin)/self.game.height
        
        # maintain a map from pillar id to the display objects, so that when a pillar is moved
        # out of the display, it can be deleted. pid -> (top_rect_id, bottom_rect_id)
        self.pillar_id_dict = {}
        
        self.canvas = Canvas(self.root, width=self.display_width, height=self.display_height, background='white')        
        self.update_display()
        
    def update_display(self):
        '''
        Update the game display
        '''
        current_pids = [p.pid for p in self.game.pillars]
        logger.info('current pillars: {}'.format(current_pids))
        displayed_pids = self.pillar_id_dict.keys()
        logger.info('display pillars: {}'.format(displayed_pids))
        removed_pids = set(displayed_pids) - set(current_pids)
        new_pids = set(current_pids) - set(displayed_pids)
        
        for pid in removed_pids:
            logger.info('Removing pillar from display - id={}'.format(pid))
            (top_rect_id, bottom_rect_id) = self.pillar_id_dict[pid]
            self.canvas.delete(top_rect_id)
            self.canvas.delete(bottom_rect_id)
            del self.pillar_id_dict[pid]
        
        for pillar in self.game.pillars:
            if pillar.pid in new_pids:
                top_rect_id = self._create_rect(pillar.top_rect)
                bottom_rect_id = self._create_rect(pillar.bottom_rect)
                self.pillar_id_dict[pillar.pid] = (top_rect_id, bottom_rect_id)
                logger.info('Adding pillar to display - id={}, rect_id={} {}'.format(pillar.pid, top_rect_id, bottom_rect_id))
            else:
                (top_rect_id, bottom_rect_id) = self.pillar_id_dict[pillar.pid]
                self.move_rect(top_rect_id, pillar.top_rect)
                self.move_rect(bottom_rect_id, pillar.bottom_rect)
        self.canvas.pack()
        self.canvas.update()
    
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
        
    def _create_rect(self, rect):
        x1, y1, x2, y2 = self._get_rect_display_coordinates(rect)
        oid = self.canvas.create_rectangle(x1, y1, x2, y2, outline='gray', outlinestipple='gray25')
        return oid
    
    def move_rect(self, oid, rect):
        x1, y1, x2, y2 = self._get_rect_display_coordinates(rect)
        self.canvas.coords(oid, x1, y1, x2, y2)
    
    def game_coordinate_to_display_coordinate(self, x_game, y_game, x0_game):
        '''
        Convert from game coordinate to display coordinate
        '''
        x_display = (x_game - x0_game) * self.x_factor + self.x_margin
        y_display = self.display_height - y_game * self.y_factor - self.y_margin
        return x_display, y_display
        
