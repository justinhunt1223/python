import mutagen
import os.path
import math

class PLAYLIST:

    def __init__(self, sName, cMain):
        self.sName = sName
        self.cMain = cMain
        self.iIndex = int(self.cMain.Get_Config('currentPlaylistIndex', '-1'))
        self.aTracks = [int(self.cMain.Get_Config('currentTrackID', '-1'))]
        if -1 in self.aTracks: self.aTracks.remove(-1)

    def Get_Current_Track(self):
        if self.aTracks:
            return self.aTracks[self.iIndex]
        else:
            return None

    def Clear(self):
        self.aTracks = []
        self.iIndex = -1
        self.Save()

    def Save(self):
        if self.aTracks:
            iTrackID = self.aTracks[self.iIndex]
        else:
            iTrackID = ''
        self.cMain.Write_Config('currentTrackID', iTrackID)
        self.cMain.Write_Config('currentTrackPlaylistIndex', self.iIndex)

    def Add(self, iTrackID):
        self.aTracks.append(iTrackID)
        self.iIndex = len(self.aTracks) - 1
        self.Save()

    def Get_Previous_Track(self, bRepeat, bRandom):
        if len(self.aTracks) == 0:
            return None
        elif len(self.aTracks) == 1:
            self.iIndex = 0
            qCurrentTrack = self.cMain.cMySQL.Run_Query("SELECT * FROM Tracks WHERE TrackID = %s;", (self.aTracks[self.iIndex]))[0]
            iTrackNumber = int(qCurrentTrack['TrackNumber'])
            iAlbumID = int(qCurrentTrack['AlbumID'])
            if iTrackNumber == 0:
                #If the album has no track numbers, then get the previous track id based on alphabetical order.
                qAlbum = self.cMain.cMySQL.Run_Query("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackTitle ASC;", (iAlbumID))
                aTrackID = [i['TrackID'] for i in qAlbum]
                iIndex = aTrackID.index(qCurrentTrack['TrackID'])
                if iIndex == (0):
                    #The current track is the last alphabetically in the album, so return the first track.
                    return aTrackID[len(aTrackID) - 1]
                else:
                    #Return the current index - 1.
                    return aTrackID[iIndex - 1]
            else:
                aPreviousTrack = self.cMain.cMySQL.Run_Query("SELECT * FROM Tracks WHERE AlbumID = %s AND TrackNumber < %s ORDER BY TrackNumber DESC LIMIT 1;", (iAlbumID, iTrackNumber))
                if aPreviousTrack:
                    #Found previous track.
                    return aPreviousTrack[0]['TrackID']
                else:
                    #Either the current track is the last in the album or there is only 1 track in the album. Either way, get the first track in the album.
                    aLastTrack = self.cMain.cMySQL.Run_Query("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackNumber DESC LIMIT 1;", (iAlbumID))[0]
                    return aLastTrack['TrackID']
        else:
            self.iIndex -= 1
            if self.iIndex < 0: self.iIndex = (len(self.aTracks) - 1)
            return self.aTracks[self.iIndex]

    def Get_Next_Track(self, bRepeat, bRandom):
        if len(self.aTracks) == 0:
            return None
        elif len(self.aTracks) == 1:
            self.iIndex = 0
            qCurrentTrack = self.cMain.cMySQL.Run_Query("SELECT * FROM Tracks WHERE TrackID = %s;", (self.aTracks[self.iIndex]))[0]
            iTrackNumber = int(qCurrentTrack['TrackNumber'])
            iAlbumID = int(qCurrentTrack['AlbumID'])
            if iTrackNumber == 0:
                #If the album has no track numbers, then get the next track id based on alphabetical order.
                qAlbum = self.cMain.cMySQL.Run_Query("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackTitle ASC;", (iAlbumID))
                aTrackID = [i['TrackID'] for i in qAlbum]
                iIndex = aTrackID.index(qCurrentTrack['TrackID'])
                if iIndex == (len(aTrackID) - 1):
                    #The current track is the last alphabetically in the album, so return the first track.
                    return aTrackID[0]
                else:
                    #Return the current index + 1.
                    return aTrackID[iIndex + 1]
            else:
                aNextTrack = self.cMain.cMySQL.Run_Query("SELECT * FROM Tracks WHERE AlbumID = %s AND TrackNumber > %s ORDER BY TrackNumber ASC LIMIT 1;", (iAlbumID, iTrackNumber))
                if aNextTrack:
                    #Found next track.
                    return aNextTrack[0]['TrackID']
                else:
                    #Either the current track is the last in the album or there is only 1 track in the album. Either way, get the first track in the album.
                    aFirstTrack = self.cMain.cMySQL.Run_Query("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackNumber ASC LIMIT 1;", (iAlbumID))[0]
                    return aFirstTrack['TrackID']
        else:
            self.iIndex += 1
            if self.iIndex > len(self.aTracks) - 1: self.iIndex = 0
            return self.aTracks[self.iIndex]

class MIXER:

    def __init__(self, cMain):
        self.cMain = cMain
        self.fVolume = float(self.cMain.Get_Config('volume', '0.1')) * 1.0
        self.bPaused = int(self.cMain.Get_Config('paused', '0'))
        self.lblStatusItem = None
        self.bPlaylistRepeat = True
        self.bPlaylistRandom = False
        self.bAlbumArtUseFolder = True
        self.bAlbumArtUseTags = True
        self.dTrackInfo = {'Album Art': None,
                           'Artist': '',
                           'Album': '',
                           'Track': '',
                           'Track #': '',
                           'Length': 0,
                           'Seeked': 0}
        self.aPlaylists = []
        self.plCurrentPlaylist = PLAYLIST('Default', self.cMain)
        self.aEqualizer = self.cMain.Get_Config('equalizerSettings', "9:10:11:12:13:13:12:11:10:9").split(':')

    def Close(self):
        sEq = ''
        for sEqualizerSetting in self.aEqualizer: sEq = sEq + sEqualizerSetting + ':'
        self.cMain.Write_Config('equalizerSettings', sEq[:-1])

    def Add_Track_To_Playlist(self, iArtistID, iAlbumID, iTrackID, bClearPlaylist = False):
        if bClearPlaylist: self.plCurrentPlaylist.Clear()
        if iAlbumID: #queue all tracks in album
            for dTrack in self.cMain.cMusicLibrary.Get_Tracks(iAlbumID):
                self.currentPlaylist.Add(dTrack['TrackID'])
            #sources.main.getMenu('Now Playing').updateScrollInfo(resources.main.getMenu('Now Playing').playlistScrollInfo, self.currentPlaylist.getItems())
            if not self.cMain.cRenderer.bPlaying or bClearPlaylist:
                self.Play_Track(self.plCurrentPlaylist.Get_Next_Track(bRepeat = self.bPlaylistRepeat, bRandom = self.bPlaylistRandom))
        elif iArtistID:
            for dctAlbum in self.cMain.cMusicLibrary.Get_Albums(iArtistID):
                for dTrack in self.cMain.cMusicLIbrary.Get_Tracks(dctAlbum['AlbumID']):
                    self.plCurrentPlaylist.Add(dTrack['TrackID'])
            #resources.main.getMenu('Now Playing').updateScrollInfo(resources.main.getMenu('Now Playing').playlistScrollInfo, self.currentPlaylist.getItems())
            if not self.cMain.cRenderer.bPlaying or bClearPlaylist:
                self.Play_Track(self.plCurrentPlaylist.Get_Next_Track(bRepeat = self.bPlaylistRepeat, bRandom = self.bPlaylistRandom))
        elif iTrackID:
            self.plCurrentPlaylist.Add(iTrackID)
            self.Play_Track(iTrackID)

    def Get_Label_Base_Text(self):
        return self.dTrackInfo['Title'] + ' - ' + self.dTrackInfo['Artist']

    def Update_Label(self, iTrackPosition = -1):
        if iTrackPosition != -1:
            sTime = str(int(math.floor(iTrackPosition / 60))).zfill(2) + ":" + str((iTrackPosition % 60)).zfill(2)
            self.lblStatusItem.Text(sTime + " " + self.Get_Label_Base_Text())

    def Play_Track(self, iTrackID):
        if iTrackID == None:
            return False
        dTrack = self.cMain.cMusicLibrary.Get_Track_Info(iTrackID)
        self.dTrackInfo = {'Artist': dTrack['ArtistName'],
                           'Album': dTrack['AlbumName'],
                           'Title': dTrack['TrackTitle'],
                           'Track #': dTrack['TrackNumber'],
                           'Track Dict': dTrack,
                           'Album Art': None,
                           'Length': 0,
                           'Seeked': 0,
                           'Track ID': iTrackID}
        
        # Update the equalizer setting when the track is played.
        self.cMain.cRenderer.Play_Track(dTrack['Filename'])
        self.cMain.cRenderer.Update_Equalizer(self.aEqualizer)
        
        # The status item text needs to modified (or the item created if its the first track being played).
        if self.lblStatusItem == None:
            self.lblStatusItem = self.cMain.cStatusBar.Add_Item('', True)
        self.lblStatusItem.Text(self.Get_Label_Base_Text())

        try: mtAudioFile=mutagen.File(dTrack['Filename'])
        except: mtAudioFile=None
        if mtAudioFile:
            self.dTrackInfo['Length'] = mtAudioFile.info.length
            # try to get album art from tags
            if self.bAlbumArtUseTags:
                try:
                    fileAlbumArt = open('artwork.png', 'wb')
                    fileAlbumArt.write(mtAudioFile['APIC:'].data)
                    fileAlbumArt.close()
                    self.dTrackInfo['Album Art'] = self.cMain.cMenuBase.Get_Sprite('artwork.png', width = 295, height = 344)
                except: pass
        # check in folder
        if self.bAlbumArtUseFolder and not self.dTrackInfo['Album Art'] and os.path.isfile(dTrack['Filename']):
            sDir=os.path.dirname(dTrack['Filename'])
            for sFilename in os.listdir(sDir + "/"):
                if os.path.splitext(sFilename)[1] in ['.jpeg', '.jpg', '.png', 'bmp']:
                    try:
                        spAlbumArt=self.cMain.cMenuBase.Get_Sprite(sDir + "/" + sFilename, width = 295, height = 344)
                        if self.dTrackInfo['Album Art']:
                            if spAlbumArt.width > self.dTrackInfo['Album Art'].width:
                                if spAlbumArt.height > self.dTrackInfo['Album Art'].height: self.dTrackInfo['Album Art'] = spAlbumArt
                        if not self.dTrackInfo['Album Art']: self.dTrackInfo['Album Art'] = spAlbumArt
                    except: pass

    def Play_Next_Track(self):
        iTrackID = self.plCurrentPlaylist.Get_Next_Track(True, False)
        self.Add_Track_To_Playlist(None, None, iTrackID, len(self.plCurrentPlaylist.aTracks) == 1)

    def Play_Previous_Track(self):
        iTrackID = self.plCurrentPlaylist.Get_Previous_Track(True, False)
        self.Add_Track_To_Playlist(None, None, iTrackID, len(self.plCurrentPlaylist.aTracks) == 1)

    def Volume_Up(self, fAmount):
        self.fVolume = min(1.0, self.fVolume + fAmount)
        self.cMain.Write_Config('volume', self.fVolume)
        self.cMain.cRenderer.Set_Volume(self.fVolume)

    def Volume_Down(self, fAmount):
        self.fVolume = max(0.0, self.fVolume - fAmount)
        self.cMain.Write_Config('volume', self.fVolume)
        self.cMain.cRenderer.Set_Volume(self.fVolume)

    def Seek(self, fPercentage):
        if fPercentage != -1:
            self.dTrackInfo['Seeked'] = int(fPercentage * self.dTrackInfo['Length'])
            self.cMain.cRenderer.Seek(self.dTrackInfo['Seeked'])

    def Toggle_Pause(self):
        if self.cMain.cRenderer.bPlaying:
            if not self.bPaused:
                self.cMain.cRenderer.Toggle_Pause()
                self.bPaused = True
            elif self.bPaused:
                self.cMain.cRenderer.Toggle_Pause()
                self.bPaused = False
        if not self.cMain.cRenderer.bPlaying and self.dTrackInfo:
            try:
                self.Play_Track(self.dTrackInfo['Track ID'])
                if self.bPaused:
                    self.cMain.cRenderer.Toggle_Pause()
                    self.bPaused = False
            except: pass
        self.cMain.Write_Config('paused', self.bPaused)
        self.lblStatusItem.Text([self.Get_Label_Base_Text(), 'PAUSED'][self.bPaused])