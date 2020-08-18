#******************************************************************************
#             Classe de leitura de dados do satélite GOES-16
#
#    A classe faz a leitura de um arquivo de produto GOES-16 e extrai todos os
#  dados necessários de um produto. Através da função get_data, uma tupla
#  com o valor do produto e seu bit de Qualidade é obtido.
#******************************************************************************
from netCDF4 import Dataset
from osgeo import gdal, osr
import numpy as np
import pytz
import os
from datetime import datetime, timedelta
from Scripts.remap_g16 import remap

class goes16Data:
    def __init__(self, path, extent, tzinfo=pytz.utc):
        self.path = path
        self.tzinfo = tzinfo
        self.extent = extent

        nc = Dataset(path)

        # Obtém do arquivo os limites da imagem
        H = nc.variables['goes_imager_projection'].perspective_point_height
        self.x1 = nc.variables['x_image_bounds'][0] * H 
        self.x2 = nc.variables['x_image_bounds'][1] * H 
        self.y1 = nc.variables['y_image_bounds'][1] * H 
        self.y2 = nc.variables['y_image_bounds'][0] * H

        # Obtém do arquivo a resolução espacial da imagem
        res = nc.getncattr('spatial_resolution')
        self.resolution = float(res[:res.find("km")])

        # Obtém do arquivo a data e hora do começo e fim da captura de dados
        data = datetime(2000,1,1,12, tzinfo=pytz.utc) + timedelta(seconds=int(nc.variables['time_bounds'][0]))
        self.start_time = data.astimezone(self.tzinfo)
        data = datetime(2000,1,1,12, tzinfo=pytz.utc) + timedelta(seconds=int(nc.variables['time_bounds'][1]))
        self.end_time = data.astimezone(self.tzinfo)

        # Obtém do arquivo qual o produto
        filename = path.split('\\')[-1]
        self.product = (filename[filename.find("L2-")+3:filename.find("-M")])
        if self.product == "AODF":
            self.variable = 'AOD'
            self.qvariable = 'DQF'
            self.nomenclature = 'AEROPT'
            self.scale = nc.variables['AOD'].scale_factor
            self.offset = nc.variables['AOD'].add_offset
            self.quality_invalid_value = 3
        elif self.product == "CPSF":
            self.variable = 'PSD'
            self.qvariable = 'DQF'
            self.nomenclature = 'CLDPAS'
            self.scale = nc.variables['PSD'].scale_factor
            self.offset = nc.variables['PSD'].add_offset
            self.quality_invalid_value = 14
        elif self.product == "ADPF":
            self.variable = 'Smoke'
            self.qvariable = 'DQF'
            self.nomenclature = 'AERDET'
            self.scale = 1
            self.offset = 0
            self.quality_invalid_value = 129
        else:
            self.variable = 'None'
            self.qvariable = 'None'
            self.nomenclature = 'None'
            self.quality_invalid_value = 255

        # A variável long_name contém uma descrição mais detalhada do produto
        self.product_name = nc.variables[self.variable].getncattr('long_name')

        self.minval = np.ushort(nc.variables[self.variable].valid_range[0]) * self.scale + self.offset
        self.maxval = np.ushort(nc.variables[self.variable].valid_range[1]) * self.scale + self.offset

        self.fillvalue = nc.variables[self.variable]._FillValue
        self.qualityFillvalue = np.uint8(nc.variables[self.qvariable]._FillValue)

        # Fecha o Dataset para que o gdal não dê erro ao processar os dados do arquivo
        nc.close()

    def get_data(self, latitude, longitude):
        # Processa primeiro os dados do produto
        product_grid = remap(self.path, self.variable, self.extent, self.resolution, self.x1, self.y1, self.x2, self.y2)
        product_data = product_grid.ReadAsArray()
        product_data[product_data == self.fillvalue] = np.nan
        product_data = product_data.astype(np.float64)
        product_data = product_data * self.scale + self.offset
        # Processa os dados de bit de qualidade
        quality_grid = remap(self.path, self.qvariable, self.extent, self.resolution, self.x1, self.y1, self.x2, self.y2)
        quality_data = quality_grid.ReadAsArray()
        quality_data[quality_data == self.qualityFillvalue] = self.quality_invalid_value
        quality_data = quality_data.astype(np.ushort)
        # Faz a leitura dos valores para a coordenada desejada
        resx = (self.extent[2] - self.extent[0]) / product_data.shape[1]
        resy = -(self.extent[3] - self.extent[1]) / product_data.shape[0]
        x_sample = int((latitude - self.extent[0])/resx)
        y_sample = int((longitude - self.extent[3])/resy)

        value = product_data[y_sample][x_sample]
        quality = quality_data[y_sample][x_sample]

        # Deleta o arquivo aux
        os.remove(self.path + '.aux.xml')
        return [value, quality]
