# import the required modules
import tkinter as tk  # for creating graphical user interface
from tkcalendar import DateEntry  # for creating calendar widgets
import matplotlib.pyplot as plt  # for plotting graphs
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
)  # for embedding graphs in tkinter GUI
import webbrowser  # for opening links in browser
from tkinter import ttk  # for creating treeview and notebook widgets
from datetime import datetime, date
from mt import MT5
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import re


# define a class for creating and displaying the graphical user interface
class GUI:
    def __init__(self, root: tk.Tk, mt5: MT5):
        self.root = root  # the root window of the GUI
        self.mt5 = mt5  # the MT5 object for accessing the data
        self.tabs_list = [
            "Sum Profit",
            "Mean Profit",
            "Profit Goal",
        ]  # the list of tabs for the plots
        self.filters_window = None  # the window for editing the filters
        self.info_window = None  # the window for showing the information
        self.create_options_menu()  # create the options menu
        self.treeview = ttk.Treeview(root)  # create the treeview widget
        self.tab_control = ttk.Notebook(root)  # create the notebook widget
        self.start_date, self.end_date = self.create_date_widgets(
            root
        )  # create date widgets and get their values
        self.create_plot_button(root)  # create plot button
        self.fig, self.canvas = self.create_canvas(
            root
        )  # create figure and canvas objects
        self.create_tree_view()  # create the tree view widget
        self.tab_control.pack(
            fill="both", expand=True
        )  # pack the tab control widget into the root window and display it
        # create a new figure for each tab
        for title in self.tabs_list:
            frame = ttk.Frame(self.tab_control)
            frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            self.tab_control.add(frame, text=title)

    def create_date_widgets(self, parent):
        # create a frame to hold the date widgets
        date_frame = tk.Frame(parent)
        date_frame.pack(pady=10)
        # place the frame with some padding
        # create a label for the start date
        start_date_label = tk.Label(date_frame, text="Start Date:")
        start_date_label.grid(row=0, column=0, padx=10, pady=10, sticky="E")
        # place the label in a grid layout
        # create a date entry widget for the start date
        start_date = DateEntry(
            date_frame,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
        )
        start_date.set_date(datetime(year=2023, month=1, day=1))
        # set the default value to Jan 1, 2023
        start_date.grid(row=0, column=1, padx=10, pady=10)
        # place the widget in a grid layout
        # create a label for the end date
        end_date_label = tk.Label(date_frame, text="End Date:")
        end_date_label.grid(row=0, column=2, padx=10, pady=10, sticky="E")
        # place the label in a grid layout
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

    def create_plot_button(self, parent):
        # create a button to plot the data based on the selected dates
        plot_button = tk.Button(
            parent,
            text="Plot Data",
            command=lambda: self.plot_data(
                self.start_date.get_date(), self.end_date.get_date()
            ),
        )
        plot_button.pack(
            pady=(0, 10), padx=(150, 150)
        )  # place the button with some padding

    def create_plot_button(self, parent):
        # create a button to plot the data based on the selected dates
        plot_button = tk.Button(parent, text="Plot Data", command=self.plot_data)
        plot_button.pack(
            pady=(0, 10), padx=(150, 150)
        )  # place the button with some padding

    def create_canvas(self, parent):
        # create a figure object to hold the graph
        self.fig = plt.Figure(figsize=(5, 4), dpi=100)

        # create a canvas object to display the figure in tkinter GUI
        canvas = FigureCanvasTkAgg(self.fig, master=parent)

        return self.fig, canvas  # return the figure and canvas objects for later use

    def read_data_file(self):
        try:
            with open("data.txt", "r") as f:
                data = eval(f.read())
                return data
        except FileNotFoundError:
            return None

    # define a function to plot the data based on the selected dates
    def plot_data(self):
        is_connected, connection_string = self.mt5.get_connection()
        self.root.title(connection_string)
        if not is_connected:
            self.mt5.initialize()
            is_connected, connection_string = self.mt5.get_connection()
            self.root.title(connection_string)
            if not is_connected:
                return

        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        # convert the dates to datetime objects
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.min.time())
        if end_datetime.date() == date.today():
            end_datetime = datetime.now()
        # fetch the data from MetaTrader 5
        deals = self.mt5.fetch_data(start_datetime, end_datetime)
        if deals == None or len(deals) == 0:
            self.clear_all()
            return
        # check if there is a data.txt file saved from the save_data function
        # read the data dictionary from the file
        saved_data = self.read_data_file()
        deals = self.mt5.get_filtered_deals(saved_data, deals)
        # group the data by time and magic number and sum up the profit values
        filtered_data = self.mt5.group_data_by_time_and_magic(deals)
        # clear the treeview
        self.treeview.delete(*self.treeview.get_children())
        # create a tab container to hold the plots
        # create a new figure for each tab
        self.fig.clear()
        for i, title, data in self.mt5.get_plot_data(
            saved_data, self.tabs_list, filtered_data
        ):
            self.fig = plt.Figure(figsize=(5, 4), dpi=100)
            ax = self.fig.add_subplot(111)
            data.unstack().plot(ax=ax)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

            # rotate the x-axis labels for better visibility
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            ax.set_title(title + " by Magic Number")
            # create a new canvas for each tab
            # add the canvas to the tab and the tab to the tab control
            tab = self.tab_control.tabs()[i]
            if self.tab_control.tab(tab, "text") == title:
                tab_frame = self.tab_control.nametowidget(tab)
                for tab_child in tab_frame.winfo_children():
                    tab_child.destroy()
                canvas = FigureCanvasTkAgg(self.fig, master=tab_frame)
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
            self.treeview.tag_configure(tag_name, background=color)
            # deals.reset_index()
        positions_count = self.mt5.get_positions(start_date, deals)
        # clear previous treeview items and insert new items with updated tags
        self.treeview.delete(*self.treeview.get_children())
        for magic_number, row in total_profit_df.iterrows():
            mean_mask = mean_profit_df["magic"] == magic_number
            tag_name = f"magic_{magic_number}"
            self.treeview.insert(
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

    def clear_all(self):
        # clear all tabs
        for tab in self.tab_control.tabs():
            tab_frame = self.tab_control.nametowidget(tab)
            for tab_child in tab_frame.winfo_children():
                tab_child.destroy()
        for child in self.treeview.get_children():
            self.treeview.delete(child)

    def clear_plot(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()  # destroy the widget
        for child in self.treeview.get_children():
            self.treeview.delete(child)

    def create_tree_view(self):
        self.treeview["columns"] = (
            "Magic Number",
            "Mean Daily Profit",
            "Total Profit",
            "Opened Positions",
        )

        # format column headings
        self.treeview.column("#0", width=0, stretch=tk.NO)
        self.treeview.column("Magic Number", anchor=tk.CENTER, width=100)
        self.treeview.column("Mean Daily Profit", anchor=tk.CENTER, width=100)
        self.treeview.column("Total Profit", anchor=tk.CENTER, width=100)
        self.treeview.column("Opened Positions", anchor=tk.CENTER, width=100)

        self.treeview.heading("#0", text="", anchor=tk.CENTER)
        self.treeview.heading("Magic Number", text="Magic Number", anchor=tk.CENTER)
        self.treeview.heading(
            "Mean Daily Profit", text="Mean Daily Profit", anchor=tk.CENTER
        )
        self.treeview.heading("Total Profit", text="Profit", anchor=tk.CENTER)
        self.treeview.heading("Opened Positions", text="Positions", anchor=tk.CENTER)

        # pack the self.treeview.view widget into the root window and display it
        self.treeview.pack(fill="both", expand=True)

    # define a function to create an options menu
    def create_options_menu(self):
        # create a menu bar
        menu_bar = tk.Menu(self.root)

        # create an options menu
        options_menu = tk.Menu(menu_bar, tearoff=0)

        # add a command to the options menu to open a panel for getting deals history
        options_menu.add_command(
            label="Edit filters",
            command=lambda: self.filters_window.focus_set()
            if self.filters_window
            else self.show_edit_filters_window(),
        )

        # add a command to the options menu to open a panel for showing information
        options_menu.add_command(
            label="Show information",
            command=lambda: self.info_window.focus_set()
            if self.info_window
            else self.show_information(),
        )

        # add the options menu to the menu bar
        menu_bar.add_cascade(label="Options", menu=options_menu)

        # configure the root window to display the menu bar
        self.root.config(menu=menu_bar)

    def clear_filters_window(self):
        self.filters_window.destroy()
        self.filters_window = None

    def clear_info_window(self):
        self.info_window.destroy()
        self.info_window = None

    def validate_float(self, new_value):
        try:
            float(new_value)
            return True
        except ValueError:
            return False

    def show_edit_filters_window(self):
        # get the deals as a pandas dataframe
        mt_deals = self.mt5.fetch_data(0, datetime.now())
        deals = self.mt5.convert_data_to_dataframe(mt_deals)
        # get the unique magic values as a list
        magic_values = sorted(deals["magic"].unique().tolist())
        self.filters_window = tk.Toplevel()
        self.filters_window.title("Show Information")
        self.filters_window.protocol(
            "WM_DELETE_WINDOW",
            self.clear_filters_window,
        )
        # update the window to get the correct size
        self.center_window(self.filters_window, w=800, h=300)
        # create a frame for the grid layout
        grid_frame = tk.Frame(self.filters_window)
        checkboxes = []
        checkboxes_states = []

        # create a list of labels and entries for each magic value
        labels = []
        entries = []
        # loop through the magic values
        for i, magic in enumerate(magic_values):
            variable = tk.IntVar()
            checkbox = tk.Checkbutton(
                grid_frame, text=str(magic), variable=variable, padx=10, pady=10
            )
            # create a label with the value of the magic
            label = tk.Label(grid_frame, text=str(magic), padx=10, pady=10)
            # create an entry for the user to see the alias for the magic
            entry = tk.Entry(grid_frame)
            # create a label for the profit goal
            profit_label = tk.Label(grid_frame, text="Profit Goal:", padx=10, pady=10)
            # create an entry for the user to see the profit goal for the magic
            profit_entry = tk.Entry(
                grid_frame,
                validate="key",
                validatecommand=(
                    self.filters_window.register(self.validate_float),
                    "%P",
                ),
            )
            # create a label for the loss goal
            loss_label = tk.Label(grid_frame, text="Loss Goal:", padx=10, pady=10)
            # create an entry for the user to see the loss goal for the magic
            loss_entry = tk.Entry(
                grid_frame,
                validate="key",
                validatecommand=(
                    self.filters_window.register(self.validate_float),
                    "%P",
                ),
            )
            # add the label and entry to their respective lists

            checkboxes.append(checkbox)
            checkboxes_states.append(variable)
            labels.append(label)
            entries.append((entry, profit_entry, loss_entry))

            # place the label and entry in the grid layout
            checkbox.grid(row=i, column=0)
            label.grid(row=i, column=1)
            entry.grid(row=i, column=2)
            profit_label.grid(row=i, column=3)
            profit_entry.grid(row=i, column=4)
            loss_label.grid(row=i, column=5)
            loss_entry.grid(row=i, column=6)
            # check if there is a data.txt file saved from the save_data function

        data = self.read_data_file()
        if data:
            for checkbox, entry in zip(checkboxes, entries):
                magic = checkbox.cget("text")
                # get the data for the magic value
                magic_data = data.get(magic, None)
                # if there is data for the magic value
                if magic_data:
                    checkbox_state = magic_data.get("state", 0)
                    checkbox.invoke() if checkbox_state else None
                    alias_input, profit_input, loss_input = entry
                    # set the alias input according to the alias field in the data
                    alias = magic_data.get("alias", "")
                    alias_input.insert(0, alias)
                    # set the profit goal input according to the profit field in the data
                    profit = magic_data.get("profit", "")
                    profit_input.insert(0, profit)
                    # set the loss goal input according to the loss field in the data
                    loss = magic_data.get("loss", "")
                    loss_input.insert(0, loss)
        else:
            for checkbox in checkboxes:
                checkbox.invoke()
            # set the alias input according to the alias field in the data
            # create a frame for the buttons
        button_frame = tk.Frame(self.filters_window)
        # create a button to cancel and close the window
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.clear_filters_window,
            padx=10,
            pady=10,
        )
        # create a button to save the checkboxes and aliases to a file and plot the data
        save_button = tk.Button(
            button_frame,
            text="Save",
            command=lambda: [
                self.save_data(checkboxes, entries, checkboxes_states),
                self.plot_data(),
                self.clear_filters_window(),
            ],
            padx=10,
            pady=10,
        )
        # place the buttons in the frame
        cancel_button.pack(side=tk.LEFT, padx=10, pady=10)
        save_button.pack(side=tk.RIGHT, padx=10, pady=10)
        # place the frames in the window
        grid_frame.pack()
        button_frame.pack()

    # define a function to show information about the project and the developer
    def show_information(self):
        self.info_window = tk.Toplevel()
        self.info_window.title("Information")
        self.info_window.protocol(
            "WM_DELETE_WINDOW",
            self.clear_info_window,
        )
        self.center_window(self.info_window, w=800, h=300)

        project_label = tk.Label(
            self.info_window,
            text="This is a project for plotting data about Expert Advisors running in the MetaTrader5 terminal.",
            padx=10,
            pady=10,
        )
        developer_label1 = tk.Label(
            self.info_window,
            text="The developer is Thiago Santana, a software engineer and data analyst. He is passionate about creating solutions with Python and other technologies.",
            padx=10,
            pady=10,
        )
        developer_label2 = tk.Label(
            self.info_window,
            text="He is passionate about creating solutions with Python and other technologies.",
            padx=10,
        )
        # create a label with the text "You can find the source code of this project on GitHub:"
        github_label = tk.Label(
            self.info_window,
            text="You can find the source code of this project on GitHub:",
            padx=10,
            pady=10,
        )
        # create a hyperlink to the GitHub repository
        github_link = tk.Label(
            self.info_window,
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
            self.info_window,
            text="You can also connect with the developer on LinkedIn:",
            padx=10,
            pady=10,
        )
        # create a hyperlink to the developer's LinkedIn profile
        linkedin_link = tk.Label(
            self.info_window,
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

    def center_window(self, window, w=None, h=None):
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
    def save_data(self, checkboxes, entries, states):
        # create an empty dictionary to store the data
        data = {}

        # loop through the checkboxes and entries
        for checkbox, entry, state in zip(checkboxes, entries, states):
            alias_input, profit_input, loss_input = entry

            # get the value of the checkbox
            magic = checkbox.cget("text")

            # get the alias of the entry
            alias = alias_input.get()
            profit = profit_input.get()
            loss = loss_input.get()
            # add the value and alias to the data dictionary
            data[magic] = {
                "alias": alias,
                "profit": profit,
                "loss": loss,
                "state": int(state.get()),
            }

        # open a file for writing
        with open("data.txt", "w") as f:
            # write the data dictionary to the file
            f.write(str(data))
