import os
import ray
from copy import deepcopy
import time, random
import argparse
import mcts
import utility
from collections import Counter
from useroracle import UserStrategy, UserOracle
from state import State, MenuState, UserState
from tkinter import font
import tkinter as tk 
from tk_tools import ButtonGrid
from design_interfaces import NewButtonGrid

#LARGE_FONT = ('Helvetica', 20)
parser = argparse.ArgumentParser()
parser.add_argument("--menu", "-m", help="Input menu name", default="menu_10items.txt")
parser.add_argument("--history", "-H", help="Click frequency file name", default="history_10items.csv")
parser.add_argument("--associations", "-a", help="Association list file name", default="associations_10items.txt")
parser.add_argument("--strategy", "-s", help="User search strategy", default="average", choices=["serial","forage","recall","average"])
parser.add_argument("--time", "-t", type=int, help="time budget", default=5000)
parser.add_argument("--iterations", "-i", type=int, help="num iterations", default=200)
parser.add_argument("--depth", "-d", type=int, help="maximum depth", default=5)
parser.add_argument("--nopp",help="disable parallelisation", action='store_true')
parser.add_argument("--pp", type=int, help="number of parallel processes", default=10)
parser.add_argument("--usenetwork", "-nn", help="Use neural network", action='store_true' )
parser.add_argument("--valuenet","-vn",help="Value network name")
parser.add_argument("--case", "-c", help="Use case e.g. 5items, 10items, toy (combination of menu, assoc, history)")
parser.add_argument("--objective", "-O", help="Objective to use", choices = ["average","optimistic","conservative", "savage"], default="average")
parser.add_argument("--model_exp", "-exp", help="The model to use for the experiment", choices = ["static", "frequency", "mcts"], default = "mcts")
parser.add_argument("--exp_num", "-n", help="The number of the experiment", default = "1")
args = parser.parse_args()

use_network = True if args.usenetwork else False

# Value network model names
if args.menu == "menu_7items.txt":
    vn_name = "value_network_7items.h5"
elif args.menu == "menu_5items.txt":
    vn_name = "value_network_5items.h5"
elif args.menu == "menu_10items.txt":
    vn_name = "value_network_10items.h5"
elif args.menu == "menu_15items.txt":
    vn_name = "value_network_15items.h5"
else: 
    vn_name: None
    use_network = False

#Objective function to be used; default is average
objective = args.objective.upper()
model_exp = args.model_exp.upper()

# Change PWD to main directory
#pwd = os.chdir(os.path.dirname(__file__))

# Set-up the menu instance
currentmenu = utility.load_menu("./input/" + args.menu) # load menu items from text file
freqdist, total_clicks, history = utility.load_click_distribution(currentmenu, "./input/" + args.history) # load from user history (CSV file)
associations = utility.load_associations(currentmenu,"./input/" + args.associations) # load assocation matrix from text file

# If --case is included in CLI arguments
if args.case is not None:
    currentmenu = utility.load_menu("./input/menu_" + args.case + ".txt")
    freqdist, total_clicks, history = utility.load_click_distribution(currentmenu, "./input/history_" + args.case + ".csv")
    associations = utility.load_associations(currentmenu,"./input/associations_" + args.case + ".txt")
    vn_name = "value_network_" + args.case + ".h5"
else:
    vn_name = str(args.valuenet)
# If different objective function is specified
strategy = UserStrategy.AVERAGE
if args.strategy == "serial":
    strategy = UserStrategy.SERIAL
elif args.strategy == "forage":
    strategy = UserStrategy.FORAGE
elif args.strategy == "recall":
    strategy = UserStrategy.RECALL

# MCTS search parameters
maxdepth = args.depth
timebudget = args.time
iteration_limit = args.iterations

weights = [0.25,0.5,0.25] # Weights for the 3 models

if strategy == UserStrategy.SERIAL:
    weights = [1.0, 0.0, 0.0]
elif strategy == UserStrategy.FORAGE:
    weights = [0.0, 1.0, 0.0]
elif strategy == UserStrategy.RECALL:
    weights = [0.0, 0.0, 1.0]

# Intialise the root state using the input menu, associations, and user history
#menu_state = MenuState(currentmenu, associations)
#user_state = UserState(freqdist, total_clicks, history, 5.0)
#root_state = State(menu_state,user_state, exposed=True)
#my_oracle = UserOracle(maxdepth, associations=menu_state.associations)
#completion_times = my_oracle.get_individual_rewards(root_state)[1] # Initial completion time for current menu
#avg_time = sum([a * b for a, b in zip(weights, completion_times)])
parallelised = False if args.nopp else True

# Start the planner
ray.init()
#print(f"Planning started. Strategy: {strategy}. Parallelisation: {parallelised}. Neural Network: {use_network}.")
#print(f"Original menu: {menu_state.simplified_menu()}. Average selection time: {round(avg_time,2)} seconds")
#print(f"User Interest (normalised): {freqdist}")
#print(f"Associations: {associations}")

# Execute the MCTS planner and return sequence of adaptations
@ray.remote
def step_func(state, oracle, weights, objective, use_network, network_name, timebudget):
    results = []
    original_times = oracle.get_individual_rewards(state)[1]
    tree = mcts.mcts(oracle, weights, objective, use_network, network_name, time_limit=timebudget,num_iterations=args.iterations)
    node = None
    while not oracle.is_terminal(state):
        _, best_child, _, _ = tree.search(state, node) # search returns selected (best) adaptation, child state, avg rewards
        node = best_child
        state = best_child.state
        #print(state.user_state.total_clicks)
        #print(state.user_state.activations)
        [rewards, times] = oracle.get_individual_rewards(state)
        if objective == "AVERAGE":
            avg_reward = sum([a*b for a,b in zip(weights, rewards)]) # Take average reward 
            avg_time = sum([a * b for a, b in zip(weights, times)])
            avg_original_time = sum([a*b for a,b in zip(weights,original_times)]) # average selection time for the original design
        elif objective == "OPTIMISTIC":
            avg_reward = max(rewards) # Take best reward
            avg_time = min(times)
            avg_original_time = min(original_times)
        elif objective == "CONSERVATIVE":
            avg_reward = min(rewards) # Take minimum; add penalty if negative
            avg_time = max(times)
            avg_original_time = max(original_times)
        elif objective == "SAVAGE":
            avg_reward = best_child.max_regret 
            #print(f"max regret of the best child: {avg_reward}")
            avg_time = max(times)
            avg_original_time = max(original_times)
            
        #avg_reward = sum([a * b for a, b in zip(weights, rewards)])
        #avg_time = sum([a * b for a, b in zip(weights, times)])
        if avg_time > avg_original_time and state.exposed: 
            exposed = False # Heuristic. There must be a time improvement to show the menu
        else: exposed = state.exposed
        results.append([state.menu_state.simplified_menu(), state.depth, exposed, round(avg_original_time,2), round(avg_time,2), round(avg_reward,2)])
    return avg_reward, results

def best_adaptation(root_state, oracle, weights, use_network, network_name, time_budget):
    print(f'selection_time in the step function:{root_state.user_state.selection_time}')
    if not parallelised:
        result = step_func(root_state,oracle,weights, objective, use_network, network_name, time_budget)
        bestmenu = result[1]
        print("\nPlanning completed. \n\n[[Menu], Step #, Is Exposed, Original Avg Time, Final Avg Time, Reward]")
        for step in bestmenu:
            print(step)
            if step[2]: print(f"The best menu is: {step[0]}")
    elif parallelised:
        parallel_instances = args.pp
        state_copies = [deepcopy(root_state)] * parallel_instances
        result_ids = []
        for i in range(parallel_instances):
            statecopy = state_copies[i]
            result_ids.append(step_func.remote(statecopy, oracle, weights, objective, use_network, network_name, time_budget))
            
        results = ray.get(result_ids)
        bestresult = float('-inf')
        bestmenu = root_state.menu_state.simplified_menu()
        
        for result in results:
            if result[0] > bestresult:
                bestresult = result[0] + 0.0
                bestmenu = result[1]
        
        #print("\nPlanning completed. \n\n[[Menu], Step #, Is Exposed, Original Avg Time, Final Avg Time, Reward]")
        for i,step in enumerate(bestmenu):
            #print(i, len(bestmenu))
            print(step)
            if objective == "SAVAGE":
                
                if step[1] == 1:
                    next_menu = step[0]
                #if step[1] == len(bestmenu) and step[2]:
                if step[2]:
                    next_menu = step[0]
                    print(f"Let's do this adaptation:{next_menu}")
                    return next_menu
                
            else:
                
                if step[1] == 5:
                    next_menu = step[0]
                if step[1] == len(bestmenu) and step[2]: 
                    #print(f"The best menu is: {step[0]}")
                    print(f"Let's do this adaptation: {next_menu}")
                    return next_menu


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
    
    #number_of_clicks = 20
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.menu = list(filter(("----").__ne__, currentmenu))
        self.history = history
        self.display_time_target = tk.DoubleVar()
        self.display_time_target.set(time.time())
        self.select_time_target = tk.DoubleVar()
        self.select_time_target.set('0')
        label = tk.Label(self, text='TARGET')
        label.pack()
        #self.random_item = tk.StringVar()
        #self.random_item.set(random.choice(self.menu))
        self.targets_history = self.simple_history()[-20:]
        self.idx_session = 1
        self.target_item = tk.StringVar()
        self.target_item.set(self.targets_history[1])
        test_font = font.Font(size=20)
        self.button = tk.Button(self, text=self.target_item.get(), height=3, width=15, font= font.Font(family="Verdana", size=10, weight="bold"),
                           command=lambda: [controller.show_frame(MenuPage), self.awareness_time(), self.update_target(controller)])
        self.button.pack()
        
    def simple_history(self):
        return [row[0] for row in self.history]
         
    def awareness_time(self):
        self.select_time_target.set(time.time())
        self.select_time_target.set(time.time() - self.display_time_target.get())
        #print(f"Time to become aware of the target item: {self.select_time_target.get()}")
        
    def update_target(self, controller):
    
        print(f"before target update: {self.target_item.get()}")
        self.idx_session += 1
        self.target_item.set(self.targets_history[self.idx_session])
        print(f"after target update: {self.target_item.get()}")
        self.button.pack_forget()
        self.button  = tk.Button(self, text=self.target_item.get(), height=3, width=15, font= font.Font(family="Verdana", size=10, weight="bold"),
                           command=lambda: [self.awareness_time(), controller.show_frame(MenuPage), self.update_target(controller)])
        controller.get_target_frame(MenuPage).display_time_menu.set(time.time())
        self.button.pack()
        
class MenuPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.display_time_menu = tk.DoubleVar()
        self.select_time = tk.DoubleVar()
        self.select_time.set('0')
        self.idx_click = 0
        self.menu = currentmenu
        self.freqdist = freqdist
        self.total_clicks = total_clicks
        self.menu_state = MenuState(self.menu, associations)
        self.user_state = UserState(self.freqdist, self.total_clicks, history, 5.0, int(self.idx_click))
        #print(f'user total clicks: {self.user_state.total_clicks}')
        self.root_state = State(self.menu_state,self.user_state, exposed=True)
        self.my_oracle = UserOracle(maxdepth, associations=self.menu_state.associations)
        self.completion_times = self.my_oracle.get_individual_rewards(self.root_state)[1] # Initial completion time for current menu
        self.avg_time = sum([a * b for a, b in zip(weights, self.completion_times)])
        #self.history = history
        self.button_grd = NewButtonGrid(self, 1, [""])

        for item in self.menu:
            self.button_grd.add_row([(item, lambda: [controller.show_frame(TargetItemPage), self.selection_time() ,self.update_menu(controller)])])
            #self.button_grd.add_row([(item, lambda: [controller.show_frame(TargetItemPage), self.update_menu(controller)])])

        self.button_grd.pack()

        #label = tk.Label(self, textvariable=str(self.select_time))
        #label.pack()
        
    def selection_time(self):
        self.select_time.set(time.time())
        self.select_time.set(time.time() - self.display_time_menu.get())
        #self.user_state = UserState(freqdist, total_clicks, history, self.select_time.get())
        #print(f"Selection time of the target item:{self.select_time.get()}")
    
    # TODO: update all the attributes of the menu!!
    def update_menu(self, controller):
        #random.shuffle(self.menu)
        # TODO: taking into account the case when no improvement is foumd
        print(f"check the menu: {self.menu}")
        print(f"Selection time of the target item just before update the user state:{self.select_time.get()}")
        utility.save_selection_time(self.select_time.get(), "output/selection_time_" + args.model_exp + "_" + args.objective + "_" + args.exp_num + ".txt")
        self.idx_click += 1
        print(f"session num: {self.idx_click}")
        print(f"before update: {len(self.user_state.history)}")
        self.user_state.update(self.menu, self.select_time.get(), self.idx_click)
        self.user_state.update_freqdist(self.menu)
        print(f"after update: {len(self.user_state.history)}")
        print(f"last item added to the history: {self.user_state.history[-1]}")
        print(self.user_state.activations)
        #print(f'after: {len(self.user_state.history)}')
        #self.user_state = UserState(freqdist, total_clicks, history, self.select_time.get())
        self.menu_state = MenuState(self.menu, associations)
        self.root_state = State(self.menu_state,self.user_state, exposed=True)
        self.my_oracle = UserOracle(maxdepth, associations=self.menu_state.associations)
        print(f"history after selecting the item in the menu: {len(self.user_state.history)}")
        print(f"the number of total clicks is: {self.user_state.total_clicks}")
        if model_exp == "STATIC":
            self.menu = currentmenu
        elif model_exp == "FREQUENCY":
            print(self.user_state.history)
            hist_freq = [item[0] for item in self.user_state.history]
            self.menu = [item for items, c in Counter(hist_freq).most_common() for item in [items]]
            print(self.menu)
        elif model_exp == "MCTS":
            self.menu = best_adaptation(self.root_state, self.my_oracle, weights, use_network, vn_name, timebudget)
            while self.menu is None:
                print(f"hello dude!!")
                self.menu = best_adaptation(self.root_state, self.my_oracle, weights, use_network, vn_name, timebudget)
        print(f"The new menu is: {self.menu}")
        self.button_grd.pack_forget()
        self.button_grd = NewButtonGrid(self, 1, [""])

        for item in self.menu:
            self.button_grd.add_row([(item, lambda: [ self.selection_time(), controller.show_frame(TargetItemPage), self.update_menu(controller)])])
            #self.button_grd.add_row([(item, lambda: [controller.show_frame(TargetItemPage), self.update_menu(controller)])])
        controller.get_target_frame(TargetItemPage).display_time_target.set(time.time())
        self.button_grd.pack()
        
        
if __name__ == "__main__":
    
    #best_adaptation(root_state, my_oracle, weights, use_network, vn_name, timebudget)
    session = Root()
    session.mainloop()
    