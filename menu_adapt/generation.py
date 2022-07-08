import json
import random
import numpy as np


def generate_history(menu, s, N):
    history = []
    freq_app = np.random.zipf(a=s, size=N)
    for item, freq in zip(menu, freq_app):
        history += freq * [item]
    random.shuffle(history)
    return history
    
def save_history(menu, filepath):
    history = generate_history(menu)
    f = open(filepath, 'w+')
    for item in history:
        f.write(item)
    f.close()

#think about a distribution law that can randomized users interests
def generate_user_interest(menu):
    pass

def save_user(menu, filepath):
    user_interests = generate_user_interest(menu)
    with open(filepath,'w') as f:
        f.write(json.dumps(user_interests))
    