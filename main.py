import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import MetaTrader5 as mt5
import tkinter as tk
from datetime import datetime
from tkcalendar import DateEntry


# establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

root = tk.Tk()
root.geometry("400x200")

root.eval("tk::PlaceWindow %s center" % root.winfo_toplevel())

date_frame = tk.Frame(root)
date_frame.pack(pady=10)

start_date_label = tk.Label(date_frame, text="Start Date:")
start_date_label.grid(row=0, column=0, padx=10, pady=10, sticky="E")
start_date = DateEntry(
    date_frame, width=12, background="darkblue", foreground="white", borderwidth=2
)
start_date.set_date(datetime(year=2023, month=1, day=1))
start_date.grid(row=0, column=1, padx=10, pady=10)
end_date_label = tk.Label(date_frame, text="End Date:")
end_date_label.grid(row=0, column=2, padx=10, pady=10, sticky="E")
end_date = DateEntry(
    date_frame, width=12, background="darkblue", foreground="white", borderwidth=2
)
end_date.set_date(datetime.now())
end_date.grid(row=0, column=3, padx=10, pady=10)

plot_button = tk.Button(
    root,
    text="Plot Data",
    command=lambda: plot_data(start_date.get_date(), end_date.get_date()),
)
plot_button.pack(pady=(0, 10), padx=(150, 150))

fig = plt.Figure(figsize=(5, 4), dpi=100)


def plot_data(start_date, end_date):
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.min.time())

    deals = mt5.history_deals_get(start_datetime, end_datetime)

    if deals == None:
        print("No deals found", " error code={}".format(mt5.last_error()))
        return
    elif len(deals) > 0:
        print(
            "history_deals_get({}, {},)={}".format(
                start_datetime, end_datetime, len(deals)
            )
        )

    deals = pd.DataFrame(list(deals), columns=deals[0]._asdict())
    deals["time"] = pd.to_datetime(deals["time"], unit="s")

    filtered_data = deals.groupby([pd.Grouper(key="time", freq="D"), "magic"]).sum()
    filtered_data["profit"].unstack().plot(ax=fig.add_subplot(111))

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH)


root.protocol("WM_DELETE_WINDOW", lambda: [mt5.shutdown(), root.destroy()])
root.mainloop()
