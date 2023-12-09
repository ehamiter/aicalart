import json
import os
import secrets
from collections import deque

"""
I started seeing the same styles propagate over and over again and realized I
wanted something a little less random and more intentional yet different every
time. Something random...ish. So this is a deque that gets randomized, recorded,
consumed, destroyed, and re-generated. So maybe it should be called RARECODEREd.
"""
def shuffle_with_secrets(lst):
    shuffled = []
    while lst:
        element = secrets.choice(lst)
        lst.remove(element)
        shuffled.append(element)
    return shuffled

def load_or_initialize_deque(file_path, style_list):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return deque(json.load(file))
    else:
        return deque(shuffle_with_secrets(style_list))

def save_deque(file_path, dq):
    with open(file_path, 'w') as file:
        json.dump(list(dq), file)

def randomish(style_list, file_path='randomish_queue.json'):
    dq = load_or_initialize_deque(file_path, style_list)
    if not dq:
        dq = deque(shuffle_with_secrets(style_list))

    style_for_today = dq.popleft()
    save_deque(file_path, dq)
    return style_for_today
