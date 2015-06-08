import pyglet
import MenuBase

class StatusBarItem:

    def __init__(self, lblText, bRepeat, bUrgent, iDelay):
        self.lblText = lblText
        self.bRepeat = bRepeat
        self.bUrgent = bUrgent
        self.iDelay = iDelay

    def RollUp(self):
        if self.lblText.y < 0:
            self.lblText.y += 3
            if self.lblText.y > 0:
                self.lblText.y = 0
            else:
                return False
        if self.lblText.y == 0:
            return True

    def RollDown(self):
        if self.lblText.y > -40:
            self.lblText.y -= 3
            if self.lblText.y < -40:
                self.lblText.y = -40
            else:
                return False
        if self.lblText.y == -40:
            return True

    def Text(self, sText = None):
        if sText == None:
            return self.lblText.text
        else:
            try:
                sText = sText.decode("latin-1")
            except:
                pass
            self.lblText.text = sText

class StatusBar(MenuBase.Base):

    def __init__(self, cMain):
        self.cMain = cMain
        self.aItems = []
        self.aUrgent = []
        self.cCurrent = None
        self.cTarget = None
        self.cTimer = cMain.Timer(0)

    def AddItem(self, sText, bRepeat, bUrgent = False, iDelay = 3):
        if bUrgent:
            #Urgent items can't repeat, it messes with the rotation.
            bRepeat = False
        cStatusItem = StatusBarItem(self.GetLabel(sText, 6, -40, font_size = 28, anchor_x = "left", anchor_y = "bottom", batch = self.cMain.batch, color = (143, 249, 255, 255), bold = True), bRepeat, bUrgent, iDelay)
        #Insert the new item at the correct position.
        if bUrgent:
            self.aUrgent.append(cStatusItem)
            self.cTimer.Clear()
        else:
            self.aItems.append(cStatusItem)
            if len(self.aItems) == 1:
                self.cTarget = cStatusItem
        return cStatusItem

    def RemoveItem(self, cStatusItem):
        if cStatusItem in self.aItems:
            try:
                self.aItems.remove(cStatusItem)
            except:
                pass
        elif cStatusItem in self.aUrgent:
            try:
                self.aUrgent.remove(cStatusItem)
            except:
                pass

    def Draw(self):
        if self.cTarget:
            if self.cCurrent and self.cTimer.Expired() and (len(self.aItems) > 1 or len(self.aUrgent) > 0):
                if self.cCurrent.RollDown() == True:
                    if self.cCurrent.bRepeat == False or self.cCurrent.bUrgent:
                        self.RemoveItem(self.cCurrent)
                        if self.cTarget == self.cCurrent:
                            #TODO: Not sure why this needs to be here. Otherwise, urgent messages display twice.
                            self.cTarget = None
                    self.cCurrent = None
            elif self.cTarget.RollUp():
                self.cCurrent = self.cTarget
                self.cTimer = self.cMain.Timer(self.cCurrent.iDelay)
                self.cTarget = None
        elif self.cTimer.Expired():
            if len(self.aUrgent) == 0:
                if len(self.aItems) > 1:
                    if self.cCurrent in self.aItems:
                        iIndex = self.aItems.index(self.cCurrent) + 1
                        if iIndex > (len(self.aItems) - 1):
                            iIndex = 0
                    else:
                        iIndex = 0
                    self.cTarget = self.aItems[iIndex]
                elif len(self.aItems) == 1:
                    self.cTarget = self.aItems[0]
                elif len(self.aItems) == 0:
                    self.cTimer = self.cMain.Timer(10)
            else:
                self.cTarget = self.aUrgent[0]