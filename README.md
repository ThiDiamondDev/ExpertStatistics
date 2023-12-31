
# Expert Statistics

This is a Python script that uses the MetaTrader 5 terminal data to plot data grouped by time and magic number. It uses Tkinter to create a graphical user interface (GUI) that allows the user to select the start and end dates for fetching and plotting the data, showing statistics about Expert Advisors running in MetaTrader5. It also have the option to set a custom alias for the magic number and show/hide info about it.

# Requirements

* Python 3.8 - 3.10
* MetaTrader 5 terminal installed and running
* The following Python modules installed:
    * matplotlib
    * pandas
    * MetaTrader5
    * tkcalendar

# Usage

* Install the dependencies with `pip install -r requirements.txt` (I highly recommend to use a venv)  and run the script using `python main.py`
* A GUI window will appear with two date entry widgets for selecting the start and end dates
* Click on the “Plot Data” button to fetch the data from MetaTrader 5 and plot it on a figure object
* The figures will be displayed on a canvas widget in the GUI window
To exit, close the window or press the Esc key

# Features

* The script uses the `mt5.history_deals_get` function to get the history deals from MetaTrader 5 terminal within the selected dates
* The script converts the deals to a pandas dataframe and groups them by time and magic number using the `pd.Grouper` and `pd.sum` functions
* The script creates a Tkinter GUI with date entry widgets from the `tkcalendar` module and a button to trigger the plotting function

* The script plots the profit values by time as a line chart using the `matplotlib` module

* The script embeds the figure object into a canvas widget using the `FigureCanvasTkAgg` class from the `matplotlib.backends.backend_tkagg` module

# Limitations

* Currently the script does not provide any options to customize or save the plot

# Future Implementations

Here are some possible future implementations for this code:

* Add error handling and exception catching to handle any issues that may arise during fetching or plotting of data.
* Add options to customize plots, such as changing color schemes, adding titles or legends, or saving plots to files.
* Add more plots.

These are just some ideas for future improvements. The possibilities are endless, and it all depends on your needs and requirements.
