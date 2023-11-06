# import the required modules
import tkinter as tk  # for creating graphical user interface
from gui import GUI
from mt import MT5


def main():
    root = tk.Tk()
    mt5 = MT5()
    # Set the geometry of frame
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.state("zoomed")

    ui = GUI(root, mt5)
    ui.center_window(root, w=w, h=h)
    root.protocol("WM_DELETE_WINDOW", lambda: [mt5.shutdown(), root.destroy()])
    ui.plot_data()
    root.mainloop()  # start the main loop of the GUI


if __name__ == "__main__":
    main()
