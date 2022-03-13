from datetime import date
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.transforms as mtransforms
from matplotlib.dates import SU
import time
from datetime import timedelta
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import PercentFormatter
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

start_time = time.time()
D100 = 1234150
DD1 = 1234150 - 101685
DD2 = 1234150 - 83946
YAXIS_MAX = 1350000
# XAXIS_MAX = date(2021, 11, 14)
# XAXIS_MIN = date(2021, 5, 1)
LINUX_DATE = date(1970, 1, 1).toordinal()


def get_ordinal(a):
    """ a: date array
        return: toordinal """
    x01 = np.array([])
    for item in a:
        x = item.toordinal()-LINUX_DATE
        x01 = np.append(x01, x)
    return x01


def get_yreg(x, a, b):
    """x:date() a:slope b:intercept
       return:y軸の値
    """
    x = x.toordinal()-LINUX_DATE
    return x*a + b


def get_xreg(y, a, b):
    """y:float a:slop, b:intercept"""
    return (y-b)/a
# 人口
po = pd.read_excel('https://www.soumu.go.jp/main_content/000762465.xlsx',
                   header=2, index_col=0, skipfooter=2)
#a=po[(po["都道府県名"]=="山口県")&(po["市区町村名"]=="-")&(po["性別"]=="計")]
#print(a["人"].values[0])
def get_po(pref):
    match pref:
        case '北海道':
            return pref
        case '東京':
            return '東京都'
        case '大阪' | '京都':
            return pref+'府'
        case '全国':
            return '合計'
    return pref+'県'

df = pd.read_json(
    'https://data.vrs.digital.go.jp'
    '/vaccination/opendata/latest/prefecture.ndjson',
    lines=True, convert_dates=True)
# df = pd.read_json('/Users/kimura/Downloads/prefecture.ndjson', lines=True)
dpref = pd.read_csv("prefecture_num.csv",
                    delimiter=',')

def wakutin_sesshu(pref_num):
    """
    ワクチン接種
    """
    if pref_num != 0:
        df1 = df[df.prefecture == pref_num]   # select Yamaguchi prefecture 35
    else:
        df1 = df
    t11 = df1[df1.status == 1]  # Vaccination　first time
    t22 = df1[df1.status == 2]  # Vaccination　second time
    t33 = df1[df1.status == 3]
    t11 = t11.groupby(["date"]).sum()   # group first time in a day
    #print(t11.columns)
    t11.rename(columns={'': ''})
    t22 = t22.groupby(["date"])['count'].sum()   # group second time in a day
    t33 = t33.groupby(['date'])['count'].sum()
    #print(t11.head())
    t11 = t11.cumsum()    # sum first vaccination in a day
    t11 = t11.reset_index()
    t22 = t22.cumsum()    # sum second vaccination in a day
    t22 = t22.reset_index()
    t33 = t33.cumsum()
    #print(t33.tail())
    t33 = t33.reset_index()
    #print(t33.tail())
    return t11, t22, t33




class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = plt.Figure(figsize=(5,3),dpi=100,tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.twin_ax = self.ax.twinx()  # y軸右側%を使うため
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        # layout = QVBoxLayout()
        self.combobox = QComboBox(self)
        #self.btn1 = QPushButton('OK')
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
        self.draw1(0,'全国')
        self.combobox.addItems(dpref['都道府県名'])
        #self.btn1.clicked.connect(self.prefecture_num)
        self.combobox.currentTextChanged.connect(self.prefecture_num)

    def prefecture_num(self):
        prefecture = self.combobox.currentText()
        pref_no = dpref[dpref.都道府県名 == prefecture]['番号']
        try:
            pref_no = pref_no.values[0]
        except:
            return
        # print('result={}'.format(pref_no))
        self.draw1(pref_no, prefecture) 
        
    def draw1(self, pref_no, prefecture):
        self.label.setText(str(pref_no))
        pref=get_po(prefecture)
        #print(pref)
        population=po[(po["都道府県名"]==pref)&(po["市区町村名"]=="-")&(po["性別"]=="計")]
        population=population["人"].values[0]
        print('人口={:,}'.format(population))
        # print(df[pref_alphabet])
        self.ax.cla()
        self.twin_ax.cla()
        t11, t22, t33 = wakutin_sesshu(pref_no)
        #XAXIS_MAX = max(t11['date']) + timedelta(days=2)
        #XAXIS_MIN = XAXIS_MAX - timedelta(days=180)
        formatter = mdates.DateFormatter('%m-%d')
        self.ax.xaxis.set_major_formatter(formatter)
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(
            byweekday=SU, interval=4, tz=None))
        self.ax.set_ylim(-population*0.02,population*1.02)
        self.ax.yaxis.set_major_formatter(lambda x,pos=None:f'{int(x/10000):,}万')
        mv = mtransforms.ScaledTranslation(0.1, 0.05, self.fig.dpi_scale_trans)
        for label in self.ax.xaxis.get_majorticklabels():
            label.set_ha('right')
            label.set_rotation(45)
            label.set_fontsize(10)
            label.set_transform(label.get_transform() + mv)
        self.ax.set_title(f'接種回数({pref:s})')
        self.ax.set_ylabel('接種回数')
        l1,=self.ax.plot(t11['date'], t11['count'],label='1回目')
        l2,=self.ax.plot(t22['date'], t22['count'],label='2回目')
        l3,=self.ax.plot(t33['date'], t33['count'],label='3回目')
        self.ax.legend(handles=[l1,l2,l3])
        ylim=self.ax.get_ylim()
        self.twin_ax.set_ylim(ylim[0]/population*100., ylim[1]/population*100.)
        self.twin_ax.yaxis.set_major_locator(MultipleLocator(10.))
        self.twin_ax.yaxis.set_major_formatter(PercentFormatter(100.0))
        self.twin_ax.set_ylabel('人口に対する%')
        self.ax.grid(axis='x')
        self.twin_ax.grid(axis='y')
        self.canvas.draw()
    

# アプリの実行と終了
app = QApplication()
window = PlotWidget()
window.show()
app.exec()
