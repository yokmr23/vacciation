import sys
import time
from datetime import date

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.dates import SU
from matplotlib.ticker import MultipleLocator, PercentFormatter
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog,
    QDialogButtonBox, QGridLayout, QLabel,
    QMainWindow, QTableWidget, QTableWidgetItem,
    QTabWidget, QToolBar, QToolTip, QVBoxLayout,
    QWidget)

LINUX_DATE = date(1970, 1, 1).toordinal()
# plt.rcParams['font.family'] = 'Sawarabi Mincho'


class Vaccin:
    """
    ワクチン摂取クラス
    """

    def __init__(self):
        self.df = pd.read_json(
            'https://data.vrs.digital.go.jp'
            '/vaccination/opendata/latest/prefecture.ndjson',
            lines=True, convert_dates=True)
        self.pivot = self.df.pivot_table(
            index='date',
            columns=['prefecture', 'status'],
            values='count', aggfunc=np.sum,
            fill_value=0)
        # 日付別。都道府県(1回目、２回目、３回目)
        # self.pivot_sum = self.pivot.cumsum()
        self.pivot = self.pivot.fillna(0).stack(1)
        self.pivot[0] = self.pivot.sum(axis=1)
        self.pivot = self.pivot.unstack()
        self.pivot_cumsum = self.pivot.cumsum()

        # 日付別、全国(1回目、２回目、３回目、・、・、・)
        self.col = len(self.pivot[0].columns)  # 接種回数
        key = []
        for i in range(1, self.col+1):
            key.append(i)
        # print(f'key={key}')
        # self.row = len(self.pivot[0].columns)

        # 全国、都道府県の人口を取得
        url = 'https://www.soumu.go.jp/main_content/000762463.xlsx'
        self.po = pd.read_excel(url,
                                header=2, index_col=0, skipfooter=2)
        self.po1 = self.po[self.po["性別"] == "計"][['都道府県名', '人']]

        self.po1 = self.po1.reset_index()[['都道府県名', '人']]
        b = self.pivot_cumsum.tail(1).stack(0)
        # b = b.reset_index()[[1, 2, 3, 4]]
        b = b.reset_index()[key]
        self.result = pd.concat([b, self.po1], axis=1)
        for i in range(1, self.col+1):
            str0 = f'percent{i}'
            self.result[str0] = self.result[i]/self.result['人']*100
        self.result.sort_values(
            by=['percent3', 'percent2', 'percent1'],
            ascending=False, inplace=True)
        self.result.reset_index(inplace=True)
        self.dpref = pd.read_csv("prefecture_num.csv",
                                 delimiter=',')

    def get_day(self):
        """
        ワクチン摂取データの日付の最大値、最小値を求める
        戻り値:int 最大年月日、最小年月日
        """
        index = self.pivot.index
        max = index[len(index)-1]
        min = index[0]
        return [min, max]

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
        ワクチン接種　日々の接種数の累計
        引数:int 全国は0、都道府県名は数値 北海道は1、沖縄は47
        戻り値:pandas
        """
        return self.pivot_cumsum[pref_num]

    def vaccin_d(self, pre_num):
        """
        ワクチン接種 日々の接種数
        引数:int 全国は0、都道府県名は数値 北海道は1、沖縄は47
        戻り値:pandas
        """
        return self.pivot[pre_num]

    def get_xaxis(self):
        return self.pivot.reset_index()['date']

    def get_lastday(self):
        a = self.get_day()
        # lastday = df.loc[len(df)-1, 'date']
        return str(a[1])[0:10]

    def get_pre(self, pref):
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

    def get_count_num(self):
        """
        接種　1回目、2 、、、n回目のnを返す
        """
        # print(f'接種回数={self.col}')
        return self.col


class PlotWidget(QWidget):
    def __init__(self, Vaccin, page, parent=None):
        super().__init__(parent)
        self.vaccin = Vaccin
        self.page = page
        self.xpos = -1
        self.disp_lin = None
        self.disp_txt = None
        self.disp_txt1 = None
        self.pref_no = -1
        self.pop = -1
        self.vaccin = Vaccin
        self.tooltip = QToolTip()
        self.fig = plt.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_axes([0.15, .15, .75, .78])
        if self.page == 0:
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
        if self.page == 0:
            wakutin = self.vaccin.vaccin_(self.pref_no)
        else:
            wakutin = self.vaccin.vaccin_d(self.pref_no)
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
                # self.disp_txt.set_text('')
                self.disp_txt1.set_text('')
                # self.disp_lin.set_xdata(0)
                self.tooltip.hideText()
                self.xpos = -1
            else:
                return
        else:
            if self.disp_lin is None:   # 表示オブジェクトがなければ
                # 表示オブジェクト作成
                self.disp_lin = self.ax.axvline(
                    event.xdata, ls='--', lw=0.5, zorder=3)
                bbox = {
                    "boxstyle": "round",
                    "edgecolor": 'black',
                    "facecolor": 'w',
                    "alpha": 0.7,
                }
                self.disp_txt1 = self.ax.text(
                    0.90, 0.02, '',
                    transform=self.fig.transFigure,
                    bbox=bbox,
                    fontsize=8,
                )
            else:  # 表示オブジェクトあり->表示
                day = int(event.xdata+0.5)
                bottom, top = self.vaccin.get_day_coodinate()
                if self.page == 0:
                    if bottom <= day <= top and 0 < event.ydata < 100:
                        ymd, rep = self.get_point_data(day)
                        if rep is not None:  # カーソルのx軸の値がデータにあれば
                            str0 = f'{ymd}'
                            for i in range(self.vaccin.get_count_num()):
                                str0 += f'\n{i+1}回 {int(rep[i+1]):,}'
                            self.tooltip.showText(QCursor().pos(), str0)
                            str0 = f'{ymd}'
                            for i in range(self.vaccin.get_count_num()):
                                str0 += f'\n{i+1}回 '
                                str0 += f'{rep[i+1]/self.pop*100.0:.2f}%'
                            self.disp_txt1.set_text(str0)
                            self.disp_lin.set_xdata(event.xdata)
                            self.xpos = 0
                        else:
                            # self.disp_txt.set_text('')
                            self.disp_txt1.set_text('')
                            self.disp_lin.set_xdata(0)
                            self.tooltip.hideText()
                    else:
                        # self.disp_txt.set_text('')
                        self.disp_txt1.set_text('')
                        self.disp_lin.set_xdata(0)
                        self.tooltip.hideText()
                else:   # page=1 の時
                    if bottom <= day <= top and\
                        self.ax.get_ylim()[0]\
                            < event.ydata < self.ax.get_ylim()[1]:
                        ymd, rep = self.get_point_data(day)
                        if rep is not None:  # カーソルのx軸の値がデータにあれば
                            str0 = f'{ymd}'
                            for i in range(self.vaccin.get_count_num()):
                                str0 += f'\n{i+1}回 {int(rep[i+1]):,}'
                            self.tooltip.showText(QCursor().pos(), str0)
                            self.disp_lin.set_xdata(event.xdata)
                            self.xpos = 0
                        else:
                            self.disp_lin.set_xdata(0)
                            self.tooltip.hideText()
                    else:
                        self.disp_lin.set_xdata(0)
                        self.tooltip.hideText()

        self.canvas.draw()
        time.sleep(0.01)

    def prefecture_num(self):
        """
        comboxの都道府県名から都道府県のローマ字表記を求めて
        draw1関数を呼ぶ
        """
        prefecture = self.combobox.currentText()
        pref_no = self.vaccin.dpref[self.vaccin.dpref.都道府県名 ==
                                    prefecture]['番号']
        try:
            pref_no = pref_no.values[0]
        except IndexError:
            return
        self.draw1(pref_no, prefecture)

    def draw1(self, pref_no, prefecture):
        """
        pref_alphabet: str 都道府県をローマ字　keyとして使う
        prefecture: str 都道府県を漢字
        """
        self.pref_no = pref_no
        self.disp_lin = None
        self.label.setText(f'都道府県コード:{pref_no: ,}')
        pref = self.vaccin.get_pre(prefecture)
        pop = self.vaccin.po[(self.vaccin.po["都道府県名"] == pref)
                             & (self.vaccin.po["性別"] == "計")]
        # 人口を求める
        self.pop = pop["人"].values[0]
        self.label1.setText(f'人口:{self.pop: ,}')
        self.ax.cla()
        if self.page == 0:
            self.twin_ax.cla()
        # wakutin = wakutin_sesshu(pref_no)  # ワクチン接触データ取得
        if self.page == 0:
            wakutin = self.vaccin.vaccin_(pref_no)
        else:
            wakutin = self.vaccin.vaccin_d(pref_no)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(
            byweekday=SU, interval=4, tz=None))
        if self.page == 0:
            self.ax.set_ylim(-self.pop*0.02, self.pop*1.02)
            self.ax.yaxis.set_major_formatter(
                lambda x, pos=None: f'{int(x/10000):,}万')
        else:
            self.ax.yaxis.set_major_formatter(
                lambda x, pos=None: f'{int(x):,}')
        mv = mtransforms.ScaledTranslation(0.1, 0.05, self.fig.dpi_scale_trans)
        for label in self.ax.xaxis.get_majorticklabels():
            label.set_ha('right')
            label.set_rotation(45)
            label.set_fontsize(9)
            label.set_transform(label.get_transform() + mv)
        self.ax.set_title(f'接種回数({pref:s})', y=0.98)
        self.ax.set_ylabel('接種回数')
        # グラフを描く
        la = []  # legend ラベル用
        for i in range(self.vaccin.get_count_num()):
            x = self.vaccin.pivot.index
            l1 = self.ax.bar(x, wakutin[i+1], label=f'{i+1}回目', zorder=2.8)
            la.append(l1)
        self.ax.legend(handles=la,
                       loc='upper left', fontsize=9)

        if self.page == 0:
            ylim = self.ax.get_ylim()
            self.twin_ax.set_ylim(ylim[0]/self.pop*100.,
                                  ylim[1]/self.pop*100.)
            self.twin_ax.yaxis.set_major_locator(MultipleLocator(10.))
            self.twin_ax.yaxis.set_major_formatter(PercentFormatter(100.0))
            self.twin_ax.set_ylabel('人口に対する%')
            self.twin_ax.yaxis.set_zorder(2)
        self.ax.grid(axis='both', zorder=1)
        for label in self.ax.yaxis.get_majorticklabels():
            label.set_fontsize(9)
        if self.page == 0:
            for label in self.twin_ax.yaxis.get_majorticklabels():
                label.set_fontsize(9)
            self.twin_ax.grid(c='grey', alpha=0.5, ls='--',
                              lw=0.5, axis='y', zorder=1)
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
        # print(self.rownum)
        self.tablew.setRowCount(self.rownum)
        colItem1 = ["都道府県名"]
        colLabel = ["都道府県名"]
        for i in range(1, vaccin.get_count_num()+1):
            colItem1.append(i)
            colLabel.append(f'{i}回目')
        for i in range(1, vaccin.get_count_num()+1):
            colItem1.append(f'percent{i}')
            colLabel.append(f'{i}回目(%)')
        # print(colItem1)
        # print(colLabel)
        self.colnum = len(colItem1)
        # print(f'colnum={self.colnum}')
        self.tablew.setColumnCount(self.colnum)
        # alignment = [Qt.AlignVCenter | Qt.AlignCenter,
        #             Qt.AlignRight | Qt.AlignVCenter,
        #             Qt.AlignRight | Qt.AlignVCenter,
        #             Qt.AlignRight | Qt.AlignVCenter,
        #             Qt.AlignRight | Qt.AlignVCenter,
        #             Qt.AlignRight | Qt.AlignVCenter,
        #             Qt.AlignRight | Qt.AlignVCenter,
        #             Qt.AlignRight | Qt.AlignVCenter,
        #             Qt.AlignRight | Qt.AlignVCenter,
        #             ]
        colNum = range(self.colnum)
        alignment = [Qt.AlignVCenter | Qt.AlignCenter]
        for i in range(self.colnum):
            alignment.append(Qt.AlignRight | Qt.AlignVCenter)
        self.tablew.setHorizontalHeaderLabels(colLabel)
        for i in range(self.rownum):
            for j in range(self.colnum):
                # print(f'colnum={self.colnum} j={j}')
                s1 = vaccin.result.loc[i, colItem1[j]]
                if type(s1) is not str:
                    if type(s1) is np.int64:
                        str1 = f'{s1:,}'
                    else:
                        str1 = f'{s1:.1f}%'
                else:
                    str1 = s1
                item = QTableWidgetItem(str1)
                item.setTextAlignment(alignment[j])
                self.tablew.setItem(i, colNum[j], item)


class TabDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.vaccin = Vaccin()
        tab_widget = QTabWidget()
        tab_widget.addTab(PlotWidget(self.vaccin, 0, self), "ワクチン接種日次推移")
        tab_widget.addTab(PlotWidget(self.vaccin, 1, self), "ワクチン接種日次回数")
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
        message = QLabel(
            'データの出展元はデジタル庁です。\n'
            'https://data.vrs.digital.go.jp'
            '/vaccination/opendata/latest/prefecture.ndjson\n'
            '人口のデータ:\n'
            'https://www.soumu.go.jp/main_content/000762463.xlsx\n'
            '2020/4/??')
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
