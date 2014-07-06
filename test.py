#!/usr/local/bin/python3

# mplWindow, a wrapper around matplotlib for GUI applications using tkinter
# Copyright (C) 2014 Alex Zylstra

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'Alex Zylstra'

from mplWindow import Plot
import numpy as np
import tkinter as tk
import tkinter.ttk as ttk
import matplotlib

class TestApp(tk.Toplevel):
    """docstring for TestApp"""
    def __init__(self):
        super(TestApp, self).__init__()
        self.__createWidgets__()

        # add a key binding to close:
        self.bind('<Escape>', self.close)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def __createWidgets__(self, *args):
        label1 = ttk.Label(self, text='Test #1')
        label1.grid(row=0, column=0)
        button1 = ttk.Button(self, text='Plot1', command=self.__plot1__)
        button1.grid(row=0, column=1)
        button1 = ttk.Button(self, text='Hist', command=self.__plot2__)
        button1.grid(row=0, column=2)

    def __plot1__(self, *args):
        data = np.asarray([[1,2,3],[1,2,3]])
        bar = Plot(data, xlabel='foo', ylabel='bar')

    def __plot2__(self, *args):
        data = np.asarray([1,2,3,2,2,2,1,1,1,1,2,3,2,2,2,2,2,1])
        bar = Plot(data, plotType=Plot.TYPE_HISTOGRAM, xlabel='foo', ylabel='bar')

    def close(self, *args):
        """Handle closing the application."""
        matplotlib.pyplot.close("all")
        self.withdraw()
        self.quit()
        
root = tk.Tk()
root.withdraw()
TestApp()
root.mainloop()

