# import the required modules
import MetaTrader5 as mt5  # for accessing MetaTrader 5 terminal data
import pandas as pd  # for data manipulation and analysis
from datetime import datetime, date  # for working with dates and times


# define a class for accessing the MetaTrader 5 terminal data
class MT5:
    def __init__(self):
        # establish connection to the MetaTrader 5 terminal
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            quit()

    def fetch_data(self, start_datetime, end_datetime):
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

    def convert_data_to_dataframe(self, deals):
        # convert the deals to a pandas dataframe
        deals = pd.DataFrame(list(deals), columns=deals[0]._asdict())
        return deals  # return the dataframe

    def group_data_by_time_and_magic(self, deals):
        # convert the time column to datetime format
        deals["time"] = pd.to_datetime(deals["time"], unit="s")
        # group the data by time and magic number and sum up the profit values
        filtered_data = deals.groupby([pd.Grouper(key="time", freq="D"), "magic"])
        return filtered_data  # return the grouped data

    def get_positions(self, start_date, deals):
        # get the positions from MetaTrader 5 terminal
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

    def get_connection_string(self):
        terminal_info = mt5.terminal_info()
        if terminal_info != None:
            terminal_info_dict = mt5.terminal_info()._asdict()
            connection_status = terminal_info_dict["connected"]
            if connection_status:
                return "Expert Statistics (CONNECTED) - Last Update: {}".format(
                    datetime.now().strftime("%d/%m/%y %H:%M:%S")
                )
        return "Expert Statistics (DISCONNECTED)"

    def shutdown(self):
        return mt5.shutdown()
