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
import webbrowser

tabs_list = ["Sum Profit", "Mean Profit"]


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


def read_data_file():
    try:
        with open("data.txt", "r") as f:
            data = eval(f.read())
    except FileNotFoundError:
        data = {}
    return data


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


# define a function to plot the data based on the selected dates
def plot_data(start_date, end_date):
    global tab_control, fig, canvas, root, treeview, deals
    set_connection_status()
    # use the global canvas variable
    # convert the dates to datetime objects
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.min.time())
    # fetch the data from MetaTrader 5
    deals = fetch_data(start_datetime, end_datetime)
    if deals == None or len(deals) == 0:
        clear_all()
        return
    # convert the data to a dataframe
    deals = convert_data_to_dataframe(deals)
    # check if there is a data.txt file saved from the save_data function
    try:
        # read the data dictionary from the file
        data = read_data_file()
        # replace the magic field with the alias and magic number in the format of {alias} - ({magic})
        deals["magic"] = deals["magic"].apply(
            lambda x: f"{data.get(str(x), {}).get('alias', '')} - ({x})"
        )
        # filter out the deals that have a state of 0 in the data.txt file
        deals = deals[
            deals["magic"].apply(
                lambda x: data.get(x.split(" - ")[-1][1:-1], {}).get("state", 1) == 1
            )
        ]
    except FileNotFoundError:
        # if there is no data.txt file, do nothing
        pass
    # group the data by time and magic number and sum up the profit values
    filtered_data = group_data_by_time_and_magic(deals)
    # clear the treeview
    treeview.delete(*treeview.get_children())
    # create a tab container to hold the plots
    # create a new figure for each tab
    fig.clear()
    for title, data in [
        (tabs_list[0], filtered_data["profit"].sum()),
        (tabs_list[1], filtered_data["profit"].mean()),
    ]:
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        data.unstack().plot(ax=ax)
        ax.set_title(title + " by Magic Number")
        # create a new canvas for each tab
        # add the canvas to the tab and the tab to the tab control
        for tab in tab_control.tabs():
            if tab_control.tab(tab, "text") == title:
                tab_frame = tab_control.nametowidget(tab)
                for tab_child in tab_frame.winfo_children():
                    tab_child.destroy()
                canvas = FigureCanvasTkAgg(fig, master=tab_frame)
                canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                canvas.draw()
        lines = ax.get_lines()
        total_profit_df = filtered_data.sum().groupby("magic").agg({"profit": "sum"})
        mean_profit_df = (
            filtered_data["profit"]
            .mean()
            .groupby("magic")
            .agg(profit="mean")
            .reset_index()
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


def clear_all():
    # clear all tabs
    for tab in tab_control.tabs():
        tab_frame = tab_control.nametowidget(tab)
        for tab_child in tab_frame.winfo_children():
            tab_child.destroy()
    for child in treeview.get_children():
        treeview.delete(child)


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
    global canvas
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


# define a function to create an options menu
def create_options_menu():
    # create a menu bar
    menu_bar = tk.Menu(root)

    # create an options menu
    options_menu = tk.Menu(menu_bar, tearoff=0)

    # add a command to the options menu to open a panel for getting deals history
    options_menu.add_command(
        label="Edit filters",
        command=lambda: filters_window.focus_set()
        if filters_window
        else show_edit_filters_window(),
    )

    # add a command to the options menu to open a panel for showing information
    options_menu.add_command(
        label="Show information",
        command=lambda: info_window.focus_set() if info_window else show_information(),
    )

    # add the options menu to the menu bar
    menu_bar.add_cascade(label="Options", menu=options_menu)

    # configure the root window to display the menu bar
    root.config(menu=menu_bar)


def clear_filters_window():
    global filters_window
    filters_window.destroy()
    filters_window = None


def clear_info_window():
    global info_window
    info_window.destroy()
    info_window = None


# define a function to get the deals of the full history from MT5
def show_edit_filters_window():
    global filters_window
    # get the deals as a pandas dataframe
    mt_deals = fetch_data(0, datetime.now())
    deals = convert_data_to_dataframe(mt_deals)
    # get the unique magic values as a list
    magic_values = sorted(deals["magic"].unique().tolist())
    filters_window = tk.Toplevel()
    filters_window.title("Edit Filters")
    filters_window.protocol(
        "WM_DELETE_WINDOW",
        clear_filters_window,
    )
    # update the window to get the correct size
    center_window(filters_window, w=500)
    # create a frame for the grid layout
    grid_frame = tk.Frame(filters_window)
    # create a list of checkboxes, labels, and entries for each magic value
    checkboxes = []
    checkboxes_states = []
    labels = []
    entries = []
    # loop through the magic values
    for i, magic in enumerate(magic_values):
        # create a checkbox with the value of the magic
        variable = tk.IntVar()
        checkbox = tk.Checkbutton(
            grid_frame, text=str(magic), variable=variable, padx=10, pady=10
        )
        # create a label with the text "Magic:"
        label = tk.Label(grid_frame, text="Alias:", padx=10, pady=10)
        # create an entry for the user to write an alias for the magic
        entry = tk.Entry(grid_frame)
        # add the checkbox, label, and entry to their respective lists
        checkboxes.append(checkbox)
        labels.append(label)
        entries.append(entry)
        checkboxes_states.append(variable)
        # place the checkbox, label, and entry in the grid layout
        checkbox.grid(row=i, column=0)
        label.grid(row=i, column=1)
        entry.grid(row=i, column=2)
        # check if there is a data.txt file saved from the save_data function
    try:
        # open the file for reading
        with open("data.txt", "r") as f:
            # read the data dictionary from the file
            data = eval(f.read())
            # loop through the checkboxes and entries
            for checkbox, entry in zip(checkboxes, entries):
                # get the value of the checkbox
                magic = checkbox.cget("text")
                # get the data for the magic value
                magic_data = data.get(magic, None)
                # if there is data for the magic value
                if magic_data:
                    # set the checkbox state according to the state field in the data
                    checkbox_state = magic_data.get("state", 0)
                    checkbox.invoke() if checkbox_state else None
                    # set the alias input according to the alias field in the data
                    alias = magic_data.get("alias", "")
                    entry.insert(0, alias)

    except FileNotFoundError:
        for checkbox, entry in zip(checkboxes, entries):
            # get the value of the checkbox
            magic = checkbox.cget("text")
            # get the data for the magic value
            checkbox_state = 1
            checkbox.invoke() if checkbox_state else None
            # set the alias input according to the alias field in the data

            entry.insert(0, "")
    # create a frame for the buttons
    button_frame = tk.Frame(filters_window)
    # create a button to cancel and close the window
    cancel_button = tk.Button(
        button_frame, text="Cancel", command=filters_window.destroy, padx=10, pady=10
    )
    # create a button to save the checkboxes and aliases to a file and plot the data
    save_button = tk.Button(
        button_frame,
        text="Save",
        command=lambda: [
            save_data(checkboxes, entries, checkboxes_states),
            plot_data(start_date.get_date(), end_date.get_date()),
            filters_window.destroy(),
        ],
        padx=10,
        pady=10,
    )
    # place the buttons in the frame
    cancel_button.pack(side=tk.LEFT)
    save_button.pack(side=tk.RIGHT)
    # place the frames in the window
    grid_frame.pack()
    button_frame.pack()


# define a function to show information about the project and the developer
def show_information():
    global info_window
    info_window = tk.Toplevel()
    info_window.title("Information")
    info_window.protocol(
        "WM_DELETE_WINDOW",
        clear_info_window,
    )
    center_window(info_window, w=800, h=300)

    project_label = tk.Label(
        info_window,
        text="This is a project for plotting data about Expert Advisors running in the MetaTrader5 terminal.",
        padx=10,
        pady=10,
    )
    developer_label1 = tk.Label(
        info_window,
        text="The developer is Thiago Santana, a software engineer and data analyst. He is passionate about creating solutions with Python and other technologies.",
        padx=10,
        pady=10,
    )
    developer_label2 = tk.Label(
        info_window,
        text="He is passionate about creating solutions with Python and other technologies.",
        padx=10,
    )
    # create a label with the text "You can find the source code of this project on GitHub:"
    github_label = tk.Label(
        info_window,
        text="You can find the source code of this project on GitHub:",
        padx=10,
        pady=10,
    )
    # create a hyperlink to the GitHub repository
    github_link = tk.Label(
        info_window,
        text="[ExpertStatistics](https://github.com/ThiDiamondDev/ExpertStatistics)",
        fg="blue",
        cursor="hand2",
        padx=10,
        pady=10,
    )
    github_link.bind(
        "<Button-1>",
        lambda e: webbrowser.open_new(
            "https://github.com/ThiDiamondDev/ExpertStatistics"
        ),
    )
    # create a label with the text "You can also connect with the developer on LinkedIn:"
    linkedin_label = tk.Label(
        info_window,
        text="You can also connect with the developer on LinkedIn:",
        padx=10,
        pady=10,
    )
    # create a hyperlink to the developer's LinkedIn profile
    linkedin_link = tk.Label(
        info_window,
        text="[Thiago Santana](https://www.linkedin.com/in/thidiamond/)",
        fg="blue",
        cursor="hand2",
        padx=10,
        pady=10,
    )
    linkedin_link.bind(
        "<Button-1>",
        lambda e: webbrowser.open_new("https://www.linkedin.com/in/thidiamond/"),
    )
    # place the labels in the window
    project_label.pack()
    developer_label1.pack()
    developer_label2.pack()
    github_label.pack()
    github_link.pack()
    linkedin_label.pack()
    linkedin_link.pack()


def center_window(window, w=None, h=None):
    # update the window to get the correct size
    window.update_idletasks()
    # get the width and height of the window
    if w:
        width = w
    else:
        width = window.winfo_width()
    if h:
        height = h
    else:
        height = window.winfo_height()
    # get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    # calculate the x and y coordinates to center the window
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    # set the geometry of the window
    window.geometry(f"{width}x{height}+{x}+{y}")


# define a function to save the checkboxes and aliases to a file
def save_data(checkboxes, entries, states):
    # create an empty dictionary to store the data
    data = {}

    # loop through the checkboxes and entries
    for checkbox, entry, state in zip(checkboxes, entries, states):
        # get the value of the checkbox
        magic = checkbox.cget("text")

        # get the alias of the entry
        alias = entry.get()

        # add the value and alias to the data dictionary
        data[magic] = {"alias": alias, "state": int(state.get())}

    # open a file for writing
    with open("data.txt", "w") as f:
        # write the data dictionary to the file
        f.write(str(data))


def set_connection_status():
    terminal_info = mt5.terminal_info()
    if terminal_info != None:
        terminal_info_dict = mt5.terminal_info()._asdict()
        connection_status = terminal_info_dict["connected"]
        if connection_status:
            root.title(
                "Expert Statistics (CONNECTED) - Last Update: {}".format(
                    datetime.now().strftime("%d/%m/%y %H:%M:%S")
                )
            )
            return

    root.title("Expert Statistics (DISCONNECTED)")


def main():
    global tab_control, connection_status, fig, canvas, start_date, end_date, root, treeview, filters_window, info_window  # use global variables for these objects

    initialize_mt5()  # initialize MetaTrader 5

    filters_window = None
    info_window = None
    root = tk.Tk()  # create a root window for the GUI

    create_options_menu()
    treeview = ttk.Treeview(root)

    tab_control = ttk.Notebook(root)

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
    tab_control.pack(fill="both", expand=True)
    # create a new figure for each tab
    for title in tabs_list:
        frame = ttk.Frame(tab_control)
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        tab_control.add(frame, text=title)
    # pack the tab control widget into the root window and display it
    root.protocol(
        "WM_DELETE_WINDOW", lambda: [mt5.shutdown(), root.destroy()]
    )  # define a function to close the connection and destroy the window when exiting
    plot_data(start_date.get_date(), end_date.get_date()),
    root.mainloop()  # start the main loop of the GUI


if __name__ == "__main__":
    main()
