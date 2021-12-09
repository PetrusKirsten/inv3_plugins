# -*- coding: utf-8 -*-
import os
import csv
import serial
import threading
import matplotlib
import numpy as np
import pandas as pd
import keyboard as kb
from scipy import signal
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class Plotter:
    def __init__(self, winSize=2000):
        matplotlib.use('TkAgg')
        plt.style.use('dark_background')
        self.winSize = winSize
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, figsize=(15, 5))

    def run(self):
        def animate(i):
            try:
                data = pd.read_csv('data_show.csv')
                x = data['time [ms]']
                y1 = data['amplitude [mV] - raw']
                y2 = data['amplitude [mV] - filtered']
                y3 = data['trigger']

                # EMG subplot config
                self.ax1.cla()
                self.ax1.set_ylim([-0.25, 0.25])
                self.ax1.plot(
                    x[-self.winSize:-1], y1[-self.winSize:-1],
                    linewidth=1, alpha=0.5, color='grey', label='EMG'
                )
                self.ax1.plot(
                    x[-self.winSize:-1], y2[-self.winSize:-1],
                    linewidth=2, alpha=1, color='coral', label='EMG filter'
                )
                self.ax1.grid(axis='x', color='gray', linewidth=0.5)
                self.ax1.legend(loc='lower left')

                # Trigger subplot config
                self.ax2.cla()
                self.ax2.set_ylim([-0.05, 1.05])
                self.ax2.plot(
                    x[-self.winSize:-1], y3[-self.winSize:-1],
                    linewidth=5, alpha=1, color='aquamarine'
                )

            except pd.errors.EmptyDataError:
                pass

        ani = FuncAnimation(self.fig, animate, interval=0.001)
        plt.tight_layout()
        plt.show()


class EmgThread(threading.Thread):
    def __init__(self, port: str):
        threading.Thread.__init__(self)
        self.tmsFlag = False
        self.sampFreq = 256 * 6
        self.winSize = 2000
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
        # self.offsetMean = None

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
            self.triggerValues = np.append(self.triggerValues, 1.)
            if self.tmsFlag is False:
                self.tmsFlag = True
                self.serialPort.write(b'H')
        else:
            self.triggerValues = np.append(self.triggerValues, 0.)
            self.tmsFlag = False

    def run(self):
        while np.size(self.rawValues) < self.winSize:
            if self.serialPort.inWaiting() > 0:
                line = self.serialPort.readline()
                if line:
                    try:
                        self.value = line.decode("utf-8").partition("\r")[0]
                    except ValueError:
                        self.value = 0
                        pass
                    # if self.value != '' and self.value != '\n' and len(self.value) <= 3:
                    #     self.serialValues = float(self.value)
            # Add signal to an array
            self.calValues = 0.125 * self.serialValues / 1023
            self.rawValues = np.append(self.rawValues, self.calValues)

        offsetMean = np.mean(self.rawValues)

        while True:
            if self.serialPort.inWaiting() > 0:
                line = self.serialPort.readline()
                if line:
                    self.value = line.decode("utf-8").partition("\r")[0]
                    if self.value != '' and self.value != '\n' and len(self.value) <= 3:
                        self.serialValues = float(self.value)
                        # Calibrate the signal: 0-1023 => 0,250 mV p-p
                        self.calValues = 0.125 * self.serialValues / 1023
                        self.rawValues = np.append(self.rawValues, self.calValues)
                        self.calValues = self.rawValues - offsetMean

                        # TODO: Filtering
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

                        EmgThread.trigger(self)

                        # Add the counting of read signals
                        self.time = np.append(self.time, self.time[-1] + (self.sampFreq ** (-1)))

                        with open('data_all.csv', 'a') as self.csv_file:
                            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
                            info = {
                                'time [ms]': self.time[-1],
                                'amplitude [mV] - raw': self.calValues[-1],
                                'amplitude [mV] - filtered': plotFilter[-1],
                                'trigger': self.triggerValues[-1]
                            }
                            self.csv_writer.writerow(info)

                        size = os.path.getsize("data_show.csv")
                        if size > 10000000:
                            with open('data_show.csv', 'r+') as self.csv_file:
                                self.csv_file.truncate(0)
                            with open('data_show.csv', 'w') as self.csv_file:
                                self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
                                self.csv_writer.writeheader()

                        with open('data_show.csv', 'a') as self.csv_file:
                            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
                            info = {
                                'time [ms]': self.time[-1],
                                'amplitude [mV] - raw': self.calValues[-1],
                                'amplitude [mV] - filtered': plotFilter[-1],
                                'trigger': self.triggerValues[-1]
                            }
                            self.csv_writer.writerow(info)

                        self.time = np.delete(self.time, 0, 0)
                        self.rawValues = np.delete(self.rawValues, 0, 0)
                        self.triggerValues = np.delete(self.triggerValues, 0, 0)


emg = EmgThread(port='COM3')
plot = Plotter()

emg.start()
plot.run()
