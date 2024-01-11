import sqlite3
import tkinter as tk
from tkinter import ttk

class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLite Database App")

        # Create a SQLite database connection
        self.conn = sqlite3.connect('your_database_name.db')
        self.cursor = self.conn.cursor()

        # Create a table if it doesn't exist
        self.create_table()

        # Create UI elements
        self.create_ui()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def create_ui(self):
        # UI components
        self.label_name = tk.Label(self.root, text="Name:")
        self.label_email = tk.Label(self.root, text="Email:")

        self.entry_name = tk.Entry(self.root)
        self.entry_email = tk.Entry(self.root)

        self.button_insert = tk.Button(self.root, text="Insert Data", command=self.insert_data)
        self.tree = ttk.Treeview(self.root, columns=("ID", "Name", "Email"), show="headings")

        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Email", text="Email")

        # Grid layout
        self.label_name.grid(row=0, column=0, padx=10, pady=10)
        self.label_email.grid(row=1, column=0, padx=10, pady=10)

        self.entry_name.grid(row=0, column=1, padx=10, pady=10)
        self.entry_email.grid(row=1, column=1, padx=10, pady=10)

        self.button_insert.grid(row=2, column=0, columnspan=2, pady=10)

        self.tree.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        # Fetch and display existing data
        self.display_data()

    def insert_data(self):
        # Get data from entry widgets
        name = self.entry_name.get()
        email = self.entry_email.get()

        # Insert data into the database
        self.cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        self.conn.commit()

        # Clear entry widgets
        self.entry_name.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)

        # Refresh the displayed data
        self.display_data()

    def display_data(self):
        # Clear existing data in the treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Fetch data from the database and display it in the treeview
        self.cursor.execute("SELECT * FROM users")
        rows = self.cursor.fetchall()

        for row in rows:
            self.tree.insert("", "end", values=row)

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()