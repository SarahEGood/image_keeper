import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from ttkwidgets.autocomplete import AutocompleteEntry

# Class for entering multiple words (tags) and having each autocomplete
class AutocompleteMultiEntry(AutocompleteEntry):
    def autocomplete(self, delta=0):
        """
        Autocomplete the Entry.
        
        Similar to original class but only autocompletes next comma'd entry
        """
        if delta:  # need to delete selection otherwise we would fix the current position
            self.delete(self.position, tk.END)
        else:  # set position to end so selection starts where textentry ended
            self.position = len(self.get())
        # collect hits
        _hits = []
        # Get current (last) entry (comma delinated)
        all_entries = self.get()
        current_entry_list = [s.strip() for s in all_entries.split(",")]
        current_entry = current_entry_list[-1].lower()
        for element in self._completion_list:
            if element.lower().startswith(current_entry) and element not in current_entry_list[:-1]:  # Match case-insensitively
                _hits.append(element)
        # if we have a new hit list, keep this in mind
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        # only allow cycling if we are in a known hit list
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        # now finally perform the auto completion
        if self._hits:
            self.delete(0, tk.END)
            self.insert(0, all_entries[:-len(current_entry)]+self._hits[self._hit_index])
            self.select_range(self.position, tk.END)