import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.dates import SU
import matplotlib.dates as mdates
# from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from PySide6.QtCore import Signal
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QButtonGroup,
    QGridLayout,
    QPushButton,
    QSlider,
)
from matplotlib.dates import DayLocator

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
            (0, 0, 0, "１ヶ月"),
            (1, 0, 1, "３ヶ月"),
            (2, 0, 2, "１年"),
            (3, 0, 3, "全て")
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

        self.fig = plt.Figure(figsize=(5, 3), dpi=100, tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolpanel = ToolPanel(self)
        self.slider = QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMinimum(100)
        self.slider.setMinimum(100)
        self.slider.setValue(100)
        self.slider.setSingleStep(3)
        # layout = QVBoxLayout()
        self.combobox = QComboBox(self)
        # self.btn1 = QPushButton('OK')
        self.label = QLabel(self)
        self.label1 = QLabel(self)
        self.label2 = QLabel(self)
        # create layout
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.combobox)
        # layout.addWidget(self.btn1)
        hlayout.addWidget(self.label)

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.toolpanel)
        vlayout.addWidget(self.label1)
        vlayout.addWidget(self.label2)
        # vlayout.addWidget(self.view)
        vlayout.addWidget(self.canvas)
        vlayout.addWidget(self.slider)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)

        self.combobox.setEditable(True)
        # コンボボックスの選択肢を追加
        self.draw1('ALL', '全国')
        self.combobox.addItems(dpref['都道府県名'])
        # self.btn1.clicked.connect(self.prefecture_num)
        self.combobox.currentTextChanged.connect(self.prefecture_num)
        self.toolpanel.button_clicked.connect(self.changeButton)
        self.slider.valueChanged.connect(self.prefecture_num)

    def changeButton(self):
        # self.slider.setValue = 100
        id = self.toolpanel.get_id()
        if id == 3:
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
        # print('result={}'.format(pref_alphabet))
        self.draw1(pref_alphabet, prefecture)

    def draw1(self, pref_alphabet, prefecture):
        id = self.toolpanel.get_id()
        slider_value = self.slider.value()
        # print(id, slider_value)
        self.label.setText(pref_alphabet)
        # print(df[pref_alphabet])
        # x = df['Date']
        # y = df[pref_alphabet]
        y0 = df.at[len(df)-1, pref_alphabet]
        y1 = df.at[len(df)-2, pref_alphabet]
        if y0 > y1:
            str0 = f'↑ {y0-y1:,}'
        else:
            if y0 == y1:
                str0 = '変化なし'
            else:
                str0 = f'↓ {y1-y0:,}'

        self.label1.setText(f'新規感染者数　{y0:,}人')
        self.label2.setText(f'前回比　{str0:}人')
        # print(y0, y1)
        self.ax.cla()
        self.ax.yaxis.set_major_formatter(lambda x, pos=None: f'{int(x):,}')
        formatter = mdates.DateFormatter('%y-%m-%d')
        self.ax.xaxis.set_major_formatter(formatter)
        s = pd.Series([1, 2, 4, 8], index=[0, 1, 2, 3])
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(
            byweekday=SU, interval=s[id], tz=None))
        self.ax.xaxis.set_minor_locator(DayLocator(interval=s[id]))
        self.ax.tick_params(axis='x', labelrotation=45)
        label0 = self.ax.xaxis.get_majorticklabels()
        for item in label0:
            item.set_ha('right')

        self.ax.set_title(f'日々の感染者数({prefecture:s})')
        self.ax.set_ylabel('感染者数')
        xmax, xmin = self.get_range(len(df), id, slider_value)
        x = df.iloc[xmin:xmax]
        x = x['Date']
        y = df.iloc[xmin:xmax]
        y = y[pref_alphabet]
        self.ax.bar(x, y)
        self.ax.grid()
        self.canvas.draw()

    def get_range(self, length, id, v):
        if id < 3:
            s = pd.Series([30, 90, 365], index=[0, 1, 2])
            s = s[id]
            xmax = int((length-s)*v/100+s)
            xmin = xmax - s
        else:
            xmax = length
            xmin = 0
        return xmax, xmin


# アプリの実行と終了
app = QApplication()
window = PlotWidget()
window.show()
app.exec()
