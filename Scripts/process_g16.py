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
	
#==============================================================================
# Acronym Description
#==============================================================================
# ACHAF - Cloud Top Height: 'HT'
# ACHTF - Cloud Top Temperature: 'TEMP'
# ACMF - Clear Sky Masks: 'BCM'
# ACTPF - Cloud Top Phase: 'Phase'
# ADPF - Aerosol Detection: 'Smoke'
# ADPF - Aerosol Detection: 'Dust'
# AODF - Aerosol Optical Depth: 'AOD'
# CMIPF - Cloud and Moisture Imagery: 'CMI'
# CMIPC - Cloud and Moisture Imagery: 'CMI'
# CMIPM - Cloud and Moisture Imagery: 'CMI'
# CODF - Cloud Optical Depth: 'COD'
# CPSF - Cloud Particle Size: 'PSD'
# CTPF - Cloud Top Pressure: 'PRES'
# DMWF - Derived Motion Winds: 'pressure'
# DMWF - Derived Motion Winds: 'temperature'
# DMWF - Derived Motion Winds: 'wind_direction'
# DMWF - Derived Motion Winds: 'wind_speed'
# DSIF - Derived Stability Indices: 'CAPE' 
# DSIF - Derived Stability Indices: 'KI'
# DSIF - Derived Stability Indices: 'LI'
# DSIF - Derived Stability Indices: 'SI'
# DSIF - Derived Stability Indices: 'TT'
# DSRF - Downward Shortwave Radiation: 'DSR'   
# FDCF - Fire-Hot Spot Characterization: 'Area'
# FDCF - Fire-Hot Spot Characterization: 'Mask'
# FDCF - Fire-Hot Spot Characterization: 'Power'
# FDCF - Fire-Hot Spot Characterization: 'Temp'
# FSCF - Snow Cover: 'FSC'
# LSTF - Land Surface (Skin) Temperature: 'LST'
# RRQPEF - Rainfall Rate - Quantitative Prediction Estimate: 'RRQPE'
# RSR - Reflected Shortwave Radiation: 'RSR'
# SSTF - Sea Surface (Skin) Temperature: 'SST'
# TPWF - Total Precipitable Water: 'TPW'
# VAAF - Volcanic Ash: 'VAH'
# VAAF - Volcanic Ash: 'VAML'
 
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

#print(x1)
#print(x2)
#print(y1)
#print(y2)
 
#======================================================================================================
# Detect the product type
#======================================================================================================
product = (path[path.find("L2-")+3:path.find("-M")])
#print(product)
 
# CMIPF - Cloud and Moisture Imagery: 'CMI'
if (product == "CMIPF") or (product == "CMIPC") or (product == "CMIPM"):
    variable = 'CMI'
    nomenclature = 'BAND'
    # Getting the band, with left zero padding (2 digits)
    band = str(nc.variables['band_id'][0]).zfill(2)
    #print(band) 
     
# ACHAF - Cloud Top Height: 'HT'    
elif product == "ACHAF":
    variable = 'HT'
    nomenclature = 'CLDHGT'
	
# ACHTF - Cloud Top Temperature: 'TEMP'
elif product == "ACHTF":
    variable = 'TEMP'
    nomenclature = 'CLDTMP'
	
# ACMF - Clear Sky Masks: 'BCM'
elif product == "ACMF":
    variable = 'BCM'
    nomenclature = 'CLDMSK'
	
# ACTPF - Cloud Top Phase: 'Phase'
elif product == "ACTPF":
    variable = 'Phase'
    nomenclature = 'CLDPHA'
	
# ADPF - Aerosol Detection: 'Smoke'
elif product == "ADPF":
    variable = 'DQF'
    nomenclature = 'AERDET'
    #variable = 'Dust'  
 
# AODF - Aerosol Optical Depth: 'AOD'    
elif product == "AODF":
    variable = 'AOD'
    nomenclature = 'AEROPT'
	
# CODF - Cloud Optical Depth: 'COD'    
elif product == "CODF":
    variable = 'COD'
    nomenclature = 'CLDOPT'
	
# CPSF - Cloud Particle Size: 'PSD'
elif product == "CPSF":
    variable = 'PSD'
    nomenclature = 'CLDPAS'
	
# CTPF - Cloud Top Pressure: 'PRES'
elif product == "CTPF":
    variable = 'PRES'
    nomenclature = 'CLDPRE'

# DMWF - Derived Motion Winds: 'pressure','temperature', 'wind_direction', 'wind_speed'    
#elif product == "DMWF":
#    variable = 'pressure'
    #variable = 'temperature'
    #variable = 'wind_direction'
    #variable = 'wind_speed'    
 
# DSIF - Derived Stability Indices: 'CAPE', 'KI', 'LI', 'SI', 'TT' 
elif product == "DSIF":
    variable = 'CAPE'
    nomenclature = 'DSCAPE'	
    #variable = 'KI'
    #nomenclature = 'DSINKI'	
    #variable = 'LI'   
    #nomenclature = 'DSINLI'	
    #variable = 'SI'
    #nomenclature = 'DSINSI'	
    #variable = 'TT'
    #nomenclature = 'DSINTT'	
	
# DSRF - Downward Shortwave Radiation: 'DSR'  
#elif product == "DSRF":
#    variable = 'DSR'
 
# FDCF - Fire-Hot Spot Characterization: 'Area', 'Mask', 'Power', 'Temp'    
elif product == "FDCF":
    #variable = 'Area'   
    variable = 'Mask'     
    nomenclature = 'FIRMSK'
    #variable = 'Power' 
    #variable = 'Temp' 
 
# FSCF - Snow Cover: 'FSC'    
elif product == "FSCF":
    variable = 'FSC'
    nomenclature = 'SNWCOV'
	
# LSTF - Land Surface (Skin) Temperature: 'LST'    
elif product == "LSTF":
    variable = 'LST'   
    nomenclature = 'LSTSKN'
	
# RRQPEF - Rainfall Rate - Quantitative Prediction Estimate: 'RRQPE'    
elif product == "RRQPEF":
    variable = 'RRQPE'
    nomenclature = 'RARQPE' 
	
# RSR - Reflected Shortwave Radiation: 'RSR'    
#elif product == "RSRF":
#    variable = 'RSR'       
 
# SSTF - Sea Surface (Skin) Temperature: 'SST'
elif product == "SSTF":
    variable = 'SST'
    nomenclature = 'SSTSKN'
	
# TPWF - Total Precipitable Water: 'TPW'
elif product == "TPWF":
    variable = 'TPW'
    nomenclature = 'TOTPWA' 
    
# VAAF - Volcanic Ash: 'VAH', 'VAML'    
elif product == "VAAF":
    #variable = 'VAH'   
    variable = 'VAML'
    nomenclature = 'VOLASH'
	
# Close the NetCDF file after getting the data
nc.close()
 
# Call the reprojection funcion
grid = remap(path, variable, extent, resolution, x1, y1, x2, y2)
     
# Read the data returned by the function 
data = grid.ReadAsArray()

# Convert from int16 to uint16
data = data.astype(np.float64)

if (variable == "Dust") or (variable == "Smoke") or (variable == "TPW") or (variable == "PRES") or  (variable == "HT") or \
   (variable == "TEMP") or (variable == "AOD") or (variable == "COD") or (variable == "PSD") or  (variable == "CAPE") or  (variable == "KI") or \
   (variable == "LI") or (variable == "SI") or (variable == "TT") or (variable == "FSC") or  (variable == "RRQPE") or (variable == "VAML") or (variable == "VAH"):
   data[data == max(data[0])] = np.nan
   data[data == min(data[0])] = np.nan

if (variable == "CMI"):
   #data[data == max(data[0])] = np.nan
   #data[data == min(data[0])] = np.nan
   if int(band) <= 6:
      data = data * 100
   data[data >= 4116] = np.nan  
if (variable == "SST"):
   data[data == max(data[0])] = np.nan   
   data[data == min(data[0])] = np.nan  
    
   # Call the reprojection funcion again to get only the valid SST pixels
   grid = remap(path, "DQF", extent, resolution, x1, y1, x2, y2)
   data_DQF = grid.ReadAsArray()
   # If the Quality Flag is not 0, set as NaN 
   data[data_DQF != 0] = 0
 
if (variable == "Mask"):
   #data[data == -99] = np.nan
   data[data == 40] = np.nan
   data[data == 50] = np.nan
   data[data == 60] = np.nan
   data[data == 150] = np.nan
   data[data < 10] = np.nan
   data[data > 15] = np.nan
   data[data == max(data[0])] = np.nan
   data[data == min(data[0])] = np.nan
    
if (variable == "BCM"):
   data[data == 255] = np.nan
   data[data == 0] = np.nan
    
if (variable == "Phase"):
   data[data >= 5] = np.nan
   data[data == 0] = np.nan   
    
if (variable == "LST"):
   data[data >= 335] = 0
   data[data == 190] = np.nan
   
    
# Export the result to GeoTIFF ================================================
# Get GDAL driver GeoTiff
driver = gdal.GetDriverByName('GTiff')
# Get dimensions
nlines = data.shape[0]
ncols = data.shape[1]
nbands = len(data.shape)
data_type = gdal.GDT_Float32 # gdal.GDT_Int16 # gdal.GDT_Float32
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

if (variable == "CMI"):
	print('Generated GeoTIFF: ', 'G16_BAND' + band + '_' + date + '.tif')
	driver.CreateCopy('G16_BAND' + band + '_' + date + '.tif', grid, 0)
else:
	print('Generated GeoTIFF: ', 'G16_' + nomenclature + '_' + date + '.tif')
	driver.CreateCopy('G16_' + nomenclature + '_' + date + '.tif', grid, 0)	

# Close the file
driver = None
grid = None

import os
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
	   
#==============================================================================

# Put the processed file on the log
import datetime # Basic Date and Time types
with open('gnc_log_' + str(datetime.datetime.now())[0:10] + '.txt', 'a') as log:
 log.write(str(datetime.datetime.now()))
 log.write('\n')
 log.write(path + '\n')
 log.write('\n')