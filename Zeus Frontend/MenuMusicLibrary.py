import MenuBase
import pyglet

class Menu(MenuBase.Base):

    def __init__(self, cMain):
        self.cMain = cMain
        self.lblTitle = None
        self.UpdateTitle(self.cMain.GetConfig('musicLibraryTitle', 'MUSIC LIBRARY'))
        self.aMenuButtons = [[self.GetSprite("images/arrow/arrow-left.png"), (960, 662), self.LibraryBack]]
        self.x = 0
        self.batch = pyglet.graphics.Batch()
        self.dSprites = {"List Background1": self.GetSprite("images/library/library-list-background.png", self.batch),
                         "List Background2": self.GetSprite("images/library/library-list-background.png", self.batch),
                         "List Background Cover": self.GetSprite("images/library/library-list-background-cover.png")}
        
        self.dListInfo = {"Item Height": 66,
                          "Start Index": int(self.cMain.GetConfig('startIndex', '0')),
                          "Start Index Artists": int(self.cMain.GetConfig('artistsStartIndex', '0')),
                          "Scroll Y": int(self.cMain.GetConfig('scrollY', '0')),
                          "Scroll Y Artists": int(self.cMain.GetConfig('artistsScrollY', '0')),
                          "Max Y": 0,
                          "Min Y": 0,
                          "List Width": self.dSprites["List Background1"].width,
                          "List Height": self.dSprites["List Background1"].height,
                          "Background Y": 177,
                          "Background Y Offset": int(self.cMain.GetConfig('backgroundYOffset', '0')),
                          "Slide X": 0,
                          "Slide X Speed": 0}
        self.aArtists = []
        self.aAlbums = []
        self.aTracks = []
        self.iArtistIndex = int(self.cMain.GetConfig('artistIndex', '-1'))
        self.iAlbumIndex = int(self.cMain.GetConfig('albumIndex', '-1'))
        if self.iAlbumIndex != -1:
            self.UpdateTracks()
        elif self.iArtistIndex != -1:
            self.UpdateAlbums()
        else:
            self.UpdateArtists()
        self.bFade = False
        self.iLabelColorAlpha = 255
        self.iLabelColorAlphaSpeed = -25
        self.iSelectedIndex = -1

    def Init(self):
        iScrollY = self.dListInfo['Scroll Y']
        self.dListInfo['Scroll Y'] = self.dListInfo['Scroll Y Artists']
        self.DrawList(83, 177, self.aArtists, 0, -1, self.batch, self.bFade, self.iLabelColorAlpha, bSetY = True)
        self.dListInfo['Scroll Y'] = iScrollY

    def Save(self):
        self.cMain.WriteConfig('scrollY', self.dListInfo['Scroll Y'])
        self.cMain.WriteConfig('artistsScrollY', self.dListInfo['Scroll Y Artists'])
        self.cMain.WriteConfig('artistsStartIndex', self.dListInfo['Start Index Artists'])
        self.cMain.WriteConfig('startIndex', self.dListInfo['Start Index'])
        self.cMain.WriteConfig('backgroundYOffset', self.dListInfo['Background Y Offset'])
        self.cMain.WriteConfig('artistIndex', self.iArtistIndex)
        self.cMain.WriteConfig('albumIndex', self.iAlbumIndex)
        self.cMain.WriteConfig('musicLibraryTitle', self.lblTitle[0].text)

    def UpdateArtists(self):
        self.aArtists = []
        iY = 0
        for aArtist in self.cMain.cMusicLibrary.GetArtists():
            self.aArtists.append([self.GetLabel(aArtist[1],
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

    def UpdateAlbums(self):
        self.aAlbums = []
        iY = 0
        if not self.aArtists:
            self.UpdateArtists()
        for aAlbum in self.cMain.cMusicLibrary.GetAlbums(self.aArtists[self.iArtistIndex][1]):
            self.aAlbums.append([self.GetLabel(aAlbum[1],
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

    def UpdateTracks(self):
        self.aTracks = []
        iY = 0
        if not self.aAlbums:
            self.UpdateAlbums()
        for aTrack in self.cMain.cMusicLibrary.GetTracks(self.aAlbums[self.iAlbumIndex][1]):
            self.aTracks.append([self.GetLabel(aTrack[1],
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

    def UpdateTitle(self, sNewTitle):
        if self.lblTitle:
            self.lblTitle[0].delete()
        self.lblTitle = [self.GetLabel(sNewTitle, -5000, -5000, font_size = 22, anchor_y = "top", color = (143, 249, 255, 255), bold = True), self.cMain.window.width/2, 754]

    def LibraryBack(self):
        if not self.bFade:
            if self.iAlbumIndex > -1 or self.iArtistIndex > -1:
                self.bFade = True
                self.iSelectedIndex = -1

    def Destroy(self):
        self.lblTitle[0].x = -5000
        self.lblTitle[0].y = -5000
        for spSprite in self.dSprites.values():
            spSprite.set_position(-5000, -5000)

    def DrawMenu(self):
        aItems = []
        if self.iArtistIndex == -1:
            if not self.aArtists: self.UpdateArtists()
            aItems = self.aArtists
        elif self.iAlbumIndex == -1 and self.iArtistIndex > -1:
            if not self.aAlbums: self.UpdateAlbums()
            aItems = self.aAlbums
        elif self.iAlbumIndex > -1:
            if not self.aTracks: self.UpdateTracks()
            aItems = self.aTracks
        iSelectedIndex = self.DrawList(83, 177, aItems, 0, -1, self.batch, self.bFade, self.iLabelColorAlpha)
        if iSelectedIndex > -1:
            if self.iAlbumIndex > -1:
                self.cMain.cMixer.AddTrackToPlaylist(None, None, self.aTracks[iSelectedIndex][1], True)
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
                        self.UpdateTitle(self.aArtists[self.iArtistIndex][0].text)
                        for aArtist in self.aArtists: aArtist[0].x = -5000
                        self.dListInfo["Start Index Artists"] = self.dListInfo["Start Index"]
                        self.dListInfo["Scroll Y Artists"] = self.dListInfo["Scroll Y"]
                    elif self.iAlbumIndex == -1:
                        self.iAlbumIndex = self.iSelectedIndex
                        self.UpdateTitle(self.aArtists[self.iArtistIndex][0].text + ' - ' + self.aAlbums[self.iAlbumIndex][0].text)
                        for aAlbum in self.aAlbums: aAlbum[0].x = -5000
                    self.dListInfo["Start Index"] = 0
                    self.dListInfo["Scroll Y"] = 0
                else:
                    self.dListInfo["Start Index"] = 0
                    self.dListInfo["Scroll Y"] = 0
                    if self.iAlbumIndex > -1:
                        self.iAlbumIndex = -1
                        self.UpdateTitle(self.aArtists[self.iArtistIndex][0].text)
                        for aTrack in self.aTracks: aTrack[0].x = -5000
                        for aAlbum in self.aAlbums: aAlbum[0].color = (255, 255, 255, 255)
                        self.aTracks = []
                    elif self.iArtistIndex > -1:
                        self.iArtistIndex = -1
                        self.UpdateTitle("MUSIC LIBRARY")
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