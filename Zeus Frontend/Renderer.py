import subprocess
import pyglet

class RENDERER:

    def __init__(self, cMain):
        self.cMain = cMain
        self.iTrackPosition = -1
        self.bPlaying = False
        
        self.sFifo = '/home/justin/.mplayer/fifo'
        self.sOutput = '/home/justin/.mplayer/output'
        subprocess.Popen('mkfifo ' + self.sFifo, shell=True)
        subprocess.Popen('sudo killall mplayer', shell=True)
        self.renderer = subprocess.Popen('mplayer -slave -quiet -idle -input file=' + self.sFifo + ' > ' + self.sOutput, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        pyglet.clock.schedule_interval(lambda e: self.Hook_MPlayer(), 1)

    def Close(self):
        fPosition = '0.0'
        if self.bPlaying:
            fPosition = self.iTrackPosition / self.Get_Track_Length()
        self.cMain.Write_Config('trackPosition', fPosition)
        #TODO: This doesn't seem to be stopping MPlayer...
        self.renderer.kill()
        self.renderer = None

    def MPlayer_Send(self, sCommand): subprocess.Popen('echo "' + sCommand + '\n" >> ' + self.sFifo, shell = True)

    def Get_Track_Length(self): return self.cMain.cMixer.dTrackInfo['Length']
    def Get_Album_Art(self): return self.cMain.cMixer.dTrackInfo['Album Art']
    def Get_Track_Number(self): return self.cMain.cMixer.dTrackInfo['Track #']

    def Update_Equalizer(self, sEqualizerSetting):
        sEq = ''
        for sEqSetting in sEqualizerSetting: sEq = sEq + str(-1 * (sEqSetting - 12)) + ':'
        self.MPlayer_Send('af_cmdline equalizer ' + sEq[:-1])

    def Get_Position(self): return self.iTrackPosition

    def Seek(self, fPercentage):
        if fPercentage > 0:
            self.MPlayer_Send('seek ' + str(fPercentage * 100) + ' 1')
            self.MPlayer_Send('get_time_pos')
            try:
                self.iTrackPosition = int(fPercentage * self.cMain.cMixer.dTrackInfo['Length'])
            except:
                pass

    def Stop_Track(self):
        self.bPlaying = False
        self.MPlayer_Send('stop')

    def Play_Track(self, sFilename):
        self.bPlaying = True
        self.MPlayer_Send('loadfile ' + sFilename.replace(' ', '\ '))
        self.iTrackPosition = 0
        self.MPlayer_Send('get_time_pos')
        self.Set_Volume(self.cMain.cMixer.fVolume, bMessage = False)
        #resources.main.getMenu('Panel').addStatusItem('currentTrack', self.mixer.trackInfo['Track'] + ' - ' + self.mixer.trackInfo['Artist'] + ' - ' + self.mixer.trackInfo['Album'], repeat=True, urgent=True)

    def Toggle_Pause(self):
        self.MPlayer_Send('pause')

    def Set_Volume(self, fLevel, bMessage = True):
        self.cMain.Write_Config('volume', fLevel)
        self.MPlayer_Send('volume ' + str(fLevel * 100) + ' 1')
        if bMessage:
            try:
                #resources.main.getMenu('Panel').addStatusItem('setVolume', 'Volume: ' + str(fLevel * 100) + '%', bUrgent = True, iTime = 2500)
                pass
            except:
                pass

    def Hook_MPlayer(self):
        if self.bPlaying:
            f = open(self.sOutput, 'r')
            for line in [i.replace('\n', '').replace('\x00', '') for i in f.readlines()]:
                if line.rfind("ANS_TIME_POSITION=") > -1:
                    iNewPosition = int(line.split("=")[1].split('.')[0])
                    self.iTrackPosition = iNewPosition
            f.close()
            f = open(self.sOutput, 'w')
            f.write('\n')
            f.close()
            self.MPlayer_Send('get_time_pos')
            if self.iTrackPosition + 2 >= int(self.Get_Track_Length()):
                print "Playing next..."
                self.cMain.cMixer.Play_Next_Track()