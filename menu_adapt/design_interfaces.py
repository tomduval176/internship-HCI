import tkinter as tk
from tkinter import font
from tk_tools import ButtonGrid

class NewButtonGrid(ButtonGrid):
    
    
    def add_row(self, data: list, row_label: str = None):
        """
        Add a row of buttons each with their own callbacks to the
        current widget.  Each element in `data` will consist of a
        label and a command.
        :param data: a list of tuples of the form ('label', <callback>)
        :return: None
        """

        # validation
        if self.headers and data:
            if len(self.headers) != len(data):
                raise ValueError

        for widget in self.headers:
            widget.grid_forget()

        for row in self._rows:
            for widget in row:
                widget.grid_forget()

        row = list()

        if row_label is not None:
            lbl = tk.Label(self, text=row_label)
            row.append(lbl)

        for i, e in enumerate(data):
            if not isinstance(e, tuple):
                raise ValueError(
                    "all elements must be a tuple " 'consisting of ("label", <command>)'
                )

            label, command = e
            button = tk.Button(
                self,
                text=str(label),
                relief=tk.RAISED,
                height=3, 
                width=15, 
                font= font.Font(family="Verdana", size=10, weight="bold"),
                command=command,
                padx=self.padding,
                pady=self.padding,
            )

            row.append(button)

        self._rows.append(row)

        # check if row has row labels
        has_row_labels = False
        for row in self._rows:
            if isinstance(row[0], tk.Label):
                has_row_labels = True
                break

        r = 0 if not self.headers else 1

        for i, widget in enumerate(self.headers):
            if has_row_labels:
                widget.grid(row=0, column=i + 1, sticky="ew")
            else:
                widget.grid(row=0, column=i, sticky="ew")

        for i, row in enumerate(self._rows):
            for j, widget in enumerate(row):
                widget.grid(row=i + r, column=j, sticky="ew")