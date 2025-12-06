# MNMarketLink Python App Setup

1. In MySQL, make sure the MNMarketLink database is already created with schema.sql and has the data from data.sql loaded.
   (You don't need to run the files again if you already have before)

2. Install Python if you haven't already, be sure to check “Add Python to PATH” during installation: https://www.python.org/downloads/

3. Create a project folder and place the files from the "MNMarket" folder from this repository inside, make sure you're inside this project folder in your IDE.

4. In your IDE with the project folder open, open the Terminal and run this command to install required packages:

   > python -m pip install -r requirements.txt

   (If that command doesn't work, try using "py" instead of "python")

5. Create a file named db_config.py, and copy the contents of db_config_example.py into it. You'll need to change the username and password to be your own MySQL login.

6. Run this command in your terminal to open the program in your browser (ignore the pop-up that appears):

   > python -m streamlit run mnmarketlink.py

   (If that command doesn't work, try using "py" instead of "python")
