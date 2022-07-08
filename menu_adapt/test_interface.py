import tkinter as tk
import time
from tk_tools import ButtonGrid

def selection_time():
    global select_time
    select_time.set(time.time() - display_time.get())    

root = tk.Tk()

display_time = tk.DoubleVar()
display_time.set(time.time())
select_time = tk.DoubleVar()
select_time.set('0')
menu = "tomato,potato,carrot,onion,beans".split(sep=",")
data = [(item, selection_time) for item in menu]
button_grd = ButtonGrid(root, 1, [""])

for item in menu:
    button_grd.add_row([(item, selection_time)])

button_grd.pack()

label = tk.Label(root, textvariable=str(select_time))
label.pack()

root.mainloop()