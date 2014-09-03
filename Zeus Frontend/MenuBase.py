import pyglet

class BASE:

    def Init(self):
        pass

    def Close(self):
        pass

    def Draw(self):
        if self.lblTitle:
            self.lblTitle[0].x = self.Get_X() + self.lblTitle[1]
            self.lblTitle[0].y = self.lblTitle[2]
        for m in self.aMenuButtons:
            m[0].set_position(self.Get_X() + m[1][0], m[1][1])
            if self.Is_Active():
                if self.Clicked():
                    if self.Mouse_Over(sprite = m[0]): m[2]()
        self.Draw_Menu()

    def Draw_Menu(self):
        # Menu's can define this method and have it called on each redraw.
        pass

    def Draw_List(self, x, y, aItems, iLabelIndex, iSelectedIndex, batch, bFade, bAlpha, bSetY = False):
        iSelectedIndex = -1
        x += self.Get_X()
        if self.cMain.cMouse.bDragging:
            if self.Is_Active() and not bFade:
                if self.cMain.cMouse.bDragging == "y":
                    self.dListInfo["Scroll Y"] = min(max(self.dListInfo["Scroll Y"] + int(-self.cMain.cMouse.iDragY / 5), 0), len(aItems) * self.dListInfo["Item Height"] - self.dListInfo["List Height"])
        
        #Instead of Drawing all the items, draw only those that will be displayed.
        if self.cMain.cMouse.bDragging == "y":
            self.dListInfo["Start Index"] = int(self.dListInfo["Scroll Y"] / self.dListInfo["Item Height"])
        self.dListInfo["Background Y Offset"] = self.dListInfo["Scroll Y"]
        if self.dListInfo["Scroll Y"] > self.dListInfo["List Height"]:
            self.dListInfo["Background Y Offset"] = self.dListInfo["Scroll Y"] % self.dListInfo["List Height"]
        self.dSprites["List Background1"].set_position(x, self.dListInfo["Background Y"] + self.dListInfo["Background Y Offset"])
        self.dSprites["List Background2"].set_position(x, self.dListInfo["Background Y"] + self.dListInfo["Background Y Offset"] - self.dListInfo["List Height"])
        for i, aItem in enumerate(aItems):
            if (i >= self.dListInfo["Start Index"] and i <= self.dListInfo["Start Index"] + 9) or bSetY:
                aItem[0].x = x + 5
                if self.cMain.cMouse.bDragging == "y" or self.dListInfo["Start Index"] == 0 or bSetY:
                    #Items that are to be displayed within the window need their coordinates set.
                    aItem[iLabelIndex].y = (y + self.dListInfo["List Height"]) - int(self.dListInfo["Item Height"] * (i + 0.5)) + self.dListInfo["Scroll Y"]
                if self.Clicked() and not bFade:
                    if self.Mouse_Over(label = aItem[0]) and self.Mouse_Over(sprite = self.dSprites['List Background Cover']):
                        iSelectedIndex = i
                if bFade:
                    aItem[0].color = (aItem[0].color[0], aItem[0].color[1], aItem[0].color[2], bAlpha)
            elif (i < self.dListInfo["Start Index"] and i >= (self.dListInfo["Start Index"] - 5)) or (i > self.dListInfo["Start Index"] + 9 and i <= (self.dListInfo["Start Index"] + 13)):
                #Hide the ones that are above and below the drawn ones.
                aItem[0].x = -5000
            elif i > self.dListInfo["Start Index"] + 13:
                #These ones don't even need to be checked.
                break
        pyglet.gl.glScissor(x, y, self.dListInfo["List Width"], self.dListInfo["List Height"])
        pyglet.gl.glEnable(pyglet.gl.GL_SCISSOR_TEST)
        batch.draw()
        pyglet.gl.glDisable(pyglet.gl.GL_SCISSOR_TEST)
        self.dSprites["List Background Cover"].set_position(x - 11, y - 9)
        return iSelectedIndex

    def Clicked(self):
        return self.cMain.cMouse.Clicked

    def Long_Clicked(self):
        return self.cMain.cMouse.LongClick

    def Rapid_Clicked(self):
        if self.cMain.cMouse.bDown:
            return self.cMain.cMouse.cRapidTimer.Expired()
        return False

    def Mouse_Over(self, sprite = None, label = None):
        # Returns true if mouse is over passed object.
        if sprite != None:
            if self.cMain.cMouse.iX >= sprite.x and self.cMain.cMouse.iX < (sprite.x + sprite.width):
                if self.cMain.cMouse.iY >= sprite.y and self.cMain.cMouse.iY < (sprite.y + sprite.height):
                    return True
            return False
        elif label != None:
            iX = label.x
            iY = label.y
            iWidth = [label.content_width, label.width][label.width != None]
            iHeight = [label.content_height, label.height][label.height != None]
            if label.anchor_y == "center":
                iY -= iHeight/2
            if self.cMain.cMouse.iX >= iX and self.cMain.cMouse.iX < (iX + iWidth):
                if self.cMain.cMouse.iY >= iY and self.cMain.cMouse.iY < (iY + iHeight):
                    return True
            return False
        return False

    def Is_Active(self): return (self == self.cMain.Get_Active_Menu() and self.cMain.bMoving == False)

    def Get_X(self):
        x = self.x + self.cMain.aDraw[0] - 1024 * self.cMain.iCurrentIndex
        if self.cMain.cMouse.bDragging == "x":
            x += self.cMain.cMouse.iDragX
        return int(x)

    def Set_X(self):
        self.x = 1024 * self.cMain.Get_Menu_Index(self)

    def Select_Menu(self, sMenuName):
        self.cMain.Queue_Menu(sMenuName)

    def Get_Sprite(self, sFilename, batch = None, width = 0, height = 0, group = None):
        if not batch:
            batch = self.cMain.batch
        imgSprite = pyglet.image.load(sFilename)
        if width == 0 or height == 0:
            #TODO: Fix image sizing.
            #iTempWidth = imgSprite.width
            #iTempHeight = imgSprite.height
            #if width: iTempWidth = width
            #if height: iTempHeight = height
            #imgSprite = pyglet.image.load(sFilename, width = iTempWidth, height = iTempHeight)
            pass
        return pyglet.sprite.Sprite(imgSprite,
                                    x = -5000,
                                    y = -5000,
                                    batch = batch,
                                    group = group)

    def Get_Label(self, sText, x, y, font_size = 36, anchor_x = "center", anchor_y = "center", color = (255, 255, 255, 255), bold = False, batch = None, width = None, height = None):
        if not batch:
            batch = self.cMain.batch
        return pyglet.text.Label(sText,
                                 font_name = 'DejaVu Sans',
                                 font_size = font_size,
                                 x = x,
                                 y = y,
                                 width = width,
                                 height = height,
                                 anchor_x = anchor_x,
                                 anchor_y = anchor_y,
                                 color = color,
                                 batch = batch,
                                 bold = bold)

    def Crop_Image(self, img, x, y, width, height, iGroupIndex = 0):
        return img.get_region(x, y, width, height)
        return pyglet.sprite.Sprite(img.get_region(x, y, width, height),
                                    x = -5000,
                                    y = -5000,
                                    batch = self.cMain.batch,
                                    group = [None, self.cMain.aGroups[iGroupIndex]][iGroupIndex > 0])