# -*- coding: utf-8 -*-
import wx
import gui


def load():
    g = gui.Dialog(wx.GetApp().GetTopWindow())
    g.Show()
