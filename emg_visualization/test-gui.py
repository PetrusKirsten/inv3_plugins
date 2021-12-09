import wx


class Dialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="EMG visualization",
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
        )

        txt_hotspot_x = wx.TextCtrl(self, -1, '0.00')
        txt_hotspot_y = wx.TextCtrl(self, -1, '0.00')
        txt_hotspot_z = wx.TextCtrl(self, -1, '198.57')

        ecc_ellipse = wx.TextCtrl(self, -1, '0.75')
        max_radius = wx.TextCtrl(self, -1, '40')
        points_dist = wx.TextCtrl(self, -1, '20')

        txt_traj = wx.FlexGridSizer(3, 4, 5, 20)
        txt_traj.AddMany(
            ((wx.StaticText(self, -1, 'X axis hotspot:'), 0, wx.ALIGN_CENTER_VERTICAL),
             (txt_hotspot_x, 0, wx.ALIGN_RIGHT),
             (wx.StaticText(self, -1, 'Ellipse eccentricity:'), 0, wx.ALIGN_CENTER_VERTICAL),
             (ecc_ellipse, 0, wx.ALIGN_RIGHT),
             (wx.StaticText(self, -1, 'Y axis hotspot:'), 0, wx.ALIGN_CENTER_VERTICAL),
             (txt_hotspot_y, 0, wx.ALIGN_RIGHT),
             (wx.StaticText(self, -1, 'Max ellipse radius [mm]:'), 0, wx.ALIGN_CENTER_VERTICAL),
             (max_radius, 0, wx.ALIGN_RIGHT),
             (wx.StaticText(self, -1, 'Z axis hotspot:'), 0, wx.ALIGN_CENTER_VERTICAL),
             (txt_hotspot_z, 0, wx.ALIGN_RIGHT),
             (wx.StaticText(self, -1, 'Points distance [mm]:'), 0, wx.ALIGN_CENTER_VERTICAL),
             (points_dist, 0),)
        )

        noPath_traj = wx.StaticText(self, -1, '   No path generate yet!   ')
        noPath_traj.SetBackgroundColour('yellow')
        path_traj = wx.StaticText(self, -1, '   Path generate successfully!   ')
        path_traj.SetBackgroundColour('green')

        buttons_traj = wx.BoxSizer(wx.HORIZONTAL)
        buttons_traj.Add(
            noPath_traj, 0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 120
        )
        buttons_traj.Add(
            path_traj, 0,
            wx.ALIGN_CENTER_VERTICAL
        )
        buttons_traj.Add(
            wx.Button(self, 4, 'Reset'),
            1, wx.ALIGN_CENTER_VERTICAL
        )
        buttons_traj.Add(
            wx.Button(self, 5, 'Generate Path'),
            2, wx.ALIGN_CENTER_VERTICAL
        )

        traj_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, 'Path')
        traj_sizer.Add(
            txt_traj, 0,
            wx.ALL, 5
        )
        traj_sizer.Add(
            buttons_traj, 0,
            wx.ALL, 10
        )

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(
            traj_sizer, 1,
            wx.EXPAND | wx.ALL, 5
        )

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def OnCancel(self, evt):
        print("Closing...")
        self.Close(True)

    def OnApply(self, evt):
        print("Run realtime plot...")


if __name__ == '__main__':
    app = wx.App()
    dlg = Dialog(None)
    dlg.Show()
    app.MainLoop()
