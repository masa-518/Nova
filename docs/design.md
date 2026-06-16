# Nova 設計書

## 1. 概要

Nova は、株価データを取得してローソク足チャートとテクニカル指標を表示し、
簡易的な価格予測（5営業日先）を行う Python 製デスクトップアプリケーションである。

- 対象: 日本株（証券コードのみ入力時は東証コードとして自動補完）、および米国株などのティッカーシンボル
- UI: Tkinter によるシンプルな GUI（銘柄コード入力 → チャート表示）
- チャート: ローソク足 + 移動平均線(5/25/75) + ボリンジャーバンド + MACD + RSI + 予測線

## 2. ディレクトリ構成

```
Nova/
├── main.py            # エントリーポイント
├── gui.py             # GUI（Tkinterアプリ本体）
├── tool/
│   ├── stock_data.py  # 株価データ取得
│   ├── indicators.py  # テクニカル指標計算
│   ├── predictor.py   # 価格予測
│   └── logger.py      # ロギング設定
├── log/               # 実行時に生成されるログ出力先（.gitignore対象）
└── .gitignore
```

## 3. 使用技術・主要ライブラリ

| 用途 | ライブラリ |
| --- | --- |
| GUI | tkinter |
| チャート描画 | matplotlib, mplfinance |
| データ処理 | pandas, numpy |
| 株価データ取得 | yfinance |
| 価格予測 | scikit-learn (LinearRegression) |
| ロギング | logging（標準ライブラリ） |

※ `requirements.txt` 等の依存定義ファイルは現状存在しない。

## 4. アーキテクチャ

UI層（gui.py）から `tool` パッケージ内の各モジュール（データ取得・指標計算・予測・ロギング）
を呼び出す、シンプルな関数ベースの構成。

```
main.py
 └─ gui.py (StockApp)
      ├─ tool/stock_data.py   … 株価データ取得
      ├─ tool/indicators.py   … MACD / RSI / Bollinger Bands
      ├─ tool/predictor.py    … 価格予測（内部で indicators を再利用）
      └─ tool/logger.py       … 全モジュール共通のロガー
```

## 5. 機能一覧

| 機能 | 概要 |
| --- | --- |
| 銘柄コード入力・検索 | テキスト入力後、Enter または「表示」ボタンでチャート更新 |
| 株価データ取得 | yfinance から直近6ヶ月の日足データを取得 |
| チャート表示 | ローソク足 + 移動平均線(5/25/75) |
| ボリンジャーバンド表示 | ±2σの上下バンドをチャートに重畳表示 |
| MACDパネル表示 | MACD / Signal / Histogram を別パネルに表示 |
| RSIパネル表示 | RSIを別パネルに表示し、30/70に基準線を表示 |
| 価格予測 | 線形回帰により5営業日先の終値を予測し、点線で表示 |
| ログ出力 | アプリ動作・エラーをファイル＋コンソールへ出力 |
| 入力エラー処理 | 未入力時は警告ダイアログ、取得失敗時はエラーダイアログ |

## 6. モジュール詳細設計

### 6.1 main.py

- アプリケーションのエントリーポイント
- 処理フロー
  1. ロガーを初期化（`get_logger(__name__)`）
  2. 起動ログを出力
  3. `gui.run()` を呼び出し GUI を起動
  4. 終了ログを出力

### 6.2 tool/logger.py

- `get_logger(name) -> logging.Logger`
  - 既にハンドラ登録済みの場合はそのまま返す（重複登録防止）
  - ログレベル: ロガー全体は `DEBUG`
  - 出力先
    - ファイル: `log/{YYYYMMDD_HHMMSS_ffffff}.txt`（`DEBUG`以上）
    - コンソール: 標準出力/標準エラー（`INFO`以上）
  - フォーマット: `YYYY-MM-DD HH:MM:SS [LEVEL] logger名: メッセージ`
  - stdout/stderr を UTF-8 に再設定し、文字コード崩れを防止
  - モジュール読み込み時に `log/` ディレクトリを自動作成

### 6.3 tool/stock_data.py

- `normalize_code(code: str) -> str`
  - 入力文字列をトリム・大文字化
  - 数字のみの場合は `{code}.T`（東証）に変換し、それ以外はそのまま返す
- `fetch_daily_prices(code: str, period: str = "6mo") -> pd.DataFrame`
  - `normalize_code` で正規化したシンボルを `yfinance.Ticker(...).history(period=period, interval="1d")` で取得
  - 取得結果が空の場合は `ValueError` を発生（呼び出し元でエラーダイアログ表示）
  - 取得開始・完了・失敗をログ出力

### 6.4 tool/indicators.py

- `calculate_macd(df, fast=12, slow=26, signal=9) -> pd.DataFrame`
  - 終値のEMA(fast)・EMA(slow)からMACD算出
  - MACDのEMA(signal)をSignal線とし、差分をHistogramとして算出
  - 戻り値カラム: `MACD`, `Signal`, `Histogram`
- `calculate_rsi(df, period=14) -> pd.Series`
  - 終値の差分から上昇/下落分を分離し、EWM（`alpha=1/period`）で平均化
  - RS = 平均上昇 / 平均下落、RSI = 100 - 100/(1+RS)
- `calculate_bollinger_bands(df, window=20, num_std=2.0) -> pd.DataFrame`
  - 終値の単純移動平均（Middle）と標準偏差から Upper/Lower バンドを算出
  - 戻り値カラム: `Middle`, `Upper`, `Lower`

### 6.5 tool/predictor.py

- `predict_prices(df, days=5) -> pd.Series`
  - 特徴量を作成
    - `time`: 行インデックスの連番（時系列トレンド）
    - `MA5` / `MA25` / `MA75`: 終値の移動平均
    - `MACD`: `calculate_macd` の結果
    - `RSI`: `calculate_rsi` の結果
  - 欠損値を含む行を除外（移動平均の計算開始前期間など）したうえで `LinearRegression` を学習
  - 学習データの最終行の特徴量を基準に、`time` のみを `+1`〜`+days` した未来の特徴量を作成し予測
  - 予測対象日付は `pd.bdate_range`（営業日ベース）で算出
  - 戻り値: 予測終値の `pd.Series`（名前: `Prediction`、インデックス: 予測対象日付）

### 6.6 gui.py

- `StockApp(tk.Tk)`
  - ウィンドウ初期化（タイトル「株価分析アプリ」、サイズ 900x600）
  - matplotlib のフォントを "Yu Gothic" に設定（日本語表示対応）
  - `_build_widgets()`
    - 上部: 銘柄コード入力欄（Enterキー対応）＋「表示」ボタン
    - 中央: チャート表示用フレーム
  - `on_search()`
    1. 入力欄の値を取得・トリム
    2. 空文字なら警告ダイアログを表示して終了
    3. `fetch_daily_prices(code)` を呼び出し、例外時はエラーダイアログを表示して終了
    4. `_plot_chart(df, code)` を呼び出してチャート描画
  - `_plot_chart(df, code)`
    1. 既存チャートがあれば破棄
    2. `predict_prices(df)` で予測値を取得
    3. 予測期間分インデックスを拡張し、価格データ・MACD・ボリンジャーバンド・RSIを拡張インデックスに合わせて reindex
    4. 予測線用Series（最終終値 → 予測値）を作成
    5. `mpf.make_addplot` でボリンジャーバンド・MACD（パネル1）・予測線・RSI（パネル2）を構成
    6. `mpf.plot` でローソク足＋移動平均線(5,25,75)を3パネル構成で描画
    7. RSIパネルに30/70の基準線（赤点線）を追加
    8. `_set_weekly_xticks` で週単位のx軸ラベルを設定
    9. `FigureCanvasTkAgg` でTkinterに埋め込み描画
  - `_find_bottom_axis(axes)`
    - x軸ラベルを持つ軸の中で最も下に位置する軸（RSIパネル）を取得
  - `_set_weekly_xticks(axes, index, bottom_ax)`
    - 日付インデックスを `年-週番号` でグルーピングし、週が変わるごとにラベルを表示
    - 直前のラベルから3点未満の間隔は間引き、ラベル密集を防止
    - 最下段の軸にのみ `MM/DD` 形式でラベル表示（45度回転）
  - `run()`
    - `StockApp` を生成し `mainloop()` を開始

## 7. データフロー

```
[ユーザー入力: 銘柄コード]
        │
        ▼
normalize_code()  ──► シンボル正規化（数字のみ→東証コード化）
        │
        ▼
fetch_daily_prices()  ──► yfinanceから直近6ヶ月の日足取得
        │
        ├─► calculate_macd / calculate_rsi / calculate_bollinger_bands
        │
        ├─► predict_prices()  ──► 5営業日先の終値を線形回帰で予測
        │
        ▼
インデックス拡張・reindex（実績＋予測期間）
        │
        ▼
mplfinanceでローソク足＋各指標＋予測線を3パネル描画
        │
        ▼
Tkinterキャンバスへ埋め込み表示
```

## 8. 画面設計

```
┌─────────────────────────────────────────────┐
│ 銘柄コード: [______________]  [表示]          │  ← input_frame
├─────────────────────────────────────────────┤
│                                               │
│  パネル1: ローソク足 + MA5/25/75              │
│           + ボリンジャーバンド + 予測線       │
│                                               │  ← chart_frame
│  パネル2: MACD / Signal / Histogram           │
│                                               │
│  パネル3: RSI（30/70に基準線）                │
│                                               │
└─────────────────────────────────────────────┘
```

- パネル比率: 3 : 1 : 1（価格 : MACD : RSI）
- x軸: 週単位で間引いた `MM/DD` ラベル（最下段パネルのみ表示）

## 9. ログ設計

- 出力先: `log/{実行開始時刻}.txt`（実行ごとに新規ファイル作成）
- ログレベル
  - ファイル: `DEBUG` 以上（データ取得の開始/完了などの詳細を含む）
  - コンソール: `INFO` 以上
- 主なログ出力タイミング
  - アプリ起動・終了
  - 銘柄コード検索実行
  - 株価データ取得の開始・完了・失敗（警告/エラー）

## 10. 例外処理・入力チェック

| ケース | 挙動 |
| --- | --- |
| 銘柄コード未入力 | 警告ダイアログ「銘柄コードを入力してください」を表示し処理中断 |
| データ取得結果が空 | `stock_data.py` 内で `ValueError` を発生 |
| データ取得時の例外全般 | エラーログを出力し、エラーダイアログにメッセージを表示して処理中断 |

## 11. 既知の課題・今後の改善点

- フォント設定（`Yu Gothic`）がWindows依存のため、他OSでは代替フォント指定が必要
- 依存ライブラリを定義した `requirements.txt`（または `pyproject.toml`）が存在しない
- 自動テストが存在しない
- 価格予測は単純な線形回帰モデルであり、予測精度・モデル選定の余地がある
- 取得期間（6ヶ月）や予測期間（5営業日）が定数として固定されており、UIから変更不可
