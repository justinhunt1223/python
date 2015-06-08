import mutagen
import os.path
import math

class Playlist:

    def __init__(self, sName, cMain):
        self.sName = sName
        self.cMain = cMain
        self.iIndex = int(self.cMain.GetConfig('currentPlaylistIndex', '-1'))
        self.aTracks = [int(self.cMain.GetConfig('currentTrackID', '-1'))]
        if -1 in self.aTracks: self.aTracks.remove(-1)

    def GetCurrentTrack(self):
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
        self.cMain.WriteConfig('currentTrackID', iTrackID)
        self.cMain.WriteConfig('currentTrackPlaylistIndex', self.iIndex)

    def Add(self, iTrackID):
        self.aTracks.append(iTrackID)
        self.iIndex = len(self.aTracks) - 1
        self.Save()

    def GetPreviousTrack(self, bRepeat, bRandom):
        if len(self.aTracks) == 0:
            return None
        elif len(self.aTracks) == 1:
            self.iIndex = 0
            qCurrentTrack = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE TrackID = %s;", (self.aTracks[self.iIndex]))[0]
            iTrackNumber = int(qCurrentTrack['TrackNumber'])
            iAlbumID = int(qCurrentTrack['AlbumID'])
            if iTrackNumber == 0:
                #If the album has no track numbers, then get the previous track id based on alphabetical order.
                qAlbum = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackTitle ASC;", (iAlbumID))
                aTrackID = [i['TrackID'] for i in qAlbum]
                iIndex = aTrackID.index(qCurrentTrack['TrackID'])
                if iIndex == (0):
                    #The current track is the last alphabetically in the album, so return the first track.
                    return aTrackID[len(aTrackID) - 1]
                else:
                    #Return the current index - 1.
                    return aTrackID[iIndex - 1]
            else:
                aPreviousTrack = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE AlbumID = %s AND TrackNumber < %s ORDER BY TrackNumber DESC LIMIT 1;", (iAlbumID, iTrackNumber))
                if aPreviousTrack:
                    #Found previous track.
                    return aPreviousTrack[0]['TrackID']
                else:
                    #Either the current track is the last in the album or there is only 1 track in the album. Either way, get the first track in the album.
                    aLastTrack = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackNumber DESC LIMIT 1;", (iAlbumID))[0]
                    return aLastTrack['TrackID']
        else:
            self.iIndex -= 1
            if self.iIndex < 0: self.iIndex = (len(self.aTracks) - 1)
            return self.aTracks[self.iIndex]

    def GetNextTrack(self, bRepeat, bRandom):
        if len(self.aTracks) == 0:
            return None
        elif len(self.aTracks) == 1:
            self.iIndex = 0
            qCurrentTrack = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE TrackID = %s;", (self.aTracks[self.iIndex]))[0]
            iTrackNumber = int(qCurrentTrack['TrackNumber'])
            iAlbumID = int(qCurrentTrack['AlbumID'])
            if iTrackNumber == 0:
                #If the album has no track numbers, then get the next track id based on alphabetical order.
                qAlbum = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackTitle ASC;", (iAlbumID))
                aTrackID = [i['TrackID'] for i in qAlbum]
                iIndex = aTrackID.index(qCurrentTrack['TrackID'])
                if iIndex == (len(aTrackID) - 1):
                    #The current track is the last alphabetically in the album, so return the first track.
                    return aTrackID[0]
                else:
                    #Return the current index + 1.
                    return aTrackID[iIndex + 1]
            else:
                aNextTrack = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE AlbumID = %s AND TrackNumber > %s ORDER BY TrackNumber ASC LIMIT 1;", (iAlbumID, iTrackNumber))
                if aNextTrack:
                    #Found next track.
                    return aNextTrack[0]['TrackID']
                else:
                    #Either the current track is the last in the album or there is only 1 track in the album. Either way, get the first track in the album.
                    aFirstTrack = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackNumber ASC LIMIT 1;", (iAlbumID))[0]
                    return aFirstTrack['TrackID']
        else:
            self.iIndex += 1
            if self.iIndex > len(self.aTracks) - 1: self.iIndex = 0
            return self.aTracks[self.iIndex]

class Mixer:

    def __init__(self, cMain):
        self.cMain = cMain
        self.fVolume = float(self.cMain.GetConfig('volume', '0.1')) * 1.0
        self.bPaused = int(self.cMain.GetConfig('paused', '0'))
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
        self.plCurrentPlaylist = Playlist('Default', self.cMain)
        self.aEqualizer = self.cMain.GetConfig('equalizerSettings', "9:10:11:12:13:13:12:11:10:9").split(':')

    def Save(self):
        # TODO: Only save equalizer when it is changed (which isn't implemented yet).
        sEq = ''
        for sEqualizerSetting in self.aEqualizer: sEq = sEq + sEqualizerSetting + ':'
        self.cMain.WriteConfig('equalizerSettings', sEq[:-1])

    def AddTrackToPlaylist(self, iArtistID, iAlbumID, iTrackID, bClearPlaylist = False):
        if bClearPlaylist: self.plCurrentPlaylist.Clear()
        if iAlbumID: #queue all tracks in album
            for dTrack in self.cMain.cMusicLibrary.GetTracks(iAlbumID):
                self.currentPlaylist.Add(dTrack['TrackID'])
            #sources.main.getMenu('Now Playing').updateScrollInfo(resources.main.getMenu('Now Playing').playlistScrollInfo, self.currentPlaylist.getItems())
            if not self.cMain.cRenderer.bPlaying or bClearPlaylist:
                self.PlayTrack(self.plCurrentPlaylist.GetNextTrack(bRepeat = self.bPlaylistRepeat, bRandom = self.bPlaylistRandom))
        elif iArtistID:
            for dctAlbum in self.cMain.cMusicLibrary.GetAlbums(iArtistID):
                for dTrack in self.cMain.cMusicLIbrary.GetTracks(dctAlbum['AlbumID']):
                    self.plCurrentPlaylist.Add(dTrack['TrackID'])
            #resources.main.getMenu('Now Playing').updateScrollInfo(resources.main.getMenu('Now Playing').playlistScrollInfo, self.currentPlaylist.getItems())
            if not self.cMain.cRenderer.bPlaying or bClearPlaylist:
                self.PlayTrack(self.plCurrentPlaylist.GetNextTrack(bRepeat = self.bPlaylistRepeat, bRandom = self.bPlaylistRandom))
        elif iTrackID:
            self.plCurrentPlaylist.Add(iTrackID)
            self.PlayTrack(iTrackID)

    def GetLabelBaseText(self):
        return self.dTrackInfo['Title'] + ' - ' + self.dTrackInfo['Artist']

    def UpdateLabel(self, iTrackPosition = -1):
        if iTrackPosition != -1:
            sTime = str(int(math.floor(iTrackPosition / 60))).zfill(2) + ":" + str((iTrackPosition % 60)).zfill(2)
            self.lblStatusItem.Text(sTime + " " + self.GetLabelBaseText())

    def PlayTrack(self, iTrackID):
        if iTrackID == None:
            return False
        dTrack = self.cMain.cMusicLibrary.GetTrackInfo(iTrackID)
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
        self.cMain.cRenderer.PlayTrack(dTrack['Filename'])
        #self.cMain.cRenderer.Update_Equalizer(self.aEqualizer)
        
        # The status item text needs to modified (or the item created if its the first track being played).
        if self.lblStatusItem == None:
            self.lblStatusItem = self.cMain.cStatusBar.AddItem('', True)
        self.lblStatusItem.Text(self.GetLabelBaseText())

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
                    self.dTrackInfo['Album Art'] = self.cMain.cMenuBase.GetSprite('artwork.png', width = 295, height = 344)
                except: pass
        # check in folder
        if self.bAlbumArtUseFolder and not self.dTrackInfo['Album Art'] and os.path.isfile(dTrack['Filename']):
            sDir=os.path.dirname(dTrack['Filename'])
            for sFilename in os.listdir(sDir + "/"):
                if os.path.splitext(sFilename)[1] in ['.jpeg', '.jpg', '.png', 'bmp']:
                    try:
                        spAlbumArt=self.cMain.cMenuBase.GetSprite(sDir + "/" + sFilename, width = 295, height = 344)
                        if self.dTrackInfo['Album Art']:
                            if spAlbumArt.width > self.dTrackInfo['Album Art'].width:
                                if spAlbumArt.height > self.dTrackInfo['Album Art'].height: self.dTrackInfo['Album Art'] = spAlbumArt
                        if not self.dTrackInfo['Album Art']: self.dTrackInfo['Album Art'] = spAlbumArt
                    except: pass

    def PlayNextTrack(self):
        iTrackID = self.plCurrentPlaylist.GetNextTrack(True, False)
        self.AddTrackToPlaylist(None, None, iTrackID, len(self.plCurrentPlaylist.aTracks) == 1)

    def PlayPreviousTrack(self):
        iTrackID = self.plCurrentPlaylist.GetPreviousTrack(True, False)
        self.AddTrackToPlaylist(None, None, iTrackID, len(self.plCurrentPlaylist.aTracks) == 1)

    def VolumeUp(self, fAmount):
        self.fVolume = min(1.0, self.fVolume + fAmount)
        self.cMain.WriteConfig('volume', self.fVolume)
        self.cMain.cRenderer.Set_Volume(self.fVolume)

    def VolumeDown(self, fAmount):
        self.fVolume = max(0.0, self.fVolume - fAmount)
        self.cMain.WriteConfig('volume', self.fVolume)
        self.cMain.cRenderer.Set_Volume(self.fVolume)

    def Seek(self, fPercentage):
        if fPercentage != -1:
            self.dTrackInfo['Seeked'] = int(fPercentage * self.dTrackInfo['Length'])
            self.cMain.cRenderer.Seek(self.dTrackInfo['Seeked'])

    def TogglePause(self):
        if self.cMain.cRenderer.bPlaying:
            if not self.bPaused:
                self.cMain.cRenderer.TogglePause()
                self.bPaused = True
            elif self.bPaused:
                self.cMain.cRenderer.TogglePause()
                self.bPaused = False
        if not self.cMain.cRenderer.bPlaying and self.dTrackInfo:
            try:
                self.PlayTrack(self.dTrackInfo['Track ID'])
                if self.bPaused:
                    self.cMain.cRenderer.TogglePause()
                    self.bPaused = False
            except: pass
        self.cMain.WriteConfig('paused', self.bPaused)
        self.lblStatusItem.Text([self.GetLabelBaseText(), 'PAUSED'][self.bPaused])