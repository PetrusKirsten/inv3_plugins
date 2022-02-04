# -*- coding: utf-8 -*-
import os
import csv
import sys
import glob
import serial
import threading
import matplotlib
import numpy as np
import pandas
# from pandas import read_csv
import keyboard as kb
import pyqtgraph as pg
from scipy import signal
import matplotlib.pyplot as plt
# from pandas import Series as Sr
from pyqtgraph.Qt import QtGui, QtCore
from matplotlib.animation import FuncAnimation


def serial_ports():
    """ Lists serial port names
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class Plotter:
    def __init__(self, winSize=5000, speed=4, rawSignal=False, showTrigger=False):
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow()
        self.win.resize(1200, 400)
        self.win.setWindowIcon(QtGui.QIcon('emg-icon.png'))
        self.win.setWindowTitle('EMG')
        self.win.setBackground((18, 18, 18))

        self.winSize = winSize
        self.speed = speed
        self.rawSignal = rawSignal
        self.showTrigger = showTrigger

        self.emgPlot = self.win.addPlot(colspan=2, title='Electromyography')
        self.emgPlot.setLabel(axis='left', text='Amplitude Signal [mV]')
        self.emgPlot.setLabel(axis='bottom', text='Time [ms]')
        self.emgPlot.showGrid(x=True, y=True, alpha=0.15)
        self.emgPlot.getAxis('bottom').setTickSpacing(0.2, 0.04)
        self.emgPlot.getAxis('left').setTextPen('w')
        self.emgPlot.getAxis('bottom').setTextPen('w')
        self.emgPlot.setYRange(-0.1, 0.1)

        if self.showTrigger:
            self.win.nextRow()
            self.triggerPlot = self.win.addPlot(colspan=2, title='Trigger Signal')
            self.triggerPlot.setLabel(axis='left', text='Amplitude')
            self.triggerPlot.setLabel(axis='bottom', text='Time [ms]')
            self.triggerPlot.showGrid(x=True, y=True, alpha=0.15)
            self.triggerPlot.getAxis('bottom').setTickSpacing(0.2, 0.04)
            self.triggerPlot.getAxis('left').setTextPen('w')
            self.triggerPlot.getAxis('bottom').setTextPen('w')
            self.triggerPlot.setYRange(0, 1)

        if self.rawSignal:
            self.rawPen = pg.mkPen(color='gray', width=0.15, alpha=0.35)
            self.rawCurve = self.emgPlot.plot(pen=self.rawPen)
        self.emgPen = pg.mkPen(color=(255, 127, 80), width=1)
        self.emgCurve = self.emgPlot.plot(pen=self.emgPen)
        if self.showTrigger:
            self.triggerPen = pg.mkPen(color=(100, 149, 237), width=5)
            self.triggerCurve = self.triggerPlot.plot(pen=self.triggerPen)

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(speed)

        QtGui.QApplication.instance().exec_()

    def update(self):
        # TODO: alternativa para o pandas
        data = read_csv('data_show.csv')
        time = Sr.tolist(data['time [ms]'])
        rawSignal = Sr.tolist(data['amplitude [mV] - raw'])
        filterSignal = Sr.tolist(data['amplitude [mV] - filtered'])
        triggerSignal = Sr.tolist(data['trigger'])

        if self.rawSignal:
            self.rawCurve.setData(time[-self.winSize:], rawSignal[-self.winSize:])

        self.emgCurve.setData(time[-self.winSize:], filterSignal[-self.winSize:])

        if self.showTrigger:
            self.triggerCurve.setData(time[-self.winSize:], triggerSignal[-self.winSize:])

        self.app.processEvents()


class EmgThread(threading.Thread):
    def __init__(self, port: str, winsize=2000):
        threading.Thread.__init__(self)
        self.tmsFlag = False
        self.sampFreq = 256 * 6
        self.winSize = winsize
        self.b, self.a = signal.butter(3, 0.03)
        self.calValues = 0
        self.initFilter = signal.lfilter_zi(self.b, self.a)
        self.packets = np.array([])
        self.port = port
        self.rawValues = np.array([])
        self.serialValues = 0
        self.time = np.array([0])
        self.triggerValues = np.zeros(self.winSize)
        self.value = ()

        self.serialPort = serial.Serial(
            port=port,
            baudrate=57600,
            bytesize=8
        )
        self.fieldnames = [
            'time [ms]',
            'amplitude [mV] - raw',
            'amplitude [mV] - filtered',
            'trigger'
        ]
        with open('data_all.csv', 'w') as self.csv_file:
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
            self.csv_writer.writeheader()

        with open('data_show.csv', 'w') as self.csv_file:
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
            self.csv_writer.writeheader()

    def trigger(self):
        if kb.is_pressed('e'):
            if self.tmsFlag is False:
                self.tmsFlag = True
                self.serialPort.write(b'H')
                self.triggerValues = np.append(self.triggerValues, 1.)

        else:
            self.triggerValues = np.append(self.triggerValues, 0.)
            self.tmsFlag = False

    def readsignal(self):
        line = self.serialPort.readline()
        if line:
            try:
                self.value = line.decode("utf-8").partition("\r")[0]
            except ValueError:
                self.value = 0
                pass

    def calibsignal(self):
        offsetMean = np.mean(self.rawValues)
        line = self.serialPort.readline()
        if line:
            self.value = line.decode("utf-8").partition("\r")[0]
            if self.value != '' and self.value != '\n' and len(self.value) <= 3:
                self.serialValues = float(self.value)
                self.calValues = 0.125 * self.serialValues / 1023
                self.rawValues = np.append(self.rawValues, self.calValues)
                self.calValues = self.rawValues - offsetMean

    def filtering(self):
        firstFilter, _ = signal.lfilter(
            self.b, self.a,
            self.calValues,
            zi=self.initFilter * self.calValues[0]
        )
        plotFilter, _ = signal.lfilter(
            self.b, self.a,
            firstFilter,
            zi=self.initFilter * firstFilter[0]
        )
        return plotFilter

    def truncate(self):
        with open('data_show.csv', 'r+') as self.csv_file:
            self.csv_file.truncate(0)
        with open('data_show.csv', 'w') as self.csv_file:
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
            self.csv_writer.writeheader()

    def writer(self, truncate: bool, filtered):
        if not truncate:
            with open('data_all.csv', 'a') as self.csv_file:
                self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
                info = {
                    'time [ms]': self.time[-1],
                    'amplitude [mV] - raw': self.calValues[-1],
                    'amplitude [mV] - filtered': filtered[-1],
                    'trigger': self.triggerValues[-1]
                }
                self.csv_writer.writerow(info)

        if truncate:
            with open('data_show.csv', 'a') as self.csv_file:
                self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
                info = {
                    'time [ms]': self.time[-1],
                    'amplitude [mV] - raw': self.calValues[-1],
                    'amplitude [mV] - filtered': filtered[-1],
                    'trigger': self.triggerValues[-1]
                }
                self.csv_writer.writerow(info)

        if type(truncate) is not bool:
            print(TypeError)

    def run(self):
        while np.size(self.rawValues) < self.winSize:
            if self.serialPort.inWaiting() > 0:
                EmgThread.readsignal(self)
            self.calValues = 0.125 * self.serialValues / 1023
            self.rawValues = np.append(self.rawValues, self.calValues)

        while True:
            if self.serialPort.inWaiting() > 0:
                EmgThread.calibsignal(self)
                plotFilter = EmgThread.filtering(self)
                EmgThread.trigger(self)
                self.time = np.append(self.time, self.time[-1] + (self.sampFreq ** (-1)))

                EmgThread.writer(self, filtered=plotFilter, truncate=False)

                dataSize = os.path.getsize("data_show.csv")
                if dataSize > 10000000:
                    EmgThread.truncate(self)
                EmgThread.writer(self, filtered=plotFilter, truncate=True)

                self.time = np.delete(self.time, 0, 0)
                self.rawValues = np.delete(self.rawValues, 0, 0)
                self.triggerValues = np.delete(self.triggerValues, 0, 0)


# def load():
#     app = wx.App()
#     dlg = gui.Dialog(None)
#     dlg.Show()
#     app.MainLoop()

# def load():
#     p = project.Project()
#     g = gui.Dialog(wx.GetApp().GetTopWindow())
#
#     if g.ShowModal() == wx.ID_OK:
#         pass
#
#     g.Destroy()

if __name__ == '__main__':
    emg = EmgThread(port='COM4')
    emg.start()

    # plotlib = MatPlotPlotter()
    # plotlib.run()

    qt = Plotter(rawSignal=True, showTrigger=True)
