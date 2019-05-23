# -*- coding: utf-8 -*-
"""
Created on Tue May 21 21:49:01 2019

@author: Gustavo
"""

#******************************************************************************
# Bibliotecas para importar
#******************************************************************************
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt   # Importando o pacote Matplotlib
from mpl_toolkits.basemap import Basemap  # Importando o Basemap (Ref: https://matplotlib.org/basemap/users/intro.html)
from matplotlib.patches import Rectangle # Library to draw rectangles on the plot

from cpt_convert import loadCPT   # Importa a função de converter CPTs
from matplotlib.colors import LinearSegmentedColormap # Linear interpolation for color maps

# Required libraries ==========================================================
from remap_g16 import remap                               # Import the Remap function  
from datetime import datetime, timedelta              # Library to convert julian day to dd-mm-yyyy
from netCDF4 import Dataset                           # Import the NetCDF Python interface
from osgeo import gdal, osr, ogr                      # Import GDAL
import numpy as np                                    # Import the Remap function 
import sys                                            # Import the "system specific parameters and functions" module
import os 					      # Miscellaneous operating system interfaces
import glob                                             # Unix style pathname pattern expansion

UIClass, QtBaseClass = uic.loadUiType("Interface.ui")

class MyApp(UIClass, QtBaseClass):
    def __init__(self):
        UIClass.__init__(self)
        QtBaseClass.__init__(self)
        self.setupUi(self)
        self.pBtnCarregar.clicked.connect(self.Executar)
    def Executar(self):
        print("Printing files from " + self.txtInputDir.text() + '*.nc')
        for path in glob.glob(self.txtInputDir.text() + '*.nc'):
            print("Processing " + path)
            nc = Dataset(path)
            # Getting the file date
            add_seconds = int(nc.variables['time_bounds'][0])
            date = datetime(2000,1,1,12) + timedelta(seconds=add_seconds)
            date = date.strftime('%Y/%m/%d %H:%M')
            print(date)

app = QtWidgets.QApplication([])
window = MyApp()
window.show()
app.exec_()