import wx
import vtk
import sys
import serial
from . import emg
import numpy as np
from . import spiralTMS
import invesalius.project as prj
from serial import SerialException
from pubsub import pub as Publisher
import invesalius.constants as const
import invesalius.data.vtk_utils as vtku
from vtkmodules.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor


class MotorMapGui(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title='Automated motor mapping',
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # EMG visualization variables
        self.plot_sizer = wx.StaticBoxSizer(
            wx.HORIZONTAL, self,
            'EMG Visualization')

        self.left_emgSizer = wx.BoxSizer(wx.VERTICAL)
        self.combobox_plot = wx.BoxSizer(wx.HORIZONTAL)
        self.save_plot = wx.BoxSizer(wx.HORIZONTAL)
        self.right_emgSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_plot = wx.BoxSizer(wx.VERTICAL)

        self.saveplot_check = wx.CheckBox(self, -1, 'Save the estimulation plot')
        self.ports = emg.serial_ports()
        self.savePlot = None
        self.location = None
        self.portIndex = None
        self.runButton = None
        self.localButton = None

        # Robot coil trajectory variables
        self.mainTraj_sizer = wx.StaticBoxSizer(
            wx.VERTICAL, self,
            'Robotic coil trajectory')

        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_trajSizer = wx.BoxSizer(wx.VERTICAL)
        self.txt_sizer = wx.FlexGridSizer(6, 2, 10, 10)
        self.right_trajSizer = wx.BoxSizer(wx.VERTICAL)
        self.surf_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom_sizer = wx.BoxSizer(wx.VERTICAL)

        self.x_ctrl = None
        self.y_ctrl = None
        self.z_ctrl = None
        self.ecc_ctrl = None
        self.radius_ctrl = None
        self.pointsdist_ctrl = None
        self.generateButton = None
        self.x_marker = None
        self.y_marker = None

        self.txt_surface = wx.StaticText(self, -1, 'Select the surface:')
        self.x_sta = wx.StaticText(self, -1, 'X axis hotspot:')
        self.y_sta = wx.StaticText(self, -1, 'Y axis hotspot:')
        self.z_sta = wx.StaticText(self, -1, 'Z axis hotspot:')
        self.ecc_sta = wx.StaticText(self, -1, 'Ellipse eccentricity:')
        self.radius_sta = wx.StaticText(self, -1, 'Max ellipse radius [mm]:')
        self.pointsdist_sta = wx.StaticText(self, -1, 'Points distance [mm]:')
        self.noPath_traj = wx.StaticText(self, -1)
        self.noPath_traj.SetLabel('   No surface selected yet!   ')
        self.noPath_traj.SetBackgroundColour('YELLOW')
        self.progress = wx.Gauge(self, -1)

        # ICP variables
        self.obj_actor = None
        self.polydata = None
        self.surface = None
        self.combo_surface_name = None
        self.collect_points = None
        self.m_icp = None

        self.staticballs = []
        self.point_coord = []
        self.icp_points = []
        self.obj_orients = np.full([5, 3], np.nan)
        self.obj_fiducials = np.full([5, 3], np.nan)

        self.interactor = wxVTKRenderWindowInteractor(self, -1, size=self.GetSize())
        self.ren = vtk.vtkRenderer()
        self.proj = prj.Project()

        self.init_gui()

    def EmgVisGui(self):
        self.combobox_plot.Add(
            wx.StaticText(
                self, -1,
                'Serial Port'),
            0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.combobox_plot.Add(
            wx.ComboBox(
                self, -1, style=wx.CB_READONLY,
                choices=emg.serial_ports()),
            2, wx.EXPAND)

        self.save_plot.Add(
            self.saveplot_check,
            0, wx.ALIGN_CENTER_VERTICAL)
        self.localButton = wx.Button(
            self, 1,
            'Location')
        self.save_plot.Add(
            self.localButton,
            0, wx.ALIGN_CENTER_VERTICAL)
        self.localButton.Enable(False)

        self.runButton = wx.Button(
            self, 3,
            'Run', size=(-1, 56))
        self.buttons_plot.Add(
            self.runButton,
            0, wx.ALIGN_RIGHT | wx.BOTTOM, 5)
        self.runButton.Enable(False)

        self.buttons_plot.Add(
            wx.Button(
                self, 2,
                'Cancel'), 0,
            wx.ALIGN_RIGHT)

        self.left_emgSizer.Add(
            self.combobox_plot,
            0, wx.EXPAND | wx.ALL, 10)
        self.left_emgSizer.Add(
            self.save_plot,
            0, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 10)
        self.right_emgSizer.Add(
            self.buttons_plot,
            1, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)

        self.plot_sizer.Add(
            self.left_emgSizer, 0,
            wx.EXPAND | wx.BOTTOM, 10)
        self.plot_sizer.Add(
            self.right_emgSizer, 2,
            wx.EXPAND | wx.ALIGN_RIGHT | wx.BOTTOM, 10)

        self.Bind(wx.EVT_COMBOBOX, self.OnSelCom)
        self.Bind(wx.EVT_CHECKBOX, self.OnSavePlot)
        self.Bind(wx.EVT_BUTTON, self.OnLocal, id=1)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=2)
        self.Bind(wx.EVT_BUTTON, self.OnRun, id=3)

    def CoilTrajGui(self):
        self.left_trajSizer.Add(
            self.noPath_traj, 0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)

        ctrl_size = (60, -1)
        self.x_ctrl = wx.TextCtrl(self, -1, '155.99', size=ctrl_size)
        self.y_ctrl = wx.TextCtrl(self, -1, '112.13', size=ctrl_size)
        self.z_ctrl = wx.TextCtrl(self, -1, '149.12', size=ctrl_size)
        self.ecc_ctrl = wx.TextCtrl(self, -1, '0.75', size=ctrl_size)
        self.radius_ctrl = wx.TextCtrl(self, -1, '40', size=ctrl_size)
        self.pointsdist_ctrl = wx.TextCtrl(self, -1, '20', size=ctrl_size)
        self.txt_sizer.AddMany(
            ((self.x_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.x_ctrl, 0),
             (self.y_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.y_ctrl, 0),
             (self.z_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.z_ctrl, 0),
             (self.ecc_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.ecc_ctrl, 0),
             (self.radius_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.radius_ctrl, 0),
             (self.pointsdist_sta, 0, wx.ALIGN_CENTER_VERTICAL), (self.pointsdist_ctrl, 0)))
        self.left_trajSizer.Add(
            self.txt_sizer, 0,
            wx.ALIGN_CENTER_VERTICAL | wx.TOP, 10)

        self.generateButton = wx.Button(
            self, 4,
            'Generate trajectory',
            size=(175, -1))
        self.generateButton.Enable(False)
        self.left_trajSizer.Add(
            self.generateButton, 0,
            wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)

        combo_surface_name = wx.ComboBox(self, -1, size=(150, -1),
                                         style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if sys.platform != 'win32':
            combo_surface_name.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
        combo_surface_name.Bind(wx.EVT_COMBOBOX, self.OnComboName)
        for n in range(len(self.proj.surface_dict)):
            combo_surface_name.Insert(str(self.proj.surface_dict[n].name), n)
        self.combo_surface_name = combo_surface_name

        self.surf_sizer.Add(
            self.txt_surface, 0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.RIGHT, 5)
        self.surf_sizer.Add(
            combo_surface_name, 0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.LEFT, 5)
        self.right_trajSizer.Add(
            self.surf_sizer, 0,
            wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM, 5
        )

        self.interactor.Enable(1)
        self.interactor.GetRenderWindow().AddRenderer(self.ren)
        self.right_trajSizer.Add(
            self.interactor, 0,
            wx.ALL, 5)

        self.top_sizer.Add(
            self.right_trajSizer, 0,
            wx.ALL, 10)
        self.top_sizer.Add(
            self.left_trajSizer, 0,
            wx.ALL, 10)

        init_surface = 0
        combo_surface_name.SetSelection(init_surface)

        self.bottom_sizer.Add(
            self.progress, 0,
            wx.EXPAND | wx.ALL, 10)

        self.mainTraj_sizer.Add(
            self.top_sizer, 0)
        self.mainTraj_sizer.Add(
            self.bottom_sizer, 0,
            wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)

        self.Bind(wx.EVT_BUTTON, self.OnGen2d, id=4)

    def init_gui(self):
        self.EmgVisGui()
        self.CoilTrajGui()

        self.main_sizer.Add(
            self.mainTraj_sizer, 1,
            wx.ALL, 10)
        self.main_sizer.Add(
            self.plot_sizer, 0,
            wx.EXPAND | wx.ALL, 10)

        self.SetSizer(self.main_sizer)
        self.main_sizer.Fit(self)
        self.Layout()

    def LoadActor(self):
        """
        Load the selected actor from the project (self.surface) into the scene
        """
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.surface)
        mapper.ScalarVisibilityOff()
        # mapper.ImmediateModeRenderingOn()

        obj_actor = vtk.vtkActor()
        obj_actor.SetMapper(mapper)
        self.obj_actor = obj_actor

        poses_recorded = vtku.Text()
        poses_recorded.SetSize(const.TEXT_SIZE_LARGE)
        poses_recorded.SetPosition((const.X, const.Y))
        poses_recorded.ShadowOff()
        poses_recorded.SetValue("Poses recorded: ")

        collect_points = vtku.Text()
        collect_points.SetSize(const.TEXT_SIZE_LARGE)
        collect_points.SetPosition((const.X + 0.35, const.Y))
        collect_points.ShadowOff()
        collect_points.SetValue("0")
        self.collect_points = collect_points

        self.ren.AddActor(obj_actor)
        self.ren.AddActor(poses_recorded.actor)
        self.ren.AddActor(collect_points.actor)
        self.ren.ResetCamera()
        self.interactor.Render()

    def RemoveActor(self):
        """
        Remove the actors from the scene
        """
        self.ren.RemoveAllViewProps()
        self.point_coord = []
        self.icp_points = []
        self.m_icp = None
        self.SetProgress(0)
        self.ren.ResetCamera()
        self.interactor.Render()

    def OnComboName(self, evt):
        """
        Select an available surface
        """
        surface_name = evt.GetString()
        surface_index = evt.GetSelection()
        self.surface = self.proj.surface_dict[surface_index].polydata
        if self.obj_actor:
            self.RemoveActor()
        self.LoadActor()
        self.noPath_traj.Destroy()
        self.generateButton.Enable(True)

    def SetProgress(self, progress):
        """
        Set the progress of the gauge

        Args:
            progress: progress percentage
        """
        self.progress.SetValue(progress * 100)
        self.interactor.Render()

    def OnGen2d(self, evt):
        """
        Generate the 2D ellipse trajectory
        """
        self.RemoveActor()
        self.LoadActor()

        print('Generating coil trajectory')
        self.x_marker, self.y_marker, x_path, y_path, data = spiralTMS.ellipse_path(
            x_hotspot=float(self.x_ctrl.GetValue()),
            y_hotspot=float(self.y_ctrl.GetValue()),
            z_hotspot=float(self.z_ctrl.GetValue()),
            e=float(self.ecc_ctrl.GetValue()),
            size=float(self.radius_ctrl.GetValue()),
            distance=float(self.pointsdist_ctrl.GetValue()))
        spiralTMS.info(data)

        print('Adding markers')
        self.SetProgress(0.1)
        for index in range(len(self.x_marker)):
            current_coord = [float(self.x_marker[index]),
                             -float(self.y_marker[index]),
                             float(self.z_ctrl.GetValue())]
            self.ICP(current_coord)
            self.SetProgress(index / len(self.x_marker))
        self.collect_points.SetValue(str(len(self.x_marker)))
        self.interactor.Render()
        self.SetProgress(1)

        for i in range(len(self.icp_points)):
            img_coord = self.icp_points[i][0], -self.icp_points[i][1], self.icp_points[i][2], None, None, None
            Publisher.sendMessage('Create marker', coord=img_coord, colour=(1, 1, 0))

    def OnSelCom(self, evt):
        """
         Select the serial port to connect the EMG
        """
        self.portIndex = evt.GetSelection()
        self.runButton.Enable(True)

    def OnLocal(self, evt):
        """
         Select the destination path to save de trig. est. plots
        """
        with wx.FileDialog(self, 'Save EMG plots',
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.location = fileDialog.GetPath()
            print(f'saving plot estimulations as {self.location}')

    def OnSavePlot(self, evt):
        """
        To save the triggered estimulation plots
        """
        if self.saveplot_check.GetValue():
            self.localButton.Enable(True)
            self.savePlot = True
        else:
            self.localButton.Enable(False)
            self.savePlot = False

    def OnCancel(self, evt):
        """
        Close dialog
        """
        print('Closing automated motor maping dialog')
        self.Close(True)

    def OnRun(self, evt):
        """
        Run de quasi-realtime emg visualization dialog
        """
        print('Run realtime EMG plot...')
        try:
            serialPort = serial.Serial(
                port=self.ports[self.portIndex],
                baudrate=9600,
                bytesize=8)
            emgPlot = emg.EmgThread(port=serialPort)
            emgPlot.start()
            emg.Plotter(
                savePlot=self.savePlot,
                saveLocation=self.location,
                showTrigger=True)
            serialPort.close()
        except SerialException:
            print('Unable to access this serial port')
        except TypeError:
            print('Select an available serial port')

    def ICP(self, coord):
        """
        Apply ICP transforms to fit the espiral points to the surface

        Args:
            coord: raw coordinates to apply ICP
        """
        sourcePoints = np.array(coord)
        sourcePoints_vtk = vtk.vtkPoints()
        for i in range(len(sourcePoints)):
            id0 = sourcePoints_vtk.InsertNextPoint(sourcePoints)
        source = vtk.vtkPolyData()
        source.SetPoints(sourcePoints_vtk)

        icp = vtk.vtkIterativeClosestPointTransform()
        icp.SetSource(source)
        icp.SetTarget(self.surface)

        icp.GetLandmarkTransform().SetModeToRigidBody()
        # icp.GetLandmarkTransform().SetModeToAffine()
        icp.DebugOn()
        icp.SetMaximumNumberOfIterations(250)
        icp.Modified()
        icp.Update()

        self.m_icp = self.vtkmatrix2numpy(icp.GetMatrix())

        icpTransformFilter = vtk.vtkTransformPolyDataFilter()
        icpTransformFilter.SetInputData(source)
        icpTransformFilter.SetTransform(icp)
        icpTransformFilter.Update()

        transformedSource = icpTransformFilter.GetOutput()
        for i in range(transformedSource.GetNumberOfPoints()):
            p = [0, 0, 0]
            transformedSource.GetPoint(i, p)
            self.icp_points.append(p)
            point = vtk.vtkSphereSource()
            point.SetCenter(p)
            point.SetRadius(2)
            point.SetPhiResolution(3)
            point.SetThetaResolution(3)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(point.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor((1, 1, 0))
            self.ren.AddActor(actor)
            self.interactor.Render()

    @staticmethod
    def vtkmatrix2numpy(matrix):
        """
        Copies the elements of a vtkMatrix4x4 into a numpy array.
        param matrix: The matrix to be copied into an array.

        Args:
            matrix: vtk type matrix
        """
        m = np.ones((4, 4))
        for i in range(4):
            for j in range(4):
                m[i, j] = matrix.GetElement(i, j)
        return m


class MyApp(wx.App):
    def OnInit(self):
        self.dlg = MotorMapGui(None)
        self.SetTopWindow(self.dlg)
        self.dlg.Show()
        return True


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
