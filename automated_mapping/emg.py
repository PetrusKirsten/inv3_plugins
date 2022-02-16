# -*- coding: utf-8 -*-
import os
import csv
import sys
import glob
import serial
import threading
import numpy as np
import keyboard as kb
import pyqtgraph as pg
from scipy import signal
from pandas import Series
from pandas import read_csv
from matplotlib import pyplot as plt
from pyqtgraph.Qt import QtGui, QtCore
global staticTrigger


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


def save_static(x, y, saveLocation):
    from datetime import datetime
    plt.style.use('dark_background')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude Signal [mV]')
    plt.ylim(-0.01, 0.01)
    plt.title(datetime.now().strftime('Triggered signal at %d-%m-%Y %H:%M:%S'))
    plt.plot(
        x, y, linewidth=2,
        color='#48C9B0'
    )
    if saveLocation is None:
        plt.savefig('triggered-signal_' + datetime.now().strftime("%d%m%Y%H%M%S") + '.png')
        plt.close()
    else:
        plt.savefig(saveLocation + '_' + datetime.now().strftime("%d%m%Y%H%M%S") + '.png')
        plt.close()


class Plotter:
    def __init__(
            self,
            winSize=500,
            savePlot=False,
            saveLocation=None,
            rawSignal=False,
            showTrigger=False
    ):
        global staticTrigger
        staticTrigger = False
        self.savePlot = savePlot
        self.saveLocation = saveLocation
        self.staticSize = 50
        self.sampFreq = 873
        self.staticSignal = []
        self.showTrigger = showTrigger
        self.rawSignal = rawSignal
        self.winSize = winSize

        # PyQtGraph config
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow()
        self.win.resize(1200, 600)
        self.win.setWindowIcon(QtGui.QIcon('emg-icon.png'))
        self.win.setWindowTitle('EMG')
        self.win.setBackground((18, 18, 18))

        # Emg plot config
        self.emgPlot = self.win.addPlot(colspan=2, title='Electromyography')
        self.emgPlot.setLabel(axis='left', text='Amplitude Signal [mV]')
        self.emgPlot.setLabel(axis='bottom', text='Time [s]')
        self.emgPlot.showGrid(x=True, y=True, alpha=0.15)
        # self.emgPlot.getAxis('bottom').setTickSpacing(0.2, 0.04)
        self.emgPlot.getAxis('left').setTextPen('w')
        self.emgPlot.getAxis('bottom').setTextPen('w')
        self.emgPlot.setYRange(-0.01, 0.01)
        if self.rawSignal:
            self.rawPen = pg.mkPen(color='white', width=0.5)
            self.rawCurve = self.emgPlot.plot(pen=self.rawPen)
        self.emgPen = pg.mkPen(color=(236, 112, 99), width=1)
        self.emgCurve = self.emgPlot.plot(pen=self.emgPen)

        # Emg static plot
        self.win.nextRow()
        self.staticPlot = self.win.addPlot(colspan=2, title='Last triggered EMG signal')
        self.staticPlot.setLabel(axis='left', text='Amplitude Signal [mV]')
        self.staticPlot.setLabel(axis='bottom', text='Time [s]')
        self.staticPlot.showGrid(x=True, y=True, alpha=0.15)
        self.staticPlot.getAxis('left').setTextPen('w')
        self.staticPlot.getAxis('bottom').setTextPen('w')
        self.staticPlot.setYRange(-0.01, 0.01)
        self.staticPen = pg.mkPen(color=(72, 201, 176), width=2.5)
        self.staticCurve = self.staticPlot.plot(pen=self.staticPen)

        # Trigger plot config (if enabled)
        if self.showTrigger:
            self.win.nextRow()
            self.triggerPlot = self.win.addPlot(colspan=2, title='Trigger Signal')
            self.triggerPlot.setLabel(axis='left', text='Amplitude')
            self.triggerPlot.setLabel(axis='bottom', text='Time [ms]')
            self.triggerPlot.showGrid(x=True, y=True, alpha=0.15)
            # self.triggerPlot.getAxis('bottom').setTickSpacing(0.2, 0.04)
            self.triggerPlot.getAxis('left').setTextPen('w')
            self.triggerPlot.getAxis('bottom').setTextPen('w')
            self.triggerPlot.setYRange(0, 1)
            self.triggerPen = pg.mkPen(color=(100, 149, 237), width=5)
            self.triggerCurve = self.triggerPlot.plot(pen=self.triggerPen)

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start()
        QtGui.QApplication.instance().exec_()

    def update(self):
        global staticTrigger
        data = read_csv('data_show.csv')
        time = Series.tolist(data['time [ms]'])
        rawSignal = Series.tolist(data['amplitude [mV] - raw'])
        filterSignal = Series.tolist(data['amplitude [mV] - filtered'])
        triggerSignal = Series.tolist(data['trigger'])

        # Trigger to show the static plot
        if len(self.staticSignal) == self.staticSize and staticTrigger is True:
            staticTime = np.arange(0, len(self.staticSignal)) / self.sampFreq
            if self.savePlot:
                save_static(x=staticTime, y=self.staticSignal, saveLocation=self.saveLocation)
            self.staticSignal = []
        elif staticTrigger:
            self.staticSignal.append(filterSignal[-10])

        # Insert data to plot
        if len(self.staticSignal) == self.staticSize:
            staticTime = np.arange(0, len(self.staticSignal)) / self.sampFreq
            self.staticCurve.setData(staticTime, self.staticSignal)
            staticTrigger = False
        if self.rawSignal:
            self.rawCurve.setData(time[-self.winSize:], rawSignal[-self.winSize:])
        self.emgCurve.setData(time[-self.winSize:], filterSignal[-self.winSize:])
        if self.showTrigger:
            self.triggerCurve.setData(time[-self.winSize:], triggerSignal[-self.winSize:])

        self.app.processEvents()


class EmgThread(threading.Thread):
    def __init__(self, port, winSize=500):
        threading.Thread.__init__(self)
        self.value = ()
        self.tmsFlag = False
        self.calValues = 0
        self.serialValues = 0
        self.winSize = winSize
        self.sampFreq = 873
        self.time = np.array([0])
        self.packets = np.array([])
        self.rawValues = np.array([])
        self.triggerValues = np.zeros(self.winSize)
        self.b, self.a = signal.butter(3, 0.03)
        self.initFilter = signal.lfilter_zi(self.b, self.a)
        self.serialPort = port
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
        global staticTrigger
        if kb.is_pressed('e'):
            if self.tmsFlag is False:
                staticTrigger = True
                self.tmsFlag = True
                self.serialPort.write(b'H')
                self.triggerValues = np.append(self.triggerValues, 1.)
        else:
            self.triggerValues = np.append(self.triggerValues, 0.)
            self.tmsFlag = False

    def readsignal(self):
        if self.serialPort is None:
            pass
        elif self.serialPort.readline():
            try:
                self.value = self.serialPort.readline().decode("utf-8").partition("\r")[0]
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
            try:
                if self.serialPort.inWaiting() > 0:
                    EmgThread.calibsignal(self)
                    plotFilter = EmgThread.filtering(self)
                    EmgThread.trigger(self)
                    self.time = np.append(self.time, self.time[-1] + 1)

                    EmgThread.writer(self, filtered=plotFilter, truncate=False)

                    dataSize = os.path.getsize("data_show.csv")
                    if dataSize > 10000000:
                        EmgThread.truncate(self)
                    EmgThread.writer(self, filtered=plotFilter, truncate=True)

                    self.time = np.delete(self.time, 0, 0)
                    self.rawValues = np.delete(self.rawValues, 0, 0)
                    self.triggerValues = np.delete(self.triggerValues, 0, 0)
            except serial.serialutil.SerialException:
                pass


if __name__ == '__main__':
    emg = EmgThread(port='COM4')
    emg.start()
    Plotter(showTrigger=True, savePlot=False)
