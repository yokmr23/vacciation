from datetime import date
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.transforms as mtransforms
from matplotlib.dates import SU
import time
# from datetime import timedelta
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import PercentFormatter
# from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
)

LINUX_DATE = date(1970, 1, 1).toordinal()
# 人口　https://www.soumu.go.jp/main_content/000762463.xlsx
# po = pd.read_excel('https://www.soumu.go.jp/main_content/000762465.xlsx',
#                   header=2, index_col=0, skipfooter=2)
po = pd.read_excel('https://www.soumu.go.jp/main_content/000762463.xlsx',
                   header=2, index_col=0, skipfooter=2)
# a=po[(po["都道府県名"]=="山口県")&(po["市区町村名"]=="-")&(po["性別"]=="計")]
# print(a["人"].values[0])


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


dpref = pd.read_csv("prefecture_num.csv",
                    delimiter=',')


class Vaccin:
    """
    ワクチン摂取クラス
    """

    def __init__(self):
        self.df = pd.read_json(
            'https://data.vrs.digital.go.jp'
            '/vaccination/opendata/latest/prefecture.ndjson',
            lines=True, convert_dates=True)
        self.pivot_x = self.df.pivot_table(index='date',
                                           columns=['prefecture', 'status'],
                                           values='count', aggfunc=np.sum)
        self.pivot_x = self.pivot_x.fillna(0)
        self.pivot_x = self.pivot_x.cumsum()

        self.pivot_all = self.df.pivot_table(
            index='date', columns='status', values='count', aggfunc=np.sum)
        self.pivot_all = self.pivot_all.fillna(0)
        self.pivot_all = self.pivot_all.cumsum()

    def get_len(self):
        """
        データ長を求める
        戻り値:int データ長
        """
        return len(self.pivot_x)

    def get_day(self):
        """
        ワクチン摂取データの日付の最大値、最小値を求める
        戻り値:int 最大年月日、最小年月日
        """
        index = self.pivot_x.index
        max = index[len(index)-1]
        min = index[0]
        return min, max

    def get_day_coodinate(self):
        """
        ワクチン摂取データの日付の最大値、最小値を求める
        戻り値:int 最大年月日の数値、最小年月日の数値
        """
        min, max = self.get_day()
        max1 = max.toordinal()-LINUX_DATE
        min1 = min.toordinal()-LINUX_DATE
        return min1, max1

    def vaccin(self, pref_num):
        """
        ワクチン接種
        引数:int 全国は0、都道府県名は数値 北海道は1、沖縄は47
        戻り値:pandas
        """
        if pref_num != 0:
            return self.pivot_x[pref_num]
        else:
            return self.pivot_all


class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.xpos = -1
        self.disp_lin = None
        self.disp_txt = None
        self.disp_txt1 = None
        self.pref_no = -1
        self.population = -1
        self.vaccin = Vaccin()
        # self.fig = plt.Figure(figsize=(5, 3), dpi=100, tight_layout=True)
        self.fig = plt.Figure(figsize=(5, 3), dpi=100)
        # self.ax = self.fig.add_subplot(111)
        # left,bottom,width,height
        self.ax = self.fig.add_axes([0.18, .18, .68, .75])
        self.twin_ax = self.ax.twinx()  # y軸右側%を使うため
        self.twin_ax.tick_params()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        # layout = QVBoxLayout()
        self.combobox = QComboBox(self)
        # self.btn1 = QPushButton('OK')
        self.label = QLabel(self)
        self.label1 = QLabel(self)
        # create layout
        layout = QHBoxLayout()
        layout.addWidget(self.combobox)
        # layout.addWidget(self.btn1)
        layout.addWidget(self.label)
        layout.addWidget(self.label1)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        # vlayout.addWidget(self.view)
        vlayout.addWidget(self.canvas)
        vlayout.addLayout(layout)
        self.setLayout(vlayout)

        self.combobox.setEditable(True)
        # コンボボックスの選択肢を追加
        self.draw1(0, '全国')
        self.combobox.addItems(dpref['都道府県名'])
        # self.btn1.clicked.connect(self.prefecture_num)
        self.combobox.currentTextChanged.connect(self.prefecture_num)
        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

    def get_point_data(self, xpos):
        """
        仮引数:x座標の値 日付がordinary
        戻り値:str 日付、１回目、２回目、３回目摂取数
        """
        # wakutin = wakutin_sesshu(self.pref_no)  # ワクチン接触データ取得
        wakutin = self.vaccin.vaccin(self.pref_no)
        xpos += LINUX_DATE
        xpos = int(xpos)
        ymd = pd.to_datetime(date.fromordinal(xpos))  # x軸yy-mm-dd:h:m:sを求める
        try:
            df1 = wakutin.loc[ymd]    # その日の感染者数日の集合を取得
        except IndexError:  # key にymdがなければ、Noneを返す
            return None
        ymd_str = (str(ymd))[0:10]  # 例2021-04-01に変換
        return ymd_str, df1

    def hover(self, event):
        """
        マウスカーソルのグラフ上の値を表示する
        """
        if self.xpos == event.xdata:
            return
        else:
            self.xpos = event.xdata
        if self.disp_lin is None or self.disp_txt is None:
            self.disp_lin = self.ax.axvline(
                event.xdata, ls='--', lw=0.5, zorder=3)
            # self.txt_flag = self.fig.text(
            #    0, 0.03, "",
            #    backgroundcolor='y', fontsize=8, zorder=3)

            self.disp_txt = self.ax.text(0.01, 0.02, '',
                                         transform=self.fig.transFigure,
                                         bbox={
                                             "boxstyle": "round",
                                             "edgecolor": 'black',
                                             "facecolor": 'w',
                                             "alpha": 0.7},
                                         fontsize=8,
                                         )
            self.disp_txt1 = self.ax.text(0.86, 0.02, '',
                                          transform=self.fig.transFigure,
                                          bbox={
                                              "boxstyle": "round",
                                              "edgecolor": 'black',
                                              "facecolor": 'w',
                                              "alpha": 0.7},
                                          fontsize=8,
                                          )

        else:
            if event.xdata is not None:
                day = int(event.xdata)
                bottom, top = self.vaccin.get_day_coodinate()
                if bottom <= day <= top:
                    ymd, rep = self.get_point_data(day)
                    if rep is not None:
                        str0 = f'{ymd}\n'
                        str0 += f'1回{int(rep[1]):,}\n'
                        str0 += f'2回{int(rep[2]):,}\n'
                        str0 += f'3回{int(rep[3]):,}'
                        self.disp_txt.set_text(str0)

                        str0 = f'{ymd}\n'
                        str0 += f'1回{rep[1]/self.population*100.0:.2f}%\n'
                        str0 += f'2回{rep[2]/self.population*100.0:.2f}%\n'
                        str0 += f'3回{rep[3]/self.population*100.0:.2f}%'
                        self.disp_txt1.set_text(str0)
                        self.disp_lin.set_xdata(event.xdata)
                    else:
                        self.disp_txt.set_text('')
                        self.disp_txt1.set_text('')
                        self.disp_lin.set_xdata(0)
                else:
                    self.disp_txt.set_text('')
                    self.disp_txt1.set_text('')
                    self.disp_lin.set_xdata(0)
            else:
                self.disp_txt.set_text('')
                self.disp_txt1.set_text('')
                self.disp_lin.set_xdata(0)
        self.canvas.draw()
        time.sleep(0.01)

    def prefecture_num(self):
        prefecture = self.combobox.currentText()
        pref_no = dpref[dpref.都道府県名 == prefecture]['番号']
        try:
            pref_no = pref_no.values[0]
        except IndexError:
            return
        # print('result={}'.format(pref_no))
        self.draw1(pref_no, prefecture)

    def draw1(self, pref_no, prefecture):
        self.pref_no = pref_no
        self.disp_lin = None
        self.label.setText(f'都道府県コード:{pref_no: ,}')
        pref = get_po(prefecture)
        # print(pref)
        # population = po[(po["都道府県名"] == pref) & (
        #    po["市区町村名"] == "-") & (po["性別"] == "計")]
        popul = po[(po["都道府県名"] == pref) & (po["性別"] == "計")]
        # 人口を求める
        self.population = popul["人"].values[0]
        self.label1.setText(f'人口:{self.population: ,}')
        # print('人口={:,}'.format(population))
        # print(df[pref_alphabet])
        self.ax.cla()
        self.twin_ax.cla()
        # t11, t22, t33 = wakutin_sesshu(pref_no)
        # wakutin = wakutin_sesshu(pref_no)  # ワクチン接触データ取得
        wakutin = self.vaccin.vaccin(pref_no)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(
            byweekday=SU, interval=4, tz=None))
        self.ax.set_ylim(-self.population*0.02, self.population*1.02)
        self.ax.yaxis.set_major_formatter(
            lambda x, pos=None: f'{int(x/10000):,}万')
        mv = mtransforms.ScaledTranslation(0.1, 0.05, self.fig.dpi_scale_trans)
        for label in self.ax.xaxis.get_majorticklabels():
            label.set_ha('right')
            label.set_rotation(45)
            label.set_fontsize(9)
            label.set_transform(label.get_transform() + mv)
        self.ax.set_title(f'接種回数({pref:s})', y=0.98)
        self.ax.set_ylabel('接種回数')
        la = []
        for i in range(3):
            l1, = self.ax.plot(wakutin[i+1], label=f'{i+1}回目', zorder=2.8)
            la.append(l1)
        self.ax.legend(handles=[la[0], la[1], la[2]],
                       loc='upper left', fontsize=9)
        ylim = self.ax.get_ylim()
        self.twin_ax.set_ylim(
            ylim[0]/self.population*100., ylim[1]/self.population*100.)
        self.twin_ax.yaxis.set_major_locator(MultipleLocator(10.))
        self.twin_ax.yaxis.set_major_formatter(PercentFormatter(100.0))
        self.twin_ax.set_ylabel('人口に対する%')
        self.twin_ax.yaxis.set_zorder(2)
        self.ax.grid(axis='both', zorder=2)
        for label in self.ax.yaxis.get_majorticklabels():
            label.set_fontsize(9)
        for label in self.twin_ax.yaxis.get_majorticklabels():
            label.set_fontsize(9)
        self.twin_ax.grid(axis='both', zorder=2)
        self.canvas.draw()


# アプリの実行と終了
app = QApplication()
window = PlotWidget()
window.show()
app.exec()
