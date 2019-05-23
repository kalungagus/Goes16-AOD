#######################################################################################################
# LICENSE
# Copyright (C) 2018 - INPE - NATIONAL INSTITUTE FOR SPACE RESEARCH
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
#######################################################################################################
 
#======================================================================================================
# GNC-A Blog Python and GOES-16 Level 2 Data Python Example
#======================================================================================================
 
# Required libraries ==========================================================
from remap_g16 import remap                               # Import the Remap function  
from datetime import datetime, timedelta              # Library to convert julian day to dd-mm-yyyy
from netCDF4 import Dataset                           # Import the NetCDF Python interface
from osgeo import gdal, osr, ogr                      # Import GDAL
import numpy as np                                    # Import the Remap function 
import sys                                            # Import the "system specific parameters and functions" module
import os 					      # Miscellaneous operating system interfaces
import glob                                             # Unix style pathname pattern expansion

# Ignore possible warnings
import warnings
warnings.filterwarnings("ignore")

def getGeoTransform(extent, nlines, ncols):
    resx = (extent[2] - extent[0]) / ncols
    resy = (extent[3] - extent[1]) / nlines
    return [extent[0], resx, 0, extent[3] , 0, -resy]

# Pixel Values
#0: Low Confidence Smoke Detection
#4: Medium Confidence Smoke Detection
#12: High Confidence Smoke Detection
#0: Low Confidence Dust Detection
#16: Medium Confidence Dust Detection
#17: Medium Confidence Dust Detection
#48: High Confidence Dust Detection
#49: High Confidence Dust Detection
#1: Invalid Smoke Detection
#2: Invalid Dust Detection
#64: Within Sun Glint
#65: Within Sun Glint
#128: Outside Valid Area
#129: Outside Valid Area
#130: Outside Valid Area

def procDsif(variable,nomenclature):
 
    # Call the reprojection funcion
    grid = remap(path, variable, extent, resolution, x1, y1, x2, y2)
     
    # Read the data returned by the function 
    data = grid.ReadAsArray()

    # Convert from int16 to uint16
    data = data.astype(np.float64)

    # ELiminate non valid data
    data[data == max(data[0])] = np.nan
    data[data == min(data[0])] = np.nan

    # Call the reprojection funcion again to get only the valid SST pixels
    grid = remap(path, "DQF", extent, resolution, x1, y1, x2, y2)
    data_DQF = grid.ReadAsArray()
    # If the Quality Flag is not 0, set as NaN 
    data_DQF[data != 1] = np.nan
    data = data_DQF   
    data[data == 1] = np.nan             # Invalid Smoke Detection
    data[data == 2] = np.nan             # Invalid Dust Detection
    data[data == 64] = np.nan            # Sunglint
    data[data == 65] = np.nan            # Sunglint 
    data[data == 128] = np.nan           # Outside Valid Area
    data[data == 129] = np.nan           # Outside Valid Area
    data[data == 130] = np.nan           # Outside Valid Area
    data[data == max(data[0])] = np.nan
    data[data == min(data[0])] = np.nan
    if variable == 'Smoke': data[data == 0] = 3 
    if variable == 'Dust': data[data == 0] = 15 
    
    # Export the result to GeoTIFF ================================================
    # Get GDAL driver GeoTiff
    driver = gdal.GetDriverByName('GTiff')
    # Get dimensions
    nlines = data.shape[0]
    ncols = data.shape[1]
    nbands = len(data.shape)
    data_type = gdal.GDT_Int16 # gdal.GDT_Int16 # gdal.GDT_Float32
    # Create grid
    #options = ['COMPRESS=JPEG', 'JPEG_QUALITY=80', 'TILED=YES']
    grid = driver.Create('grid', ncols, nlines, 1, data_type)#, options)
    # Write data for each bands
    grid.GetRasterBand(1).WriteArray(data)
    # Lat/Lon WSG84 Spatial Reference System
    srs = osr.SpatialReference()
    srs.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    # Setup projection and geo-transform
    grid.SetProjection(srs.ExportToWkt())
    grid.SetGeoTransform(getGeoTransform(extent, nlines, ncols))
    # Save the file
    #print('G16_' + product + '_' + variable + '_' + date + '.tif')
    #driver.CreateCopy('G16_' + product + '_' + variable + '_' + date + '.tif', grid, 0)

    print('Generated GeoTIFF: ', 'G16_' + nomenclature + '_' + date + '.tif')
    driver.CreateCopy('G16_' + nomenclature + '_' + date + '.tif', grid, 0)	

    # Close the file
    driver = None
    grid = None

    import os
    # Delete the grid
    os.remove('grid')
    # Delete the aux file
    os.remove(path + '.aux.xml')
	
#==============================================================================
# Acronym Description
#==============================================================================
# DSIF - Derived Stability Indices: 'CAPE', 'KI', 'LI', 'SI', 'TT'

#======================================================================================================
# Load the GOES-16 Data
#======================================================================================================
# Load the Data ===============================================================
# Path to the GOES-16 image file
path = sys.argv[1]
# Open the file using the NetCDF4 library
nc = Dataset(path)

#======================================================================================================
# Getting Information From the File
#======================================================================================================
# Getting the image resolution
resolution = getattr(nc, 'spatial_resolution')
resolution = float(resolution[:resolution.find("km")])

# Getting the file date
add_seconds = int(nc.variables['time_bounds'][0])
date = datetime(2000,1,1,12) + timedelta(seconds=add_seconds)
date = date.strftime('%Y%m%d%H%M')

# Get the latitude and longitude image bounds
geo_extent = nc.variables['geospatial_lat_lon_extent']
min_lon = float(geo_extent.geospatial_westbound_longitude)
max_lon = float(geo_extent.geospatial_eastbound_longitude)
min_lat = float(geo_extent.geospatial_southbound_latitude)
max_lat = float(geo_extent.geospatial_northbound_latitude)

# Choose the visualization extent (min lon, min lat, max lon, max lat)
extent = [float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])]

# Calculate the image extent required for the reprojection
H = nc.variables['goes_imager_projection'].perspective_point_height
x1 = nc.variables['x_image_bounds'][0] * H 
x2 = nc.variables['x_image_bounds'][1] * H 
y1 = nc.variables['y_image_bounds'][1] * H 
y2 = nc.variables['y_image_bounds'][0] * H 
 
#======================================================================================================
# Detect the product type
#======================================================================================================
product = (path[path.find("L2-")+3:path.find("-M")])
#print(product)
  
# Close the NetCDF file after getting the data
nc.close()
	
# ADPF - Aerosol Detection
variable = 'Smoke'
nomenclature = 'ADTSMK'	
procDsif(variable, nomenclature)
variable = 'Dust'
nomenclature = 'ADTDST'	
procDsif(variable, nomenclature)

gdal.BuildVRT('G16_' + 'AERDET' + '_' + date + '.vrt', sorted(glob.glob('G16_' + 'ADT*' + '_' + date + '.tif'), key=os.path.getmtime), srcNodata = -32768)
gdal.Translate('G16_' + 'AERDET' + '_' + date + '.tif', 'G16_' + 'AERDET' + '_' + date + '.vrt')        
print('Generated GeoTIFF: ','G16_' + 'AERDET' + '_' + date + '.tif') 

import os 
os.remove('G16_' + 'AERDET' + '_' + date + '.vrt')
os.remove('G16_' + 'ADTSMK' + '_' + date + '.tif')
os.remove('G16_' + 'ADTDST' + '_' + date + '.tif')
	
#mosaic = gdal.Warp('G16_' + 'AERDET' + '_' + date + '.tif', 'G16_' + 'ADTDST' + '_' + date + '.tif', 'G16_' + 'ADTSMK' + '_' + date + '.tif', srcNodata = -32768)
#mosaic = None

# Put the processed file on the log
import datetime # Basic Date and Time types
with open('gnc_log_' + str(datetime.datetime.now())[0:10] + '.txt', 'a') as log:
 log.write(str(datetime.datetime.now()))
 log.write('\n')
 log.write(path + '\n')
 log.write('\n')