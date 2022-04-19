from datetime import date
import pandas as pd
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.transforms as mtransforms
from matplotlib.dates import SU
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import PercentFormatter
from PySide6.QtGui import QAction
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QToolBar,
    QComboBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QTabWidget,
    QMainWindow,
    QToolTip,
    QGridLayout,
    QDialogButtonBox,
)

LINUX_DATE = date(1970, 1, 1).toordinal()


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
        # 日付別。都道府県(1回目、２回目、３回目)
        self.pivot_x = self.pivot_x.cumsum()

        self.pivot_all = self.df.pivot_table(
            index='date', columns='status', values='count', aggfunc=np.sum)
        self.pivot_all = self.pivot_all.fillna(0)
        # 日付別、全国(1回目、２回目、３回目)
        self.pivot_all = self.pivot_all.cumsum()

        # 人口
        url = 'https://www.soumu.go.jp/main_content/000762463.xlsx'
        self.po = pd.read_excel(url,
                                header=2, index_col=0, skipfooter=2)
        self.po1 = self.po[self.po["性別"] == "計"][['都道府県名', '人']]
        # 都道府県別、ワクチン接種数を1回目、2回目、3回目　のピポットテーブル作成
        self.piv = self.df.pivot_table(index='prefecture', columns='status',
                                       values='count', aggfunc=np.sum)
        self.piv.columns = ['first', 'second', 'third']
        self.piv = self.piv.reset_index()
        self.b = pd.DataFrame({'prefecture': [0], 'first': [
            0], 'second': [0], 'third': [0]})
        self.piv = pd.concat([self.b, self.piv], ignore_index=True)
        self.piv.loc[0, 'first':'third'] = self.piv.loc[1:,
                                                        'first':'third'].sum()

        self.dpref = pd.read_csv("prefecture_num.csv",
                                 delimiter=',')
        # x = pd.concat([piv, dpref], axis=1)
        self.po1 = self.po1.reset_index()[['都道府県名', '人']]
        self.result = pd.concat([self.piv, self.po1], axis=1)
        self.result['percent1'] = self.result['first']/self.result['人']*100
        self.result['percent2'] = self.result['second']/self.result['人']*100
        self.result['percent3'] = self.result['third']/self.result['人']*100

    def get_po(self):
        return self.po

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

    def vaccin_(self, pref_num):
        """
        ワクチン接種
        引数:int 全国は0、都道府県名は数値 北海道は1、沖縄は47
        戻り値:pandas
        """
        if pref_num != 0:
            return self.pivot_x[pref_num]
        else:
            return self.pivot_all

    def get_lastday(self):
        a, b = self.get_day()
        # lastday = df.loc[len(df)-1, 'date']
        return str(b)[0:10]

    def get_lastday_result(self):
        x = self.pivot_x.loc[len(self.pivot_x)-1]
        all = self.pivot_all.loc[len(self.pivot_all)-1]
        return x, all

    def get_po(self, pref):
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


class PlotWidget(QWidget):
    def __init__(self, Vaccin, parent=None):
        super().__init__(parent)
        self.vaccin = Vaccin
        self.xpos = -1
        self.disp_lin = None
        self.disp_txt = None
        self.disp_txt1 = None
        self.pref_no = -1
        self.population = -1
        self.vaccin = Vaccin
        self.tooltip = QToolTip()
        self.fig = plt.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_axes([0.15, .15, .75, .78])
        self.twin_ax = self.ax.twinx()  # y軸右側%を使うため
        self.twin_ax.tick_params()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.combobox = QComboBox(self)
        self.label = QLabel(self)
        self.label1 = QLabel(self)

        self.combobox.setEditable(True)
        glayout = QGridLayout(self)
        glayout.addWidget(self.canvas, 0, 0, 1, 5)
        glayout.addWidget(self.toolbar, 1, 0, 1, 4)
        glayout.addWidget(self.combobox, 2, 0)
        glayout.addWidget(self.label, 2, 1)
        glayout.addWidget(self.label1, 2, 4)
        glayout.setVerticalSpacing(5)
        self.setLayout(glayout)
        # コンボボックスの選択肢を追加
        self.draw1(0, '全国')
        self.combobox.addItems(self.vaccin.dpref['都道府県名'])
        # self.btn1.clicked.connect(self.prefecture_num)
        self.combobox.currentTextChanged.connect(
            self.prefecture_num)
        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

    def get_point_data(self, xpos):
        """
        仮引数:x座標の値 日付がordinary
        戻り値:str 日付、１回目、２回目、３回目摂取数
        """
        # wakutin = wakutin_sesshu(self.pref_no)  # ワクチン接触データ取得
        wakutin = self.vaccin.vaccin_(self.pref_no)
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
        if event.xdata is None:
            if self.xpos != -1:  # 前回表示あり->表示を消す
                self.disp_txt.set_text('')
                self.disp_txt1.set_text('')
                self.disp_lin.set_xdata(0)
                self.xpos = -1
            else:
                return
        else:
            if self.disp_lin is None:   # 表示オブジェクトあれば
                # 表示オブジェクト作成
                self.disp_lin = self.ax.axvline(
                    event.xdata, ls='--', lw=0.5, zorder=3)
                bbox = {
                    "boxstyle": "round",
                    "edgecolor": 'black',
                    "facecolor": 'w',
                    "alpha": 0.7,
                }
                self.disp_txt = self.ax.text(0.01, 0.02, '',
                                             transform=self.fig.transFigure,
                                             bbox=bbox,
                                             fontsize=8,

                                             )
                self.disp_txt1 = self.ax.text(0.90, 0.02, '',
                                              transform=self.fig.transFigure,
                                              bbox=bbox,
                                              fontsize=8,

                                              )
            else:  # 表示オブジェクトあり->表示
                day = int(event.xdata)
                bottom, top = self.vaccin.get_day_coodinate()
                if bottom <= day <= top and 0 < event.ydata < 100:
                    ymd, rep = self.get_point_data(day)
                    if rep is not None:
                        str0 = f'{ymd}'
                        for i in range(3):
                            str0 += f'\n{i+1}回 {int(rep[i+1]):,}'
                        # self.disp_txt.set_text(str0)
                        self.tooltip.showText(QCursor().pos(), str0)
                        str0 = f'{ymd}'
                        for i in range(3):
                            str0 += f'\n{i+1}回 '
                            str0 += f'{rep[i+1]/self.population*100.0: .2f}%'
                        self.disp_txt1.set_text(str0)
                        self.disp_lin.set_xdata(event.xdata)
                    else:
                        self.disp_txt.set_text('')
                        self.disp_txt1.set_text('')
                        self.disp_lin.set_xdata(0)
                        self.tooltip.hideText()
                else:
                    self.disp_txt.set_text('')
                    self.disp_txt1.set_text('')
                    self.disp_lin.set_xdata(0)
                    self.tooltip.hideText()

        self.canvas.draw()
        time.sleep(0.01)

    def prefecture_num(self):
        prefecture = self.combobox.currentText()
        pref_no = self.vaccin.dpref[self.vaccin.dpref.都道府県名 ==
                                    prefecture]['番号']
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
        pref = self.vaccin.get_po(prefecture)
        popul = self.vaccin.po[(self.vaccin.po["都道府県名"] == pref)
                               & (self.vaccin.po["性別"] == "計")]
        # 人口を求める
        self.population = popul["人"].values[0]
        self.label1.setText(f'人口:{self.population: ,}')
        # print('人口={:,}'.format(population))
        # print(df[pref_alphabet])
        self.ax.cla()
        self.twin_ax.cla()
        # wakutin = wakutin_sesshu(pref_no)  # ワクチン接触データ取得
        wakutin = self.vaccin.vaccin_(pref_no)
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


class VaccinTable(QWidget):
    def __init__(self, vaccin, parent: QtWidgets = None):
        super().__init__(parent)
        vaccin = vaccin
        layout = QVBoxLayout()
        self.tablew = QTableWidget()
        self.label = QLabel()
        layout.addWidget(self.tablew)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.label.setText(f'{vaccin.get_lastday()} 時点')
        hheader = QtWidgets.QHeaderView(Qt.Orientation.Horizontal)
        hheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tablew.setHorizontalHeader(hheader)
        vheader = QtWidgets.QHeaderView(Qt.Orientation.Vertical)
        vheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tablew.setVerticalHeader(vheader)
        self.rownum = len(vaccin.result)
        self.tablew.setRowCount(self.rownum)
        # colItem = ["都道府県名", 'first', 'second', 'third']
        colItem1 = ["都道府県名", 'first', 'second',
                    'third', 'percent1', 'percent2', 'percent3']
        self.colnum = len(colItem1)
        self.tablew.setColumnCount(self.colnum)

        colLabel = ["都道府県名", '１回目', '２回目', '３回目',
                    '１回目(%)', '２回目(%)', '３回目(%)']
        alignment = [Qt.AlignVCenter | Qt.AlignCenter,
                     Qt.AlignRight | Qt.AlignVCenter,
                     Qt.AlignRight | Qt.AlignVCenter,
                     Qt.AlignRight | Qt.AlignVCenter,
                     Qt.AlignRight | Qt.AlignVCenter,
                     Qt.AlignRight | Qt.AlignVCenter,
                     Qt.AlignRight | Qt.AlignVCenter]
        colNum = range(self.colnum)
        self.tablew.setHorizontalHeaderLabels(colLabel)
        for i in range(self.rownum):
            # cellsize = QSize(-1, -1)
            # for i in range(1):
            # print(result.loc[i])
            for j in range(self.colnum):
                s1 = vaccin.result.loc[i, colItem1[j]]
                if type(s1) is not str:
                    if type(s1) is np.int64:
                        str1 = f'{s1:,}'
                    else:
                        str1 = f'{s1:.1f}%'
                else:
                    str1 = s1
                item = QTableWidgetItem(str1)
                # item.setSizeHint(cellsize)
                item.setTextAlignment(alignment[j])
                self.tablew.setItem(i, colNum[j], item)
                # item = QTableWidgetItem(str(i*j))
                # self.tablew.setItem(i, j, item)


class TabDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.vaccin = Vaccin()
        tab_widget = QTabWidget()
        tab_widget.addTab(PlotWidget(self.vaccin, self), "ワクチン接種日次推移")
        tab_widget.addTab(VaccinTable(self.vaccin, self), "ワクチン推移状況")

        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        # main_layout.addWidget(button_box)
        self.setLayout(main_layout)
        self.setWindowTitle("ワクチン接種")


class HelpDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Help')
        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.layout = QVBoxLayout()
        message = QLabel('By Y.Kimura 2022 April')
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("ワクチン摂取")
        self.toolbar = QToolBar("Qt bar")
        self.addToolBar(self.toolbar)
        button_action = QAction('Exit', self)
        button_action.triggered.connect(lambda x: self.exit_app("End!"))
        button_action.setChecked(True)
        self.toolbar.addAction(button_action)
        button_action2 = QAction('Help', self)
        button_action2.triggered.connect(lambda x: self.help('Help'))
        self.toolbar.addAction(button_action2)
        self.setCentralWidget(widget)

    @ Slot()
    def exit_app(self, s):
        print(s)
        QApplication.quit()

    @ Slot()
    def help(self, s):
        print(s)
        dlg = HelpDialog()
        dlg.resize(50, 100)
        dlg.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tabdialog = TabDialog()
    window = MainWindow(tabdialog)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
