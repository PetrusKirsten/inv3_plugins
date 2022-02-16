# -*- coding: utf-8 -*-
import wx
from . import gui
# import gui


def load():
    g = gui.MotorMapGui(wx.GetApp().GetTopWindow())
    g.Show()
