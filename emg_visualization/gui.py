import wx


class Dialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Automated motor mapping",
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
        )

        self.pathgenerated = False
        self.initgui()

    def onpath(self, evt):
        with wx.FileDialog(self, "Save EMG plots", wildcard="PNG files (*.png)|*.png",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            print(pathname)
            # try:
            #     with open(pathname, 'w') as file:
            #         print(pathname)
            # except IOError:
            #     wx.LogError("Cannot save current data in file '%s'." % pathname)

    def oncancel(self, evt):
        print("Closing...")
        self.Close(True)

    def onapply(self, evt):
        print("Run realtime plot...")

    def onreset(self, evt):
        print("Reseting path parameters values...")

    def ongenerate(self, evt):
        print("Generating path...")
        self.pathgenerated = True

    def initgui(self):
        # EMG plotting GUI
        combobox_plot = wx.BoxSizer(wx.HORIZONTAL)
        combobox_plot.Add(
            wx.StaticText(self, -1, 'Serial Port'),
            0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        combobox_plot.Add(
            wx.ComboBox(self, -1, style=wx.CB_READONLY),
            1, wx.EXPAND)

        save_plot = wx.BoxSizer(wx.HORIZONTAL)
        saveplot_check = wx.CheckBox(self, -1, 'Save the estimulation')
        save_plot.Add(
            saveplot_check,
            0, wx.ALIGN_CENTER_VERTICAL)
        save_plot.Add(
            wx.Button(self, 1, 'Select Location'),
            1, wx.ALIGN_CENTER_VERTICAL)

        buttons_plot = wx.BoxSizer(wx.HORIZONTAL)
        buttons_plot.Add(
            wx.Button(self, 2, 'Cancel'),
            0, wx.ALIGN_LEFT | wx.RIGHT, 20
        )
        buttons_plot.Add(
            wx.Button(self, 3, 'Run'), 2
        )

        plot_sizer = wx.StaticBoxSizer(
            wx.VERTICAL, self, 
            'EMG Visualization')
        plot_sizer.Add(
            combobox_plot, 
            0, wx.EXPAND | wx.ALL, 20)
        plot_sizer.Add(
            save_plot, 
            0, wx.EXPAND | wx.ALL, 20)
        plot_sizer.Add(
            buttons_plot, 
            1, wx.EXPAND | wx.ALL, 20)
        
        self.Bind(wx.EVT_BUTTON, self.onpath, id=1)
        self.Bind(wx.EVT_BUTTON, self.oncancel, id=2)
        self.Bind(wx.EVT_BUTTON, self.onapply, id=3)

        # Path generation GUI
        txtctrl_x = wx.TextCtrl(self, -1, '0.00')
        statxt_x = wx.StaticText(self, -1, 'X axis hotspot:')
        txtctrl_y = wx.TextCtrl(self, -1, '0.00')
        statxt_y = wx.StaticText(self, -1, 'Y axis hotspot:')
        txtctrl_z = wx.TextCtrl(self, -1, '198.57')
        statxt_z = wx.StaticText(self, -1, 'Z axis hotspot:')

        ecc_ctrl = wx.TextCtrl(self, -1, '0.75')
        ecc_sta = wx.StaticText(self, -1, 'Ellipse eccentricity:')
        radius_ctrl = wx.TextCtrl(self, -1, '40')
        radius_sta = wx.StaticText(self, -1, 'Max ellipse radius [mm]:')
        pointsdist_ctrl = wx.TextCtrl(self, -1, '20')
        pointsdist_sta = wx.StaticText(self, -1, 'Points distance [mm]:')

        txt_traj = wx.FlexGridSizer(3, 4, 10, 10)
        txt_traj.AddMany(
            ((statxt_x, 0, wx.ALIGN_CENTER_VERTICAL), (txtctrl_x, 0),
             (ecc_sta, 0, wx.ALIGN_CENTER_VERTICAL), (ecc_ctrl, 0),
             (statxt_y, 0, wx.ALIGN_CENTER_VERTICAL), (txtctrl_y, 0),
             (radius_sta, 0, wx.ALIGN_CENTER_VERTICAL), (radius_ctrl, 0),
             (statxt_z, 0, wx.ALIGN_CENTER_VERTICAL), (txtctrl_z, 0),
             (pointsdist_sta, 0, wx.ALIGN_CENTER_VERTICAL), (pointsdist_ctrl, 0),)
        )

        buttons_traj = wx.BoxSizer(wx.HORIZONTAL)
        if self.pathgenerated:
            # path_traj = wx.StaticText(self, -1, '   Path generate successfully!   ')
            path_traj = wx.StaticText(self, -1)
            path_traj.SetLabel('   Path generate successfully!   ')
            path_traj.SetBackgroundColour('GREEN')
            buttons_traj.Add(
                path_traj, 0,
                wx.ALIGN_CENTER_VERTICAL
            )
        else:
            # noPath_traj = wx.StaticText(self, -1, '   No path generate yet.   ')
            noPath_traj = wx.StaticText(self, -1)
            noPath_traj.SetLabel('   No path generate yet.   ')
            noPath_traj.SetBackgroundColour('YELLOW')
            buttons_traj.Add(
                noPath_traj, 0,
                wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 0
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

        self.Bind(wx.EVT_BUTTON, self.onreset, id=4)
        self.Bind(wx.EVT_BUTTON, self.ongenerate, id=5)

        # Main sizer GUI
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(
            traj_sizer, 1,
            wx.EXPAND | wx.ALL, 5
        )
        main_sizer.Add(
            plot_sizer, 0,
            wx.EXPAND | wx.ALL, 5
        )

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()


if __name__ == '__main__':
    app = wx.App()
    dlg = Dialog(None)
    dlg.Show()
    app.MainLoop()
