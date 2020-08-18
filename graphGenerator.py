#******************************************************************************
#            Gerador de gráficos temporais para produtos GOES-16
#
#    Os dados são obtidos pela classe getGoes16Data e processados pela classe
#   goes16Data. A classe aqui cria uma janela para definição dos parâmetros
#   do processamento e então faz a chamada das funções apropriadas.
#******************************************************************************
from PyQt5 import uic, QtWidgets, QtGui
import matplotlib.pyplot as plt
from Scripts.goes16ProcessData import goes16ProcessData
from datetime import datetime, timedelta
import pandas as pd
import os

UIClass, QtBaseClass = uic.loadUiType("graphGenerator.ui")

class myApp(UIClass, QtBaseClass):
    def __init__(self):
        UIClass.__init__(self)
        QtBaseClass.__init__(self)
        self.setWindowIcon(QtGui.QIcon('Satelite.png'))
        self.setupUi(self)
        self.pBtnCarregar.clicked.connect(self.Executar)
        self.calendarInitialData.selectionChanged.connect(self.new_init_date)
        self.dateEdtFrom.dateChanged.connect(self.new_init_edited_date)
        self.calendarFinalData.selectionChanged.connect(self.new_end_date)
        self.dateEdtTo.dateChanged.connect(self.new_end_edited_date)
        self.dateEdtFrom.setDate(datetime.now())
        self.dateEdtTo.setDate(datetime.now())
        self.dateEdtTo.setMaximumDate(self.calendarInitialData.selectedDate())
        self.calendarFinalData.setMaximumDate(self.calendarInitialData.selectedDate())
    def Executar(self):
        self.pBtnCarregar.setEnabled(False)
        self.txtWorkFolder.setEnabled(False)
        self.dateEdtFrom.setEnabled(False)
        self.dateEdtTo.setEnabled(False)
        self.calendarInitialData.setEnabled(False)
        self.calendarFinalData.setEnabled(False)
        self.gpbxLocal.setEnabled(False)
        self.ckbxEraseData.setEnabled(False)
        self.pgBarProcess.setValue(0)
        data_inicial = datetime.combine(self.calendarInitialData.selectedDate().toPyDate(), datetime.min.time())
        data_final = datetime.combine(self.calendarFinalData.selectedDate().toPyDate(), datetime.min.time())
        latitude = float(self.txtLatitude.text())
        longitude = float(self.txtLongitude.text())
        self.process_thread = goes16ProcessData(data_inicial, data_final, self.txtWorkFolder.text(), latitude, longitude)
        self.process_thread.finished.connect(self.processFinished)
        self.process_thread.update.connect(self.updateProgressBar)
        self.process_thread.start()
    def processFinished(self, processed_data):
        self.pgBarProcess.setValue(100)
        print(processed_data)
        if not os.path.exists(self.txtWorkFolder.text() + "\\Relatórios"):
            os.makedirs(self.txtWorkFolder.text() + "\\Relatórios")
        processed_data.to_csv(path_or_buf=self.txtWorkFolder.text() + "\\Relatórios\\dados.csv",sep=';')
        self.pBtnCarregar.setEnabled(True)
        self.txtWorkFolder.setEnabled(True)
        self.dateEdtFrom.setEnabled(True)
        self.dateEdtTo.setEnabled(True)
        self.calendarInitialData.setEnabled(True)
        self.calendarFinalData.setEnabled(True)
        self.gpbxLocal.setEnabled(True)
        self.ckbxEraseData.setEnabled(True)
    def updateProgressBar(self, value):
        self.pgBarProcess.setValue(value)
    def set_init_date(self):
        self.selected_entry = self.dateEdtFrom
    def new_init_date(self):
        self.dateEdtFrom.setDate(self.calendarInitialData.selectedDate())
        self.dateEdtTo.setMinimumDate(self.calendarInitialData.selectedDate())
        self.calendarFinalData.setMinimumDate(self.calendarInitialData.selectedDate())
    def new_init_edited_date(self, date):
        self.calendarInitialData.setSelectedDate(date)
        self.dateEdtTo.setMinimumDate(date)
        self.calendarFinalData.setMinimumDate(date)
    def new_end_date(self):
        self.dateEdtTo.setDate(self.calendarFinalData.selectedDate())
        self.dateEdtFrom.setMaximumDate(self.calendarFinalData.selectedDate())
        self.calendarInitialData.setMaximumDate(self.calendarFinalData.selectedDate())
    def new_end_edited_date(self, date):
        self.calendarFinalData.setSelectedDate(date)
        self.dateEdtFrom.setMaximumDate(date)
        self.calendarInitialData.setMaximumDate(date)

app = QtWidgets.QApplication([])
window = myApp()
window.show()
app.exec_()