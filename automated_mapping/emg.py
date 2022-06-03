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

import locale

locale.setlocale(locale.LC_ALL, 'en_GB')

from pandas import Series
from pandas import read_csv
from matplotlib import pyplot as plt
from pyqtgraph.Qt import QtGui, QtCore

from pubsub import pub as Publisher

global staticTrigger


def serial_ports():
    """
    List serial port names

    Returns:
        object: A list of the serial ports available on the system
    Raises:
        EnviromentError: On unsupported or unknown platforms
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
    """
    Save last triggered estimulation plot

    Args:
        x: time values
        y: signal amplitude values
        saveLocation: local path to save the files
    """
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
            winSize=2000,
            savePlot=False,
            saveLocation=None,
            rawSignal=False,
            showTrigger=False):
        """
        Read stimulation data in csv and plot in quasi-real time

        Args:
            winSize: size of showing plot
            savePlot: flag to save or not the last triggered stimulation
            saveLocation: local path to save the plot
            rawSignal: flag to show the raw signal data
            showTrigger: flag to show the trigger plot
        """

        # Args vars
        self.winSize = winSize
        self.savePlot = savePlot
        self.saveLocation = saveLocation
        self.rawSignal = rawSignal
        self.showTrigger = showTrigger

        global staticTrigger
        staticTrigger = False

        # Signal vars
        self.sampFreq = 256
        self.staticSize = 50
        self.peakSignal = 0
        self.textPeak = ''
        self.staticSignal = []
        self.staticTime = []

        # Plots vars
        self.emgPlot = None
        self.emgPen = None
        self.emgCurve = None
        self.rawPen = None
        self.rawCurve = None
        self.staticPlot = None
        self.staticPen = None
        self.staticCurve = None
        self.triggerPlot = None
        self.triggerPen = None
        self.triggerCurve = None

        # Data vars
        self.data = None
        self.time = None
        self.filterSignal = None
        self.triggerSignal = None

        # PyQt vars
        self.app = None
        self.win = None

        self.init_pyqt()

    def init_pyqt(self):
        # PyQtGraph config
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow()
        self.win.resize(600, 800)
        # self.win.setWindowIcon(QtGui.QIcon('emg-icon.png'))
        self.win.setWindowTitle('EMG')
        self.win.setBackground((18, 18, 18))

        self.plotConfig('emg')

        self.win.nextRow()
        self.plotConfig('static')

        if self.showTrigger:
            self.win.nextRow()
            self.plotConfig('trigger')

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start()
        QtGui.QApplication.instance().exec_()

    def plotConfig(self, plot: str):
        if plot == 'emg':
            self.emgPlot = self.win.addPlot(colspan=2, title='Electromyography')
            self.emgPlot.setLabel(axis='left', text='Amplitude Signal [mV]')
            self.emgPlot.setLabel(axis='bottom', text='Time [s]')
            self.emgPlot.showGrid(x=True, y=True, alpha=0.15)
            self.emgPlot.getAxis('bottom').setTickSpacing(0.5, 0.1)
            self.emgPlot.getAxis('left').setTextPen('w')
            self.emgPlot.getAxis('bottom').setTextPen('w')
            self.emgPlot.setYRange(200, 400)
            if self.rawSignal:
                self.rawPen = pg.mkPen(color='white', width=0.5)
                self.rawCurve = self.emgPlot.plot(pen=self.rawPen)
            self.emgPen = pg.mkPen(color=(236, 112, 99), width=1)
            self.emgCurve = self.emgPlot.plot(pen=self.emgPen)

        if plot == 'static':
            self.staticPlot = self.win.addPlot(colspan=2, title='Last triggered EMG signal')
            self.staticPlot.setLabel(axis='left', text='Amplitude Signal')
            self.staticPlot.setLabel(axis='bottom', text='Time [ms]')
            self.staticPlot.showGrid(x=True, y=True, alpha=0.15)
            self.staticPlot.getAxis('left').setTextPen('w')
            self.staticPlot.getAxis('bottom').setTextPen('w')
            self.emgPlot.setYRange(200, 400)
            self.staticPen = pg.mkPen(color=(72, 201, 176), width=2.5)
            self.staticCurve = self.staticPlot.plot(pen=self.staticPen)

        if plot == 'trigger':
            self.triggerPlot = self.win.addPlot(colspan=2, title='Trigger Signal')
            self.triggerPlot.setLabel(axis='left', text='Amplitude')
            self.triggerPlot.setLabel(axis='bottom', text='Time')
            self.triggerPlot.showGrid(x=True, y=True, alpha=0.15)
            # self.triggerPlot.getAxis('bottom').setTickSpacing(0.2, 0.04)
            self.triggerPlot.getAxis('left').setTextPen('w')
            self.triggerPlot.getAxis('bottom').setTextPen('w')
            self.triggerPlot.setYRange(0, 1)
            self.triggerPen = pg.mkPen(color=(100, 149, 237), width=5)
            self.triggerCurve = self.triggerPlot.plot(pen=self.triggerPen)

    def peakMEP(self):
        self.peakSignal = max(self.staticSignal)  # Find de MEP peak
        self.textPeak = pg.TextItem(text=f'MEP peak: {self.peakSignal:.2f}')
        self.textPeak.setParentItem(self.staticCurve)
        self.textPeak.setPos(self.staticTime[-50], self.peakSignal)

    def curveConfig(self):
        if self.rawSignal:
            self.rawCurve.setData(self.time[-self.winSize:], self.rawSignal[-self.winSize:])

        self.emgCurve.setData(self.time[-self.winSize:], self.filterSignal[-self.winSize:])

        if self.showTrigger:
            self.triggerCurve.setData(self.time[-self.winSize:], self.triggerSignal[-self.winSize:])

    def update(self):
        """
        Update the data in plot
        """
        global staticTrigger
        self.data = read_csv('data_show.csv')
        self.time = Series.tolist(self.data['time'])
        self.rawSignal = Series.tolist(self.data['amplitude - raw'])
        self.filterSignal = Series.tolist(self.data['amplitude - filtered'])
        self.triggerSignal = Series.tolist(self.data['trigger'])

        # Trigger to show the static plot TODO: make a function
        if len(self.staticSignal) == self.staticSize and staticTrigger is True:
            self.staticTime = []

            if self.savePlot:
                save_static(x=self.staticTime, y=self.staticSignal, saveLocation=self.saveLocation)

            self.staticSignal = []

        elif staticTrigger:
            self.staticSignal.append(self.filterSignal[-10])
            self.staticTime.append(self.time[-10])

        # Insert data to static plot
        if len(self.staticSignal) == self.staticSize:
            # EMG static signal to show
            self.staticCurve.setData(self.staticTime, self.staticSignal)

            self.peakMEP()  # Show the MEP peak

            staticTrigger = False

        self.curveConfig()

        self.app.processEvents()


class EmgThread(threading.Thread):
    def __init__(self, port, winSize=2000):
        """
        Read and store the emg signals to a .csv fil

        Args:
            port: serial port to connect with emg/arduino
            winSize: size of showing plot
        """
        threading.Thread.__init__(self)
        self.serialPort = port
        self.winSize = winSize

        self.coilAtTarger = False
        self.triggerFlag = True
        self.sampFreq = 256
        self.value = ()
        self.calValues = 0
        self.serialValues = 0

        self.packets = np.array([])
        self.time = np.array([0])
        self.rawValues = np.array([])
        self.triggerValues = np.zeros(self.winSize)

        self.fieldnames = [
            'time',
            'amplitude - raw',
            'amplitude - filtered',
            'trigger'
        ]
        with open('data_all.csv', 'w') as self.csv_file:
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
            self.csv_writer.writeheader()
        with open('data_show.csv', 'w') as self.csv_file:
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
            self.csv_writer.writeheader()

        self.__bind_events()

    def __bind_events(self):
        Publisher.subscribe(self.CoilAtTarget, 'Coil at target')

    def CoilAtTarget(self, state):
        self.coilAtTarger = state

    def trigger(self):
        """
        Send a square signal to arduino to locate stimulations
        """
        global staticTrigger

        staticTrigger = True
        self.serialPort.write(b'H')
        self.triggerValues = np.append(self.triggerValues, 1.)

    def readsignal(self):
        """
        Read the serial signals
        """
        if self.serialPort is None:
            pass
        elif self.serialPort.readline():
            try:
                self.value = self.serialPort.readline().decode("utf-8").partition("\r")[0]
            except ValueError:
                self.value = 0
                pass

    def calibsignal(self):
        """
        Read the firsts serial signals
        """
        offsetMean = np.mean(self.rawValues)
        line = self.serialPort.readline()
        if line:
            self.value = line.decode("utf-8").partition("\r")[0]
            if self.value != '' and self.value != '\n' and len(self.value) <= 3:
                self.serialValues = float(self.value)
                self.calValues = 3125 * self.serialValues / 1023
                # self.calValues = self.serialValues
                self.rawValues = np.append(self.rawValues, self.calValues)
                self.calValues = self.rawValues - offsetMean
                # self.calValues = self.rawValues

    def filtering(self):
        """
        Filter the data

        Returns: an array with filtered values
        """
        fNyq = 0.5 * self.sampFreq

        b, a = signal.butter(5, 4 / fNyq, 'lowpass')
        filterValues = signal.filtfilt(b, a, self.calValues)

        return filterValues

    def truncate(self):
        """
        Truncate the data in csv file
        """
        with open('data_show.csv', 'r+') as self.csv_file:
            self.csv_file.truncate(0)
        with open('data_show.csv', 'w') as self.csv_file:
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
            self.csv_writer.writeheader()

    def writer(self, truncate: bool, filtered):
        """
        Config and write the reading signals in csv file

        Args:
            truncate: flag to truncate data
            filtered: filtered data
        """
        if not truncate:
            with open('data_all.csv', 'a') as self.csv_file:
                self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
                info = {
                    'time': self.time[-1],
                    'amplitude - raw': self.calValues[-1],
                    'amplitude - filtered': filtered[-1],
                    'trigger': self.triggerValues[-1]
                }
                self.csv_writer.writerow(info)

        if truncate:
            with open('data_show.csv', 'a') as self.csv_file:
                self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
                info = {
                    'time': self.time[-1],
                    'amplitude - raw': self.calValues[-1],
                    'amplitude - filtered': filtered[-1],
                    'trigger': self.triggerValues[-1]
                }
                self.csv_writer.writerow(info)

        if type(truncate) is not bool:
            print(TypeError)

    def run(self):
        """
        Run the reading as a thread class
        """
        while np.size(self.rawValues) < self.winSize:
            if self.serialPort.inWaiting() > 0:
                EmgThread.readsignal(self)
            # self.calValues = 0.125 * self.serialValues / 1023
            self.calValues = self.serialValues
            self.rawValues = np.append(self.rawValues, self.calValues)

        while True:
            try:
                if self.serialPort.inWaiting() > 0:
                    EmgThread.calibsignal(self)
                    plotFilter = EmgThread.filtering(self)

                    if self.coilAtTarger and self.triggerFlag:
                        print('Send trigger')
                        EmgThread.trigger(self)
                        self.triggerFlag = False
                    elif self.coilAtTarger:
                        self.triggerValues = np.append(self.triggerValues, 0.)
                    else:
                        self.triggerValues = np.append(self.triggerValues, 0.)
                        self.triggerFlag = True

                    self.time = np.append(self.time, self.time[-1] + 1 / self.sampFreq)

                    EmgThread.writer(self, filtered=plotFilter, truncate=False)

                    dataSize = os.path.getsize("data_show.csv")

                    if dataSize > 10**7:
                        EmgThread.truncate(self)

                    EmgThread.writer(self, filtered=plotFilter, truncate=True)

                    self.time = np.delete(self.time, 0, 0)
                    self.rawValues = np.delete(self.rawValues, 0, 0)
                    self.triggerValues = np.delete(self.triggerValues, 0, 0)

            except serial.serialutil.SerialException:
                pass


if __name__ == '__main__':
    serialPort = serial.Serial(
        port='COM3',
        baudrate=9600,
        bytesize=8)

    emgPlot = EmgThread(port=serialPort)
    emgPlot.start()

    Plotter(
        savePlot=False,
        showTrigger=True,
        rawSignal=True)
