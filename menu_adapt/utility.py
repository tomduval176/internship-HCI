import csv
import os
#For fasttext word embedding
#import fasttext 
#import fasttext.util
#from gensim.models.fasttext import load_facebook_model
#For word2vec embeddings
import gensim.downloader as api
#from gensim.models import KeyedVectors
#To compute cosine similarity
from scipy import spatial
import math
import pickle

# reads a log file and returns a frequency distribution as a dict
def load_click_distribution (menu, filename, normalize = True):
    history = []
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            history.append(row[0])
    return get_click_distribution(menu, history, normalize)
    
# returns frequency distribution given a menu and history
def get_click_distribution(menu, history, normalize = True):
    frequency = {}
    separator = "----"
    for command in menu:
        if command != separator:
            frequency[command] = 0

    item_list = list(filter((separator).__ne__, menu)) #menu without separators
    indexed_history = []
    for item in history:
        indexed_history.append([item, item_list.index(item)])
        if item not in list(frequency.keys()):
            frequency[item] = 1.
        else:
            frequency[item] += 1.
    if normalize:
        total_clicks = sum(list(frequency.values()))
        for command in list(frequency.keys()):
            frequency[command] = round(frequency[command] / total_clicks,3)
    return frequency, total_clicks, indexed_history


# Computes associatons based on word-embedding models. For each menu item, a list of associated items is returned
def compute_associations(menu):
    #print(menu)
    # Load pre-trained FT model from wiki corpus
    #ft = load_facebook_model('https://s3.amazonaws.com/dl4j-distribution/GoogleNews-vectors-negative300.bin.gz')
    #fasttext.util.reduce_model(ft, 100) 
    # Load pre-trained word2vec models. SO_vectors_200 = software engineering domain
    # model = KeyedVectors.load_word2vec_format('../fastText/models/SO_vectors_200.bin', binary=True)
    #model = KeyedVectors.load_word2vec_format('https://s3.amazonaws.com/dl4j-distribution/GoogleNews-vectors-negative300.bin.gz', binary=True)  
    model = api.load("glove-wiki-gigaword-100")
    separator = "----"
    associations = {}
    associations_w2v = {}
    for command in menu:
        if command != separator:
            #associations[command] = {command:1.0}
            associations_w2v[command] = {command:1.0}

    for i in menu:
        if i == separator: continue
        #Load word vector
        #vector1 = ft.get_word_vector(i)
        vector1_word2vec = model[i]
        for j in menu:
            if i == j or j == separator: continue
            #vector2 = ft.get_word_vector(j)
            vector2_word2vec = model[j]
            #Compute similarity score
            #score = 1 - spatial.distance.cosine(vector1, vector2)
            score_word2vec = 1 - spatial.distance.cosine(vector1_word2vec, vector2_word2vec)
            #print(i + "," + j + " w2v = " + str(round(score_word2vec,3)) )
            #associations[i][j] = score
            associations_w2v[i][j] = score_word2vec
            
    sorted_associations_w2v = {}
    for key_item, _ in associations_w2v.items():
        sorted_associations_w2v[key_item] = {k: v for k, v in sorted(associations_w2v[key_item].items(), key=lambda item: item[1], reverse=True)}
    #print(f"The associations that we want are this ones: {sorted_associations_w2v}")
    return sorted_associations_w2v

    # >>> vector1 = ft.get_word_vector('print')
    # >>> vector2 = ft.get_word_vector('duplicate')

    # >>> 1 - spatial.distance.cosine(vector1,vector2)
    # >>> 1 - spatial.distance.cosine(ft.get_word_vector('asparagus'),ft.get_word_vector('aubergine'))

def load_activations(history):
    print("HELLLO")
    total_clicks = len(history)
    activations = {} # Activation per target per location
    duration_between_clicks = 20.0 # Wait time between two clicks
    session_interval = 50.0 # Wait time between 2 sessions
    session_click_length = 40 # Clicks per session
    total_sessions = math.ceil(total_clicks/session_click_length) # Number of sessions so far    
    for i in range(0, int(total_clicks)):
        session = math.ceil((i+1)/session_click_length) # Session index
        item = history[i][0]
        position = history[i][1]
        if item not in activations.keys(): activations[item] = {position:0} # Item has not been seen yet. Add to dictionary
        if position not in activations[item].keys(): activations[item][position] = 0 # Item not seen at this position yet. Add to item's dictionary
        time_difference = duration_between_clicks*(total_clicks - i) + (total_sessions - session)*session_interval # Difference between time now and time of click
        activations[item][position] += pow(time_difference, -0.5)
    return activations

# in our example cats = food, clothes, animals, furniture
def load_w2v_associations(menu):
    categories = {"food": "tomato,potato,carrot,onion,beans".split(sep=","),
                  "clothes": "gloves,shoes,bikini,skirt".split(sep=","),
                  "animals": "rabbit,tiger,panda".split(sep=","),
                  "furniture": "chair,sofa,table".split(sep=","),
    }
    w2v_associations = compute_associations(menu)
    associations = {key_item: list(w2v_associations[key_item].keys())[1:]
                    for key_item in w2v_associations.keys()}

    for item in menu:
        for k, v in categories.items():
            if k == "food" and item in v:
                associations[item] = associations[item][:4]
            elif k == "clothes" and item in v:
                associations[item] = associations[item][:3]
            elif k == "furniture" and item in v:
                associations[item] = associations[item][:2]
            elif k == "animals" and item in v:
                associations[item] = associations[item][:2]
    print(associations)
    return associations
                
# do it for a general case by taking into account the nb of items 
def load_w2v_associations_general():
    pass 
    
def load_associations (menu, filename):
    separator = "----"
    associations = {}
    for command in menu:
        if command != separator:
            associations[command] = []
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, skipinitialspace=True)
        for row in csv_reader:
            for item in row:
                if item in associations.keys():
                    associations[item] = associations[item] + row[0:]

    for key in associations:
        if associations[key] == []:
            associations[key] = [key]
    


    # with open(filename) as csv_file:
    #     csv_reader = csv.reader(csv_file)
    #     for row in csv_reader:
    #         if row[0] not in list(associations.keys()):
    #             associations[row[0]] = []
    #         associations[row[0]]= row[1:]
    return associations

def save_menu (menu, filename):
    f = open(filename, "w+")
    for command in menu:
        f.write(command + "\n")
    f.close()

def load_menu (filename):
    menu = []
    f = open(filename, "r")
    for line in f:
        line = line.rstrip()
        if len(line) < 2: continue
        menu.append(line)
    return menu

def save_selection_time(time, filename):
    f = open(filename, "a")
    f.write(str(time) + "\n")
    f.close()
    
def save_activations(dict, filename):
    with open(filename, "wb") as f:
        pickle.dump(dict, f)
        
def load_activations(filename):
    with open(filename, "rb") as f:
        loaded_dict = pickle.load(f)
    return loaded_dict
        

# Returns association matrix for a menu using the associations dictionary
def get_association_matrix(menu, associations):
    association_matrix = []
    for k in range (0, len(menu)):
        if menu[k] in associations:
            for l in range (0, len(menu)):
                if menu[l] in associations[menu[k]]:
                    association_matrix.append(1.0)
                else:
                    association_matrix.append(0.0)
        else:
            for l in range (0, len(menu)):
                association_matrix.append(0.0)
    return association_matrix

# Returns sorted frequencies list for a menu using the frequency dictionary
def get_sorted_frequencies(menu,frequency):
    separator = "----"
    sorted_frequencies = []
    for k in range (0, len(menu)):
        if menu[k] == separator:
            sorted_frequencies.append(0.0)
        else:
            sorted_frequencies.append(frequency[menu[k]])
    return sorted_frequencies

#function that can replace the two previous functions in one 
def get_assoc_and_freq_list(state):
    separator = "----"
    associations = state.menu_state.associations
    frequency = state.user_state.freqdist
    menu = state.menu_state.menu
    # total_clicks = state.user_state.total_clicks
    # associations = load_associations(menu, filename)
    # frequency, total_clicks = load_click_distribution(menu, filename)
    assoc_list = []
    freq_list = []

    for k in range(0, len(menu)):
        if menu[k] in associations:
            for l in range(0, len(menu)):
                if menu[l] in associations[menu[k]]:
                    assoc_list.append(1.0)
                else:
                    assoc_list.append(0.0)
        else:
            for l in range (0, len(menu)):
                assoc_list.append(0.0)
    
    for k in range(0, len(menu)):
        if menu[k] == separator:
            freq_list.append(0.0)
        else:
            freq_list.append(frequency[menu[k]])
    return assoc_list, freq_list

#get the index of the first item of a group
def get_header_indexes(menu):
        header_indexes = []
        separator = "----"
        groupboundary = False
        for i in range(0, len(menu)):
            if i == 0 or menu[i] == separator:
                groupboundary = True # Found a group start indicator
            if groupboundary and menu[i] != separator:
                header_indexes += [i] # First item of group (header)
                groupboundary = False
        return header_indexes