import MenuBase

class MENU(MenuBase.BASE):

    def __init__(self, cMain):
        self.cMain = cMain
        self.lblTitle = None
        self.aMenuButtons=[[self.Get_Sprite('images/menu-buttons/music.png'), (75, 467), lambda: self.Select_Menu('Music')],
                           [self.Get_Sprite('images/menu-buttons/video.png'), (378, 467), lambda: self.Select_Menu('Video')],
                           [self.Get_Sprite('images/menu-buttons/gps.png'), (681, 467), lambda: None], 
                           [self.Get_Sprite('images/menu-buttons/web.png'), (75, 181), lambda: None], 
                           [self.Get_Sprite('images/menu-buttons/apps.png'), (378, 181), lambda: None],
                           [self.Get_Sprite('images/menu-buttons/extras.png'), (681, 181), lambda: None]]
        self.x = 0