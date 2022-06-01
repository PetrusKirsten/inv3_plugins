import wx  # pandas only works with wxPython 4.0.7
import vtk
import sys
import serial
import numpy as np
from serial import SerialException

from . import emg
from . import spiralTMS

from pubsub import pub as Publisher
from vtkmodules.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

import invesalius.project as prj
import invesalius.constants as const
import invesalius.data.vtk_utils as vtku
import invesalius.data.coregistration as dcr
from invesalius.navigation import navigation
from invesalius.navigation import icp


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

        self.saveplot_check = wx.CheckBox(self, -1, 'Save the motor evoked potential')
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
        self.txt_sizer = wx.FlexGridSizer(6, 2, 7, 10)
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
        self.sendButton = None
        self.sendIndex = 0
        self.x_marker = None
        self.y_marker = None

        self.txt_surface = wx.StaticText(self, -1, 'Select the surface:')
        self.x_sta = wx.StaticText(self, -1, 'X axis hotspot:')
        self.y_sta = wx.StaticText(self, -1, 'Y axis hotspot:')
        self.z_sta = wx.StaticText(self, -1, 'Z axis hotspot:')
        self.ecc_sta = wx.StaticText(self, -1, 'Ellipse eccentricity:')
        self.radius_sta = wx.StaticText(self, -1, 'Max ellipse radius [mm]:')
        self.pointsdist_sta = wx.StaticText(self, -1, 'Points distance [mm]:')
        self.progress = wx.Gauge(self, -1)

        # ICP variables
        self.obj_actor = None
        self.polydata = None
        self.surface = None
        self.combo_surface_name = None
        self.collect_points = None
        self.m_icp = None
        self.ActorCollection = vtk.vtkActorCollection()

        self.staticballs = []
        self.point_coord = []
        self.icp_points = []
        self.obj_orients = np.full([5, 3], np.nan)
        self.obj_fiducials = np.full([5, 3], np.nan)

        self.interactor = wxVTKRenderWindowInteractor(self, -1, size=[800, 600])
        self.ren = vtk.vtkRenderer()
        self.proj = prj.Project()

        self.init_gui()

        self.__bind_events()

    def __bind_events(self):
        Publisher.subscribe(self.CoilAtTarget, 'Coil at target')

    def CoilAtTarget(self, state):
        self.coil_at_target = state

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
            wx.EXPAND | wx.BOTTOM, 10)

        self.Bind(wx.EVT_COMBOBOX, self.OnSelCom)
        self.Bind(wx.EVT_CHECKBOX, self.OnSavePlot)
        self.Bind(wx.EVT_BUTTON, self.OnLocal, id=1)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=2)
        self.Bind(wx.EVT_BUTTON, self.OnRun, id=3)

    def CoilTrajGui(self):
        ctrl_size = (60, -1)
        self.x_ctrl = wx.TextCtrl(self, -1, '155.99', size=ctrl_size)
        self.y_ctrl = wx.TextCtrl(self, -1, '112.13', size=ctrl_size)
        self.z_ctrl = wx.TextCtrl(self, -1, '149.12', size=ctrl_size)
        self.ecc_ctrl = wx.TextCtrl(self, -1, '0.75', size=ctrl_size)
        self.radius_ctrl = wx.TextCtrl(self, -1, '40', size=ctrl_size)
        self.pointsdist_ctrl = wx.TextCtrl(self, -1, '20', size=ctrl_size)
        self.txt_sizer.AddMany(
            ((self.x_sta, 0), (self.x_ctrl, 0),
             (self.y_sta, 0), (self.y_ctrl, 0),
             (self.z_sta, 0), (self.z_ctrl, 0),
             (self.ecc_sta, 0), (self.ecc_ctrl, 0),
             (self.radius_sta, 0), (self.radius_ctrl, 0),
             (self.pointsdist_sta, 0), (self.pointsdist_ctrl, 0)))
        self.left_trajSizer.Add(
            self.txt_sizer, 0)

        self.generateButton = wx.Button(
            self, 4,
            'Generate trajectory',
            size=(175, -1))
        self.generateButton.Enable(False)
        self.left_trajSizer.Add(
            self.generateButton, 0, wx.TOP, 5)

        self.sendButton = wx.Button(
            self, 5,
            'Send to robot')
        self.sendButton.Enable(False)
        self.left_trajSizer.Add(
            self.sendButton, 0, wx.TOP, 5)

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
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.surf_sizer.Add(
            combo_surface_name, 0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.right_trajSizer.Add(
            self.surf_sizer, 0, wx.TOP | wx.BOTTOM, 5)

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
            wx.EXPAND)

        self.Bind(wx.EVT_BUTTON, self.OnGen2d, id=4)
        self.Bind(wx.EVT_BUTTON, self.OnSend, id=5)

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
        self.generateButton.Enable(True)

    def OnGen2d(self, evt):
        """
        Generate the 2D ellipse trajectory
        """
        print('Generating coil trajectory')
        self.SetProgress(0.1)

        self.RemoveActor()
        self.LoadActor()

        self.x_marker, self.y_marker, _, _, data = spiralTMS.ellipse_path(
            x_hotspot=float(self.x_ctrl.GetValue()),
            y_hotspot=float(self.y_ctrl.GetValue()),
            z_hotspot=float(self.z_ctrl.GetValue()),
            e=float(self.ecc_ctrl.GetValue()),
            size=float(self.radius_ctrl.GetValue()),
            distance=float(self.pointsdist_ctrl.GetValue()))
        spiralTMS.info(data)

        print('Adding markers')
        self.spiral()

        self.collect_points.SetValue(str(len(self.x_marker)))
        self.interactor.Render()
        self.sendButton.Enable(True)

        self.SetProgress(1)

    def OnSend(self, evt):
        """
        Send individually each coordinate to robot system
        """
        self.SendTarget()

        self.SetProgress((self.sendIndex + 1) / (len(self.icp_points)))
        self.sendIndex += 1
        if self.sendIndex >= len(self.icp_points):
            print('All coordinates sent')
            self.sendButton.Enable(False)

        if self.coil_at_target:
            print("Send trigger")
        else:
            print("Coil not at target")

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
                showTrigger=True,
                rawSignal=True)
            serialPort.close()
        except SerialException:
            print('Unable to access this serial port')
        except TypeError:
            print('Select an available serial port')

    def SetProgress(self, progress):
        """
        Set the progress of the gauge

        Args:
            progress: progress percentage
        """
        self.progress.SetValue(progress * 100)
        self.interactor.Render()

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
        poses_recorded.SetValue('Poses generated: ')

        collect_points = vtku.Text()
        collect_points.SetSize(const.TEXT_SIZE_LARGE)
        collect_points.SetPosition((const.X + 0.35, const.Y))
        collect_points.ShadowOff()
        collect_points.SetValue('0')
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

    def ICP(self, coord):
        """
        Apply ICP transforms to fit the spiral points to the surface

        Args:
            coord: raw coordinates to apply ICP
        """
        sourcePoints = np.array(coord)
        sourcePoints_vtk = vtk.vtkPoints()
        for i in range(len(sourcePoints)):
            id0 = sourcePoints_vtk.InsertNextPoint(sourcePoints)
        source = vtk.vtkPolyData()
        source.SetPoints(sourcePoints_vtk)

        if float(self.x_ctrl.GetValue()) > 100.0:
            transform = vtk.vtkTransform()
            transform.Translate(
                float(self.x_ctrl.GetValue()),
                -float(self.y_ctrl.GetValue()),
                float(self.z_ctrl.GetValue()))
            transform.RotateY(35)
            transform.Translate(
                -float(self.x_ctrl.GetValue()),
                float(self.y_ctrl.GetValue()),
                -float(self.z_ctrl.GetValue()))

        if float(self.x_ctrl.GetValue()) <= 100.00:
            transform = vtk.vtkTransform()
            transform.Translate(
                float(self.x_ctrl.GetValue()),
                -float(self.y_ctrl.GetValue()),
                float(self.z_ctrl.GetValue()))
            transform.RotateY(-35)
            transform.Translate(
                -float(self.x_ctrl.GetValue()),
                float(self.y_ctrl.GetValue()),
                -float(self.z_ctrl.GetValue()))

        transform_filt = vtk.vtkTransformPolyDataFilter()
        transform_filt.SetTransform(transform)
        transform_filt.SetInputData(source)
        transform_filt.Update()

        source_points = transform_filt.GetOutput()

        icp = vtk.vtkIterativeClosestPointTransform()
        icp.SetSource(source_points)
        icp.SetTarget(self.surface)

        icp.GetLandmarkTransform().SetModeToRigidBody()
        # icp.GetLandmarkTransform().SetModeToAffine()
        icp.DebugOn()
        icp.SetMaximumNumberOfIterations(100)
        icp.Modified()
        icp.Update()

        self.m_icp = self.vtkmatrix2numpy(icp.GetMatrix())

        icpTransformFilter = vtk.vtkTransformPolyDataFilter()
        icpTransformFilter.SetInputData(source_points)
        icpTransformFilter.SetTransform(icp)
        icpTransformFilter.Update()

        transformedSource = icpTransformFilter.GetOutput()
        p = [0, 0, 0]
        transformedSource.GetPoint(0, p)
        # source_points.GetPoint(0, p)
        point = vtk.vtkSphereSource()
        point.SetCenter(p)
        point.SetRadius(1.5)
        point.SetPhiResolution(10)
        point.SetThetaResolution(10)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(point.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor((0, 0, 1))

        self.ren.AddActor(actor)
        self.ActorCollection.AddItem(actor)
        self.interactor.Render()

        p[1] = -p[1]
        self.icp_points.append(p)

    def spiral(self):
        for index in range(len(self.x_marker)):
            current_coord = [float(self.x_marker[index]),
                             -float(self.y_marker[index]),
                             float(self.z_ctrl.GetValue())]
            self.ICP(current_coord)
            self.SetProgress(index / len(self.x_marker))

    def SendTarget(self):
        """
        Update robot target to the next spiral coordinate
        """
        if self.sendIndex > 0:
            pastCoord = self.ActorCollection.GetItemAsObject(self.sendIndex - 1)
            pastCoord.GetProperty().SetColor((0, 1, 0))
        actualCoord = self.ActorCollection.GetItemAsObject(self.sendIndex)
        actualCoord.GetProperty().SetColor((1, 1, 0))
        self.interactor.Render()

        coord = (self.icp_points[self.sendIndex][0],
                 self.icp_points[self.sendIndex][1],
                 self.icp_points[self.sendIndex][2],
                 0, 1, 1)

        Publisher.sendMessage('Create marker', coord=coord, colour=[0, 0, 1])
        Publisher.sendMessage('Define target')
        Publisher.sendMessage('Target navigation mode', target_mode=True)

        # target = dcr.image_to_tracker(
        #     navigation.Navigation().m_change,
        #     self.icp_points[self.sendIndex],
        #     icp.ICP())

        # Publisher.sendMessage('Update robot target',
        #                       robot_tracker_flag=True,
        #                       target_index=0,  # doesnt matter
        #                       target=target.tolist())

        print(f'\n>> Sent #{self.sendIndex + 1} coordinate'
              f'\n>> Target: {self.icp_points[self.sendIndex]}')

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
