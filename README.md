# nicolivebot

ニコニコ生放送のコメントを拾うためのPythonスクリプト

# 使用法

Python3.10と`poetry`コマンドが必要です。
Poetryコマンドは`pip install poetry`でインストールできます。(Windowsの場合、Microsoft Store版のPythonだとPoetryが使えないようなので公式版を使ってください。)

以下のようなファイルを作り、`.env`という名前でこのリポジトリのトップ階層に置いておきます。
ここで設定したファイルの中身が、`config.py`の設定に上書きされる形になります。
```
NICONICO_MAIL="niconicoアカウントのメールアドレス"
NICONICO_PASSWORD="niconicoアカウントのパスワード"
```

1. このリポジトリを`git clone`します。
2. `poetry install` で必要モジュールをインストールします。
3. `poetry run python ./nicolivebot/main.py` でプログラムを実行します。

# できること

ニコ生のコメントを監視して、新たにコメントがついたら反応したりとかのプログラムが書けます。