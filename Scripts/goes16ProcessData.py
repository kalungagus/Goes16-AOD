#******************************************************************************
#                   Processador de produtos GOES-16
#
#    Os dados são obtidos pela classe getGoes16Data e processados pela classe
#   goes16Data. A classe aqui busca dados que foram requisitados e monta uma
#   série temporal, realizado por uma thread.
#******************************************************************************
from PyQt5.QtCore import QThread, pyqtSignal
from Scripts.goes16Data import goes16Data
from Scripts.getGoes16Data import getGoes16Data
from datetime import datetime, timedelta
from pytz import timezone
import os
import pandas as pd
import numpy as np

class goes16ProcessData(QThread):
    # Criando os sinais para aplicações que utilizem esta classe
    update = pyqtSignal(int)
    finished = pyqtSignal(pd.DataFrame)
    def __init__(self, data_init:datetime, data_fim:datetime, path, latitude, longitude, keep_files=True):
        QThread.__init__(self)
        self.data_init = data_init
        self.data_fim = data_fim+timedelta(days=1)
        self.latitude = latitude
        self.longitude = longitude
        self.keep_files = keep_files
        self.path = path
    def __del__(self):
        self.wait()
    def get_data_start_minute(self, filepath):
        minuto = int(filepath[filepath.find("_s")+11:filepath.find("_e")-3])
        return minuto
    def run(self):
        fileManagerAODF = getGoes16Data(self.path, 'ABI-L2-AODF')
        fileManagerCPSF = getGoes16Data(self.path, 'ABI-L2-CPSF')
        fileManagerADPF = getGoes16Data(self.path, 'ABI-L2-ADPF')
        extent = [-54.0, -20.0, -44.0, -12.0]
        lista_tempos = pd.date_range(self.data_init.strftime("%Y-%m-%d"), self.data_fim.strftime("%Y-%m-%d"), freq='H', tz=timezone('America/Sao_Paulo'))
        info_list = [["Tempo","AODF","Qualidade(AODF)","CPSF","Qualidade(CPSF)","ADPF","Qualidade(ADPF)"]]
        total_count = len(lista_tempos) * 6
        time_count = 0
        lista = pd.DataFrame(info_list, columns=info_list[0])
        for tempo in lista_tempos:
            print("Obtendo dados de " + tempo.strftime("%Y-%m-%d %H:%M:%S"))
            data_file_name = "dados-" + tempo.strftime("%Y.%m.%d.%H") + ".csv"
            if os.path.exists(self.path + "\\Relatórios\\" + data_file_name):
                temp = pd.read_csv(self.path + "\\Relatórios\\" + data_file_name, sep=';', engine='python', index_col=0)
                lista = lista.append(temp, sort=False, ignore_index=True)
                time_count = time_count + 6
                self.update.emit(int((time_count*100)/total_count))
            else:
                aodf_Files = fileManagerAODF.get_data(tempo)
                if len(aodf_Files) == 0:
                    print("Não há dados de AODF")
                    time_count = time_count + 6
                    self.update.emit(int((time_count*100)/total_count))
                    continue
                cpsf_Files = fileManagerCPSF.get_data(tempo)
                if len(cpsf_Files) == 0:
                    print("Não há dados de CPSF")
                    time_count = time_count + 6
                    self.update.emit(int((time_count*100)/total_count))
                    continue
                adpf_Files = fileManagerADPF.get_data(tempo)
                if len(adpf_Files) == 0:
                    print("Não há dados de ADPF")
                    time_count = time_count + 6
                    self.update.emit(int((time_count*100)/total_count))
                    continue
                aodf_count = cpsf_count = adpf_count = 0
                hour_list = []
                for minuto in range(0, 60, 10):
                    row = [(tempo + timedelta(minutes=minuto)).strftime("%Y-%m-%d %H:%M:%S")]
                    if self.get_data_start_minute(aodf_Files[aodf_count]) == minuto:
                        product_data = goes16Data(aodf_Files[aodf_count], extent, tzinfo=timezone('America/Sao_Paulo'))
                        result = product_data.get_data(self.latitude, self.longitude)
                        row = row + result
                        aodf_count = aodf_count + 1
                    else:
                        row = row + [np.nan, 3]
                    if self.get_data_start_minute(cpsf_Files[cpsf_count]) == minuto:
                        product_data = goes16Data(cpsf_Files[cpsf_count], extent, tzinfo=timezone('America/Sao_Paulo'))
                        result = product_data.get_data(self.latitude, self.longitude)
                        row = row + result
                        cpsf_count = cpsf_count + 1
                    else:
                        row = row + [np.nan, 14]
                    if self.get_data_start_minute(adpf_Files[adpf_count]) == minuto:
                        product_data = goes16Data(adpf_Files[adpf_count], extent, tzinfo=timezone('America/Sao_Paulo'))
                        result = product_data.get_data(self.latitude, self.longitude)
                        row = row + result
                        adpf_count = adpf_count + 1
                    else:
                        row = row + [np.nan, 129]
                    time_count = time_count + 1
                    hour_list.append(row)
                    self.update.emit(int((time_count*100)/total_count))
                hour_dataframe = pd.DataFrame(hour_list, columns=["Tempo","AODF","Qualidade(AODF)","CPSF","Qualidade(CPSF)","ADPF","Qualidade(ADPF)"])
                lista = lista.append(hour_dataframe, sort=False, ignore_index=True)
                hour_dataframe.to_csv(path_or_buf=self.path + "\\Relatórios\\" + data_file_name,sep=';')
        lista.drop(lista.index[0], inplace=True)
        self.finished.emit(lista)