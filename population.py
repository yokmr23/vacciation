import sys
import matplotlib
import pandas as pd
# matplotlib.use('Qt5Agg')

from PySide6.QtWidgets import (
    QMainWindow, 
    QApplication,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLineEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

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

def func(tick):
    tick.set_ha('right')
    tick.set_rotation(45)


def autolabel(ax, rects, str_):
    for rect in rects:
        width = rect.get_width()
        ax.annotate('{:,}'.format(width),
                    xy=(width, rect.get_y() + rect.get_height() / 2),
                    xytext=(0, 0),
                    textcoords="offset pixels",
                    ha=str_, va='center',
                    fontsize=6)


def currency(x, pos):
    """The two args are the value and tick position"""
    x /= 10000
    s = '{}万'.format(int(x))
    return s


def currency1(x, pos):
    return '{:,}'.format(int(x))


class population:
    def __init__(self) -> None:
        self.df = pd.read_excel('https://www.soumu.go.jp/main_content/000762465.xlsx',
                   header=2, index_col=0, skipfooter=2)
        # print(df.columns)
        self.male = self.df.iloc[1, 3:]
        self.female = self.df.iloc[2, 3:]
        self.b = ['総数', '0歳～4歳',
            '5歳～9歳', '10歳～14歳', '15歳～19歳', '20歳～24歳', '25歳～29歳', '30歳～34歳',
            '35歳～39歳', '40歳～44歳', '45歳～49歳', '50歳～54歳', '55歳～59歳', '60歳～64歳',
            '65歳～69歳', '70歳～74歳', '75歳～79歳', '80歳～84歳', '85歳～89歳', '90歳～94歳',
            '95歳～99歳', '100歳以上']
    def find_a(self,index,name):
        try:
            if index == 1:
                self.df3 = self.df[self.df.市区町村名 == name]
            else:
                self.df3 = self.df[(self.df.都道府県名 == name) & (self.df.市区町村名 == "-")]
            self.df3 = self.df3.reset_index(drop=True)
            self.s_male = self.df3.iloc[1, 3:]
            self.s_female = self.df3.iloc[2, 3:]
        except:
            msgBox = QMessageBox()
            msgBox.setText(f'{name}が見つかりません')
            msgBox.exec()
            return False
        print(self.s_male.tail())
        return True


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=6, height=6, dpi=100,tight_layout=True):
        self.fig = plt.Figure(figsize=(width, height), dpi=dpi,tight_layout=tight_layout)
        super(MplCanvas, self).__init__(self.fig)
        self.axes1 = self.fig.add_subplot(2,2,1)
        self.axes2 = self.fig.add_subplot(2,2,2)
        self.axes3 = self.fig.add_subplot(2,2,3)
        self.axes4 = self.fig.add_subplot(2,2,4)
        self.axes1.set_position([0.04, 0.58, .4, .35])
        self.axes2.set_position([.57, .58, .4, .35])
        self.axes3.set_position([0.04, 0.1, .4, .35])
        self.axes4.set_position([.57, .1, .4, .35])
        self.popul = population()
    def get_axes(self):
        return self.axes1, self.axes2, self.axes3, self.axes4, self.fig
    def show_population(self,index,city):
        #print(pref,city)
        flag = self.popul.find_a(index,city)
        if flag == False:
            print(f'{city} is Not found!')
            return
        else:
            print(f'{city} is Found')
        self.axes1.cla()
        self.axes2.cla()
        self.axes3.cla()
        self.axes4.cla()
        print('*** plot')
        datasets0 = {
            0: [self.axes1, self.popul.male[1:], '男', 'right', 'b', 5.9e+6, 0],
            1: [self.axes2, self.popul.female[1:], '女', 'left', 'r', 0, 5.9e+6],
            2: [self.axes3, self.popul.s_male[1:], '男', 'right', 'b', 15000, 0],
            3: [self.axes4, self.popul.s_female[1:], '女', 'left', 'r', 0, 15000]
        }
        for label, (ax, pop, s, str_, col_, min_, max_) in datasets0.items():
            p = ax.barh(self.popul.b[1:], pop, label=s, color=col_, zorder=2)
            [func(tick) for tick in ax.get_xticklabels()]
            if (label % 2) == 0:
                ax.invert_xaxis()
                ax.yaxis.tick_right()
                ax.legend(loc=2)
                ax.set_yticklabels([])
            else:
                ax.legend()
                ax.tick_params(axis='y', labelsize=8)
    # ax1.yaxis.tick_labels([])
            ax.tick_params(axis='x', labelsize=8, labelrotation=45)
            autolabel(ax, p, str_)
            ax.grid(axis='x', linestyle='--', lw=0.8, zorder=0.9)
            #ax.set_xlim(min_, max_)
            if label < 2:
                ax.xaxis.set_major_formatter(currency)
            else:
                ax.xaxis.set_major_formatter(currency1)


        self.fig.text(0.5, 0.95, "日本の人口", ha='center', fontsize=14,
             bbox=dict(boxstyle='round', fc='w', ec='k'))
        self.fig.text(0.5, 0.47, f'{city}の人口', ha='center', fontsize=14,
             bbox=dict(boxstyle='round', fc='w', ec='k'))
        self.draw()
    

class MainWindow(QWidget):
    def __init__(self,*args,**kwargs):
        super(MainWindow,self).__init__(*args,**kwargs)
        self.canvas = MplCanvas(self,width=6,height=7,tight_layout=False)
        self.combobox = QComboBox(self)
        self.combobox.addItems(['都道府県名','市町村名'])
        # self.label1 = QLabel('都道府県名')
        # self.label2 = QLabel('都道府県あるいは市町村名')
        # self.input1 = QLineEdit()
        self.input2 = QLineEdit()
        self.ok = QPushButton('OK')
        toolbar = NavigationToolbar2QT(self.canvas, self)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        hlayout = QHBoxLayout()
        #hlayout.addWidget(self.label1)
        #hlayout.addWidget(self.input1)
        #hlayout.addWidget(self.label2)
        hlayout.addWidget(self.combobox)
        hlayout.addWidget(self.input2)
        hlayout.addWidget(self.ok)
        #layout.addWidget(self.combobox)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.ok.clicked.connect(self.a)
        self.canvas.show_population('市町村名','宇部市')
        self.input2.returnPressed.connect(self.a)
        self.show()
    def a(self):
        index = self.combobox.currentIndex()
        city = self.input2.text()
        print(f'input {index},{city}')
        self.canvas.show_population(index,city)
        
app = QApplication(sys.argv)
w = MainWindow()
app.exec()