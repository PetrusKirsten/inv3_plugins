import time
import random
import pyqtgraph as pg
from collections import deque
from pyqtgraph.Qt import QtGui, QtCore


class Graph:
    def __init__(self, ):
        self.dat = deque()
        self.maxLen = 2000  # max number of data points to show on graph
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow()

        self.p1 = self.win.addPlot(colspan=2)
        self.win.nextRow()
        self.p2 = self.win.addPlot(colspan=2)
        self.win.nextRow()

        self.curve1 = self.p1.plot()
        self.curve2 = self.p2.plot()

        graphUpdateSpeedMs = 0.001
        timer = QtCore.QTimer()  # to create a thread that calls a function at intervals
        timer.timeout.connect(self.update)  # the update function keeps getting called at intervals
        timer.start(graphUpdateSpeedMs)
        QtGui.QApplication.instance().exec_()

    def update(self):
        if len(self.dat) > self.maxLen:
            self.dat.popleft()  # remove oldest
        self.dat.append(random.randint(0, 100))

        self.curve1.setData(self.dat)
        self.curve2.setData(self.dat)
        self.app.processEvents()


if __name__ == '__main__':
    g = Graph()
