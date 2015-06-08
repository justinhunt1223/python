import mutagen
import os.path
import time

class ScanMusic:

    def __init__(self, cMain):
        self.aDirectories = ["/media/music/"]
        self.aScanFiles = []
        self.cMain = cMain
        self.cMySQL = cMain.cMySQL
        #self.Scan()

    def Scan(self):
        #Scan should be a one time thing since it takes so much time.
        aFiles = []
        for sDir in self.aDirectories:
            for sDirPath, aDirNames, aFilenames in os.walk(sDir):
                for sFilename in [f for f in aFilenames if f.endswith(".mp3") or f.endswith(".ogg") or f.endswith(".flac") or f.endswith(".wma")]:
                    sFilename = os.path.join(sDirPath, sFilename)
                    self.ScanFile(sFilename)
                    # Not used. A scan is a one time thing right now.
                    #self.AddFilenameToScan(sFilename)
        self.aScanFiles = aFiles

    def AddFilenameToScan(self, sFilename):
        self.cMySQL.RunQuery("INSERT INTO `FilesToScan` (Filename) VALUES (%s);", (sFilename))

    def GetArtistID(self, sArtist):
        qArtistID = self.cMySQL.RunQuery("SELECT ArtistID FROM Artists WHERE ArtistName = %s;", (sArtist))
        if len(qArtistID) > 0:
            return str(int(qArtistID[0]['ArtistID']))
        else:
            self.cMySQL.RunQuery("INSERT INTO Artists (ArtistName) VALUES (%s);", (sArtist))
            return self.GetArtistID(sArtist)

    def GetAlbumID(self, sAlbum, iArtistID):
        qAlbumID = self.cMySQL.RunQuery("SELECT AlbumID FROM Albums WHERE AlbumName = %s and ArtistID = %s;", (sAlbum, iArtistID))
        if len(qAlbumID) > 0:
            return str(int(qAlbumID[0]['AlbumID']))
        else:
            self.cMySQL.RunQuery("INSERT INTO Albums (AlbumName, ArtistID) VALUES (%s, %s);", (sAlbum, iArtistID))
            return self.GetAlbumID(sAlbum, iArtistID)

    def GetTrackID(self, sFilename, iAlbumID, iArtistID, sTrackTitle, iTrackNumber):
        qTrackID = self.cMySQL.RunQuery("SELECT TrackID FROM Tracks WHERE Filename = %s;", (sFilename))
        if len(qTrackID) > 0:
            return str(int(qTrackID[0]['TrackID']))
        else:
            self.cMySQL.RunQuery("INSERT INTO Tracks (AlbumID, ArtistID, Filename, TrackTitle, TrackNumber) VALUES (%s, %s, %s, %s, %s);", (iAlbumID, iArtistID, sFilename, sTrackTitle, iTrackNumber))
            return self.GetTrackID(sFilename, iAlbumID, iArtistID, sTrackTitle, iTrackNumber)

    def ScanFile(self, sFilename):
        try:
            mutFile=mutagen.File(sFilename, easy=True)
            if os.path.splitext(sFilename)[1] == '.wma':
                sArtist = mutFile['WM/AlbumArtist'][0].encode("iso-8859-1")
                sAlbum = mutFile['WM/AlbumTitle'][0].encode("iso-8859-1")
                sTrackTitle = mutFile['Title'][0].encode("iso-8859-1")
                try:
                    iTrackNumber = mutFile['WM/Track'][0].encode("iso-8859-1")
                    if iTrackNumber.rfind('/') > -1: iTrackNumber = iTrackNumber.split('/')[0]
                except: iTrackNumber = "0"
                iArtistID = self.GetArtistID(sArtist)
                iAlbumID = self.GetAlbumID(sAlbum, iArtistID)
                iTrackID = self.GetAlbumID(sFilename, iAlbumID, iArtistID, sTrackTitle, iTrackNumber)
            if os.path.splitext(sFilename)[1] != '.wma':
                sArtist = None
                for i in ['album artist', 'performer', 'artist']:
                    if mutFile.has_key(i):
                        sArtist = mutFile[i][0].encode("iso-8859-1")
                        break
                sAlbum = mutFile['album'][0].encode("iso-8859-1")
                sTrackTitle = mutFile['title'][0].encode("iso-8859-1")
                try:
                    iTrackNumber = mutFile['tracknumber'][0].encode("iso-8859-1")
                    if iTrackNumber.rfind('/') > -1: iTrackNumber = iTrackNumber.split('/')[0]
                except: iTrackNumber = "0"
                iArtistID = self.GetArtistID(sArtist)
                iAlbumID = self.GetAlbumID(sAlbum, iArtistID)
                iTrackID = self.GetTrackID(sFilename, iAlbumID, iArtistID, sTrackTitle, iTrackNumber)
            #resources.main.getMenu('Panel').addStatusItem('scannedFile', "Scanning " + self.getPercentageScanned() + "%: " + artist + " - " + album + " - " + title, repeat=True)
        except:
            self.cMySQL.RunQuery("INSERT INTO FailedToScan (Filename) VALUES (%s);", (sFilename))
            #####resources.main.getMenu('Panel').addStatusItem(filename, "Failed: " + filename)

class MusicLibrary:

    def __init__(self, cMain):
        self.cMain = cMain

    def GetArtists(self):
        qArtists = self.cMain.cMySQL.RunQuery("SELECT * FROM Artists ORDER BY ArtistName ASC;")
        aArtists = []
        for dArtist in qArtists:
            #ISO-8859-1 helps with accent marks.
            aArtists.append([int(dArtist["ArtistID"]), dArtist["ArtistName"].decode("ISO-8859-1")])
        return aArtists

    def GetAlbums(self, iArtistID):
        qAlbums = self.cMain.cMySQL.RunQuery("SELECT * FROM Albums WHERE ArtistID = %s ORDER BY AlbumName ASC;", (iArtistID))
        aAlbums = []
        for dAlbum in qAlbums:
            #ISO-8859-1 helps with accent marks.
            aAlbums.append([int(dAlbum["AlbumID"]), dAlbum["AlbumName"].decode("ISO-8859-1")])
        return aAlbums

    def GetTracks(self, iAlbumID):
        qTracks = self.cMain.cMySQL.RunQuery("SELECT * FROM Tracks WHERE AlbumID = %s ORDER BY TrackNumber ASC;", (iAlbumID))
        aTracks = []
        for dTrack in qTracks:
            #ISO-8859-1 helps with accent marks.
            aTracks.append([int(dTrack["TrackID"]), dTrack["TrackTitle"].decode("ISO-8859-1"), dTrack['TrackNumber']])
        return aTracks

    def GetTrackInfo(self, sTrackID):
        qTrack = self.cMain.cMySQL.RunQuery("""SELECT * FROM Tracks
                                                  JOIN Albums ON Tracks.AlbumID = Albums.ALbumID
                                                  JOIN Artists ON Tracks.ArtistID = Artists.ArtistID
                                                  WHERE Tracks.TrackID = %s;""", (sTrackID))
        return qTrack[0]
