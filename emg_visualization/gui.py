import wx
import spiralTMS
import matplotlib as mpl
from matplotlib import pyplot as plt
from serial.serialutil import SerialException
from main import serial_ports, Plotter, EmgThread


class Dialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title='Automated motor mapping',
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
        )

        self.noPath_traj = wx.StaticText(self, -1)
        self.x_ctrl = None
        self.y_ctrl = None
        self.z_ctrl = None
        self.ecc_ctrl = None
        self.radius_ctrl = None
        self.pointsdist_ctrl = None

        self.portIndex = None
        self.ports = serial_ports()

        self.initgui()

    def onselect(self, evt):
        self.portIndex = evt.GetSelection()

    def onpath(self, evt):
        with wx.FileDialog(self, 'Save EMG plots', wildcard='PNG files (*.png)|*.png',
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            print(f'saving plot estimulations as {pathname}')
            # try:
            #     with open(pathname, 'w') as file:
            #         print(pathname)
            # except IOError:
            #     wx.LogError("Cannot save current data in file '%s'." % pathname)

    def oncancel(self, evt):
        print('Closing automated motor maping dialog')
        self.Close(True)

    def onrun(self, evt):
        print('Run realtime EMG plot...')
        try:
            emg = EmgThread(port=self.ports[self.portIndex])
            emg.start()
            Plotter(rawSignal=True, showTrigger=True)
        except SerialException:
            print('Unable to access this serial port')
        except TypeError:
            print('Select an available serial port')

    def ongenerate(self, evt):
        print('Generating coil path')
        mpl.rcParams['toolbar'] = 'None'
        plt.figure('Robotic coil trajectory preview')
        plt.style.use('ggplot')
        plt.xlabel('X [mm]')
        plt.ylabel('Y [mm]')
        plt.title('Coordinate System')

        x_marker, y_marker, x_path, y_path, data = spiralTMS.ellipse_path(
            x_hotspot=float(self.x_ctrl.GetValue()),
            y_hotspot=float(self.x_ctrl.GetValue()),
            z_hotspot=float(self.x_ctrl.GetValue()),
            e=float(self.ecc_ctrl.GetValue()),
            size=float(self.radius_ctrl.GetValue()),
            distance=float(self.pointsdist_ctrl.GetValue())
        )
        spiralTMS.info(data)
        plt.plot(
            x_path,
            y_path,
            color='k',
            linewidth=0.5,
            label='TMS coil path'
        )
        plt.scatter(
            x_marker,
            y_marker,
            color='r',
            label='TMS stimulation'
        )
        plt.legend()
        plt.show()

        try:
            self.noPath_traj.Destroy()
        except RuntimeError:
            pass

    def initgui(self):
        # EMG plotting GUI
        combobox_plot = wx.BoxSizer(wx.HORIZONTAL)
        combobox_plot.Add(
            wx.StaticText(self, -1, 'Serial Port'),
            0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10
        )
        combobox_plot.Add(
            wx.ComboBox(self, -1, style=wx.CB_READONLY, choices=serial_ports()),
            1, wx.EXPAND
        )

        save_plot = wx.BoxSizer(wx.VERTICAL)
        saveplot_check = wx.CheckBox(self, -1, 'Save the estimulation plot')
        save_plot.Add(
            saveplot_check,
            0, wx.ALIGN_CENTER_HORIZONTAL
        )
        save_plot.Add(
            wx.Button(self, 1, 'Location'),
            0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10
        )

        buttons_plot = wx.BoxSizer(wx.HORIZONTAL)
        buttons_plot.Add(
            wx.Button(self, 2, 'Cancel'), 0,
            wx.ALIGN_BOTTOM | wx.RIGHT, 14
        )
        buttons_plot.Add(
            wx.Button(self, 3, 'Run', size=(-1, 56)), 0,
            wx.ALIGN_BOTTOM

        )

        plot_sizer = wx.StaticBoxSizer(
            wx.VERTICAL, self,
            'EMG Visualization')
        plot_sizer.Add(
            combobox_plot,
            0, wx.EXPAND | wx.ALL, 20)
        plot_sizer.Add(
            save_plot,
            0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20
        )
        plot_sizer.Add(
            buttons_plot,
            1, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT, 20
        )
        self.Bind(wx.EVT_COMBOBOX, self.onselect)
        self.Bind(wx.EVT_BUTTON, self.onpath, id=1)
        self.Bind(wx.EVT_BUTTON, self.oncancel, id=2)
        self.Bind(wx.EVT_BUTTON, self.onrun, id=3)

        # Path generation GUI
        ctrl_size = (60, -1)
        self.x_ctrl = wx.TextCtrl(self, -1, '0.00', size=ctrl_size)
        self.y_ctrl = wx.TextCtrl(self, -1, '0.00', size=ctrl_size)
        self.z_ctrl = wx.TextCtrl(self, -1, '198.57', size=ctrl_size)
        self.ecc_ctrl = wx.TextCtrl(self, -1, '0.75', size=ctrl_size)
        self.radius_ctrl = wx.TextCtrl(self, -1, '40', size=ctrl_size)
        self.pointsdist_ctrl = wx.TextCtrl(self, -1, '20', size=ctrl_size)

        x_sta = wx.StaticText(self, -1, 'X axis hotspot:')
        y_sta = wx.StaticText(self, -1, 'Y axis hotspot:')
        z_sta = wx.StaticText(self, -1, 'Z axis hotspot:')
        ecc_sta = wx.StaticText(self, -1, 'Ellipse eccentricity:')
        radius_sta = wx.StaticText(self, -1, 'Max ellipse radius [mm]:')
        pointsdist_sta = wx.StaticText(self, -1, 'Points distance [mm]:')

        txt_traj = wx.FlexGridSizer(3, 4, 10, 10)
        txt_traj.AddMany(
            ((x_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.x_ctrl, 0),
             (ecc_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.ecc_ctrl, 0),
             (y_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.y_ctrl, 0),
             (radius_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.radius_ctrl, 0),
             (z_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.z_ctrl, 0),
             (pointsdist_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.pointsdist_ctrl, 0),)
        )

        buttons_traj = wx.BoxSizer(wx.VERTICAL)

        self.noPath_traj.SetLabel('   No path generate yet.   ')
        self.noPath_traj.SetBackgroundColour('YELLOW')
        buttons_traj.Add(
            self.noPath_traj, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 10
        )
        buttons_traj.Add(
            wx.Button(self, 4, 'Generate trajectory', size=(150, 35)),
            0, wx.ALIGN_CENTER_HORIZONTAL,
        )

        traj_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, 'Robotic coil trajectory')
        traj_sizer.Add(
            txt_traj, 0,
            wx.ALL, 20
        )
        traj_sizer.Add(
            buttons_traj, 0,
            wx.ALIGN_CENTER_HORIZONTAL | wx.LEFT, 20
        )

        self.Bind(wx.EVT_BUTTON, self.ongenerate, id=4)

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
