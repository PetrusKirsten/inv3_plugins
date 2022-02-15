# -*- coding: utf-8 -*-
import wx
# from . import gui
import gui


def load():
    g = gui.EMGui(wx.GetApp().GetTopWindow())
    g.Show()
