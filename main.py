# main.py
from gui import FaceSearchApp
import tkinter as tk
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)

if __name__ == '__main__':
    logging.info("Starting Face Search Application.")
    root = tk.Tk()
    app = FaceSearchApp(root)
    root.mainloop()