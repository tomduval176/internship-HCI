import tkinter as tk
import time, random
from tk_tools import ButtonGrid
import argparse

LARGE_FONT = ('Verdana', 12)
parser = argparse.ArgumentParser()
parser.add_argument("--menu", "-m", help="The future menu displayed", type=str)
args = parser.parse_args()

class Root(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        
        container.pack(side='top', fill='both', expand=True)
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        self.display_time = tk.DoubleVar()
        self.display_time.set(time.time())
        
        for F in (TargetItemPage, MenuPage):
            
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')
            
        self.show_frame(TargetItemPage)
        
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
    
    def get_target_frame(self, cont):
        return self.frames[cont]
        

class TargetItemPage(tk.Frame):
        
    def __init__(self, parent, controller):
        self.menu = "rabbit,tiger,panda,gloves,shoes,bikini,skirt,chair,sofa,table,tomato,potato,carrot,onion,beans".split(sep=",")
        tk.Frame.__init__(self, parent)
        self.display_time_target = tk.DoubleVar()
        self.display_time_target.set(time.time())
        #print(self.display_time.get())
        self.select_time_target = tk.DoubleVar()
        self.select_time_target.set('0')
        label = tk.Label(self, text='TARGET1', font= LARGE_FONT)
        label.pack()
        self.random_item = tk.StringVar()
        self.random_item.set(random.choice(self.menu))
        self.button = tk.Button(self, text=self.random_item.get(),
                           command=lambda: [controller.show_frame(MenuPage), self.reset_time(), self.update_target(controller)])
        self.button.pack()
         
    def reset_time(self):
        print("such")
        #print(f"before reset:{self.display_time.get()}")
        #before_reset = self.display_time_target.get()
        self.select_time_target.set(time.time())
        #print(f"after reset:{self.display_time.get()}")
        self.select_time_target.set(time.time() - self.display_time_target.get())
        #after_reset = self.display_time_target.get()
        print(f"Time to become aware of the target item: {self.select_time_target.get()}")
        #print(f"Time to become aware of th target item: {after_reset - before_reset}")
        
    #TODO: method to update the next item to display
    def update_target(self, controller):
        self.random_item.set(random.choice(self.menu)) 
        self.button.pack_forget()
        self.button  = tk.Button(self, text=self.random_item.get(),
                           command=lambda: [self.reset_time(), controller.show_frame(MenuPage), self.update_target(controller)])
        controller.get_target_frame(MenuPage).display_time_menu.set(time.time())
        self.button.pack()
        #self.random_item.set('HELLO')
        
        
        
class MenuPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        #print(controller.get_target_frame(TargetItemPage1).display_time.get())
        #label = tk.Label(self, text='Page One!!', font=LARGE_FONT)
        self.display_time_menu = tk.DoubleVar()
        #self.display_time_menu.set(time.time())
        #print(f"normally after reset: {self.menu_time.get()}")
        self.select_time = tk.DoubleVar()
        self.select_time.set('0')
        self.menu = args.menu.split(sep=",")
        #print(self.menu)
        self.button_grd = ButtonGrid(self, 1, [""])

        for item in self.menu:
            self.button_grd.add_row([(item, lambda: [controller.show_frame(TargetItemPage), self.selection_time() ,self.update_menu(controller)])])

        self.button_grd.pack()

        #label = tk.Label(self, textvariable=str(self.select_time))
        #label.pack()
        
    def selection_time(self):
        print('pula')
        #self.select_time.set(time.time() - self.display_time.get())
        before_reset = self.select_time.get()
        self.select_time.set(time.time())
        #after_reset = self.select_time.get()
        self.select_time.set(time.time() - self.display_time_menu.get())
        print(f"Selection time of the target item:{self.select_time.get()}")
        #print(f"Selection time of the target item:{after_reset - before_reset}")
    
    def update_menu(self, controller):
        random.shuffle(self.menu)
        #print(self.menu)
        self.button_grd.pack_forget()
        self.button_grd = ButtonGrid(self, 1, [""])

        for item in self.menu:
            self.button_grd.add_row([(item, lambda: [ self.selection_time(), controller.show_frame(TargetItemPage), self.update_menu(controller)])])
        controller.get_target_frame(TargetItemPage).display_time_target.set(time.time())
        self.button_grd.pack()     
        
        
    # TODO: implement method to update the next menu after clicking on the button

if __name__ == "__main__":
    
    session = Root()
    session.mainloop()