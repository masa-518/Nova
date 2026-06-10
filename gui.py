import tkinter as tk
from tkinter import messagebox

import matplotlib
import mplfinance as mpf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from tool.logger import get_logger
from tool.stock_data import fetch_daily_prices

matplotlib.rcParams["font.family"] = "Yu Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

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

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

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

        self._plot_candlestick(df, code)

    def _plot_candlestick(self, df, code):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        mpf.plot(df, type="candle", ax=ax, style="yahoo")
        ax.set_title(f"{code} 日足")
        self.figure.autofmt_xdate()
        self.canvas.draw()


def run():
    app = StockApp()
    app.mainloop()
