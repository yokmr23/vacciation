import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QDoubleSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
)

df = pd.read_csv(
    'https://covid19.mhlw.go.jp/public/opendata/'
    'newly_confirmed_cases_daily.csv',
    parse_dates=['Date'])

dpref = pd.read_csv("prefecture_num.csv",
                    delimiter=',')

class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    
        self.fig = plt.Figure(figsize=(5,3),dpi=100,tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        # layout = QVBoxLayout()
        self.combobox = QComboBox(self)
        # self.btn1 = QPushButton('OK')
        self.label = QLabel(self) 
        # create layout
        layout = QHBoxLayout()
        layout.addWidget(self.combobox)
        #layout.addWidget(self.btn1)
        layout.addWidget(self.label)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        #vlayout.addWidget(self.view)
        vlayout.addWidget(self.canvas)
        vlayout.addLayout(layout)
        self.setLayout(vlayout)
        
        self.combobox.setEditable(True)
        # コンボボックスの選択肢を追加
        self.draw1('ALL','全国')
        self.combobox.addItems(dpref['都道府県名'])
        #self.btn1.clicked.connect(self.prefecture_num)
        self.combobox.currentTextChanged.connect(self.prefecture_num)

    def prefecture_num(self):
        prefecture = self.combobox.currentText()
        pref_alphabet = dpref[dpref.都道府県名 == prefecture]['Prefecture']
        try:
            pref_alphabet = pref_alphabet.values[0]
        except:
            return
        #print('result={}'.format(pref_alphabet))
        self.draw1(pref_alphabet, prefecture) 
        
    def draw1(self, pref_alphabet, prefecture):
        self.label.setText(pref_alphabet)
        # print(df[pref_alphabet])
        x = df['Date']
        y = df[pref_alphabet]
        self.ax.cla()
        self.ax.yaxis.set_major_formatter(lambda x,pos=None:f'{int(x):,}')
        self.ax.tick_params(axis='x', labelrotation=30)
        label0 = self.ax.xaxis.get_majorticklabels()
        for item in label0:
            item.set_ha('right')
        
        self.ax.set_title(f'日々の感染者数({prefecture:s})')
        self.ax.set_ylabel('感染者数')
        self.ax.plot(x,y)
        self.ax.grid()
        self.canvas.draw()
    

# アプリの実行と終了
app = QApplication()
window = PlotWidget()
window.show()
app.exec()
