import MenuBase

class Menu(MenuBase.Base):

    def __init__(self, cMain):
        self.cMain = cMain
        self.lblTitle = None
        self.aMenuButtons=[[self.GetSprite('images/menu-buttons/music.png'), (75, 467), lambda: self.SelectMenu('Music')],
                           [self.GetSprite('images/menu-buttons/video.png'), (378, 467), lambda: self.SelectMenu('Video')],
                           [self.GetSprite('images/menu-buttons/gps.png'), (681, 467), lambda: None], 
                           [self.GetSprite('images/menu-buttons/web.png'), (75, 181), lambda: None], 
                           [self.GetSprite('images/menu-buttons/apps.png'), (378, 181), lambda: None],
                           [self.GetSprite('images/menu-buttons/extras.png'), (681, 181), lambda: None]]
        self.x = 0