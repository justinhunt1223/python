import pyglet
import MenuBase

class STATUS_ITEM:

    def __init__(self, lblText, bRepeat, bUrgent, iDelay):
        self.lblText = lblText
        self.bRepeat = bRepeat
        self.bUrgent = bUrgent
        self.iDelay = iDelay
        self.bUp = False
        self.bDown = False

    def Roll_Up(self):
        if self.lblText.y < 0:
            self.lblText.y += 2
            if self.lblText.y > 0:
                self.lblText.y = 0
            else:
                return False
        if self.lblText.y == 0:
            self.bUp = True
            return True

    def Roll_Down(self):
        if self.lblText.y > -40:
            self.lblText.y -= 2
            if self.lblText.y < -40:
                self.lblText.y = -40
            else:
                return False
        if self.lblText.y == -40:
            self.bDown = True
            return True

class STATUS_BAR(MenuBase.BASE):

    def __init__(self, cMain):
        self.cMain = cMain
        self.aItems = []
        self.cCurrent = None
        self.cTarget = None
        self.iDelay = 0
        self.cDelay = cMain.Timer(0)
        self.Add_Item("TESTING 123", True, False)

    def Add_Item(self, sText, bRepeat, bUrgent = False, iDelay = 3000):
        if bUrgent:
            #Urgent items can't repeat, it messes with the rotation.
            bRepeat = False
        cStatusItem = STATUS_ITEM(self.Get_Label(sText, 6, -40, font_size = 28, anchor_x = "left", anchor_y = "bottom", batch = self.cMain.batch, color = (143, 249, 255, 255), bold = True), bRepeat, bUrgent, iDelay)
        #Insert the new item at the correct position.
        if bUrgent:
            self.aItems.insert(0, cStatusItem)
        else:
            self.aItems.append(cStatusItem)
        #
        if bUrgent or len(self.aItems) == 1:
            self.cTarget = cStatusItem
            if len(self.aItems) == 1:
                #The first item needs to be shown.
                cStatusItem.Roll_Up()
        return cStatusItem

    def Draw(self):
        if self.cTarget != self.cCurrent:
            if self.cCurrent:
                if self.cCurrent.Roll_Down() == True:
                    self.cTarget = self.cCurrent
                    self.cCurrent = None
            elif self.cTarget:
                if self.cTarget.Roll_Up() == True:
                    self.cCurrent = self.cTarget
                    self.iDelay = self.cMain.iTick + self.cCurrent.iDelay
                    self.cTarget = None