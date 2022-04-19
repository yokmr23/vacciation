import pandas as pd
import sys
from datetime import date
from matplotlib import pyplot as plt
from matplotlib.dates import SU
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, Slot
from PySide6 import QtCore
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QComboBox,
    QLabel,
    QButtonGroup,
    QGridLayout,
    QPushButton,
    QSlider,
    QToolTip,
    QMainWindow,
    QToolBar,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
)
from matplotlib.dates import DayLocator, WeekdayLocator

LINUX_DATE = date(1970, 1, 1).toordinal()

df = pd.read_csv(
    'https://covid19.mhlw.go.jp/public/opendata/'
    'newly_confirmed_cases_daily.csv',
    parse_dates=['Date'])

dpref = pd.read_csv("prefecture_num.csv",
                    delimiter=',')


class ToolPanel(QWidget):
    button_clicked = Signal(int)

    def __init__(self, *argv, **keywords):
        super(ToolPanel, self).__init__(*argv, **keywords)
        self.group = QButtonGroup()
        gb = QGridLayout()
        data = [
            (0, 0, 0, "1週間"),
            (1, 0, 1, "１ヶ月"),
            (2, 0, 2, "３ヶ月"),
            (3, 0, 3, "１年"),
            (4, 0, 4, "全て")
        ]
        for x, y, id, s in data:
            button = QPushButton(s, self)
            button.setCheckable(True)
            self.group.addButton(button, id)
            gb.addWidget(button, y, x)
        self.setLayout(gb)
        self.group.setExclusive(True)
        self.group.button(3).setChecked(True)
        self.group.buttonClicked.connect(self.changed_button)

    def changed_button(self):
        self.button_clicked.emit(self.group.checkedId())

    def get_id(self):
        return self.group.checkedId()


class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tooltip = QToolTip()
        self.pref_alphabet = 'ALL'
        self.fig = plt.Figure(figsize=(5, 4), dpi=100, tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolpanel = ToolPanel(self)
        self.slider = QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMaximum(100)
        self.slider.setMinimum(0)
        self.slider.setValue(100)
        self.slider.setSingleStep(4)
        # layout = QVBoxLayout()
        self.combobox = QComboBox(self)
        # self.btn1 = QPushButton('OK')
        self.label = QLabel(self)
        self.label1 = QLabel(self)  # 新規感染者数表示
        self.label2 = QLabel(self)  # 一週間平均
        self.label3 = QLabel(self)  # 前週平均
        self.label4 = QLabel(self)  # 前回比表示
        self.label5 = QLabel(self)  # 前週平均比
        # create layout
        glayout = QGridLayout()
        glayout.addWidget(self.toolbar, 0, 0, 1, 4)
        glayout.addWidget(self.toolpanel, 1, 0, 1, 5)
        glayout.addWidget(self.label1, 2, 0, 1, 1)
        glayout.addWidget(self.label2, 2, 1, 1, 1)
        glayout.addWidget(self.label3, 2, 2, 1, 1)
        glayout.addWidget(self.label4, 3, 0, 1, 1)
        glayout.addWidget(self.label5, 3, 1, 1, 1)
        glayout.addWidget(self.canvas, 4, 0, 1, 5)
        glayout.addWidget(self.slider, 5, 0, 1, 5)
        glayout.addWidget(self.combobox, 6, 0, 1, 1)
        glayout.addWidget(self.label, 6, 1, 1, 1)
        glayout.setSpacing(5)
        self.setLayout(glayout)

        self.combobox.setEditable(False)
        # コンボボックスの選択肢を追加
        self.draw1('ALL', '全国')
        self.combobox.addItems(dpref['都道府県名'])
        # self.btn1.clicked.connect(self.prefecture_num)
        self.combobox.currentTextChanged.connect(self.prefecture_num)
        self.toolpanel.button_clicked.connect(self.changeButton)
        self.slider.valueChanged.connect(self.prefecture_num)
        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

    def hover(self, event):
        if self.bar is None or self.ax is not event.inaxes:
            self.tooltip.hideText()
            return
        # print(event.canvas, event.guiEvent)
        if event.xdata is not None and event.ydata is not None:
            w = self.bar.patches[0].get_width()  # 棒グラフの幅
            x = int(event.xdata)
            dif = event.xdata - x
            if dif > w/2 and dif < 1-w/2:
                self.tooltip.hideText()
                return
            if dif > 1-w/2:
                x += 1
            x += LINUX_DATE
            # ymd = date.fromordinal(x)
            ymd = pd.to_datetime(date.fromordinal(x))  # x軸の年月日
            df1 = df[df.Date == ymd]    # その日の感染者数日の集合を取得
            try:
                # 感染者数を求める
                y = df1[self.pref_alphabet].values[0]
            except IndexError:
                # 感染者数を得られなければ
                self.tooltip.hideText()
                return
            if y > event.ydata and event.ydata > 0:
                # マウスカーソルが棒グラうの高さ内にあれば
                ymd = str(ymd)[2:10]
                # ymd = ymd[2:10]
                text = f'{ymd}\n {y:,}'
                self.tooltip.showText(QCursor().pos(), text)
            else:
                self.tooltip.hideText()
        else:
            self.tooltip.hideText()

    def changeButton(self):
        id = self.toolpanel.get_id()
        if id == 4:
            self.slider.setMaximum(100)
            self.slider.setMinimum(100)
        else:
            self.slider.setMaximum(100)
            self.slider.setMinimum(0)
        self.slider.setValue(100)
        self.prefecture_num()

    def prefecture_num(self):
        prefecture = self.combobox.currentText()
        pref_alphabet = dpref[dpref.都道府県名 == prefecture]['Prefecture']
        try:
            pref_alphabet = pref_alphabet.values[0]
        except IndexError:
            return
        self.pref_alphabet = pref_alphabet
        self.draw1(self.pref_alphabet, prefecture)

    def draw1(self, pref_alphabet, prefecture):
        id = self.toolpanel.get_id()
        slider_value = self.slider.value()
        # print(id, slider_value)
        self.label.setText(pref_alphabet)
        # print(df[pref_alphabet])
        n = len(df)-1   # 最終行のindexを求める
        # 最新の感染者数を求める
        y0 = df.at[n, pref_alphabet]
        # 前回の感染者数を求める
        y1 = df.at[n-1, pref_alphabet]
        if y0 > y1:
            str0 = f'↑ {y0-y1:,}'
        else:
            if y0 == y1:
                str0 = '変化なし'
            else:
                str0 = f'↓ {y1-y0:,}'

        self.label1.setText(f'新規感染者数 {y0:,}人')
        self.label4.setText(f'前回比 {str0:}人')
        # 今週の感染者数の一日あたりの平均値(四捨五入)を求める
        ave_one_week = int(
            df.loc[n-6:n, pref_alphabet].mean()+0.5)
        # 前週の感染者数の一日あたりの平均値(四捨五入)を求める
        ave_before_week = int(
            df.loc[n-13:n-7, pref_alphabet].mean()+0.5)
        if ave_one_week > ave_before_week:
            str0 = f'↑ {ave_one_week-ave_before_week:,}'
        else:
            if ave_one_week == ave_before_week:
                str0 == '変化なし'
            else:
                str0 = f'↓ {ave_one_week-ave_before_week:,}'
        self.label2.setText(f'一週間の平均 {ave_one_week:,}人/日')
        self.label3.setText(f'前週の平均 {ave_before_week:,}人/日')
        self.label5.setText(f'前週平均比 {str0}人/日')
        # print(y0, y1)
        self.ax.cla()
        self.ax.yaxis.set_major_formatter(lambda x, pos=None: f'{int(x):,}')
        # formatter = mdates.DateFormatter('%y-%m-%d')
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m-%d'))
        match id:
            case 0:
                self.ax.xaxis.set_major_locator(DayLocator())
            case 1:
                self.ax.xaxis.set_major_locator(WeekdayLocator(
                    byweekday=SU, tz=None))
                self.ax.xaxis.set_minor_locator(DayLocator())
            case 2:
                self.ax.xaxis.set_major_locator(WeekdayLocator(
                    byweekday=SU, interval=2, tz=None))
                self.ax.xaxis.set_minor_locator(DayLocator())
            case 3:
                self.ax.xaxis.set_major_locator(mdates.MonthLocator(
                    bymonthday=1, interval=2))
                self.ax.xaxis.set_minor_locator(mdates.MonthLocator(
                    bymonthday=1
                ))
            case 4:
                self.ax.xaxis.set_major_locator(mdates.MonthLocator(
                    bymonthday=1, interval=4))
                self.ax.xaxis.set_minor_locator(mdates.MonthLocator(
                    bymonthday=1
                ))
        self.ax.tick_params(axis='x', labelrotation=45)
        label0 = self.ax.xaxis.get_majorticklabels()
        for item in label0:
            item.set_ha('right')

        self.ax.set_title(f'日々の感染者数({prefecture})')
        self.ax.set_ylabel('感染者数')
        # グラフ表示データ範囲を求める
        xmax, xmin = self.get_range(len(df), id, slider_value)
        x = df.iloc[xmin:xmax]
        x = x['Date']
        y = df.iloc[xmin:xmax]
        y = y[pref_alphabet]
        self.bar = self.ax.bar(x, y, zorder=3)
        if id == 0:
            for i in range(xmin, xmax):
                self.ax.annotate(
                    f'{y.loc[i]:,}',
                    xy=(x.loc[i], y.loc[i]),
                    xytext=(0, -10),
                    fontsize=8,
                    color='white',
                    textcoords='offset points',
                    bbox={'boxstyle': 'round,pad=0.1', 'ec': 'None'},
                    ha='center')
        self.ax.grid()
        self.canvas.draw()

    def get_range(self, length, id, v):
        if id < 4:
            s = pd.Series([7, 30, 90, 365], index=[0, 1, 2, 3])
            s = s[id]
            xmax = int((length-s)*v/100+s)
            xmin = xmax - s
        else:
            xmax = length
            xmin = 0
        return xmax, xmin


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
        self.setWindowTitle("感染者数")
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
    plotwidge = PlotWidget()
    window = MainWindow(plotwidge)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
