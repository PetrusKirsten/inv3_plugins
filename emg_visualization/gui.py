import wx


class Dialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Automated Motor Map",
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
        )

        self.init_gui()

    def OnPath(self, evt):
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

    def OnCancel(self, evt):
        print("Closing...")
        self.Close(True)

    def OnApply(self, evt):
        print("Run realtime plot...")

    def init_gui(self):
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
        
        self.Bind(wx.EVT_BUTTON, self.OnPath, id=1)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=2)
        self.Bind(wx.EVT_BUTTON, self.OnApply, id=3)

        # Path generation GUI
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


if __name__ == '__main__':
    app = wx.App()
    dlg = Dialog(None)
    dlg.Show()
    app.MainLoop()
