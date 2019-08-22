# -*- coding: utf-8 -*-
"""
Created on Tue May 21 21:49:01 2019

@author: Gustavo
"""

#******************************************************************************
# Bibliotecas para importar
#******************************************************************************
from PyQt5 import uic, QtWidgets
import matplotlib.pyplot as plt   # Importando o pacote Matplotlib
from mpl_toolkits.basemap import Basemap  # Importando o Basemap (Ref: https://matplotlib.org/basemap/users/intro.html)
from matplotlib.patches import Rectangle # Library to draw rectangles on the plot

from Scripts.cpt_convert import loadCPT   # Importa a função de converter CPTs
from matplotlib.colors import LinearSegmentedColormap # Linear interpolation for color maps

# Required libraries ==========================================================
from Scripts.remap_g16 import remap                               # Import the Remap function  
from datetime import datetime, timedelta              # Library to convert julian day to dd-mm-yyyy
from netCDF4 import Dataset                           # Import the NetCDF Python interface
from osgeo import gdal, osr                           # Import GDAL
import numpy as np                                    # Import the Remap function 
import os 					                          # Miscellaneous operating system interfaces
import glob                                           # Unix style pathname pattern expansion

UIClass, QtBaseClass = uic.loadUiType("Interface.ui")

def getGeoTransform(extent, nlines, ncols):
        resx = (extent[2] - extent[0]) / ncols
        resy = (extent[3] - extent[1]) / nlines
        return [extent[0], resx, 0, extent[3] , 0, -resy]

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
            # Getting the image resolution
            resolution = getattr(nc, 'spatial_resolution')
            resolution = float(resolution[:resolution.find("km")])
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
                    # Close the NetCDF file after getting the data
                    nc.close()
                    # Call the reprojection funcion
                    grid = remap(path, variable, extent, resolution, x1, y1, x2, y2)
                    quality = remap(path, 'DQF', extent, resolution, x1, y1, x2, y2)
                    # Read the data returned by the function 
                    data = grid.ReadAsArray()
                    data2 = quality.ReadAsArray()
                    # Convert from int16 to uint16
                    data = data.astype(np.float64)
                    data[data == max(data[0])] = np.nan
                    data[data == min(data[0])] = np.nan
                    data2 = data2.astype(np.float64)
                    data2[data2 == max(data2[0])] = np.nan
                    data2[data2 == min(data2[0])] = np.nan
                    # Define o tamanho da figura salva=====================================================================
                    DPI = 150
                    plt.figure(figsize=(2000/float(DPI), 2000/float(DPI)), frameon=True, dpi=DPI)
                    # Plota os dados =======================================================================================
                    # Cria a referência basemap para a projeção retangular
                    bmap = Basemap(llcrnrlon=extent[0], llcrnrlat=extent[1], urcrnrlon=extent[2], urcrnrlat=extent[3], epsg=4326)
                     
                    # Desenha os países e os estados brasileiros
                    bmap.readshapefile('Shapefiles\\BRA_adm1','BRA_adm1',linewidth=0.50,color='cyan')
                    bmap.readshapefile('Shapefiles\\ne_10m_admin_0_countries','ne_10m_admin_0_countries',linewidth=0.50,color='cyan')
                     
                    # Desenha os paralelos e meridianos
                    bmap.drawparallels(np.arange(-90.0, 90.0, 2.5), linewidth=0.3, dashes=[4, 4], color='white', labels=[False,False,False,False], fmt='%g', labelstyle="+/-", xoffset=-0.80, yoffset=-1.00, size=7)
                    bmap.drawmeridians(np.arange(0.0, 360.0, 2.5), linewidth=0.3, dashes=[4, 4], color='white', labels=[False,False,False,False], fmt='%g', labelstyle="+/-", xoffset=-0.80, yoffset=-1.00, size=7)
                    # Aqui, vamos utilizar um arquivo de esquemas de cores.
                    # Tais arquivos podem ser encontrados no link: http://soliton.vm.bytemark.co.uk/pub/cpt-city/
                    # Este arquivo é baixado do site de exemplos, e é o arquivo específico para temperaturas.
                    cpt = loadCPT('Colortables\\temperature.cpt')
                    # Faz a interpolação linear com o arquivo CPT
                    cpt_convert = LinearSegmentedColormap('cpt', cpt)
                    # Plota o canal do GOES-16 com as cores convertidas do CPT
                    #bmap.imshow(data, origin='upper', cmap=cpt_convert, vmin=-103, vmax=84)
                    # Configuração para o esquema de cores SVGAIR_TEMP
                    #bmap.imshow(data, origin='upper', cmap=cpt_convert, vmin=-112.15, vmax=56.85)
                    # Configuração para o esquema de cores Square Root Visible Enhancement
                    bmap.imshow(data, origin='upper', cmap=cpt_convert, vmin=0, vmax=5)
                    # Insere a barra de cores embaixo
                    # cb = bmap.colorbar(location='bottom', size = '2%', pad = '-4%')
                    # Passo para o exercício 3
                    cb = bmap.colorbar(location='bottom', size = '2%', pad = '-4%', ticks=[0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0])
                    
                    cb.outline.set_visible(False) # Remove the colorbar outline
                    cb.ax.tick_params(width = 0) # Remove the colorbar ticks
                    cb.ax.xaxis.set_tick_params(pad=-12.5) # Put the colobar labels inside the colorbar
                    cb.ax.tick_params(axis='x', colors='yellow', labelsize=8) # Change the color and size of the colorbar labels
                    # Passo para o exercício 3
                    cb.ax.set_xticklabels(['0.2', '0.4', '0.6', '0.8', '1.0', '1.2', '1.4', '1.6', '1.8', '2.0', '2.2', '2.4', '2.6', '2.8', '3.0', '3.2', '3.4', '3.6', '3.8', '4.0', '4.2', '4.4', '4.6', '4.8', '5.0'])
                    
                    #Unit = "Brightness Temperature [°C]"
                    #Unit = "Reflectance"
                    Title = " GOES-16 AEROSOL PRODUCT "
                    Institution = "Instituto Federal de Goiás "
                     
                    # Add a black rectangle in the bottom to insert the image description
                    lon_difference = (extent[2] - extent[0]) # Max Lon - Min Lon
                    currentAxis = plt.gca()
                    currentAxis.add_patch(Rectangle((extent[0], extent[1]), lon_difference, lon_difference * 0.015, alpha=1, zorder=3, facecolor='black'))
                     
                    # Add the image description inside the black rectangle
                    lat_difference = (extent[3] - extent[1]) # Max lat - Min lat
                    plt.text(extent[0], extent[1] + lat_difference * 0.003,Title,horizontalalignment='left', color = 'white', size=10)
                    plt.text(extent[2], extent[1],Institution, horizontalalignment='right', color = 'yellow', size=10)
                     
                    # Add logos / images to the plot
                    #logo_IFG = plt.imread('Logos\\IFG.png')
                    #logo_GNC = plt.imread('Logos\\GNC Logo.png')
                    #logo_INPE = plt.imread('Logos\\INPE Logo.png')
                    #logo_NOAA = plt.imread('Logos\\NOAA Logo.png')
                    #logo_GOES = plt.imread('Logos\\GOES Logo.png')
                    #ax.figimage(logo_GNC, 10, 50, zorder=3, alpha = 1, origin = 'upper')
                    #ax.figimage(logo_INPE, 400, 50, zorder=3, alpha = 1, origin = 'upper')
                    #ax.figimage(logo_NOAA, 500, 50, zorder=3, alpha = 1, origin = 'upper')
                    #ax.figimage(logo_GOES, 585, 50, zorder=3, alpha = 1, origin = 'upper')
                    #ax.figimage(logo_IFG, 10, 50, zorder=3, alpha = 1, origin = 'upper')
                    
                    # Save the result
                    if not os.path.exists('Output\\' + date.strftime("%Y\\%m\\%d\\")):
                        os.makedirs('Output\\' + date.strftime("%Y\\%m\\%d\\"))
                        print('Directory Output\\' + date.strftime("%Y\\%m\\%d\\ created!"))
                    plt.savefig('Output\\' + date.strftime("%Y\\%m\\%d\\") + 'G16_' + nomenclature + '_' + date.strftime("%M-%H-%d-%m-%Y") + '.png', dpi=DPI, bbox_inches='tight', pad_inches=0)
                    plt.close()
                    print('Generated .png: ', 'G16_' + nomenclature + '_' + date.strftime("%M-%H-%d-%m-%Y") + '.png')
                    # Export the result to GeoTIFF ================================================
                    # Get GDAL driver GeoTiff
                    driver = gdal.GetDriverByName('GTiff')
                    # Get dimensions
                    nlines = data.shape[0]
                    ncols = data.shape[1]
                    data_type = gdal.GDT_Float32 # gdal.GDT_Int16 # gdal.GDT_Float32
                    # Create grid
                    #options = ['COMPRESS=JPEG', 'JPEG_QUALITY=80', 'TILED=YES']
                    grid = driver.Create('grid', ncols, nlines, 2, data_type)#, options)
                    # Write data for each bands
                    grid.GetRasterBand(1).WriteArray(data)
                    grid.GetRasterBand(2).WriteArray(data2)
                    # Lat/Lon WSG84 Spatial Reference System
                    srs = osr.SpatialReference()
                    srs.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
                    # Setup projection and geo-transform
                    grid.SetProjection(srs.ExportToWkt())
                    grid.SetGeoTransform(getGeoTransform(extent, nlines, ncols))
                    # Save the file
                    #print('G16_' + product + '_' + variable + '_' + date + '.tif')
                    #driver.CreateCopy('G16_' + product + '_' + variable + '_' + date + '.tif', grid, 0)
                    print('Generated GeoTIFF: ', 'Output\\' + date.strftime("%Y\\%m\\%d\\") + 'G16_' + nomenclature + '_' + date.strftime("%Y-%m-%d-%H-%M") + '.tif')
                    driver.CreateCopy('Output\\' + date.strftime("%Y\\%m\\%d\\") + 'G16_' + nomenclature + '_' + date.strftime("%Y-%m-%d-%H-%M") + '.tif', grid, 0)	
                    # Close the file
                    driver = None
                    grid = None
                    # Delete the grid
                    os.remove('grid')
                    # Delete the aux file
                    #print(path + '.aux.xml')
                    os.remove(path + '.aux.xml')
                    gdal.UseExceptions()
                    # Generating the SST and LST daily accumulate
                    if product == "LSTF":
                        start_day = date[0:8]
                        gdal.BuildVRT('G16_' + nomenclature + '_' + date + '.vrt', sorted(glob.glob('G16_' + nomenclature + '_' + start_day + '*.tif'), key=os.path.getmtime), srcNodata = 0)# , reverse=True), srcNodata = 0)
                        gdal.Translate('G16_' + nomenclature[0:4] + 'DA_' + date + '.tif', 'G16_' + nomenclature + '_' + date + '.vrt')       
                        print('Generated GeoTIFF: ','G16_' + nomenclature[0:4] + 'DA_' + date + '.tif')  
                        os.remove('G16_' + nomenclature + '_' + date + '.vrt')
                    elif product == "TPWF":
                        start_day = date[0:8]
                        gdal.BuildVRT('G16_' + nomenclature + '_' + date + '.vrt', sorted(glob.glob('G16_' + nomenclature + '_' + start_day + '*.tif'), key=os.path.getmtime), srcNodata = np.nan)# , reverse=True), srcNodata = 0)
                        gdal.Translate('G16_' + nomenclature[0:4] + 'DA_' + date + '.tif', 'G16_' + nomenclature + '_' + date + '.vrt')       
                        print('Generated GeoTIFF: ','G16_' + nomenclature[0:4] + 'DA_' + date + '.tif')  
                        os.remove('G16_' + nomenclature + '_' + date + '.vrt')
                        os.remove('G16_' + nomenclature[0:4] + 'DA_' + date + '.tif.aux.xml')
                    elif product == "SSTF":
                        start_day = date[0:6]
                        gdal.BuildVRT('G16_' + nomenclature + '_' + date + '.vrt', sorted(glob.glob('G16_' + nomenclature + '_' + start_day + '*.tif'), key=os.path.getmtime), srcNodata = 0)# , reverse=True), srcNodata = 0)
                        gdal.Translate('G16_' + nomenclature[0:4] + 'MA_' + date + '.tif', 'G16_' + nomenclature + '_' + date + '.vrt')       
                        print('Generated GeoTIFF: ','G16_' + nomenclature[0:4] + 'MA_' + date + '.tif')  
                        os.remove('G16_' + nomenclature + '_' + date + '.vrt')
        print("Conversão Concluída!")

app = QtWidgets.QApplication([])
window = MyApp()
window.show()
app.exec_()