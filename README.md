# vaccination-jp

## 都道府県別ワクチン接種グラフ化

## データ取得

* ワクチン接種データは`https://info.vrs.digital.go.jp/opendata/` に詳細が記載されている。
* 人口は`https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou_jinkoudoutai-setaisuu.html` の令和3年1月1日住民基本台帳年齢階級別人口（市区町村別）（総計）を用いた。	

## 開発環境

* vscode

* python 3.10
* extensions

```zsh
$pip install pyside6 matplotlib numpy pandas
```

* ソースコード　vaccination.py
* 都道府県名コード　prefecture_num.csv

## 参考資料

* `https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/index.html?highlight=qtwidgets`

* `https://www.pythonguis.com/tutorials/pyside-plotting-matplotlib/`
