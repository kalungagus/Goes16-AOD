#******************************************************************************
#             Classe de download de dados do GOES16 da AWS
#
# S3Fs:
# Site: https://s3fs.readthedocs.io/en/latest/
# Instalação: conda install s3fs -c conda-forge
#******************************************************************************
import s3fs
import numpy as np
import pytz
import os
from datetime import datetime, timedelta, timezone

class getGoes16Data:
    def __init__(self, path, product_name):
        self.product_name = product_name
        if path[-1] is not '\\':
            self.working_path = path + '\\Product\\' + product_name + '\\'
        else:
            self.working_path = path + 'Product\\' + product_name + '\\'
    def get_data(self, selected_datetime:datetime):
        # Verifica se a pasta de trabalho existe
        if not os.path.exists(self.working_path):
            os.makedirs(self.working_path)
            print('Criando pasta de trabalho.')

        data = selected_datetime.astimezone(tz=timezone.utc)
        file_path = 's3://noaa-goes16/' + self.product_name + '/' + str(data.year) + '/' + str(data.timetuple().tm_yday) + '/' + str(data.hour).zfill(2) + '/'
        fs = s3fs.S3FileSystem(anon=True)
        files = np.array(fs.ls(file_path))
        local_files = []
        for file_with_path in files:
            filename = file_with_path.split('/')[-1]
            local_files.append(self.working_path+filename)
            if not os.path.exists(self.working_path+filename):
                print("Arquivo " + filename + " não existe localmente. Fazendo download.")
                fs.get(file_with_path, self.working_path+filename)
            else:
                print("Arquivo já está na pasta de trabalho.")
        return local_files
    def erase_data(self, selected_datetime:datetime):
        if not os.path.exists(self.working_path):
            print('Pasta de trabalho inexistente')
        else:
            data = selected_datetime.astimezone(tz=timezone.utc)
            file_path = 's3://noaa-goes16/' + self.product_name + '/' + str(data.year) + '/' + str(data.timetuple().tm_yday) + '/' + str(data.hour).zfill(2) + '/'
            fs = s3fs.S3FileSystem(anon=True)
            files = np.array(fs.ls(file_path))
            for file_with_path in files:
                filename = file_with_path.split('/')[-1]
                if os.path.exists(self.working_path+filename):
                    os.remove(self.working_path+filename)
