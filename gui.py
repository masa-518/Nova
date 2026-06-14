import tkinter as tk
from tkinter import messagebox

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from tool.indicators import calculate_bollinger_bands, calculate_macd, calculate_rsi
from tool.logger import get_logger
from tool.predictor import predict_prices
from tool.stock_data import fetch_daily_prices

matplotlib.rcParams["font.family"] = "Yu Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

CHART_STYLE = mpf.make_mpf_style(
    base_mpf_style="yahoo",
    rc={"font.family": "Yu Gothic", "axes.unicode_minus": False},
)

logger = get_logger(__name__)


class StockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("株価分析アプリ")
        self.geometry("900x600")

        self._build_widgets()

    def _build_widgets(self):
        input_frame = tk.Frame(self)
        input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        tk.Label(input_frame, text="銘柄コード:").pack(side=tk.LEFT)

        self.code_entry = tk.Entry(input_frame, width=15)
        self.code_entry.pack(side=tk.LEFT, padx=5)
        self.code_entry.bind("<Return>", lambda event: self.on_search())

        search_button = tk.Button(input_frame, text="表示", command=self.on_search)
        search_button.pack(side=tk.LEFT)

        self.code_entry.focus_set()

        self.canvas = None
        self.chart_frame = tk.Frame(self)
        self.chart_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def on_search(self):
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showwarning("入力エラー", "銘柄コードを入力してください")
            return

        logger.info(f"銘柄コード '{code}' の株価を表示します")

        try:
            df = fetch_daily_prices(code)
        except Exception as e:
            logger.error(f"株価データの取得に失敗しました: {e}")
            messagebox.showerror("エラー", str(e))
            return

        self._plot_chart(df, code)

    def _plot_chart(self, df, code):
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()

        prediction = predict_prices(df)

        extended_index = df.index.append(prediction.index)
        extended_df = df.reindex(extended_index)
        macd_extended = calculate_macd(df).reindex(extended_index)
        bb_extended = calculate_bollinger_bands(df).reindex(extended_index)
        rsi_extended = calculate_rsi(df).reindex(extended_index)

        prediction_series = pd.Series(index=extended_index, dtype=float)
        prediction_series.loc[prediction.index] = prediction.values
        prediction_series.loc[df.index[-1]] = df["Close"].iloc[-1]

        addplots = [
            mpf.make_addplot(bb_extended["Upper"], color="gray", linestyle="--", width=0.8),
            mpf.make_addplot(bb_extended["Lower"], color="gray", linestyle="--", width=0.8),
            mpf.make_addplot(macd_extended["MACD"], panel=1, color="blue", ylabel="MACD"),
            mpf.make_addplot(macd_extended["Signal"], panel=1, color="orange"),
            mpf.make_addplot(macd_extended["Histogram"], type="bar", panel=1, color="gray", alpha=0.5),
            mpf.make_addplot(prediction_series, color="purple", linestyle="--", width=1.5),
            mpf.make_addplot(rsi_extended, panel=2, color="green", ylabel="RSI"),
        ]

        fig, axes = mpf.plot(
            extended_df,
            type="candle",
            mav=(5, 25, 75),
            addplot=addplots,
            panel_ratios=(3, 1, 1),
            style=CHART_STYLE,
            title=f"{code} 日足",
            figsize=(8, 7),
            returnfig=True,
        )

        bottom_ax = self._find_bottom_axis(axes)
        bottom_ax.axhline(30, color="red", linestyle="--", linewidth=0.7)
        bottom_ax.axhline(70, color="red", linestyle="--", linewidth=0.7)

        self._set_weekly_xticks(axes, extended_index, bottom_ax)

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.draw()

        plt.close(fig)

    def _find_bottom_axis(self, axes):
        return min(
            (ax for ax in axes if any(t.get_text() for t in ax.get_xticklabels())),
            key=lambda ax: ax.get_position().y0,
        )

    def _set_weekly_xticks(self, axes, index, bottom_ax):
        week_keys = index.to_series().dt.strftime("%Y-%U")

        tick_positions = []
        tick_labels = []
        last_week = None
        last_pos = None
        for i, week in enumerate(week_keys):
            if week != last_week:
                if last_pos is None or (i - last_pos) >= 3:
                    tick_positions.append(i)
                    tick_labels.append(index[i].strftime("%m/%d"))
                    last_pos = i
                last_week = week

        for ax in axes:
            ax.set_xticks(tick_positions)
            ax.tick_params(labelbottom=False)

        bottom_ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=7)
        bottom_ax.tick_params(labelbottom=True)


def run():
    app = StockApp()
    app.mainloop()
