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
import matplotlib.colors as mcolors
from tkinter import ttk


def initialize_mt5():
    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()


def create_date_widgets(parent):
    # create a frame to hold the date widgets
    date_frame = tk.Frame(parent)
    date_frame.pack(pady=10)  # place the frame with some padding

    # create a label for the start date
    start_date_label = tk.Label(date_frame, text="Start Date:")
    start_date_label.grid(
        row=0, column=0, padx=10, pady=10, sticky="E"
    )  # place the label in a grid layout

    # create a date entry widget for the start date
    start_date = DateEntry(
        date_frame,
        width=12,
        background="darkblue",
        foreground="white",
        borderwidth=2,
    )
    start_date.set_date(
        datetime(year=2023, month=1, day=1)
    )  # set the default value to Jan 1, 2023
    start_date.grid(
        row=0, column=1, padx=10, pady=10
    )  # place the widget in a grid layout

    # create a label for the end date
    end_date_label = tk.Label(date_frame, text="End Date:")
    end_date_label.grid(
        row=0, column=2, padx=10, pady=10, sticky="E"
    )  # place the label in a grid layout

    # create a date entry widget for the end date
    end_date = DateEntry(
        date_frame,
        width=12,
        background="darkblue",
        foreground="white",
        borderwidth=2,
    )
    end_date.set_date(datetime.now())  # set the default value to the current date
    end_date.grid(
        row=0, column=3, padx=10, pady=10
    )  # place the widget in a grid layout

    return start_date, end_date  # return the date widgets for later use


def create_plot_button(parent):
    # create a button to plot the data based on the selected dates
    plot_button = tk.Button(
        parent,
        text="Plot Data",
        command=lambda: plot_data(start_date.get_date(), end_date.get_date()),
    )
    plot_button.pack(
        pady=(0, 10), padx=(150, 150)
    )  # place the button with some padding


def create_canvas(parent):
    # create a figure object to hold the graph
    fig = plt.Figure(figsize=(5, 4), dpi=100)

    # create a canvas object to display the figure in tkinter GUI
    canvas = FigureCanvasTkAgg(fig, master=parent)

    return fig, canvas  # return the figure and canvas objects for later use


def fetch_data(start_datetime, end_datetime):
    # get the history deals from MetaTrader 5 terminal within the selected dates
    deals = mt5.history_deals_get(start_datetime, end_datetime)

    # check if there are any deals found
    if deals == None or len(deals) == 0:
        print("No deals found")
        if not mt5.last_error()[0] == 1:
            print("error code={}".format(mt5.last_error()))
        return None  # return None if no data is found
    elif len(deals) > 0:
        print(
            "history_deals_get({}, {},)={}".format(
                start_datetime, end_datetime, len(deals)
            )
        )
        return deals  # return the deals data if found


def convert_data_to_dataframe(deals):
    # convert the deals to a pandas dataframe
    deals = pd.DataFrame(list(deals), columns=deals[0]._asdict())

    return deals  # return the dataframe


def group_data_by_time_and_magic(deals):
    # convert the time column to datetime format
    deals["time"] = pd.to_datetime(deals["time"], unit="s")

    # group the data by time and magic number and sum up the profit values
    filtered_data = deals.groupby([pd.Grouper(key="time", freq="D"), "magic"])

    return filtered_data  # return the grouped data


def plot_data(start_date, end_date):
    global canvas, root, treeview, deals  # use the global canvas variable
    # convert the dates to datetime objects
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.min.time())

    # fetch the data from MetaTrader 5
    deals = fetch_data(start_datetime, end_datetime)

    # check if the data is valid
    if deals is None:
        fig.clear()  # clear the figure
        clear_plot()  # clear the canvas
        if canvas:
            canvas.draw()  # draw the figure on the canvas
        return

    # convert the data to a dataframe
    deals = convert_data_to_dataframe(deals)

    # group the data by time and magic number
    filtered_data = group_data_by_time_and_magic(deals)

    fig.clear()  # clear the figure
    ax = fig.add_subplot(111)
    # plot the profit values as a stacked bar chart and add it to the figure object
    filtered_data["profit"].sum().unstack().plot(ax=ax)

    clear_plot()  # clear the canvas

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()  # draw the figure on the canvas
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH)  # place the canvas widget

    ax.set_title("Total Profit by Magic Number")
    lines = ax.get_lines()
    total_profit_df = filtered_data.sum().groupby("magic").agg({"profit": "sum"})
    mean_profit_df = (
        filtered_data["profit"].mean().groupby("magic").agg(profit="mean").reset_index()
    )
    # configure treeview tags to match chart colors
    for i, line in enumerate(lines):
        tag_name = f"magic_{line.get_label()}"
        color = mcolors.to_hex(line.get_color())
        treeview.tag_configure(tag_name, background=color)

    deals.reset_index()
    positions_count = get_positions(start_date=start_date)
    # clear previous treeview items and insert new items with updated tags
    treeview.delete(*treeview.get_children())
    for magic_number, row in total_profit_df.iterrows():
        mean_mask = mean_profit_df["magic"] == magic_number
        tag_name = f"magic_{magic_number}"
        treeview.insert(
            "",
            "end",
            values=[
                magic_number,
                mean_profit_df[mean_mask]["profit"].values[0],
                row["profit"],
                positions_count.get(magic_number, 0),
            ],
            tags=[tag_name],
        )
        # define columns for the treeview.view widget


# define a function to get positions by magic number
def get_positions(start_date):
    positions = mt5.positions_get()
    if positions == None or len(positions) == 0:
        print("No positions found")
        positions_count = {}
        for magic_number, row in deals.iterrows():
            positions_count[magic_number] = 0
            return positions_count

    # filter positions by start date and group by magic number
    positions_df = pd.DataFrame(list(positions), columns=positions[0]._asdict())
    positions_df["time"] = pd.to_datetime(positions_df["time"], unit="s")
    start_datetime = datetime.combine(start_date, datetime.min.time())
    filtered_positions = positions_df[positions_df["time"] >= start_datetime]

    # count the number of positions for each magic number
    positions_count = filtered_positions.groupby("magic").size()
    return positions_count.to_dict()


def clear_plot():
    global canvas  # use the global canvas variable
    if canvas:
        canvas.get_tk_widget().destroy()  # destroy the widget
    for child in treeview.get_children():
        treeview.delete(child)


def create_tree_view():
    treeview["columns"] = (
        "Magic Number",
        "Mean Daily Profit",
        "Total Profit",
        "Opened Positions",
    )

    # format column headings
    treeview.column("#0", width=0, stretch=tk.NO)
    treeview.column("Magic Number", anchor=tk.CENTER, width=100)
    treeview.column("Mean Daily Profit", anchor=tk.CENTER, width=100)
    treeview.column("Total Profit", anchor=tk.CENTER, width=100)
    treeview.column("Opened Positions", anchor=tk.CENTER, width=100)

    treeview.heading("#0", text="", anchor=tk.CENTER)
    treeview.heading("Magic Number", text="Magic Number", anchor=tk.CENTER)
    treeview.heading("Mean Daily Profit", text="Mean Daily Profit", anchor=tk.CENTER)
    treeview.heading("Total Profit", text="Profit", anchor=tk.CENTER)
    treeview.heading("Opened Positions", text="Positions", anchor=tk.CENTER)

    # pack the treeview.view widget into the root window and display it
    treeview.pack(fill="both", expand=True)


def main():
    global fig, canvas, start_date, end_date, root, treeview  # use global variables for these objects

    initialize_mt5()  # initialize MetaTrader 5

    root = tk.Tk()  # create a root window for the GUI
    treeview = ttk.Treeview(root)

    # maximize the window
    # Set the geometry of frame
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("%dx%d+0+0" % (w, h))
    root.state("zoomed")
    root.eval(
        "tk::PlaceWindow %s center" % root.winfo_toplevel()
    )  # center the window on the screen

    start_date, end_date = create_date_widgets(
        root
    )  # create date widgets and get their values

    create_plot_button(root)  # create plot button

    fig, canvas = create_canvas(root)  # create figure and canvas objects
    create_tree_view()
    root.protocol(
        "WM_DELETE_WINDOW", lambda: [mt5.shutdown(), root.destroy()]
    )  # define a function to close the connection and destroy the window when exiting

    root.mainloop()  # start the main loop of the GUI


if __name__ == "__main__":
    main()
