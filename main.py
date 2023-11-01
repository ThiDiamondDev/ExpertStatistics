# import the required modules
import matplotlib.pyplot as plt  # for plotting graphs
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
)  # for embedding graphs in tkinter GUI
import pandas as pd  # for data manipulation and analysis
import MetaTrader5 as mt5  # for accessing MetaTrader 5 terminal data
import tkinter as tk  # for creating graphical user interface
from datetime import datetime  # for working with dates and times
from tkcalendar import DateEntry  # for creating calendar widgets

# establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

canvas = None
# create a root window for the GUI
root = tk.Tk()
root.geometry("600x400")  # set the window size
root.eval(
    "tk::PlaceWindow %s center" % root.winfo_toplevel()
)  # center the window on the screen

# create a frame to hold the date widgets
date_frame = tk.Frame(root)
date_frame.pack(pady=10)  # place the frame with some padding

# create a label for the start date
start_date_label = tk.Label(date_frame, text="Start Date:")
start_date_label.grid(
    row=0, column=0, padx=10, pady=10, sticky="E"
)  # place the label in a grid layout

# create a date entry widget for the start date
start_date = DateEntry(
    date_frame, width=12, background="darkblue", foreground="white", borderwidth=2
)
start_date.set_date(
    datetime(year=2023, month=1, day=1)
)  # set the default value to Jan 1, 2023
start_date.grid(row=0, column=1, padx=10, pady=10)  # place the widget in a grid layout

# create a label for the end date
end_date_label = tk.Label(date_frame, text="End Date:")
end_date_label.grid(
    row=0, column=2, padx=10, pady=10, sticky="E"
)  # place the label in a grid layout

# create a date entry widget for the end date
end_date = DateEntry(
    date_frame, width=12, background="darkblue", foreground="white", borderwidth=2
)
end_date.set_date(datetime.now())  # set the default value to the current date
end_date.grid(row=0, column=3, padx=10, pady=10)  # place the widget in a grid layout

# create a button to plot the data based on the selected dates
plot_button = tk.Button(
    root,
    text="Plot Data",
    command=lambda: plot_data(start_date.get_date(), end_date.get_date()),
)
plot_button.pack(pady=(0, 10), padx=(150, 150))  # place the button with some padding

# create a figure object to hold the graph
fig = plt.Figure(figsize=(5, 4), dpi=100)


def clear_plot():
    global canvas
    if canvas:
        canvas.get_tk_widget().destroy()
    canvas = None


# define a function to plot the data based on the selected dates
def plot_data(start_date, end_date):
    global canvas
    # convert the dates to datetime objects
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.min.time())

    # get the history deals from MetaTrader 5 terminal within the selected dates
    deals = mt5.history_deals_get(start_datetime, end_datetime)

    # check if there are any deals found
    if deals == None or len(deals) == 0:
        print("No deals found")
        if not mt5.last_error()[0] == 1:
            print("error code={}".format(mt5.last_error()))
        fig.clear()
        clear_plot()
        if canvas:
            canvas.draw()  # draw the figure on the canvas
        return
    elif len(deals) > 0:
        print(
            "history_deals_get({}, {},)={}".format(
                start_datetime, end_datetime, len(deals)
            )
        )

        # convert the deals to a pandas dataframe
        deals = pd.DataFrame(list(deals), columns=deals[0]._asdict())

        # convert the time column to datetime format
        deals["time"] = pd.to_datetime(deals["time"], unit="s")

        # group the data by time and magic number and sum up the profit values
        filtered_data = deals.groupby([pd.Grouper(key="time", freq="D"), "magic"]).sum()
        fig.clear()
        # plot the profit values as a stacked bar chart and add it to the figure object
        filtered_data["profit"].unstack().plot(ax=fig.add_subplot(111))

        clear_plot()
        # create a canvas object to display the figure in tkinter GUI
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()  # draw the figure on the canvas
        canvas.get_tk_widget().pack(
            side=tk.TOP, fill=tk.BOTH
        )  # place the canvas widget


# define a function to close the connection and destroy the window when exiting
root.protocol("WM_DELETE_WINDOW", lambda: [mt5.shutdown(), root.destroy()])

# start the main loop of the GUI
root.mainloop()
