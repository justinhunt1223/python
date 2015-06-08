import MenuBase

class Menu(MenuBase.Base):

    def __init__(self, cMain):
        self.cMain = cMain
        self.lblTitle = [self.GetLabel("MUSIC", -5000, -5000, font_size = 42, anchor_y = "top", color = (143, 249, 255, 255), bold = True), cMain.window.width/2, 738]
        self.aMenuButtons = [[self.GetSprite('images/menu-buttons/music-library.png'), (75, 372), lambda: self.SelectMenu('Music Library')],
                             [self.GetSprite('images/menu-buttons/music-cd.png'), (378, 372), lambda: self.SelectMenu('Music CD')],
                             [self.GetSprite('images/menu-buttons/music-usb.png'), (681, 372), lambda: self.SelectMenu('Music USB')]]
        self.x = 0

    def Destroy(self):
        self.lblTitle[0].x = -5000
        self.lblTitle[0].y = -5000
        for aSprite in self.aMenuButtons:
            aSprite[0].set_position(-5000, -5000)