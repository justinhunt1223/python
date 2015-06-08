#!/usr/bin/python

import pyglet
from pyglet import clock

from pyglet.gl import *
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_BLEND)

import MenuMain
import MenuMusic
import MenuMusicLibrary
import MusicLibrary
import MySQL
import Renderer
import Mixer
import StatusBar

import datetime
import time

window = pyglet.window.Window(1024, 768)
#window.set_fullscreen()

class Timer:

    def __init__(self, iDelay, cMain):
        self.cMain = cMain
        self.iDelay = iDelay
        self.fExpire = self.cMain.fSecond + self.iDelay

    def Expired(self):
        return self.fExpire <= self.cMain.fSecond

    def Clear(self):
        self.fExpire = 0

    def Reset(self):
        self.fExpire = self.cMain.fSecond + self.iDelay

class Mouse:

    def __init__(self):
        self.cMain = None
        self.iDragX = -1
        self.iDragY = -1
        self.iX = -1
        self.iY = -1
        self.Clicked = False
        self.LongClick = False
        self.bCanClick = True
        self.bDragging = False
        self.cLongClickTimer = None
        self.cRapidTimer = None
        self.bDown = False

    def ResetLongClickTimer(self):
        # 1 second long-press
        if self.cLongClickTimer == None:
            self.cLongClickTimer = Timer(1, self.cMain)
        else:
            self.cLongClickTimer.Reset()

    def ResetRapidTimer(self):
        # 1 second long-press
        if self.cRapidTimer == None:
            self.cRapidTimer = Timer(0.1, self.cMain)
        else:
            self.cRapidTimer.Reset()

class Main:

    def __init__(self, cMouse):
        self.batch = pyglet.graphics.Batch()
        self.clock = clock.Clock()
        self.fSecond = 0
        self.window = window
        self.cMouse = cMouse
        cMouse.cMain = self
        cMouse.ResetLongClickTimer()
        cMouse.ResetRapidTimer()
        self.cMySQL = MySQL.MySql()
        self.cScanMusic = MusicLibrary.ScanMusic(self)
        self.cMusicLibrary = MusicLibrary.MusicLibrary(self)
        self.cRenderer = Renderer.Renderer(self)
        self.cMixer = Mixer.Mixer(self)
        self.cStatusBar = StatusBar.StatusBar(self)
        self.imgBackground = pyglet.resource.image("images/background.png")
        self.aDraw = [0, 0.0] #x, dx
        self.fDragSpeedX = 0.0
        self.fDragSpeedY = 0.0
        self.iMoveSpeed = lambda: 3.8
        self.bMoving = False
        self.dMenus = {'Main': MenuMain.Menu(self),
                       'Music': MenuMusic.Menu(self),
                       'Music Library': MenuMusicLibrary.Menu(self)}
        self.aMenuQueue = []
        self.iCurrentIndex = -1
        self.iTargetIndex = -1
        for m in self.dMenus.values():
            m.Init()
        self.cMouse.bDragging = 'y'
        for sName in self.GetConfig('menus', 'Main').split(','):
            self.QueueMenu(sName)
            self.aMenuQueue[self.iTargetIndex].Draw()
            self.iCurrentIndex = self.iTargetIndex
        self.cMenuBase = self.aMenuQueue[0]
        self.aPanelButtons = [[self.cMenuBase.GetSprite('images/panel/power.png'), (25, 62), self.PanelQuit, lambda: None],
                              [self.cMenuBase.GetSprite('images/panel/back.png'), (90, 62), self.PanelHome, lambda: None],
                              [self.cMenuBase.GetSprite('images/panel/wifi.png'), (155, 62), self.PanelWiFi, lambda: None],
                              [self.cMenuBase.GetSprite('images/panel/media-play.png'), (625, 35), self.PanelPause, lambda: None],
                              [self.cMenuBase.GetSprite('images/panel/media-next.png'), (750, 35), self.PanelNext, lambda: None],
                              [self.cMenuBase.GetSprite('images/panel/media-prev.png'), (515, 35), self.PanelPrevious, lambda: None],
                              [self.cMenuBase.GetSprite('images/panel/volume-up.png'), (886, 74), lambda: None, self.PanelVolumeUp],
                              [self.cMenuBase.GetSprite('images/panel/volume-down.png'), (948, 74), lambda: None, self.PanelVolumeDown]]
        
        # Date/Time is refreshed once a second.
        self.lblTime = self.cMenuBase.GetLabel("", 220, 81, font_size = 22, anchor_x = "left", anchor_y = "bottom", bold = True, color = (143, 249, 255, 255))
        self.lblDate = self.cMenuBase.GetLabel("", 220, 52, font_size = 22, anchor_x = "left", anchor_y = "bottom", bold = True, color = (143, 249, 255, 255))
        self.UpdateDateTime()
        pyglet.clock.schedule_interval(lambda e: self.UpdateDateTime(), 1)
        
        for btnPanel in self.aPanelButtons:
            btnPanel[0].set_position(btnPanel[1][0], btnPanel[1][1])
        self.fps = pyglet.clock.ClockDisplay()
        
        self.cMixer.PlayTrack(self.cMixer.plCurrentPlaylist.GetCurrentTrack())
        self.cRenderer.Seek(float(self.GetConfig('trackPosition', '0.0')) * 1.0)
        if self.cMixer.bPaused:
            self.cRenderer.TogglePause()

    def UpdateDateTime(self):
        self.lblTime.text = time.strftime("%H:%M:%S")
        self.lblDate.text = datetime.date.today().strftime("%d %B")

    def Timer(self, iDelay): return Timer(iDelay, self)

    def Save(self):
        sMenus = ''
        for m in self.aMenuQueue:
            for sName, mMenu in self.dMenus.iteritems():
                if m == mMenu:
                    sMenus += sName + ','
        sMenus = sMenus.rstrip(',')
        self.WriteConfig('menus', sMenus)
        self.WriteConfig('menuCount', self.iCurrentIndex)

    def PanelQuit(self):
        pass

    def PanelHome(self):
        pass

    def PanelWiFi(self):
        pass

    def PanelPause(self):
        self.cMixer.TogglePause()

    def PanelNext(self):
        self.cMixer.PlayNextTrack()

    def PanelPrevious(self):
        self.cMixer.PlayPreviousTrack()

    def PanelVolumeUp(self):
        self.cMixer.VolumeUp(0.01)

    def PanelVolumeDown(self):
        self.cMixer.VolumeDown(0.01)

    def WriteConfig(self, sEntry, sData):
        if len(self.cMySQL.RunQuery("SELECT * FROM Config WHERE Entry = %s;", (sEntry))) == 0:
            #Entry doesn't exist, so make it.
            self.cMySQL.RunQuery("INSERT INTO Config (Entry, Data) VALUES(%s, %s);", (sEntry, sData))
        else:
            self.cMySQL.RunQuery("UPDATE Config SET Data = %s WHERE Entry = %s;", (sData, sEntry))

    def GetConfig(self, sEntry, sDefault = ''):
        qConfig = self.cMySQL.RunQuery("SELECT * FROM Config WHERE Entry = %s;", (sEntry))
        if qConfig:
            return qConfig[0]['Data']
        self.WriteConfig(sEntry, sDefault)
        return self.GetConfig(sEntry)

    def GetActiveMenu(self):
        return self.aMenuQueue[self.iCurrentIndex]

    def GetMenuIndex(self, cMenu):
        return self.aMenuQueue.index(cMenu)

    def GetMenu(self, sMenuName):
        return self.dMenus[sMenuName]

    def QueueMenu(self, sMenuName):
        if self.dMenus.has_key(sMenuName):
            self.aMenuQueue.append(self.dMenus[sMenuName])
            self.dMenus[sMenuName].SetX()
            self.iTargetIndex += 1

    def UnqueueMenu(self):
        self.aMenuQueue[len(self.aMenuQueue) - 1].Destroy()
        self.aMenuQueue.pop(len(self.aMenuQueue) - 1)

    def Draw(self):
        self.imgBackground.blit(0, 0)
        self.batch.draw()
        for m in self.aMenuQueue: m.Draw()
        # Menu changes
        if self.iTargetIndex != self.iCurrentIndex:
            self.bMoving = True
            if self.iTargetIndex > self.iCurrentIndex:
                self.aDraw[0] -= self.aDraw[1]
                self.aDraw[1] += self.iMoveSpeed()
                if self.aDraw[0] < -1024:
                    self.bMoving = False
                    self.aDraw[0] = 0
                    self.aDraw[1] = 0
                    self.iCurrentIndex += 1
                    self.Save()
            else:
                self.aDraw[0] += self.aDraw[1]
                self.aDraw[1] += self.iMoveSpeed()
                if self.aDraw[0] > 1024:
                    self.bMoving = False
                    self.aDraw[0] = 0
                    self.aDraw[1] = 0
                    self.iCurrentIndex -= 1
                    self.UnqueueMenu()
                    self.Save()
        elif self.aDraw[0] != 0:
            if self.aDraw[0] > 0:
                self.aDraw[1] += self.iMoveSpeed()
                self.aDraw[0] = max(0, self.aDraw[0] - self.aDraw[1])
            else:
                self.aDraw[1] += self.iMoveSpeed()
                self.aDraw[0] = min(0, self.aDraw[0] + self.aDraw[1])
            if self.aDraw[0] == 0:
                self.aDraw[1] = 0.0
        for btnPanel in self.aPanelButtons:
            if self.cMenuBase.Clicked():
                if self.cMenuBase.MouseOver(sprite = btnPanel[0]): btnPanel[2]()
            if self.cMenuBase.RapidClicked():
                if self.cMenuBase.MouseOver(sprite = btnPanel[0]): btnPanel[3]()
        self.cStatusBar.Draw()
        #self.fps.draw()

cMouse = Mouse()
cMain = Main(cMouse)

@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if cMain.bMoving == False:
        
        cMouse.iX = x
        cMouse.iDragX += dx
        cMain.fDragSpeedX = (cMain.fDragSpeedX + dx) / 2
        
        cMouse.iY = y
        cMouse.iDragY += dy
        cMain.fDragSpeedY = (cMain.fDragSpeedY + dy) / 2
        
        if (abs(cMouse.iDragY) < 45 and abs(cMouse.iDragX) >= 45 and cMouse.bDragging != "y") or cMouse.bDragging == "x":
            cMouse.iDragY = 0
            cMain.fDragSpeedY = 0
            if cMouse.bDragging != "x":
                cMouse.bDragging = "x"
                cMouse.iDragX = 0
        if (abs(cMouse.iDragX) < 45 and abs(cMouse.iDragY) >= 45 and cMouse.bDragging != "x") or cMouse.bDragging == "y":
            cMouse.iDragX = 0
            cMain.fDragSpeedX = 0
            if cMouse.bDragging != "y":
                cMouse.bDragging = "y"
                cMouse.iDragY = 0
            
        # To separate a drag from a click, disallow clicks if the mouse has been
        # drug more than 15 pixels in any direction
        if abs(cMouse.iDragX) > 15 or abs(cMouse.iDragY) > 15:# or cMouse.iDragX < -15 or cMouse.iDragY < -15:
            cMouse.bCanClick = False

@window.event
def on_mouse_press(x, y, button, modifiers):
    if cMain.bMoving == False:
        cMouse.iX = x
        cMouse.iY = y
        cMouse.Clicked = False
        cMouse.LongClick = False
        cMouse.bCanClick = True
        cMouse.bDown = True
        # Set bDragging to True since we don't know what direction the drag is going to be
        # and some functions need to know if dragging is taking place.
        cMouse.bDragging = True
        cMouse.iDragX = 0
        cMouse.iDragY = 0
        cMain.fDragSpeedX = 0.0
        cMain.fDragSpeedY = 0.0
        cMouse.ResetLongClickTimer()

@window.event
def on_mouse_release(x, y, button, modifiers):
    if cMain.bMoving == False:
        cMouse.iX = x
        cMouse.iY = y
        
        # Monitor mouse drag.
        if abs(cMouse.iDragX) >= 350 and cMouse.bDragging != "y":
            if cMouse.iDragX > 0:
                cMain.iTargetIndex = max(0, cMain.iTargetIndex - 1)
        cMain.aDraw[0] = cMouse.iDragX
        cMain.aDraw[1] = cMain.fDragSpeedX
    
        if cMouse.bCanClick:
            cMouse.Clicked = True
        cMouse.iDragX = 0
        cMouse.iDragY = 0
        cMouse.bDragging = False
        cMouse.bDown = False
        cMouse.LongClick = False

def draw(dt):
    window.Clear()
    cMain.Draw()
    # To capture a mouse click, a few flags are used.
    if cMouse.bCanClick:
        if cMouse.bDown:
            if cMouse.cLongClickTimer.Expired():
                # Mouse was long clicked.
                cMouse.LongClick = True
                cMouse.cLongClickTimer.Reset()
            if cMouse.cRapidTimer.Expired():
                cMouse.cRapidTimer.Reset()
        if cMouse.Clicked:
            cMouse.Clicked = False
            cMouse.bCanClick = False
    cMain.fSecond += cMain.clock.tick()

pyglet.clock.schedule_interval(draw, 1/60.0)
pyglet.app.run()
