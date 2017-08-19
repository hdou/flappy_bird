#from flappy_bird import flappy_bird_game
class null_display():
    '''
    A null display object
    '''
    def __init__(self, game, report_score=1000):
        self.game = game
        self.report_score = report_score    # report when score is multiple of this number
        self.score_count = 0
    
    def update_display(self):
        # doesn't display anything
        if self.game.just_scored:
            self.score_count += 1
            if (self.score_count % self.report_score) == 0:
                print 'score ', self.score_count