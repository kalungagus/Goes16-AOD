############################################################
# LICENSE
# Copyright (C) 2018 - INPE - NATIONAL INSTITUTE FOR SPACE RESEARCH
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
############################################################

from netCDF4 import Dataset
import numpy as np
from osgeo import osr
from osgeo import gdal
import time as t

# Define KM_PER_DEGREE
KM_PER_DEGREE = 111.32

# GOES-16 Spatial Reference System
sourcePrj = osr.SpatialReference()
#sourcePrj.ImportFromProj4('+proj=geos +h=35786023.0 +a=6378137.0 +b=6356752.31414 +f=0.00335281068119356027489803406172 +lat_0=0.0 +lon_0=-75 +sweep=x +no_defs')
sourcePrj.ImportFromProj4('+proj=geos +h=35786000 +a=6378140 +b=6356750 +lon_0=-75 +sweep=x')

# Lat/lon WSG84 Spatial Reference System
targetPrj = osr.SpatialReference()
#targetPrj.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
targetPrj.ImportFromProj4('+proj=latlong +datum=WGS84')

def exportImage(image,path):
    driver = gdal.GetDriverByName('netCDF')
    return driver.CreateCopy(path,image,0)

def getGeoT(extent, nlines, ncols):
    # Compute resolution based on data dimension
    resx = (extent[2] - extent[0]) / ncols
    resy = (extent[3] - extent[1]) / nlines
    return [extent[0], resx, 0, extent[3] , 0, -resy]

def getScaleOffset(path, variable):
    nc = Dataset(path, mode='r')
    
    if (variable == "BCM") or (variable == "Phase") or (variable == "Smoke") or (variable == "Dust") or (variable == "Mask") or (variable == "Power"): 
        scale = 1
        offset = 0     
    else:
        scale = nc.variables[variable].scale_factor
        offset = nc.variables[variable].add_offset
    nc.close()
    return scale, offset
    
def remap(path, variable, extent, resolution, x1, y1, x2, y2):
    
    scale = 1
    offset = 0
    
    # GOES-16 Extent (satellite projection) [llx, lly, urx, ury]
    GOES16_EXTENT = [x1, y1, x2, y2]
    
    # Setup NetCDF driver
    gdal.SetConfigOption('GDAL_NETCDF_BOTTOMUP', 'NO')
        
    if not (variable == "DQF"):              
        # Read scale/offset from file
        scale, offset = getScaleOffset(path, variable) 
        #print(scale)
        #print(offset)
      
    connectionInfo = 'HDF5:\"' + path + '\"://' + variable
    print(connectionInfo)
    
    raw = gdal.Open(connectionInfo)          
    
    # Setup projection and geo-transformation
    raw.SetProjection(sourcePrj.ExportToWkt())
    raw.SetGeoTransform(getGeoT(GOES16_EXTENT, raw.RasterYSize, raw.RasterXSize))  

    # Compute grid dimension
    sizex = int(((extent[2] - extent[0]) * KM_PER_DEGREE) / resolution)
    sizey = int(((extent[3] - extent[1]) * KM_PER_DEGREE) / resolution)
    
    # Get memory driver
    memDriver = gdal.GetDriverByName('MEM')
   
    # Create grid
    grid = memDriver.Create('grid', sizex, sizey, 1, gdal.GDT_Float32)
        
    # Setup projection and geo-transformation
    grid.SetProjection(targetPrj.ExportToWkt())
    grid.SetGeoTransform(getGeoT(extent, grid.RasterYSize, grid.RasterXSize))

    # Perform the projection/resampling 
    print ('Remapping...')#, path)
        
    start = t.time()
    
    gdal.ReprojectImage(raw, grid, sourcePrj.ExportToWkt(), targetPrj.ExportToWkt(), gdal.GRA_NearestNeighbour, options=['NUM_THREADS=ALL_CPUS']) 
    
    print ('Remap finished! Time:', t.time() - start, 'seconds')
               
    # Read grid data
    array = grid.ReadAsArray()
    
    # Mask fill values (i.e. invalid values)
    np.ma.masked_where(array, array == -1, False)
    
    array = array.astype(np.uint16)  
       
    # Apply scale and offset
    array = array * scale + offset

    # Get the raster 
    grid.GetRasterBand(1).WriteArray(array)

	# Close file
    raw = None
	
    return grid
