import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkwidgets.autocomplete import AutocompleteEntry
from helpers import *
import os
import shutil
from datetime import datetime, timezone
from tkcalendar import DateEntry
from PIL import Image
import subprocess

class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Keeper")
        root.geometry('900x600')
        
        # Create connection to db
        self.conn = sqlite3.connect('image_database.db')
        self.cursor = self.conn.cursor()

        # Create table if not exist
        self.create_tables()
        self.init_lookup_lists()

        # Initalize UI elements
        self.init_ui_elements()

        # Init settings
        self.image_destination = "images"

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS creators (
                creator_id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_name TEXT NOT NULL UNIQUE
            )
        ''' )
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                directory_path TEXT,
                creator_id INTEGER,
                source_url TEXT,
                date_added TEXT,
                date_uploaded TEXT,
                thumbnail_path TEXT,
                FOREIGN KEY (creator_id) REFERENCES creators (creator_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT NOT NULL,
                tag_description TEXT,
                category TEXT
            )
        ''' )
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_tags (
                image_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (image_id, tag_id),
                FOREIGN KEY (image_id) REFERENCES images (image_id),
                FOREIGN KEY (tag_id) REFERENCES tags (tag_id)
            )
        ''' )
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS socials (
                social_id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                social_handle TEXT,
                social_type TEXT,
                FOREIGN KEY (creator_id) REFERENCES creators (creator_id)
            )
        ''' )

        self.conn.commit()

    def init_ui_elements(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True)

        # Create tabs for the tables
        self.tab_images = ttk.Frame(self.notebook)
        self.tab_creators = ttk.Frame(self.notebook)
        self.tab_tags = ttk.Frame(self.notebook)

        self.tab_images.pack(fill='both', expand=True)
        self.tab_creators.pack(fill='both', expand=True)
        self.tab_tags.pack(fill='both', expand=True)
        
        # Add tabs to notebook
        self.notebook.add(self.tab_images, text= "Images")
        self.notebook.add(self.tab_creators, text= "Creators")
        self.notebook.add(self.tab_tags, text= "Tags")

        # Run functions for initalizing each table
        self.init_image_table()
        self.init_creator_table()
        self.init_tags_table()

    def display_data(self, data_object, table_name):
        # Clear existing data in the treeview
        for row in data_object.get_children():
            data_object.delete(row)

        # Fetch data from the database and display it in the treeview
        self.cursor.execute("SELECT * FROM '{}'".format(table_name))
        rows = self.cursor.fetchall()

        for row in rows:
            data_object.insert("", "end", iid=row[0], values=row)

    def display_image_data(self):
        # Clear existing data in the treeview
        for row in self.image_tree.get_children():
            self.image_tree.delete(row)

        # Fetch data from the database and display it in the treeview
        self.cursor.execute('''SELECT i.image_id, i.filename,
                            c.creator_name, i.source_url,
                            GROUP_CONCAT(tags.tag_name) as tags,
                            i.date_added
                            FROM images as i
                            LEFT JOIN creators as c
                            ON i.creator_id = c.creator_id
                            LEFT JOIN image_tags
                            ON i.image_id = image_tags.image_id
                            LEFT JOIN tags ON image_tags.tag_id = tags.tag_id
                            GROUP BY i.image_id, i.filename, i.creator_id, i.source_url
                            ''')
        rows = self.cursor.fetchall()

        for row in rows:
            self.image_tree.insert("", "end", iid=row[0], values=row)

    def init_image_table(self):
        # Init Inputs
        self.button_insert_image_window = tk.Button(self.tab_images, text="Add Image", command=self.windowAddImage)

        self.image_table_cols = ("image_id", "filename", "creator", "source_url", "tags", "date_added")
        self.image_tree = ttk.Treeview(self.tab_images, columns=self.image_table_cols, show="headings")
        
        for col in self.image_table_cols:
            self.image_tree.heading(col, text=col)

        self.button_edit_image = tk.Button(self.tab_images, text="Edit Entry", command=self.editImageWindow)
        self.button_delete_image = tk.Button(self.tab_images, text="Delete Entry", command=self.delete_image_data)

        # For table
        self.button_insert_image_window.grid(row=0, column=0, columnspan=2, pady=10)
        self.image_tree.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

        # For Editing and Deleting buttons
        self.button_edit_image.grid(row=2, column=0, padx=10, pady=10)
        self.button_delete_image.grid(row=2, column=2, padx=10, pady=10)

        # Fetch and display existing data
        self.display_image_data()

    def init_creator_table(self):
        # Init Inputs
        self.label_creator_name = tk.Label(self.tab_creators, text="Creator")
        self.entry_creator_name = tk.Entry(self.tab_creators)
        self.label_creator_list = tk.Label(self.tab_creators, text="Suggestions")
        self.creator_name_list = ttk.Combobox(self.tab_creators, value=[" "])

        self.button_insert_creator = tk.Button(self.tab_creators, text="Insert Data", command=self.insert_creator_data)
        self.creator_tree = ttk.Treeview(self.tab_creators, columns=("creator_id", "creator"), show="headings")

        self.creator_headers = ("creator_id", "creator_name")
        self.creator_tree = ttk.Treeview(self.tab_creators, columns=self.creator_headers, show="headings")
        
        for col in self.creator_headers:
            self.creator_tree.heading(col, text=col)

        # Place on widget
        self.label_creator_name.grid(row=0, column=0, padx=10, pady=5)
        self.entry_creator_name.grid(row=0, column=1, padx=10, pady=5)
        self.label_creator_list.grid(row=1, column=0, padx=10, pady=5)
        self.creator_name_list.grid(row=1, column=1, padx=10, pady=10)

        # For table
        self.button_insert_creator.grid(row=2, column=0, columnspan=2, pady=10)
        self.creator_tree.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.display_data(self.creator_tree, "creators")

    def init_tags_table(self):
        # Init Inputs
        self.label_tagname = tk.Label(self.tab_tags, text="Tag Name")
        self.entry_tagname = tk.Entry(self.tab_tags)

        self.label_category = tk.Label(self.tab_tags, text="Category")
        self.entry_category = tk.Entry(self.tab_tags)

        self.label_description = tk.Label(self.tab_tags, text="Description")
        self.entry_description = tk.Text(self.tab_tags, width=20, height=3)

        self.button_insert_tag = tk.Button(self.tab_tags, text="Insert Data", command=self.insert_tag_data)
        self.tag_tree = ttk.Treeview(self.tab_tags, columns=("tag_id", "tag_name", "tag_description", "category"), show="headings")

        self.tag_headers = ("tag_id", "tag_name", "tag_description", "category")
        self.tag_tree = ttk.Treeview(self.tab_tags, columns=self.tag_headers, show="headings")
        
        for col in self.tag_headers:
            self.tag_tree.heading(col, text=col)

        # Place on widget
        self.label_tagname.grid(row=0, column=0, padx=10, pady=10)
        self.entry_tagname.grid(row=0, column=1, padx=10, pady=10)

        self.label_category.grid(row=1, column=0, padx=10, pady=10)
        self.entry_category.grid(row=1, column=1, padx=10, pady=10)

        self.label_description.grid(row=2, column=0, padx=10, pady=10)
        self.entry_description.grid(row=2, column=1, padx=10, pady=10)

        # For table
        self.button_insert_tag.grid(row=2, column=0, columnspan=2, pady=10)
        self.tag_tree.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        # Fetch and display existing data
        self.display_data(self.tag_tree, "tags")

    def insert_creator_data(self):
        # Fetch name as string
        creator_name = self.entry_creator_name.get()
        creator_name = str(creator_name)

        # Check if name is a non-empty string
        if creator_name == "":
            messagebox.showerror(title="Error",
                                  message="Creator name cannot be empty.")
        else:
            # Check if name is not listed in table yet
            self.cursor.execute("SELECT creator_id FROM creators WHERE creator_name = ?", (creator_name,))
            id_result = self.cursor.fetchone()

            # Only write data if creator name doesn't already exist
            if id_result:
                messagebox.showerror(title="Error",
                                      message="Creator already exists.")
            else:
                # Insert the data
                self.cursor.execute("INSERT INTO creators (creator_name) VALUES (?)", (creator_name,))

                # Commit the change
                self.conn.commit()

        self.display_data(self.creator_tree, "creators")      

    # Deletes images by on press of "Delete" button on "creators" tab
    # NOT IMPLEMENTED
    def delete_creator_data(self):

        # Retrieve id of selected image entry/entries
        selected_creators = self.creator_tree.selection()
        number_selected = len(selected_creators)

        if (number_selected > 0):
            # Warning message: Only proceed if user answers "yes"
            try:
                delete_confirm = messagebox.askquestion(title="Warning",
                                                        message='''You are about to delete {} creator(s). This operation cannot be undone. Are you sure?'''.format(number_selected))
                if delete_confirm=='yes':
                    # For all images selected, iterate and delete all
                    for creator in selected_creators:
                        self.creator_tree.delete(creator)
                        self.cursor.execute("DELETE FROM creators WHERE creator_id = ?", (creator,))
                    
                    # Commit change and refresh table
                    self.conn.commit()
                    self.display_data(self.creator_tree, "creators")
            except:
                pass
                # If rows not selected, notify user
        else:
            messagebox.showerror(title="Error", message="No rows selected to delete.")

# Basic CRUD Operations: image data

    def insert_image_data(self):
        # Fetch information from inputs for new image
        filepath = self.browse_label.cget("text").split(':')[-1]
        creator_name = self.entry_creator.get()
        source = self.entry_source.get()
        tags = [s.strip() for s in self.entry_image_tags.get().split(",")]
        current_datetime = datetime.now(timezone.utc)
        upload_date = self.entry_dateadd.get()

        # Check if name is a non-empty string
        if not creator_name:
            messagebox.showerror(title="Error",
                                  message="Creator name cannot be empty.")
            
        elif not filepath:
            messagebox.showerror(title="Error",
                                  message="You must select an image.")
        else:
            # Look up the creator id by using given creator name
            self.cursor.execute("SELECT creator_id FROM creators WHERE creator_name = ?", (creator_name,))
            id_result = self.cursor.fetchone()

            # If the creator_id doesn't exist for a creator name, make an entry in the creator table
            #    and use this new id when creating the entry
            if not id_result:
                self.cursor.execute("INSERT INTO creators (creator_name) VALUES (?)", (creator_name,))
                self.cursor.execute("SELECT creator_id FROM creators WHERE creator_name = ?", (creator_name,))
                id_result = self.cursor.fetchone()
            
            # Convert creator_id result to integer from tuple object
            id_result = id_result[0]

            destination_path = self.addToDirectory(filepath)
            filename = os.path.basename(destination_path)

            thumbnail_path = self.createThumbnail(destination_path, "images/thumbnails")

            # Insert the image data
            self.cursor.execute("INSERT INTO images (filename, creator_id, source_url, directory_path, date_added, date_uploaded, thumbnail_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (filename, id_result, source, destination_path, current_datetime, upload_date, thumbnail_path))

            # Commit the change
            self.conn.commit()

        # Handling tag data only if a tag was submitted
        # Get image id for the entry we just submitted
        self.cursor.execute("SELECT image_id from images WHERE filename = ? AND creator_id = ?", (filename, id_result))
        image_id_result = self.cursor.fetchone()[0]
        # Get the tag id
        for tag in tags:
            self.cursor.execute("SELECT tag_id from tags WHERE tag_name = ?", (tag,))
            tag_output = self.cursor.fetchone()
            print(tag_output)
            if tag_output:
                tag_id = tag_output[0]
                self.cursor.execute("INSERT INTO image_tags (image_id, tag_id) VALUES (?, ?)", (image_id_result, tag_id))
                print((image_id_result, tag_id))
            else:
                self.cursor.execute("INSERT INTO tags (tag_name) VALUES (?)", (tag,))
                self.cursor.execute("SELECT tag_id from tags WHERE tag_name = ?", (tag,))
                tag_id = self.cursor.fetchone()[0]
                print(tag_id)
                self.cursor.execute("INSERT INTO image_tags (image_id, tag_id) VALUES (?, ?)", (image_id_result, tag_id))
                print((image_id_result, tag_id))
            # Commit changes
            self.conn.commit()

        self.display_image_data()
        self.display_data(self.tag_tree, "tags")

        # Clear inputs
        self.entry_filename.delete(0, "end")
        self.entry_creator.delete(0, "end")
        self.entry_image_tags.delete(0, "end")
        self.entry_source.delete(0, "end")
        self.browse_label.configure(text="Select File")

    def edit_image_data(self):
        # Fetch information from inputs for new image
        image_id = self.selected_image_id
        creator_name = self.entry_creator.get()
        source = self.entry_source.get()
        tags = [s.strip() for s in self.entry_image_tags.get().split(",")]
        current_datetime = datetime.now(timezone.utc)
        upload_date = self.entry_dateadd.get()

        # Check if name is a non-empty string
        if not creator_name:
            messagebox.showerror(title="Error",
                                  message="Creator name cannot be empty.")
        else:
            # Look up the creator id by using given creator name
            self.cursor.execute("SELECT creator_id FROM creators WHERE creator_name = ?", (creator_name,))
            id_result = self.cursor.fetchone()

            # If the creator_id doesn't exist for a creator name, make an entry in the creator table
            #    and use this new id when creating the entry
            if not id_result:
                self.cursor.execute("INSERT INTO creators (creator_name) VALUES (?)", (creator_name,))
                self.cursor.execute("SELECT creator_id FROM creators WHERE creator_name = ?", (creator_name,))
                id_result = self.cursor.fetchone()
            
            # Convert creator_id result to integer from tuple object
            id_result = id_result[0]

            # Insert the image data
            self.cursor.execute("UPDATE images SET creator_id = ?, source_url = ?, date_added = ?, date_uploaded = ? WHERE image_id = ?",
                                (id_result, source, current_datetime, upload_date, image_id))

            # Commit the change
            self.conn.commit()

        new_tag_ind = []
        # Check if any tags must be added to image_tags
        for tag in tags:
            self.cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag,))
            tag_output = self.cursor.fetchone()
            print(tag_output)
            # If tag doesn't exist, add to both tables
            if not tag_output:
                self.cursor.execute("INSERT INTO tags (tag_name) VALUES (?)", (tag,))
                self.cursor.execute("SELECT tag_id from tags WHERE tag_name = ?", (tag,))
                tag_id = self.cursor.fetchone()[0]
                new_tag_ind += [tag_id]
            else:
            # If tag exists in tag table, check if in image_tags
                tag_id = tag_output[0]
                new_tag_ind += [tag_id]
            
            # Commit changes
            self.conn.commit()
        
        # Build list of tag indicies
        self.cursor.execute("SELECT tag_id FROM image_tags WHERE image_id = ?", (image_id,))
        existing_tags = self.cursor.fetchall()
        existing_tags = [x[0] for x in existing_tags]
        print("existing tags: " + str(existing_tags))
        print(new_tag_ind)

        # If tag is listed in existing but not new, delete
        for tag in existing_tags:
            if tag not in new_tag_ind:
                self.cursor.execute("DELETE FROM image_tags WHERE image_id = ? AND tag_id = ?", (image_id, tag))

        # If tag is listed in new but not existing, add
        for tag in new_tag_ind:
            if tag not in existing_tags:
                self.cursor.execute("INSERT INTO image_tags (image_id, tag_id) VALUES (?, ?)", (image_id, tag_id))
        self.conn.commit()

        self.display_image_data()
        self.display_data(self.tag_tree, "tags")

    # Deletes images by on press of "Delete" button on "images" tab
    def delete_image_data(self):

        # Retrieve id of selected image entry/entries
        selected_images = self.image_tree.selection()
        number_selected = len(selected_images)

        # Check if rows are selected first
        if (number_selected > 0):
            # Warning message: Only proceed if user answers "yes"
            try:
                delete_confirm = messagebox.askquestion(title="Warning",
                                                        message='''You are about to delete {} image(s). This operation cannot be undone. Are you sure?'''.format(number_selected))
                if delete_confirm=='yes':
                    # For all images selected, iterate and delete all
                    for image in selected_images:
                        self.image_tree.delete(image)
                        self.cursor.execute("DELETE FROM images WHERE image_id = ?", (image,))
                        self.cursor.execute("DELETE FROM image_tags WHERE image_id = ?", (image,))
                    
                    # Commit change and refresh table
                    self.conn.commit()
                    self.display_image_data()
            except:
                pass
        # If rows not selected, notify user
        else:
            messagebox.showerror(title="Error", message="No rows selected to delete.")

    # Add tag data by pressing "submit"
    def insert_tag_data(self):
        tag_name = self.entry_tagname.get()
        tag_description = self.entry_description.get("1.0", 'end-1c')
        tag_category = self.entry_category.get()

        error_count = 0

        # Check tag name is not empty
        if tag_name == "":
            messagebox.showerror(title="Error",
                                  message="Tag name cannot be empty.")
            error_count += 1
        else:
            # Check tag name is not taken
            self.cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_name,))
            id_result = self.cursor.fetchone()

            if id_result:
                messagebox.showerror(title="Error",
                                     message="Tag name already taken.")
                error_count += 1
        
        if error_count == 0:
            # Insert the data
            self.cursor.execute("INSERT INTO tags (tag_name, tag_description, category) VALUES (?, ?, ?)", (tag_name, tag_description, tag_category))

            # Commit the change
            self.conn.commit()

        self.display_data(self.tag_tree, "tags")

    # Creates lookup lists for confirming if certain items already exist
    def init_lookup_lists(self):
        self.all_creators = [creator[0] for creator in self.cursor.execute("SELECT creator_name from creators")]
        self.all_tags = [tag[0] for tag in self.cursor.execute("SELECT tag_name from tags")]

    # Add Image function (can switch to edit mode)
    def windowAddImage(self, mode="Add", selection = None):
        self.image_window = tk.Toplevel(root)

        if mode == "Add":
            self.image_window.title("Add New Image")
        else:
            self.image_window.title("Edit Image")
        self.image_window.geometry("600x400")
        self.image_window.attributes('-topmost', True)

        row_offset = 0

        if mode == "Add":
            row_offset = 1

            self.browse_label = tk.Label(self.image_window, text="Select File")
            self.browse_button = tk.Button(self.image_window, text="Browse", command=self.browseForImage)

            self.label_filename = tk.Label(self.image_window, text="Filename")
            self.entry_filename = tk.Entry(self.image_window)

        self.label_creator = tk.Label(self.image_window, text="Creator")
        self.entry_creator = AutocompleteEntry(self.image_window,
                                               completevalues=self.all_creators)

        self.label_source = tk.Label(self.image_window, text="Source URL")
        self.entry_source = tk.Entry(self.image_window)

        self.label_dateadd = tk.Label(self.image_window, text="Upload Date")
        self.entry_dateadd = DateEntry(self.image_window)

        self.label_image_tags = tk.Label(self.image_window, text="Tags")
        self.entry_image_tags = AutocompleteMultiEntry(self.image_window,
                                                 completevalues=self.all_tags)

        # If editing an existing image, fill in existing information
        if selection:
            image_info = self.fetchImage(selection)
            self.selected_image_id = image_info[0]
            self.entry_creator.insert(0, image_info[3])
            self.entry_source.insert(0, image_info[4])
            self.entry_dateadd.delete(0, tk.END)
            self.entry_dateadd.insert(0, image_info[6])
            self.entry_image_tags.insert(0, image_info[-1])         
  
        if mode == "Add":
            self.button_insert_image = tk.Button(self.image_window, text="Add Image", command=self.insert_image_data)
        elif mode == "Edit":
            self.button_insert_image = tk.Button(self.image_window, text="Edit Image", command=self.edit_image_data)
        
        # Place on widget
        if mode == "Add":
            self.browse_label.grid(row=0, column=0, padx=10, pady=10)
            self.browse_button.grid(row=0, column=3, padx=10, pady=10)

        self.label_image_tags.grid(row=0+row_offset, column=0, padx=10, pady=10)
        self.entry_image_tags.grid(row=0+row_offset, column=1, padx=10, pady=10)

        self.label_creator.grid(row=0+row_offset, column=2, padx=10, pady=10)
        self.entry_creator.grid(row=0+row_offset, column=3, padx=10, pady=10)

        self.label_source.grid(row=1+row_offset, column=0, padx=10, pady=10)
        self.entry_source.grid(row=1+row_offset, column=1, padx=10, pady=10)

        self.label_dateadd.grid(row=1+row_offset, column=2, padx=10, pady=10)
        self.entry_dateadd.grid(row=1+row_offset, column=3, padx=10, pady=10)

        self.button_insert_image.grid(row=2+row_offset, column=0, padx=10, pady=10)

    def browseForImage(self):
        filename = filedialog.askopenfilename(initialdir="/",
                                              title = "Select an Image",
                                              filetypes= [("All Files",
                                                            "*.*"),
                                                            ("JPEG",
                                                             "*.jpeg")],
                                               parent=self.image_window)
        self.browse_label.configure(text="File location: {}".format(filename))

    # Copy file to images directory and return the new path of the file
    def addToDirectory(self, filepath):
        filename = os.path.basename(filepath)
        filename_noext, extension = os.path.splitext(filename)
        final_destination = os.path.join(self.image_destination, filename)
        temp_filename = filename

        counter = 1
        while os.path.exists(final_destination):
            temp_filename = "{}_{}{}".format(filename_noext, counter, extension)
            final_destination = os.path.join(self.image_destination, temp_filename)
            counter += 1

        shutil.copy2(filepath, final_destination)

        return final_destination
    
    def editImageWindow(self):

        # Retrieve id of selected image entry/entries
        selected_image = self.image_tree.selection()

        number_selected = len(selected_image)

        if (number_selected > 1):
            messagebox.showerror(title="Error",
                                  message="Must select only one image.")
        elif (number_selected == 0):
            messagebox.showerror(title="Error",
                                  message="You must select an image entry to edit.")
        else:
            self.windowAddImage(mode="Edit", selection = selected_image[0])

    def fetchImage(self, image_id):
        im_info = self.cursor.execute("SELECT * FROM images WHERE image_id = ?", (image_id,)).fetchone()
        image_info = list(im_info)
        creator_id = image_info[3]
        creator_info = self.cursor.execute("SELECT creator_name FROM creators WHERE creator_id = ?", (creator_id,)).fetchone()
        image_info[3] = creator_info[0]
        tag_ids = self.cursor.execute("SELECT tag_id FROM image_tags where image_id = ?", (image_id,)).fetchall()
        tag_string = ''
        for tag in tag_ids:
            tag_name = self.cursor.execute("SELECT tag_name FROM tags where tag_id = ?", (tag[0],)).fetchone()
            tag_string += tag_name[0] + ','
        if len(tag_string) > 0:
            tag_string = tag_string[:-1]
        image_info = image_info + [tag_string]
        return image_info
    
    def createThumbnail(self, image_path, thumbnail_dir):
        image_name = os.path.basename(image_path)
        name_only, image_ext = image_name.split('.')
        thumbnail_path = os.path.join(thumbnail_dir, name_only + '.png')

        # Generate Thumbnail depending on file
        if image_ext.lower() in ['jpg','jpeg','png','gif','tif']:
            image = Image.open(image_path)
            max_size = (100,100)
            image.thumbnail(max_size)
            image.save(thumbnail_path)
        elif image_ext.lower() in ['mp4','avi','mkv']:
            subprocess.call(['ffmpeg.exe', '-i', image_path, '-ss', '00:00:00.000', '-vframes', '1', thumbnail_path])
            image = Image.open(thumbnail_path)
            max_size = (100,100)
            image.thumbnail(max_size)
            image.save(thumbnail_path)
        else:
            pass

        return thumbnail_path

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()