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

class TIMER:

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

class MOUSE:

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

    def Reset_Long_Click_Timer(self):
        # 1 second long-press
        if self.cLongClickTimer == None:
            self.cLongClickTimer = TIMER(1, self.cMain)
        else:
            self.cLongClickTimer.Reset()

    def Reset_Rapid_Timer(self):
        # 1 second long-press
        if self.cRapidTimer == None:
            self.cRapidTimer = TIMER(0.1, self.cMain)
        else:
            self.cRapidTimer.Reset()

class MAIN:

    def __init__(self, cMouse):
        self.batch = pyglet.graphics.Batch()
        self.clock = clock.Clock()
        self.fSecond = 0
        self.window = window
        self.cMouse = cMouse
        cMouse.cMain = self
        cMouse.Reset_Long_Click_Timer()
        cMouse.Reset_Rapid_Timer()
        self.cMySQL = MySQL.MYSQL()
        self.cScanMusic = MusicLibrary.SCAN_MUSIC(self)
        self.cMusicLibrary = MusicLibrary.MUSIC_LIBRARY(self)
        self.cRenderer = Renderer.RENDERER(self)
        self.cMixer = Mixer.MIXER(self)
        self.cStatusBar = StatusBar.STATUS_BAR(self)
        self.imgBackground = pyglet.resource.image("images/background.png")
        self.aDraw = [0, 0.0] #x, dx
        self.fDragSpeedX = 0.0
        self.fDragSpeedY = 0.0
        self.iMoveSpeed = lambda: 3.8
        self.bMoving = False
        self.dMenus = {'Main': MenuMain.MENU(self),
                       'Music': MenuMusic.MENU(self),
                       'Music Library': MenuMusicLibrary.MENU(self)}
        self.aMenuQueue = []
        self.iCurrentIndex = -1
        self.iTargetIndex = -1
        for m in self.dMenus.values():
            m.Init()
        self.cMouse.bDragging = 'y'
        for sName in self.Get_Config('menus', 'Main').split(','):
            self.Queue_Menu(sName)
            self.aMenuQueue[self.iTargetIndex].Draw()
            self.iCurrentIndex = self.iTargetIndex
        self.cMenuBase = self.aMenuQueue[0]
        self.aPanelButtons = [[self.cMenuBase.Get_Sprite('images/panel/power.png'), (25, 62), self.Panel_Quit, lambda: None],
                              [self.cMenuBase.Get_Sprite('images/panel/back.png'), (90, 62), self.Panel_Home, lambda: None],
                              [self.cMenuBase.Get_Sprite('images/panel/wifi.png'), (155, 62), self.Panel_WiFi, lambda: None],
                              [self.cMenuBase.Get_Sprite('images/panel/media-play.png'), (625, 35), self.Panel_Pause, lambda: None],
                              [self.cMenuBase.Get_Sprite('images/panel/media-next.png'), (750, 35), self.Panel_Next, lambda: None],
                              [self.cMenuBase.Get_Sprite('images/panel/media-prev.png'), (515, 35), self.Panel_Previous, lambda: None],
                              [self.cMenuBase.Get_Sprite('images/panel/volume-up.png'), (886, 74), lambda: None, self.Panel_Volume_Up],
                              [self.cMenuBase.Get_Sprite('images/panel/volume-down.png'), (948, 74), lambda: None, self.Panel_Volume_Down]]
        
        # Date/Time is refreshed once a second.
        self.lblTime = self.cMenuBase.Get_Label("", 220, 81, font_size = 22, anchor_x = "left", anchor_y = "bottom", bold = True, color = (143, 249, 255, 255))
        self.lblDate = self.cMenuBase.Get_Label("", 220, 52, font_size = 22, anchor_x = "left", anchor_y = "bottom", bold = True, color = (143, 249, 255, 255))
        self.Update_Date_Time()
        pyglet.clock.schedule_interval(lambda e: self.Update_Date_Time(), 1)
        
        for btnPanel in self.aPanelButtons:
            btnPanel[0].set_position(btnPanel[1][0], btnPanel[1][1])
        self.fps = pyglet.clock.ClockDisplay()
        
        self.cMixer.Play_Track(self.cMixer.plCurrentPlaylist.Get_Current_Track())
        self.cRenderer.Seek(float(self.Get_Config('trackPosition', '0.0')) * 1.0)
        if self.cMixer.bPaused:
            self.cRenderer.Toggle_Pause()

    def Update_Date_Time(self):
        self.lblTime.text = time.strftime("%H:%M:%S")
        self.lblDate.text = datetime.date.today().strftime("%d %B")

    def Timer(self, iDelay): return TIMER(iDelay, self)

    def Save(self):
        sMenus = ''
        for m in self.aMenuQueue:
            for sName, mMenu in self.dMenus.iteritems():
                if m == mMenu:
                    sMenus += sName + ','
        sMenus = sMenus.rstrip(',')
        self.Write_Config('menus', sMenus)
        self.Write_Config('menuCount', self.iCurrentIndex)

    def Panel_Quit(self):
        pass

    def Panel_Home(self):
        pass

    def Panel_WiFi(self):
        pass

    def Panel_Pause(self):
        self.cMixer.Toggle_Pause()

    def Panel_Next(self):
        self.cMixer.Play_Next_Track()

    def Panel_Previous(self):
        self.cMixer.Play_Previous_Track()

    def Panel_Volume_Up(self):
        self.cMixer.Volume_Up(0.01)

    def Panel_Volume_Down(self):
        self.cMixer.Volume_Down(0.01)

    def Write_Config(self, sEntry, sData):
        if len(self.cMySQL.Run_Query("SELECT * FROM Config WHERE Entry = %s;", (sEntry))) == 0:
            #Entry doesn't exist, so make it.
            self.cMySQL.Run_Query("INSERT INTO Config (Entry, Data) VALUES(%s, %s);", (sEntry, sData))
        else:
            self.cMySQL.Run_Query("UPDATE Config SET Data = %s WHERE Entry = %s;", (sData, sEntry))

    def Get_Config(self, sEntry, sDefault = ''):
        qConfig = self.cMySQL.Run_Query("SELECT * FROM Config WHERE Entry = %s;", (sEntry))
        if qConfig:
            return qConfig[0]['Data']
        self.Write_Config(sEntry, sDefault)
        return self.Get_Config(sEntry)

    def Get_Active_Menu(self):
        return self.aMenuQueue[self.iCurrentIndex]

    def Get_Menu_Index(self, cMenu):
        return self.aMenuQueue.index(cMenu)

    def Get_Menu(self, sMenuName):
        return self.dMenus[sMenuName]

    def Queue_Menu(self, sMenuName):
        if self.dMenus.has_key(sMenuName):
            self.aMenuQueue.append(self.dMenus[sMenuName])
            self.dMenus[sMenuName].Set_X()
            self.iTargetIndex += 1

    def Unqueue_Menu(self):
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
                    self.Unqueue_Menu()
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
                if self.cMenuBase.Mouse_Over(sprite = btnPanel[0]): btnPanel[2]()
            if self.cMenuBase.Rapid_Clicked():
                if self.cMenuBase.Mouse_Over(sprite = btnPanel[0]): btnPanel[3]()
        self.cStatusBar.Draw()
        #self.fps.draw()

cMouse = MOUSE()
cMain = MAIN(cMouse)

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
        cMouse.Reset_Long_Click_Timer()

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
    window.clear()
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
