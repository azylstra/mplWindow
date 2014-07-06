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

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backend_bases import key_press_handler
import tkinter as tk
from tkinter.messagebox import showinfo
import tkinter.ttk as ttk
import platform

matplotlib.rcParams['toolbar'] = 'None'


class Plot(tk.Toplevel):
    """Implement a plot window, wrapping `matplotlib` with advanced GUI options that allow the user to change most aspects of the plot appearance.

    :param data: The data to plot. Must be `numpy.ndarray`. The required shape varies based on plot type (see above).
    :param plotType: The initial plot type to use.
    :param fmt: Matplotlib-style format strings to use for each series in the data. If left as `None`, default formatting is used. If 
    only one series is provided, `fmt` may be a `str`. If multiple series are provided, then `len(fmt) == len(data)` must be satisfied.
    :param labels: Labels (i.e. names) for each data series. If left as `None`, then default labels ('Series 1', etc) are used. If only
    one series is provided, `labels` may be a `str`. If multiple series are provided, then `len(series) == len(data)` must be satisfied.
    :param xlabel: The label to use for the x axis, must be a `str`
    :param xlabelSize: The font size to use for the x axis
    :param ylabel: The label to use for the y axis, must be a `str`
    :param ylabelSize: The font size to use for the y axis
    :param logX: Use a logarithmic scale for the x axis
    :param logY: Use a logarithmic scale for the y axis
    :param xlim: Limits for the x axis, must be a length-2 `tuple`, `list`, `np.ndarray`
    :param ylim: Limits for the y axis, must be a length-2 `tuple`, `list`, `np.ndarray`
    :param title: The plot title, must be a `str`
    :param titleSize: The font size to use for the plot title
    :param windowTitle: The window title
    :param kwargs: Any additional keyword args will be passed directly to the plot command.

    :author: Alex Zylstra
    :date: 2014-07-06
    """
    __author__ = 'Alex Zylstra'
    __version__ = '0.1'

    TYPE_PLOT = 0
    TYPE_ERRORBAR = 1
    TYPE_BAR = 2
    TYPE_HISTOGRAM = 3
    TYPE_2DHISTOGRAM = 4
    TYPE_CONTOUR = 5
    TYPE_IMAGE = 6
    TYPE_COLORMESH = 7
    TYPE_DATEPLOT = 8
    TYPE_VECTOR = 9

    def __init__(self, data, plotType=TYPE_PLOT, fmt=None, labels=None, 
        xlabel='', xlabelSize=12, ylabel='', ylabelSize=12,
        logX=False, logY=False, xlim=None, ylim=None,
        legend=False, legendLoc=1, legendFontSize=10,
        title='', titleSize=14, windowTitle='mplWindow', **kwargs):
        super(Plot, self).__init__()
        self.title(windowTitle)

        assert isinstance(data, np.ndarray)

        # store keyword args:
        self.kwargs = kwargs
        # Store data:
        self.data = np.copy(data)

        # Format for each series:
        if isinstance(fmt, str):  # for one data series, fmt may be passed as a str
            fmt = [fmt]
        if isinstance(fmt, list) or isinstance(fmt, tuple) and len(fmt) == self.data.shape[0]:
            self.fmt = fmt
        else:
            self.fmt = None

        # Labels for each series:
        if labels is None:  # if nothing was passed, use some default ones:
            if len(self.data.shape) == 2:
                labels = 'Series 1'
            else:
                labels = []
                for i in range(self.data.shape[0]):
                    labels.append('Series ' + str(i+1))
        if isinstance(labels, str):  # for one data series, label may be passed as a str
            labels = [labels]
        if isinstance(labels, list) or isinstance(labels, tuple):
            self.labels = labels

        # Labeling for the plot:
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.xlabelSize = xlabelSize
        self.ylabelSize = ylabelSize
        self.title = title
        self.titleSize = titleSize

        # Limits and scaling stuff:
        self.xlim = xlim
        self.ylim = ylim
        self.logX = tk.BooleanVar()
        self.logX.set(logX)
        self.logX.trace('w', self.__plot__)
        self.logY = tk.BooleanVar()
        self.logY.set(logY)
        self.logY.trace('w', self.__plot__)

        # Legend controls:
        self.legend = tk.BooleanVar()
        self.legend.set(legend)
        self.legendLoc = tk.IntVar()
        self.legendLoc.set(legendLoc)
        self.legendFontSize = tk.IntVar()
        self.legendFontSize.set(legendFontSize)
        self.legend.trace('w', self.__plot__)
        self.legendLoc.trace('w', self.__plot__)
        self.legendFontSize.trace('w', self.__plot__)

        self.menubar = None
        self.fig = None
        self.canvas = None
        self.toolbar = None
        self.frame = tk.Frame(self)
        self.frame.pack()

        self.__initPlot__()
        self.__menubar__(plotType=plotType)
        # add a key binding to close:
        self.bind('<Escape>', self.__close__)
        self.protocol("WM_DELETE_WINDOW", self.__close__)
        self.protocol("WM_STATE_ZOOMED", self.__zoom__)
        self.bind("<Configure>", self.__resize__)

        self.__plot__()

    def __initPlot__(self):
        """Initialization for the matplotlib infrastructure, e.g. setting up the figure and canvas."""
        if plt.get_backend() != 'TkAgg':
            plt.switch_backend('TkAgg')

        if self.fig == None:
            self.fig = matplotlib.pyplot.Figure(figsize=(4,3))
            self.ax = self.fig.add_subplot(111)
        

        if self.canvas is None:
            self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(self.fig, master=self)
            self.canvas.show()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
           
        self.frame.pack()

    def __plot__(self, *args):
        """Generate the plot with current parameters."""
        # clear whatever is there already:
        self.ax.clear()

        # Depending on the plot type requested, we need to do a few different things:
        plotType = self.plotTypeVar.get()
        # Standard plot
        if plotType == self.TYPE_PLOT:
            assert self.data.shape[-2] == 2  # Check the shape of the data, for this type should be 2-D

            # only one series of data
            if len(self.data.shape) == 2:
                if self.fmt is not None:
                    self.ax.plot(self.data[0,:], self.data[1,:], self.fmt[0], label=self.labels[0], **self.kwargs)
                else:
                    self.ax.plot(self.data[0,:], self.data[1,:], label=self.labels[0], **self.kwargs)

            # Loop over every series:
            else:
                for i in range(self.data.shape[0]):
                    if self.fmt is not None:
                        self.ax.plot(self.data[i, 0,:], self.data[i, 1,:], self.fmt[i], label=self.labels[i], **self.kwargs)
                    else:
                        self.ax.plot(self.data[i, 0,:], self.data[i, 1,:], label=self.labels[i], **self.kwargs)

        elif plotType == self.TYPE_ERRORBAR:
            assert self.data.shape[-2] == 2  # Check the shape of the data, for this type should be 2-D

            # only one series of data
            if len(self.data.shape) == 2:
                if self.fmt is not None:
                    self.ax.errorbar(self.data[0,:], self.data[1,:], fmt=self.fmt[0], label=self.labels[0], **self.kwargs)
                else:
                    self.ax.errorbar(self.data[0,:], self.data[1,:], label=self.labels[0], **self.kwargs)

            # Loop over every series:
            else:
                for i in range(self.data.shape[0]):
                    if self.fmt is not None:
                        self.ax.errorbar(self.data[0,:], self.data[1,:], fmt=self.fmt[i], label=self.labels[i], **self.kwargs)
                    else:
                        self.ax.errorbar(self.data[i,0,:], self.data[i,1,:], label=self.labels[i], **self.kwargs)

        elif plotType == self.TYPE_BAR:
            assert self.data.shape[-2] == 2  # Check the shape of the data, for this type should be 2-D

            # only one series of data
            if len(self.data.shape) == 2:
                self.ax.bar(self.data[0,:], self.data[1,:], label=self.labels[0], **self.kwargs)

            # Loop over every series:
            else:
                for i in range(self.data.shape[0]):
                    self.ax.bar(self.data[i,0,:], self.data[i,1,:], label=self.labels[i], **self.kwargs)

        elif plotType == self.TYPE_HISTOGRAM:
            # data should be 1-D
            if len(self.data.shape) == 1:
                self.ax.hist(self.data, label=self.labels[0], **self.kwargs)

            else:
                assert len(self.data.shape) == 2

                for i in range(self.data.shape[0]):
                    self.ax.hist(self.data[i,:], label=self.labels[i], **self.kwargs)

        # TYPE_2DHISTOGRAM
        # TYPE_CONTOUR
        # TYPE_IMAGE
        # TYPE_COLORMESH
        # TYPE_DATEPLOT
        # TYPE_VECTOR aka quiver

        # Configure the axis scales
        if self.xlim is not None:
            self.ax.set_xlim(self.xlim[0], self.xlim[1])
        if self.ylim is not None:
            self.ax.set_ylim(self.ylim[0], self.ylim[1])
        if self.logX.get():
            self.ax.set_xscale('log')
        else:
            self.ax.set_xscale('linear')
        if self.logY.get():
            self.ax.set_yscale('log')
        else:
            self.ax.set_yscale('linear')

        # Configure the labels
        if self.xlabel != '' and self.xlabel is not None:
            self.ax.set_xlabel(self.xlabel, fontsize=self.xlabelSize)
        if self.ylabel != '' and self.ylabel is not None:
            self.ax.set_ylabel(self.ylabel, fontsize=self.ylabelSize)
        if self.title != '' and self.title is not None:
            self.ax.set_title(self.title, fontsize=self.titleSize)

        # Configure the legend:
        if self.legend.get():
            self.ax.legend(loc=self.legendLoc.get(), fontsize=self.legendFontSize.get())

        # Make sure the layout is good:
        self.fig.tight_layout()

        # Generate and show the toolbar if requested:
        if self.showToolbar.get():
            self.toolbar = matplotlib.backends.backend_tkagg.NavigationToolbar2TkAgg(self.canvas, self)
            self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            self.toolbar.update()
        else:
            if self.toolbar is not None:
                self.toolbar.destroy()

        # Update the canvas at the end:
        self.canvas.draw()

    def __menubar__(self, plotType=TYPE_PLOT):
        """Generate the window menus.

        :param plotType: (optional) the type of plot to start as [default=TYPE_PLOT]
        """
        # Top-level menu bar:
        # window = plt.get_current_fig_manager().window
        self.menubar = tk.Menu(self)

        # Text for shortcuts:
        if platform.system() == 'Darwin':
            shortcutType = '⌘'
            shortcutModifier = 'Command-'
        else:
            shortcutType = 'Ctrl+'
            shortcutModifier = 'Control-'

        # File menu:
        fileMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='File', menu=fileMenu)
        # Tabs not supported on windows
        if platform.system() == 'Darwin':
            tempText = 'Save\t\t\t'
        else:
            tempText = 'Save                '
        fileMenu.add_command(label=tempText + shortcutType + 'S', command= lambda: self.__save__('plot'))
        self.bind('<' + shortcutModifier + 's>', lambda *args: self.__save__('plot'))
        fileMenu.add_command(label='Save data', command= lambda: self.__save__('data'))
        # Tabs not supported on Windows
        if platform.system() == 'Darwin':
            tempText = 'Quit\t\t\t'
        else:
            tempText = 'Quit                '
        fileMenu.add_command(label=tempText + shortcutType + 'Q', command=self.__close__)
        self.bind('<' + shortcutModifier + 'q>', self.__close__)
        self.bind('<' + shortcutModifier + 'w>', self.__close__)

        # Plot menu
        plotMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Plot', menu=plotMenu)
        plotMenu.add_command(label='X label', command=self.__setXLabel__)
        plotMenu.add_command(label='Y label', command=self.__setYLabel__)
        plotMenu.add_command(label='Title', command=self.__setTitle__)
        
        # Controls for limits and log scaling
        plotMenu.add_separator()
        plotMenu.add_checkbutton(label='Log x', onvalue=True, offvalue=False, variable=self.logX)
        plotMenu.add_checkbutton(label='Log y', onvalue=True, offvalue=False, variable=self.logY)
        plotMenu.add_command(label='Set x limits', command=self.__setXLim__)
        plotMenu.add_command(label='Set y limits', command=self.__setYLim__)

        # submenu for plot type
        plotMenu.add_separator()
        plotTypeMenu = tk.Menu(plotMenu)
        plotMenu.add_cascade(label='Plot Type', menu=plotTypeMenu)
        self.plotTypeVar = tk.IntVar()
        # Check the shape to enable or disable various types:
        if len(self.data.shape) >= 2:
            shape = self.data.shape[-2]
        else:
            shape = 1
        # Types of plots take 1-, 2-, or 3-D data
        stateHist = tk.NORMAL if shape == 1 or self.data.shape[0] == len(self.labels) else tk.DISABLED
        state2 = tk.NORMAL if shape == 2 else tk.DISABLED
        state3 = tk.NORMAL if shape == 3 else tk.DISABLED
        state4 = tk.NORMAL if shape == 4 else tk.DISABLED
        plotTypeMenu.add_radiobutton(label='Plot', value=self.TYPE_PLOT, variable=self.plotTypeVar, state=state2)
        plotTypeMenu.add_radiobutton(label='Error Bar', value=self.TYPE_ERRORBAR, variable=self.plotTypeVar, state=state2)
        plotTypeMenu.add_radiobutton(label='Bar', value=self.TYPE_BAR, variable=self.plotTypeVar, state=state2)
        plotTypeMenu.add_radiobutton(label='Histogram', value=self.TYPE_HISTOGRAM, variable=self.plotTypeVar, state=stateHist)
        plotTypeMenu.add_radiobutton(label='2-D Histogram', value=self.TYPE_2DHISTOGRAM, variable=self.plotTypeVar, state=state2)
        plotTypeMenu.add_radiobutton(label='Contour', value=self.TYPE_CONTOUR, variable=self.plotTypeVar, state=state3)
        plotTypeMenu.add_radiobutton(label='Image', value=self.TYPE_IMAGE, variable=self.plotTypeVar)
        plotTypeMenu.add_radiobutton(label='Color Mesh', value=self.TYPE_COLORMESH, variable=self.plotTypeVar, state=state3)
        plotTypeMenu.add_radiobutton(label='Date Plot', value=self.TYPE_DATEPLOT, variable=self.plotTypeVar, state=state2)
        plotTypeMenu.add_radiobutton(label='Vector', value=self.TYPE_VECTOR, variable=self.plotTypeVar, state=state4)
        self.plotTypeVar.set(plotType)
        self.plotTypeVar.trace('w', self.__plot__)

        # Controls for the legend:
        plotMenu.add_separator()
        plotMenu.add_checkbutton(label='Show Legend', onvalue=True, offvalue=False, variable=self.legend)
        legendLocMenu = tk.Menu(plotMenu)
        plotMenu.add_cascade(label='Legend location', menu=legendLocMenu)
        legendLocMenu.add_radiobutton(label='Upper Right', value=1, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Upper Left', value=2, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Lower Left', value=3, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Lower Right', value=4, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Right', value=5, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Center Left', value=6, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Center Right', value=7, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Lower Center', value=8, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Upper Center', value=9, variable=self.legendLoc)
        legendLocMenu.add_radiobutton(label='Center', value=10, variable=self.legendLoc)
        
        legendFontMenu = tk.Menu(plotMenu)
        plotMenu.add_cascade(label='Font Size', menu=legendFontMenu)
        legendFontMenu.add_radiobutton(label='6', value=6, variable=self.legendFontSize)
        legendFontMenu.add_radiobutton(label='8', value=8, variable=self.legendFontSize)
        legendFontMenu.add_radiobutton(label='10', value=10, variable=self.legendFontSize)
        legendFontMenu.add_radiobutton(label='12', value=12, variable=self.legendFontSize)
        legendFontMenu.add_radiobutton(label='14', value=14, variable=self.legendFontSize)

        self.relabelMenu = tk.Menu(plotMenu)
        plotMenu.add_cascade(label='Relabel...', menu=self.relabelMenu)
        for i in range(len(self.labels)):
            self.relabelMenu.add_command(label=self.labels[i], command= lambda i=i: self.__relabel__(i))

        # Window menu
        windowMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Window', menu=windowMenu)
        # Items in the window menu:
        windowMenu.add_command(label='Minimize', command= lambda *args: self.iconify())
        windowMenu.add_command(label='Zoom', command=self.__zoom__)
        windowMenu.add_separator()
        self.showToolbar = tk.BooleanVar()
        windowMenu.add_checkbutton(label='Show Toolbar', onvalue=True, offvalue=False, variable=self.showToolbar)
        self.showToolbar.trace('w', self.__plot__)

        # Help menu:
        helpMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Help', menu=helpMenu)
        # Options in the help menu:
        helpMenu.add_command(label='About', command=self.__about__)

        self.config(menu=self.menubar)

    def __save__(self, type, *args):
        #TODO: implement saving
        pass

    def __setXLabel__(self, *args):
        """Prompt the user for a new x label and apply the new setting."""
        t = self.ax.xaxis.get_label()
        p = textPrompt(self, title='Set x label', initValue=t.get_text(), initFontSize=t.get_fontsize())
        if p.result is not None:
            self.ax.set_xlabel(p.result[0], fontsize=p.result[1])
            self.canvas.draw()
            self.xlabel = p.result[0]
            self.xlabelSize = p.result[1]

    def __setYLabel__(self, *args):
        """Prompt the user for a new y label and apply the new setting."""
        t = self.ax.yaxis.get_label()
        p = textPrompt(self, title='Set y label', initValue=t.get_text(), initFontSize=t.get_fontsize())
        if p.result is not None:
            self.ax.set_ylabel(p.result[0], fontsize=p.result[1])
            self.canvas.draw()
            self.ylabel = p.result[0]
            self.ylabelSize = p.result[1]

    def __setTitle__(self, *args):
        """Prompt the user for a new plot title and apply the new setting."""
        t = self.ax.title
        p = textPrompt(self, title='Set title', initValue=t.get_text(), initFontSize=t.get_fontsize())
        if p.result is not None:
            self.ax.set_title(p.result[0], fontsize=p.result[1])
            self.fig.tight_layout()
            self.canvas.draw()
            self.title = p.result[0]
            self.titleSize = p.result[1]

    def __close__(self, *args):
        """Close this window."""
        self.withdraw()

    def __about__(self, *args):
        """Display information about the module."""
        title = 'mplWindow'
        text = 'Version: ' + self.__version__ + '\n'
        text += 'mplWindow, a wrapper around matplotlib for GUI applications using tkinter \n \n \
Copyright (C) 2014 Alex Zylstra \n \n \
This program is free software: you can redistribute it and/or modify \n \
it under the terms of the GNU General Public License as published by \n \
the Free Software Foundation, either version 3 of the License, or \n \
(at your option) any later version. \n \n \
This program is distributed in the hope that it will be useful, \n \
but WITHOUT ANY WARRANTY; without even the implied warranty of \n \
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the \n \
GNU General Public License for more details. \n \n \
You should have received a copy of the GNU General Public License \n \
along with this program.  If not, see <http://www.gnu.org/licenses/>.'
        showinfo(title=title, message=text)
    
    def __resize__(self, event):
        """Handle configuration (i.e. resize) GUI events."""
        # Need to make sure the figure packing is done correctly:
        try:
            self.fig.tight_layout()
        except ValueError as e:
            pass

    def __zoom__(self, *args):
        """Handle window zoom action."""
        self.wm_state('zoomed')
        self.canvas.draw()

    def __relabel__(self, i, *args):
        """Relabel one of the series."""
        p = textPrompt(self, title='Relabel '+self.labels[i], initValue=self.labels[i], getFontSize=False)
        if p.result is not None:
            self.labels[i] = p.result[0]
            self.__plot__()
            self.relabelMenu.entryconfig(i, label=p.result[0])

    def __setXLim__(self, *args):
        """Set new x axis limits"""
        curr = self.ax.xaxis.get_data_interval()
        p = limitPrompt(self, title='x axis limits', initValue=curr)
        if p.result is not None:
            self.xlim = p.result
            self.ax.set_xlim(self.xlim[0], self.xlim[1])
            self.canvas.draw()

    def __setYLim__(self, *args):
        """Set new y axis limits"""
        curr = self.ax.yaxis.get_data_interval()
        p = limitPrompt(self, title='y axis limits', initValue=curr)
        if p.result is not None:
            self.ylim = p.result
            self.ax.set_ylim(self.ylim[0], self.ylim[1])
            self.canvas.draw()


class textPrompt(tk.Toplevel):
    """Implement a dialog window to prompt a user to input some text, e.g. for axis labels. The value can be retrieved by the `result` member::

        s = textPrompt(...)
        text, fontSize = s.result

    :param parent: The parent UI element
    :param title: (optional) A title to display on this window [default=None]
    :param text: (optional) Text to display next to the prompt [default=None]
    :param initValue: (optional) The initial value to set in the prompt [default=None]
    :param initFontSize: (optional) The initial value for font size [default=None]
    :param getFontSize: (optional) Whether to prompt for font size [default=True]

    :author: Alex Zylstra
    :date: 2014-07-06
    """

    def __init__(self, parent, title=None, text=None, initValue=None, initFontSize=None, getFontSize=True):
        """Initialize the dialog window"""
        super(textPrompt, self).__init__(parent)
        self.transient(parent)
        self.parent = parent
        self.lift()
        self.grab_set()

        self.result = None
        self.getFontSize = getFontSize
        self.__create_widgets__(title, text, initValue, initFontSize, getFontSize)

        # a couple key bindings:
        self.bind('<Return>', self.__ok__)
        self.bind('<Escape>', self.__cancel__)
        self.protocol("WM_DELETE_WINDOW", self.__cancel__)

        # Configure column weights:
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)

        # Set window background
        if platform.system() == 'Darwin':
            self.configure(background='#E8E9E8')
        else:
            self.configure(background='#F1F1F1')

        self.wait_window(self)

    def __create_widgets__(self, title, text, initValue, initFontSize, getFontSize):
        """Create the UI"""
        if title is not None:
            self.title(title)

        row = 0
        if text is not None:
            label1 = ttk.Label(self, text=text)
            label1.grid(row=row, column=0, columnspan=2)
            row += 1

        if initValue is None:
            initValue = ''
        if initFontSize is None:
            initFontSize = 10

        label2 = ttk.Label(self, text='Text')
        label2.grid(row=row, column=0)
        self.var = tk.StringVar(value=str(initValue))
        entry = ttk.Entry(self, textvariable=self.var)
        entry.grid(row=row, column=1)
        entry.focus_force()
        row += 1

        if getFontSize:
            label3 = ttk.Label(self, text='Font size')
            label3.grid(row=row, column=0)
            self.fontVar = tk.StringVar(value=str(initFontSize))
            entry2 = ttk.Entry(self, textvariable=self.fontVar)
            entry2.grid(row=row, column=1)
            row += 1

        # Buttons at the bottom:
        box = tk.Frame(self)
        if platform.system() == 'Darwin':
            box.configure(background='#E8E9E8')
        else:
            box.configure(background='#F1F1F1')

        w = ttk.Button(box, text="OK", width=10, command=self.__ok__)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.__cancel__)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.__ok__)
        self.bind("<Escape>", self.__cancel__)

        box.grid(row=row, column=0, columnspan=2)

    def __ok__(self, event=None):
        """Handle activation of the OK button."""
        if not self.__validate__():
            print('not valid')
            return

        self.__apply__()
        self.withdraw()
        self.update_idletasks()

        self.__cancel__()

    def __cancel__(self, event=None):
        """Handle cancel button"""
        # put focus back to the parent window
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()

    def __validate__(self):
        """Validate the selection, returns true if it is OK"""
        if not self.getFontSize:
            return True

        try:
            temp = float(self.fontVar.get())
            return True
        except:
            return False

    def __apply__(self):
        """Set the result"""
        if self.getFontSize:
            self.result = (self.var.get(), float(self.fontVar.get()))
        else:
            self.result = (self.var.get(), None)


class limitPrompt(tk.Toplevel):
    """Implement a dialog window to prompt a user to input two numbers, e.g. for axis limits. The value can be retrieved by the `result` member::

        s = textPrompt(...)
        min, max = s.result

    :param parent: The parent UI element
    :param title: (optional) A title to display on this window [default=None]
    :param initValue: (optional) The initial value to set in the prompt, must be a tuple length-2 [default=(0,1)]

    :author: Alex Zylstra
    :date: 2014-07-06
    """

    def __init__(self, parent, title=None, initValue=(0,1)):
        """Initialize the dialog window"""
        super(limitPrompt, self).__init__(parent)
        assert len(initValue) == 2

        self.transient(parent)
        self.parent = parent
        self.lift()
        self.grab_set()

        self.result = None
        self.__create_widgets__(title, initValue)

        # a couple key bindings:
        self.bind('<Return>', self.__ok__)
        self.bind('<Escape>', self.__cancel__)
        self.protocol("WM_DELETE_WINDOW", self.__cancel__)

        # Configure column weights:
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)

        # Set window background
        if platform.system() == 'Darwin':
            self.configure(background='#E8E9E8')
        else:
            self.configure(background='#F1F1F1')

        self.wait_window(self)

    def __create_widgets__(self, title, initValue):
        """Create the UI"""
        if title is not None:
            self.title(title)

        self.var1 = tk.StringVar(value=str(initValue[0]))
        self.var2 = tk.StringVar(value=str(initValue[1]))
        entry1 = ttk.Entry(self, textvariable=self.var1)
        entry1.configure(width=8)
        entry1.grid(row=0, column=0)
        entry1.focus_force()
        entry2 = ttk.Entry(self, textvariable=self.var2)
        entry2.configure(width=8)
        entry2.grid(row=0, column=1)

        # Buttons at the bottom:
        box = tk.Frame(self)
        if platform.system() == 'Darwin':
            box.configure(background='#E8E9E8')
        else:
            box.configure(background='#F1F1F1')

        w = ttk.Button(box, text="OK", width=10, command=self.__ok__)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.__cancel__)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.__ok__)
        self.bind("<Escape>", self.__cancel__)

        box.grid(row=1, column=0, columnspan=2)

    def __ok__(self, event=None):
        """Handle activation of the OK button."""
        if not self.__validate__():
            print('not valid')
            return

        self.__apply__()
        self.withdraw()
        self.update_idletasks()
        self.__cancel__()

    def __cancel__(self, event=None):
        """Handle cancel button"""
        # put focus back to the parent window
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()

    def __validate__(self):
        """Validate the selection, returns true if it is OK"""
        try:
            temp1 = float(self.var1.get())
            temp2 = float(self.var2.get())
            return temp2 > temp1
        except:
            return False

    def __apply__(self):
        """Set the result"""
        self.result = (float(self.var1.get()), float(self.var2.get()))

