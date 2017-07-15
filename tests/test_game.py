#!/usr/bin/python

import unittest
from flappy_bird import flappy_bird_game

class test_game(unittest.TestCase):
    def test_update_pillars(self):
        g1 = flappy_bird_game(10.0)
        self._verify_pillars(g1)
        g2 = flappy_bird_game(7.0)
        self._verify_pillars(g2)
        g2.x = 0.5                # move the time line
        g2.update_pillars()
        self._verify_pillars(g2)
        g2.x = 1.2                # move the time line
        g2.update_pillars()
        self._verify_pillars(g2)
        
    def _verify_pillars(self, game):
        pillars = game.pillars
        self.assertTrue(len(pillars) >= 1)      # no matter what parameters, there must be one pillar loaded
        for p in pillars:
            xmin, xmax = p.get_x_range()
            self.assertTrue(xmin < (game.x + game.dx_loaded))
            self.assertTrue(xmax >= game.x)
        
        if pillars[0].pid > 0:
            p = game.create_pillar(pillars[0].pid-1)
            _, xmax = p.get_x_range()
            self.assertTrue(xmax < game.x)
            
        p = game.create_pillar(pillars[-1].pid+1)
        xmin, _ = p.get_x_range()
        self.assertTrue(xmin >= game.x + game.dx_loaded)
