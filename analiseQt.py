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

from Scripts.cpt_convert import loadCPT   # Importa a função de converter CPTs
from matplotlib.colors import LinearSegmentedColormap # Linear interpolation for color maps

# Required libraries ==========================================================
from Scripts.remap_g16 import remap                               # Import the Remap function  
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
        print("A partir de:" + self.dateEdtFrom.date().toString())
        fromDate = datetime(self.dateEdtFrom.date().year(),self.dateEdtFrom.date().month(),self.dateEdtFrom.date().day())
        toDate = datetime(self.dateEdtTo.date().year(),self.dateEdtTo.date().month(),self.dateEdtTo.date().day())
        # Choose the visualization extent (min lon, min lat, max lon, max lat)
        # Extent from Goiás
        extent = [-54.0, -20.0, -44.0, -12.0]
        for path in glob.glob(self.txtInputDir.text() + '*.nc'):
            print("Processing " + path)
            nc = Dataset(path)
            # Getting the file date
            add_seconds = int(nc.variables['time_bounds'][0])
            date = datetime(2000,1,1,12) + timedelta(seconds=add_seconds)
            print(date)
            if(date > fromDate and date < toDate) :
                # Get the latitude and longitude image bounds
                geo_extent = nc.variables['geospatial_lat_lon_extent']
                min_lon = float(geo_extent.geospatial_westbound_longitude)
                max_lon = float(geo_extent.geospatial_eastbound_longitude)
                min_lat = float(geo_extent.geospatial_southbound_latitude)
                max_lat = float(geo_extent.geospatial_northbound_latitude)
                # Calculate the image extent required for the reprojection
                H = nc.variables['goes_imager_projection'].perspective_point_height
                x1 = nc.variables['x_image_bounds'][0] * H 
                x2 = nc.variables['x_image_bounds'][1] * H 
                y1 = nc.variables['y_image_bounds'][1] * H 
                y2 = nc.variables['y_image_bounds'][0] * H
                # Detect the product type
                product = (path[path.find("L2-")+3:path.find("-M")])
                # AODF - Aerosol Optical Depth: 'AOD'    
                if product == "AODF":
                    variable = 'AOD'
                    nomenclature = 'AEROPT'
                    data[data == max(data[0])] = np.nan
                    data[data == min(data[0])] = np.nan
                    # Define o tamanho da figura salva=====================================================================
                    DPI = 150
                    ax = plt.figure(figsize=(2000/float(DPI), 2000/float(DPI)), frameon=True, dpi=DPI)

app = QtWidgets.QApplication([])
window = MyApp()
window.show()
app.exec_()