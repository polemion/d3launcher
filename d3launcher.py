# -*- coding: utf-8 -*-

# d3Launcher, a Doom3/dhewm3 Launcher
# Copyright (C) <2021~>  <Dimitrios Koukas>

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

# 'Background on panel' (modified) code snippet credits:
# https://www.blog.pythonlibrary.org/2010/03/18/wxpython-putting-a-background-image-on-a-panel/

# Main

import wx, os, subprocess, shutil, _pickle as cPickle, locale, wx.adv as adv
import lib.singletons as singletons, lib.images as images
import wx.lib.agw.gradientbutton as GB
from lib.conf import APPNAME, APPDIR, APPVER, DPOS, DSIZE, SPC, conf, cache, defs, creds


def CreateBitmap(imgName):
    """Return embeded image."""
    return images.catalog[imgName].Bitmap


def setIcon(parent, image=None):
    """Set icon of caller window."""
    appICO = wx.Icon()
    try:
        if image is None: image = CreateBitmap('appICO')
        appICO.CopyFromBitmap(image)
    except:  # If for a reason the image is missing.
        return wx.NullBitmap
    parent.SetIcon(appICO)


class confLib:
    """Settings storage."""

    def __init__(self):
        """Init."""
        confFile = '%s.pkl' % APPNAME
        self.confFile = os.path.join(APPDIR, confFile)

    def bckConf(self):
        """Backup configuration file."""
        shutil.copyfile(self.confFile, self.confFile+'.bck')

    def restoreBck(self):
        """Restore backup configuration file."""
        if os.path.isfile(self.confFile+'.bck'):  # Try to restore backup conf
            if os.path.isfile(self.confFile): os.remove(self.confFile)
            shutil.copyfile(self.confFile+'.bck', self.confFile)
            try:
                self.fRestore()
                return
            except: pass

    def store(self):
        """Save altered settings."""
        with open(self.confFile, 'wb') as out:
            cPickle.dump(conf, out)

    def fRestore(self):
        """Parse saved settings."""
        with open(self.confFile, 'rb') as inp:
            self.raw = cPickle.load(inp)
        # Apply settings
        for x in self.raw:
            conf[x] = self.raw[x]
        # Backup conf
        self.bckConf()

    def restore(self):
        """Restore saved settings."""
        try: self.fRestore()
        except: pass


class confDialog(wx.Dialog):
    """Settings dialog."""

    def __init__(self, parent, title='Exclusions', style=wx.CAPTION|wx.CLOSE_BOX|wx.STAY_ON_TOP|wx.SYSTEM_MENU):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=DPOS, size=(-1, -1), style=style)
        self.SetSizeHints(wx.Size(257, 354), DSIZE)
        setIcon(self)
        self.timer = wx.Timer()
        # Content
        self.exclList = wx.CheckListBox(self, wx.ID_ANY,
            DPOS, (220, 340), conf['launch.exclusions'], wx.LB_EXTENDED|wx.LB_NEEDED_SB|wx.LB_SORT|wx.NO_BORDER)
        self.resBtn = GB.GradientButton(self, wx.ID_OK, None, 'Restore Selected Items', size=(130, 20))
        self.cnlBtn = GB.GradientButton(self, wx.ID_CANCEL, None, 'Cancel', size=(65, 20))
        # Theming
        self.SetForegroundColour(wx.Colour(240, 240, 240))
        self.SetBackgroundColour(wx.Colour(64, 64, 64))
        # Layout
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.AddMany([(self.resBtn, 0, 0, 5), SPC, (self.cnlBtn, 0, 0, 5)])
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.AddMany([(self.exclList, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT, 5), (btnSizer, 0, wx.EXPAND|wx.ALL, 5)])
        self.SetSizer(mainSizer)
        self.Layout()
        mainSizer.Fit(self)
        self.Centre(wx.BOTH)
        # Events
        self.timer.Bind(wx.EVT_TIMER, self.onUpdate)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.timer.Start(50)
        self.resBtn.Bind(wx.EVT_BUTTON, self.onRestore)
        self.cnlBtn.Bind(wx.EVT_BUTTON, self.onClose)

    def onUpdate(self, event):
        """Timed events."""
        if not self.exclList.GetCheckedStrings():
            if self.resBtn.IsShown(): self.resBtn.Hide()
        else:
            if not self.resBtn.IsShown(): self.resBtn.Show()

    def onRestore(self, event):
        """On restoring excluded items."""
        conf['launch.exclusions'] = [x for x in conf['launch.exclusions'] if x not in self.exclList.GetCheckedStrings()]
        singletons.confLib.store()
        self.onClose()

    def onClose(self, event=None):
        """Exit actions."""
        self.timer.Stop()
        self.Hide()
        self.Destroy()


class addDialog(wx.Dialog):
    """New launcher dialog."""

    def __init__(self, parent, title='Add Custom Launcher', edit=None, style=wx.CAPTION|wx.CLOSE_BOX|wx.MAXIMIZE_BOX|wx.STAY_ON_TOP|wx.SYSTEM_MENU):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=DPOS, size=(-1, -1), style=style)
        self.SetSizeHints(wx.Size(460, 550), DSIZE)
        setIcon(self)
        self.timer = wx.Timer()
        # Content
        sampleBox = wx.StaticBox(self, wx.ID_ANY, 'Existing Launchers (feel free to copy):')
        titleBox = wx.StaticBox(self, wx.ID_ANY, 'Title:')
        cmdBox = wx.StaticBox(self, wx.ID_ANY, 'Command (for multiple commands, separate with a new line):')
        self.sample = wx.TextCtrl(sampleBox, wx.ID_ANY, '', DPOS, DSIZE, wx.TE_DONTWRAP|wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)
        self.setSample()
        self.title = wx.TextCtrl(titleBox, wx.ID_ANY, '', DPOS, DSIZE, 0|wx.NO_BORDER)
        self.cmds = wx.TextCtrl(cmdBox, wx.ID_ANY, '', DPOS, DSIZE, wx.TE_DONTWRAP|wx.TE_MULTILINE|wx.NO_BORDER)
        self.chkEdit(edit)
        self.addBtn = GB.GradientButton(self, wx.ID_OK, None, 'Add Custom Launcher', size=(125, 20))
        self.cnlBtn = GB.GradientButton(self, wx.ID_OK, None, 'Cancel', size=(65, 20))
        # Theming
        [x.SetForegroundColour(wx.Colour(220, 220, 220)) for x in (sampleBox, titleBox, cmdBox)]
        self.SetForegroundColour(wx.Colour(240, 240, 240))
        self.SetBackgroundColour(wx.Colour(64, 64, 64))
        self.sample.SetBackgroundColour(wx.Colour(140, 140, 140))
        [x.SetForegroundColour(wx.Colour(255, 255, 255)) for x in (self.title, self.cmds)]
        [x.SetBackgroundColour(wx.Colour(48, 48, 48)) for x in (self.title, self.cmds)]
        # Layout
        self.cmds.SetMinSize(wx.Size(-1, 60))
        self.sample.SetMinSize(wx.Size(650, 300))
        sampleSizer = wx.StaticBoxSizer(sampleBox, wx.VERTICAL)
        sampleSizer.Add(self.sample, 1, wx.EXPAND, 5)
        titleSizer = wx.StaticBoxSizer(titleBox, wx.VERTICAL)
        titleSizer.Add(self.title, 0, wx.EXPAND, 5)
        cmdSizer = wx.StaticBoxSizer(cmdBox, wx.VERTICAL)
        cmdSizer.Add(self.cmds, 0, wx.EXPAND, 5)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.AddMany([(self.addBtn, 0, 0, 5), SPC, (self.cnlBtn, 0, 0, 5)])
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.AddMany([(sampleSizer, 1, wx.EXPAND|wx.ALL, 5), (titleSizer, 0, wx.ALL|wx.EXPAND, 5),
            (cmdSizer, 0, wx.EXPAND|wx.ALL, 5), (btnSizer, 0, wx.EXPAND|wx.ALL, 5)])
        self.SetSizer(mainSizer)
        self.Layout()
        mainSizer.Fit(self)
        self.Centre(wx.BOTH)
        # Events
        self.timer.Bind(wx.EVT_TIMER, self.onUpdate)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.timer.Start(50)
        self.addBtn.Bind(wx.EVT_BUTTON, self.onCustom)
        self.cnlBtn.Bind(wx.EVT_BUTTON, self.onClose)

    def onUpdate(self, event):
        """Timed events."""
        if not self.title.GetValue().strip():
            if self.addBtn.IsShown(): self.addBtn.Hide()
        else:
            if not self.addBtn.IsShown(): self.addBtn.Show()
        if '%s%s' % (defs['list.spc'], self.title.GetValue().strip()) in cache['launchers.full'
            ] or '%s%s' % (defs['list.spc'], self.title.GetValue().strip()) in conf['custom.launchers']:
            if self.addBtn.GetLabel() == 'Add Custom Launcher':
                self.addBtn.SetLabel('Update Launcher')
                self.addBtn.Refresh()
        else:
            if self.addBtn.GetLabel() == 'Update Launcher':
                self.addBtn.SetLabel('Add Custom Launcher')
                self.addBtn.Refresh()

    def chkEdit(self, edit):
        """On editing fill the required fields."""
        if edit is not None:
            self.title.SetValue(edit[0])
            self.cmds.SetValue('\n'.join(edit[1]))

    def setSample(self):
        """Construct Custom Launcher's texts."""
        self.sample.SetValue('\n'.join(['%s\n%s\n' %
            (x, '\n'.join(cache['launchers.full'][x])) for x in cache['launchers.full']]))

    def onCustom(self, event):
        """On adding custom items."""
        title = '%s%s' % (defs['list.spc'], self.title.GetValue().strip())
        cmdRaw = [x for x in self.cmds.GetValue().strip().split('\n') if x]
        conf['custom.launchers'].update({title: cmdRaw})
        singletons.confLib.store()
        self.onClose()

    def onClose(self, event=None):
        """Exit actions."""
        self.timer.Stop()
        self.Hide()
        self.Destroy()


class ErrDialog(wx.Dialog):
    """Show a themed error dialog."""

    def __init__(self, parent, title, head, msg, style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=DPOS, size=(540, 220), style=style)
        setIcon(self)
        self.SetSizeHints(DSIZE, DSIZE)
        # Layout
        self.panel = wx.Panel(self, wx.ID_ANY, DPOS, DSIZE, wx.TAB_TRAVERSAL)
        self.sign = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MESSAGE_BOX), DPOS, DSIZE, 0)
        self.headTxt = wx.StaticText(self.panel, wx.ID_ANY, head, DPOS, DSIZE, 0)
        self.mainTxt = wx.StaticText(self.panel, wx.ID_ANY, msg, DPOS, DSIZE, 0)
        self.exitBtn = GB.GradientButton(self, wx.ID_EXIT, None, 'Exit d3launcher')
        # Theming
        font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, '')
        self.headTxt.SetFont(font)
        self.SetBackgroundColour(wx.Colour(64, 64, 64))
        [x.SetBackgroundColour(wx.Colour(80, 80, 80)) for x in (self.sign, self.panel)]
        self.headTxt.SetForegroundColour(wx.Colour(224, 224, 224))
        self.mainTxt.SetForegroundColour(wx.Colour(240, 240, 240))
        # Layout
        [x.Wrap(-1) for x in (self.mainTxt, self.headTxt)]
        txtSizer = wx.BoxSizer(wx.VERTICAL)
        txtSizer.AddMany([(self.headTxt, 1, wx.EXPAND|wx.ALL, 5), (self.mainTxt, 1, wx.EXPAND|wx.RIGHT|wx.LEFT, 5), SPC])
        cntSizer = wx.BoxSizer(wx.HORIZONTAL)
        cntSizer.AddMany([(self.sign, 0, wx.ALL, 5), (txtSizer, 1, wx.EXPAND, 5)])
        self.panel.SetSizer(cntSizer)
        self.panel.Layout()
        cntSizer.Fit(self.panel)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.AddMany([(self.panel, 1, wx.EXPAND, 5), (self.exitBtn, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)])
        self.SetSizer(mainSizer)
        self.Layout()
        self.Centre(wx.BOTH)
        # Events
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.exitBtn.Bind(wx.EVT_BUTTON, self.onClose)

    def onClose(self, event):
        """Exit actions."""
        self.Destroy()


class aboutDialog(wx.Dialog):
    """About, help, credits and license dialog."""

    def __init__(self, parent, title='Information', style=wx.CAPTION|wx.CLOSE_BOX|wx.STAY_ON_TOP|wx.SYSTEM_MENU):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=DPOS, size=(370, 440), style=style)
        self.SetSizeHints(wx.Size(370, 440), DSIZE)
        setIcon(self)
        # Contents
        self.abtBtn = wx.Button(self, wx.ID_ANY, 'About', DPOS, DSIZE, wx.BU_EXACTFIT|wx.NO_BORDER, name='About')
        self.hlpBtn = wx.Button(self, wx.ID_ANY, 'Help', DPOS, DSIZE, wx.BU_EXACTFIT|wx.NO_BORDER, name='Help')
        self.licBtn = wx.Button(self, wx.ID_ANY, 'License', DPOS, DSIZE, wx.BU_EXACTFIT|wx.NO_BORDER, name='License')
        self.mainTxt = wx.TextCtrl(self, wx.ID_ANY, '', DPOS, DSIZE, wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH|wx.NO_BORDER)
        self.mainTxt.SetValue(creds['About'])
        self.authLnk = adv.HyperlinkCtrl(self, wx.ID_ANY, 'Author\'s WebSite', creds['home.url'], DPOS, DSIZE, adv.HL_DEFAULT_STYLE)
        self.gitLnk = adv.HyperlinkCtrl(self, wx.ID_ANY, 'GitHub', creds['GitHub.url'], DPOS, DSIZE, adv.HL_DEFAULT_STYLE)
        self.dmLnk = adv.HyperlinkCtrl(self, wx.ID_ANY, 'dhewm3', creds['dhewm3.url'], DPOS, DSIZE, adv.HL_DEFAULT_STYLE)
        self.tabs = (self.abtBtn, self.hlpBtn, self.licBtn)
        # Theming
        [x.SetForegroundColour(wx.Colour(240, 240, 240)) for x in (self, self.abtBtn, self.licBtn, self.hlpBtn, self.mainTxt)]
        self.abtBtn.SetBackgroundColour(wx.Colour(60, 60, 60))
        [x.SetBackgroundColour(wx.Colour(80, 80, 80)) for x in (self.licBtn, self.hlpBtn)]
        self.SetBackgroundColour(wx.Colour(45, 45, 45))
        self.mainTxt.SetBackgroundColour(wx.Colour(112, 112, 112))
        [x.SetHoverColour(wx.Colour(255, 255, 255)) for x in (self.authLnk, self.gitLnk, self.dmLnk)]
        [x.SetNormalColour(wx.Colour(240, 240, 240)) for x in (self.authLnk, self.gitLnk, self.dmLnk)]
        [x.SetVisitedColour(wx.Colour(240, 240, 240)) for x in (self.authLnk, self.gitLnk, self.dmLnk)]
        # Layout
        self.mainTxt.SetMinSize((350,420))
        tabsSizer = wx.BoxSizer(wx.HORIZONTAL)
        tabsSizer.AddMany([(self.abtBtn, 0, wx.TOP|wx.LEFT, 5), (self.licBtn, 0, wx.TOP|wx.LEFT, 5), (self.hlpBtn, 0, wx.TOP|wx.LEFT, 5)])
        lnkSizer = wx.BoxSizer(wx.HORIZONTAL)
        lnkSizer.AddMany([(self.authLnk, 0, wx.ALL, 5), (self.gitLnk, 0, wx.ALL, 5), (self.dmLnk, 0, wx.ALL, 5)])
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.AddMany([(tabsSizer, 0, 0, 5), (self.mainTxt, 1, wx.EXPAND|wx.RIGHT|wx.LEFT, 5), (lnkSizer, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)])
        self.SetSizer(mainSizer)
        self.Layout()
        mainSizer.Fit(self)
        self.Centre(wx.BOTH)
        # Events
        [x.Bind(wx.EVT_BUTTON, self.onTabClick) for x in self.tabs]
        self.mainTxt.Bind(wx.EVT_ENTER_WINDOW, self.onHovCtrl)
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def onTabClick(self, event):
        """On tab selection."""
        selTab = event.GetEventObject().GetName()
        for tab in self.tabs:
            if tab.GetName() == selTab:
                tab.SetBackgroundColour(wx.Colour(60, 60, 60))
            else: tab.SetBackgroundColour(wx.Colour(80, 80, 80))
        self.mainTxt.SetValue(creds[selTab])

    def onHovCtrl(self, event):
        """On hovering over text ctrl."""
        event.GetEventObject().SetFocus()

    def setContent(self, field):
        """Set content for text fields."""
        self.mainTxt.SetValue(creds[field])

    def onClose(self, event):
        """Exit actions."""
        self.Hide()
        self.Destroy()


class MainPanel(wx.Panel):
    """MainPanel."""

    def __init__(self, parent):
        """Init."""
        wx.Panel.__init__(self, parent=parent)
        self.frame = parent
        # Content
        self.confBtn = GB.GradientButton(self, wx.ID_ANY, None, 'Exclusions', size=(65, 15))
        self.abtBtn = GB.GradientButton(self, wx.ID_ANY, None, 'i', size=(15, 15))
        self.listBoxChoices = self.scanMods()
        self.listBox = wx.ListBox(self, wx.ID_ANY, DPOS, DSIZE, self.listBoxChoices, wx.LB_SINGLE|wx.SIMPLE_BORDER)
        origListBoxSize = self.listBox.GetSize()
        self.listBox.SetSize((origListBoxSize[0]+20, origListBoxSize[1]+20,))
        self.addBtn = GB.GradientButton(self, wx.ID_ANY, None, 'Add', size=(30, 15))
        self.scnBtn = GB.GradientButton(self, wx.ID_ANY, None, 'Scan', size=(32, 15))
        self.edtBtn = GB.GradientButton(self, wx.ID_ANY, None, 'Edit', size=(32, 15))
        self.rmBtn = GB.GradientButton(self, wx.ID_ANY, None, 'Hide', size=(42, 15), name='Exclude')
        self.ipTxt = wx.TextCtrl(self, wx.ID_ANY, conf['connect.ip'], DPOS, DSIZE, wx.TE_CENTRE|wx.SIMPLE_BORDER)
        self.ipTxt.SetMaxLength(15)
        self.portTxt = wx.TextCtrl(self, wx.ID_ANY, conf['connect.port'], DPOS, DSIZE, wx.TE_CENTRE|wx.SIMPLE_BORDER)
        self.portTxt.SetMaxLength(5)
        self.cnctBox = wx.CheckBox(self, wx.ID_ANY, 'Connect on launch?', DPOS, DSIZE, 0)
        self.cnctBox.SetValue(conf['connect.launch'])
        self.clsBox = wx.CheckBox(self, wx.ID_ANY, 'Auto-Quit', DPOS, DSIZE, wx.ALIGN_RIGHT)
        self.clsBox.SetValue(conf['auto.quit'])
        self.actBtn = GB.GradientButton(self, wx.ID_ANY, None, 'Launch', size=DSIZE)
        # Theming
        font = wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, 'Arial')
        [x.SetFont(font) for x in (self.listBox, self.ipTxt, self.portTxt)]
        [x.SetForegroundColour(wx.Colour(224, 224, 224)) for x in (self.listBox, self.cnctBox, self.clsBox)]
        [x.SetForegroundColour(wx.Colour(240, 240, 240)) for x in (self.ipTxt, self.portTxt)]
        [x.SetBackgroundColour(wx.Colour(16, 16, 16)) for x in (self.portTxt, self.listBox, self.ipTxt)]
        [x.SetBackgroundColour(wx.BLACK) for x in (self.clsBox, self.cnctBox)]
        # Layout
        self.ipTxt.SetMaxSize(wx.Size(120, -1))
        self.portTxt.SetMaxSize(wx.Size(50, -1))
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.AddMany([(self.confBtn, 0, wx.ALL, 5), SPC, (self.abtBtn, 0, wx.ALL, 5)])
        listBtnSizer = wx.BoxSizer(wx.HORIZONTAL)
        listBtnSizer.AddMany([(self.addBtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5), (self.scnBtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT,
            5), (self.edtBtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5), (self.rmBtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)])
        listSizer = wx.BoxSizer(wx.VERTICAL)
        listSizer.AddMany([(self.listBox, 1, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5), (listBtnSizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)])
        toolSizer = wx.BoxSizer(wx.HORIZONTAL)
        toolSizer.AddMany([(self.ipTxt, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5), (self.portTxt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5),
            (self.cnctBox, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5), SPC, (self.clsBox, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5),
                (self.actBtn, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)])
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.AddMany([(topSizer, 0, wx.EXPAND, 5), SPC, (listSizer, 1, wx.ALIGN_RIGHT|wx.ALL, 5), (toolSizer, 0, wx.EXPAND, 5)])
        self.SetSizer(mainSizer)
        # Events
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.listBox.Bind(wx.EVT_ENTER_WINDOW, self.onHovCtrl)

    def onHovCtrl(self, event):
        """On hovering over ctrl."""
        event.GetEventObject().SetFocus()

    def OnEraseBackground(self, event):
        """ Add a picture to the background."""
        # Yanked (modified for Phoenix) from ColourDB.py
        dc = event.GetDC()
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRegion(rect)
        dc.Clear()
        dc.DrawBitmap(CreateBitmap('background'), 0, 0)

    def parseFile(self, fpath):
        """Parse a file's contents."""
        with open(fpath) as inp:
            return inp.readlines()

    def parseBat(self, fpath):
        """Encapsulate a batch file contents."""
        try:
            return ['%s %s' % (defs['game.exe'] if defs['game.exe'] in x else defs['game.server'
            ], x.replace("'", '"').split('.exe')[1][1:].strip()) for x in self.parseFile(fpath) if '.exe' in x]
        except: pass  # By default None

    def scanMods(self):
        """Scan launcher choices."""
        if not os.path.isfile(os.path.join(defs['game.dir'], defs['game.exe'])): return []
        gameEXE = os.path.join(defs['game.dir'], defs['game.exe'])
        modDirs = [os.path.normpath(os.path.join(defs['game.dir'], x)) for x in os.listdir(
            defs['game.dir']) if all([os.path.isdir(os.path.join(defs['game.dir'], x)), x not in ('base',
                'd3xp'), os.path.normpath(os.path.join(defs['game.dir'], x)) != os.path.normpath(APPDIR)])]
        launchers = {}
        # Scanning
        if 'base' in [x.lower() for x in os.listdir(defs['game.dir'])]:  # Base game
            launchers['%sPlay Doom 3' % defs['list.spc']] = [gameEXE]
        if 'd3xp' in [x.lower() for x in os.listdir(defs['game.dir'])]:  # Expansion RoE
            launchers['%sPlay Resurrection of evil' % defs['list.spc']] = ['%s +set fs_game_base d3xp' % gameEXE]
        for x in modDirs:  # Scan mod dirs
            if '.bat' in [os.path.splitext(y)[1] for y in os.listdir(x)]:
                rawBatches = {os.path.splitext(y)[0]: self.parseBat(
                    os.path.join(x, y)) for y in os.listdir(x) if '.bat' in os.path.splitext(y)}
                [launchers.update({'%s%s' % (defs['list.spc'],
                    y): rawBatches[y]}) for y in rawBatches.keys() if rawBatches[y] is not None]
        cache['launchers.full'] = launchers
        cache['launchers'] = {x: launchers[x] for x in launchers if x not in conf['launch.exclusions']}
        cache['launchers'].update(conf['custom.launchers'])
        return sorted([x for x in cache['launchers']])


class MainFrame(wx.Frame):
    """MainFrame."""

    def __init__(self, parent, title, pos, size, style=wx.CLOSE_BOX|wx.SYSTEM_MENU|wx.CAPTION):
        """Init."""
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=title, pos=pos, size=size, style=style)
        setIcon(self)
        self.timer = wx.Timer()
        self.detectGameDir()
        # Layout
        self.panel = MainPanel(self)
        self.Center()
        self.SetSizeHints((645, 435), (645, 435))
        # Theming
        [x.SetBackgroundColour(wx.BLACK) for x in (self, self.panel)]
        # Events
        self.timer.Bind(wx.EVT_TIMER, self.onUpdate)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.panel.actBtn.Bind(wx.EVT_BUTTON, self.launch)
        self.panel.scnBtn.Bind(wx.EVT_BUTTON, self.scanAct)
        self.panel.confBtn.Bind(wx.EVT_BUTTON, self.initConfig)
        self.panel.rmBtn.Bind(wx.EVT_BUTTON, self.onExclude)
        self.panel.addBtn.Bind(wx.EVT_BUTTON, self.onAddCustom)
        self.panel.edtBtn.Bind(wx.EVT_BUTTON, self.onEdit)
        self.panel.abtBtn.Bind(wx.EVT_BUTTON, self.onAbout)
        # Init
        self.timer.Start(defs['main.timer'])

    def onUpdate(self, event):
        """Main GUI timed events."""
        if cache['err.exit']: self.onClose()
        curLauncherSelection = self.panel.listBox.GetSelection()
        if curLauncherSelection == -1:
            if conf['last.launched'] != -1: self.panel.listBox.SetSelection(self.panel.listBox.FindString(conf['last.launched']))
            else: self.panel.listBox.SetSelection(self.panel.listBox.FindString('%sPlay Doom 3' % defs['list.spc']))
        elif conf['last.launched'] != self.panel.listBox.GetString(curLauncherSelection):
            conf['last.launched'] = self.panel.listBox.GetString(curLauncherSelection)
        if conf['connect.ip'] != self.panel.ipTxt.GetValue(): conf['connect.ip'] = self.panel.ipTxt.GetValue()
        if conf['connect.port'] != self.panel.portTxt.GetValue(): conf['connect.port'] = self.panel.portTxt.GetValue()
        if conf['connect.launch'] != self.panel.cnctBox.GetValue(): conf['connect.launch'] = self.panel.cnctBox.GetValue()
        if conf['auto.quit'] != self.panel.clsBox.GetValue(): conf['auto.quit'] = self.panel.clsBox.GetValue()
        if curLauncherSelection != -1:
            if any([True for x in cache['launchers'][self.panel.listBox.GetString(curLauncherSelection)] if defs['game.server'] in x]):
                [x.Hide() for x in (self.panel.ipTxt, self.panel.portTxt, self.panel.cnctBox) if x.IsShown()]
            else: [x.Show() for x in (self.panel.ipTxt, self.panel.portTxt, self.panel.cnctBox) if not x.IsShown()]
            if self.panel.listBox.GetString(curLauncherSelection) in conf['custom.launchers']:
                if self.panel.rmBtn.GetLabel() == 'Hide':
                    self.panel.rmBtn.SetLabel('Delete')
                    self.panel.rmBtn.SetName('Delete')
                    self.panel.rmBtn.Refresh()
            else:
                if self.panel.rmBtn.GetLabel() == 'Delete':
                    self.panel.rmBtn.SetLabel('Hide')
                    self.panel.rmBtn.SetName('Exclude')
                    self.panel.rmBtn.Refresh()

    def scanAct(self, event=None):
        """On scan event."""
        self.panel.listBox.Clear()
        self.panel.listBox.InsertItems(self.panel.scanMods(), 0)

    def detectGameDir(self):
        """Detect game directory."""
        appTmpDir = APPDIR if not defs['dev.path'] else defs['dev.path']
        for exe in defs['port.exes'].keys():
            # Detect if installed in own dir
            if exe in [x.lower() for x in os.listdir(appTmpDir)]:
                defs['game.exe'] = [x for x in os.listdir(appTmpDir) if x.lower() == exe.lower()][0]
                defs['game.server'] = [x for x in os.listdir(appTmpDir) if x.lower() == defs['port.exes'][exe].lower()][0]
                defs['game.dir'] = appTmpDir
            # Detect if installed in game root
            elif exe in [x.lower() for x in os.listdir(os.path.dirname(appTmpDir))]:
                defs['game.exe'] = [x for x in os.listdir(os.path.dirname(appTmpDir)) if x.lower() == exe.lower()][0]
                defs['game.server'] = [x for x in os.listdir(os.path.dirname(appTmpDir)) if x.lower() == defs['port.exes'][exe].lower()][0]
                defs['game.dir'] = os.path.dirname(appTmpDir)
        if not defs['game.dir']:
            ErrDialog(None, 'Unable to detect Doom3/dhewm3 directory', 'Unable to auto-detect Doom3/dhewm3 directory!',
                'Autodetection will work if d3launcher is installed within Doom3/dhewm3 directory or in it\'s own directory '
                'nested within Doom3/dhewm3 directory.\n\nYou may override the Doom3/dhewm3 path by saving a file named \'override.'
                'ini\' in the d3launcher directory. It has to contain only something like this:\n      D:/Games/dhewm3/\n\n').ShowModal()
            cache['err.exit'] = True

    def initConfig(self, event):
        """Open configuration dialog."""
        self.timer.Stop()
        confDialog(self).ShowModal()
        self.scanAct()
        self.timer.Start(defs['main.timer'])

    def onAddCustom(self, event):
        """Open add custom launcher dialog."""
        self.timer.Stop()
        addDialog(self).ShowModal()
        self.scanAct()
        self.timer.Start(defs['main.timer'])

    def onAbout(self, event):
        """About dialog."""
        self.timer.Stop()
        aboutDialog(self).ShowModal()
        self.scanAct()
        self.timer.Start(defs['main.timer'])

    def onExclude(self, event):
        """Add items to exclusion list."""
        self.timer.Stop()
        curSelection = self.panel.listBox.GetSelection()
        action = event.GetEventObject().GetName()
        if action == 'Exclude':
            conf['launch.exclusions'].append(self.panel.listBox.GetString(curSelection))
        elif action == 'Delete':
            conf['custom.launchers'].pop(self.panel.listBox.GetString(curSelection), None)
        self.scanAct()
        self.timer.Start(defs['main.timer'])

    def onEdit(self, event):
        """Edit a launcher."""
        self.timer.Stop()
        curSelectionStr = self.panel.listBox.GetString(self.panel.listBox.GetSelection())
        addDialog(self, edit=(curSelectionStr, cache['launchers'][curSelectionStr])).ShowModal()
        self.scanAct()
        self.timer.Start(defs['main.timer'])

    def launch(self, event):
        """Launch selected."""
        curSelection = self.panel.listBox.GetSelection()
        if any([defs['game.dir'] is None, curSelection == -1]): return
        curSelectionStr = self.panel.listBox.GetString(curSelection)
        os.chdir(defs['game.dir'])
        if len(cache['launchers'][curSelectionStr]) == 1:
            if not defs['game.server'] in cache['launchers'][curSelectionStr][0]:
                if not conf['connect.launch']: subprocess.Popen(cache['launchers'][curSelectionStr][0])
                else: subprocess.Popen('%s %s' % (cache['launchers'][curSelectionStr][0],
                    '+connect %s%s' % (conf['connect.ip'], ':%s' % conf['connect.port'] if conf['connect.port'] else '')))
            else: subprocess.Popen(cache['launchers'][curSelectionStr][0])
        else: [subprocess.Popen(execCMD) for execCMD in cache['launchers'][curSelectionStr]]
        if self.panel.clsBox.GetValue(): self.onClose()

    def onClose(self, event=None):
        """Exit actions."""
        self.timer.Stop()
        singletons.confLib.store()
        singletons.MainFrame.Hide()
        singletons.MainFrame.Destroy()
        singletons.app.ExitMainLoop()


class MyApp(wx.App):
    """Bootstrap wxPython."""

    def InitLocale(self):
        """Init locale."""
        locale.setlocale(locale.LC_ALL, 'C')

    def OnInit(self):
        """OnInit."""
        wx.Locale(wx.LANGUAGE_ENGLISH_US)
        self.SetAppName(APPNAME)
        return True


class main:
    """Let the fun begin..."""

    def __init__(self):
        """Init."""
        self.detectDev()
        singletons.confLib = confLib()
        singletons.confLib.restore()
        self.storeLicense()
        self.initGUI()

    def detectDev(self):
        """Detect if on Dev mode (to override game path)."""
        try:
            devFile = os.path.join(APPDIR, 'override.ini')
            if os.path.isfile(devFile):
                with open(devFile) as inp:
                    devGamePath = inp.read()
                    if devGamePath.strip():
                        defs['dev.path']=devGamePath.strip()
        except: pass

    def storeLicense(data):
        """Store license in app dir."""
        try:
            with open(os.path.join(APPDIR, 'LICENSE'), 'w') as lf:
                lf.write(creds['License'])
        except: pass

    def initGUI(self):
        """Init GUI."""
        pos = DPOS
        size = wx.Size(645, 435)
        singletons.app = MyApp()
        singletons.MainFrame = MainFrame(None, '%s %s' % (APPNAME, APPVER[0]), pos, size)
        singletons.app.SetTopWindow(singletons.MainFrame)
        singletons.MainFrame.Show()
        singletons.app.MainLoop()


if __name__ == '__main__':
    main()
