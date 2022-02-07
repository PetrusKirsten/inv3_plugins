# -*- coding: utf-8 -*-
import wx
import gui
# from . import gui


def load():
    g = gui.Window(wx.GetApp().GetTopWindow())
    g.Show()
