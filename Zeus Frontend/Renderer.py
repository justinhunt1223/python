import subprocess
import pyglet

class Renderer:

    def __init__(self, cMain):
        self.cMain = cMain
        self.iTrackPosition = -1
        self.bPlaying = False
        
        self.sFifo = '/home/justin/.mplayer/fifo'
        self.sOutput = '/home/justin/.mplayer/output'
        subprocess.Popen('mkfifo ' + self.sFifo, shell=True)
        #subprocess.Popen('sudo killall mplayer', shell=True)
        self.renderer = subprocess.Popen('mplayer -slave -quiet -idle -input file=' + self.sFifo + ' > ' + self.sOutput, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        pyglet.clock.schedule_interval(lambda e: self.HookMPlayer(), 1)
        pyglet.clock.schedule_interval(lambda e: self.Save(), 5)

    def Save(self):
        fPosition = '0.0'
        if self.bPlaying:
            fPosition = self.iTrackPosition / self.GetTrackLength()
        self.cMain.WriteConfig('trackPosition', fPosition)

    def MPlayerSend(self, sCommand): subprocess.Popen('echo "' + sCommand + '\n" >> ' + self.sFifo, shell = True)

    def GetTrackLength(self): return self.cMain.cMixer.dTrackInfo['Length']
    def GetAlbumArt(self): return self.cMain.cMixer.dTrackInfo['Album Art']
    def GetTrackNumber(self): return self.cMain.cMixer.dTrackInfo['Track #']

    def UpdateEqualizer(self, aEqualizer):
        sEq = ''
        for sEqSetting in aEqualizer: sEq = sEq + str(-1 * (int(sEqSetting) - 12)) + ':'
        self.MPlayerSend('af_cmdline equalizer ' + sEq[:-1])

    def GetPosition(self): return self.iTrackPosition

    def Seek(self, fPercentage):
        if fPercentage > 0:
            self.MPlayerSend('seek ' + str(fPercentage * 100) + ' 1')
            self.MPlayerSend('get_time_pos')
            try:
                self.iTrackPosition = int(fPercentage * self.cMain.cMixer.dTrackInfo['Length'])
            except:
                pass

    def StopTrack(self):
        self.bPlaying = False
        self.MPlayerSend('stop')

    def PlayTrack(self, sFilename):
        self.bPlaying = True
        self.MPlayerSend('loadfile ' + sFilename.replace(' ', '\ '))
        self.iTrackPosition = 0
        self.MPlayerSend('get_time_pos')
        self.Set_Volume(self.cMain.cMixer.fVolume)

    def TogglePause(self):
        self.MPlayerSend('pause')

    def Set_Volume(self, fLevel):
        self.cMain.WriteConfig('volume', fLevel)
        self.MPlayerSend('volume ' + str(fLevel * 100) + ' 1')

    def HookMPlayer(self):
        if self.bPlaying:
            f = open(self.sOutput, 'r')
            for line in [i.replace('\n', '').replace('\x00', '') for i in f.readlines()]:
                if line.rfind("ANS_TIME_POSITION=") > -1:
                    iNewPosition = int(line.split("=")[1].split('.')[0])
                    self.iTrackPosition = iNewPosition
                    self.cMain.cMixer.UpdateLabel(iTrackPosition = iNewPosition)
            f.close()
            f = open(self.sOutput, 'w')
            f.write('\n')
            f.close()
            self.MPlayerSend('get_time_pos')
            if self.iTrackPosition + 2 >= int(self.GetTrackLength()):
                print "Playing next..."
                self.cMain.cMixer.PlayNextTrack()
