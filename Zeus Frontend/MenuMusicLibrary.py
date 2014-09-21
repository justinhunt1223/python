import MenuBase
import pyglet

class MENU(MenuBase.BASE):

    def __init__(self, cMain):
        self.cMain = cMain
        self.lblTitle = None
        self.Update_Title(self.cMain.Get_Config('musicLibraryTitle', 'MUSIC LIBRARY'))
        self.aMenuButtons = [[self.Get_Sprite("images/arrow/arrow-left.png"), (960, 662), self.Library_Back]]
        self.x = 0
        self.batch = pyglet.graphics.Batch()
        self.dSprites = {"List Background1": self.Get_Sprite("images/library/library-list-background.png", self.batch),
                         "List Background2": self.Get_Sprite("images/library/library-list-background.png", self.batch),
                         "List Background Cover": self.Get_Sprite("images/library/library-list-background-cover.png")}
        
        self.dListInfo = {"Item Height": 66,
                          "Start Index": int(self.cMain.Get_Config('startIndex', '0')),
                          "Start Index Artists": int(self.cMain.Get_Config('artistsStartIndex', '0')),
                          "Scroll Y": int(self.cMain.Get_Config('scrollY', '0')),
                          "Scroll Y Artists": int(self.cMain.Get_Config('artistsScrollY', '0')),
                          "Max Y": 0,
                          "Min Y": 0,
                          "List Width": self.dSprites["List Background1"].width,
                          "List Height": self.dSprites["List Background1"].height,
                          "Background Y": 177,
                          "Background Y Offset": int(self.cMain.Get_Config('backgroundYOffset', '0')),
                          "Slide X": 0,
                          "Slide X Speed": 0}
        self.aArtists = []
        self.aAlbums = []
        self.aTracks = []
        self.iArtistIndex = int(self.cMain.Get_Config('artistIndex', '-1'))
        self.iAlbumIndex = int(self.cMain.Get_Config('albumIndex', '-1'))
        if self.iAlbumIndex != -1:
            self.Update_Tracks()
        elif self.iArtistIndex != -1:
            self.Update_Albums()
        else:
            self.Update_Artists()
        self.bFade = False
        self.iLabelColorAlpha = 255
        self.iLabelColorAlphaSpeed = -25
        self.iSelectedIndex = -1

    def Init(self):
        iScrollY = self.dListInfo['Scroll Y']
        self.dListInfo['Scroll Y'] = self.dListInfo['Scroll Y Artists']
        self.Draw_List(83, 177, self.aArtists, 0, -1, self.batch, self.bFade, self.iLabelColorAlpha, bSetY = True)
        self.dListInfo['Scroll Y'] = iScrollY

    def Save(self):
        self.cMain.Write_Config('scrollY', self.dListInfo['Scroll Y'])
        self.cMain.Write_Config('artistsScrollY', self.dListInfo['Scroll Y Artists'])
        self.cMain.Write_Config('artistsStartIndex', self.dListInfo['Start Index Artists'])
        self.cMain.Write_Config('startIndex', self.dListInfo['Start Index'])
        self.cMain.Write_Config('backgroundYOffset', self.dListInfo['Background Y Offset'])
        self.cMain.Write_Config('artistIndex', self.iArtistIndex)
        self.cMain.Write_Config('albumIndex', self.iAlbumIndex)
        self.cMain.Write_Config('musicLibraryTitle', self.lblTitle[0].text)

    def Update_Artists(self):
        self.aArtists = []
        iY = 0
        for aArtist in self.cMain.cMusicLibrary.Get_Artists():
            self.aArtists.append([self.Get_Label(aArtist[1],
                                                 -5000,
                                                 iY, 
                                                 font_size = 32,
                                                 anchor_x = "left",
                                                 anchor_y = "center",
                                                 color = (255, 255, 255, 255),
                                                 bold = True,
                                                 batch = self.batch,
                                                 width = self.dListInfo["List Width"],
                                                 height = self.dListInfo["Item Height"]),
                                  aArtist[0]])
            iY += self.dListInfo['Item Height']

    def Update_Albums(self):
        self.aAlbums = []
        iY = 0
        if not self.aArtists:
            self.Update_Artists()
        for aAlbum in self.cMain.cMusicLibrary.Get_Albums(self.aArtists[self.iArtistIndex][1]):
            self.aAlbums.append([self.Get_Label(aAlbum[1],
                                                -5000,
                                                iY, 
                                                font_size = 32,
                                                anchor_x = "left",
                                                anchor_y = "center",
                                                color = (255, 255, 255, 255),
                                                bold = True,
                                                batch = self.batch,
                                                width = self.dListInfo["List Width"],
                                                height = self.dListInfo["Item Height"]),
                                 aAlbum[0]])
            iY += self.dListInfo['Item Height']

    def Update_Tracks(self):
        self.aTracks = []
        iY = 0
        if not self.aAlbums:
            self.Update_Albums()
        for aTrack in self.cMain.cMusicLibrary.Get_Tracks(self.aAlbums[self.iAlbumIndex][1]):
            self.aTracks.append([self.Get_Label(aTrack[1],
                                                -5000,
                                                iY, 
                                                font_size = 32,
                                                anchor_x = "left",
                                                anchor_y = "center",
                                                color = (255, 255, 255, 255),
                                                bold = True,
                                                batch = self.batch,
                                                width = self.dListInfo["List Width"],
                                                height = self.dListInfo["Item Height"]),
                                 aTrack[0]])
            iY += self.dListInfo['Item Height']

    def Update_Title(self, sNewTitle):
        if self.lblTitle:
            self.lblTitle[0].delete()
        self.lblTitle = [self.Get_Label(sNewTitle, -5000, -5000, font_size = 22, anchor_y = "top", color = (143, 249, 255, 255), bold = True), self.cMain.window.width/2, 754]

    def Library_Back(self):
        if not self.bFade:
            if self.iAlbumIndex > -1 or self.iArtistIndex > -1:
                self.bFade = True
                self.iSelectedIndex = -1

    def Destroy(self):
        self.lblTitle[0].x = -5000
        self.lblTitle[0].y = -5000
        for spSprite in self.dSprites.values():
            spSprite.set_position(-5000, -5000)

    def Draw_Menu(self):
        aItems = []
        if self.iArtistIndex == -1:
            if not self.aArtists: self.Update_Artists()
            aItems = self.aArtists
        elif self.iAlbumIndex == -1 and self.iArtistIndex > -1:
            if not self.aAlbums: self.Update_Albums()
            aItems = self.aAlbums
        elif self.iAlbumIndex > -1:
            if not self.aTracks: self.Update_Tracks()
            aItems = self.aTracks
        iSelectedIndex = self.Draw_List(83, 177, aItems, 0, -1, self.batch, self.bFade, self.iLabelColorAlpha)
        if iSelectedIndex > -1:
            if self.iAlbumIndex > -1:
                self.cMain.cMixer.Add_Track_To_Playlist(None, None, self.aTracks[iSelectedIndex][1], True)
            else:
                self.bFade = True
                #Ensure we are fading out.
                self.iLabelColorAlphaSpeed = abs(self.iLabelColorAlphaSpeed) * -1
                self.iSelectedIndex = iSelectedIndex
        if self.bFade:
            self.iLabelColorAlpha += self.iLabelColorAlphaSpeed
            if self.iLabelColorAlphaSpeed < 0 and self.iLabelColorAlpha < 0:
                if self.iSelectedIndex > -1:
                    if self.iArtistIndex == -1:
                        self.iArtistIndex = self.iSelectedIndex
                        self.Update_Title(self.aArtists[self.iArtistIndex][0].text)
                        for aArtist in self.aArtists: aArtist[0].x = -5000
                        self.dListInfo["Start Index Artists"] = self.dListInfo["Start Index"]
                        self.dListInfo["Scroll Y Artists"] = self.dListInfo["Scroll Y"]
                    elif self.iAlbumIndex == -1:
                        self.iAlbumIndex = self.iSelectedIndex
                        self.Update_Title(self.aArtists[self.iArtistIndex][0].text + ' - ' + self.aAlbums[self.iAlbumIndex][0].text)
                        for aAlbum in self.aAlbums: aAlbum[0].x = -5000
                    self.dListInfo["Start Index"] = 0
                    self.dListInfo["Scroll Y"] = 0
                else:
                    self.dListInfo["Start Index"] = 0
                    self.dListInfo["Scroll Y"] = 0
                    if self.iAlbumIndex > -1:
                        self.iAlbumIndex = -1
                        self.Update_Title(self.aArtists[self.iArtistIndex][0].text)
                        for aTrack in self.aTracks: aTrack[0].x = -5000
                        for aAlbum in self.aAlbums: aAlbum[0].color = (255, 255, 255, 255)
                        self.aTracks = []
                    elif self.iArtistIndex > -1:
                        self.iArtistIndex = -1
                        self.Update_Title("MUSIC LIBRARY")
                        for aAlbum in self.aAlbums: aAlbum[0].x = -5000
                        for aArtist in self.aArtists: aArtist[0].color = (255, 255, 255, 255)
                        self.aAlbums = []
                        self.dListInfo["Start Index"] = self.dListInfo["Start Index Artists"]
                        self.dListInfo["Scroll Y"] = self.dListInfo["Scroll Y Artists"]
                self.iSelectedIndex = -1
                self.iLabelColorAlphaSpeed = abs(self.iLabelColorAlphaSpeed)
                self.iLabelColorAlpha = 0
            if self.iLabelColorAlphaSpeed > 0 and self.iLabelColorAlpha > 255:
                self.iLabelColorAlpha = 255
                self.iLabelColorAlphaSpeed = abs(self.iLabelColorAlphaSpeed) * -1
                self.bFade = False
                self.Save()