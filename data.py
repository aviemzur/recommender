import json

import os
import pickle
import shutil

DATA_FILE_NAME = 'data.json'
DEFAULT_FILE_NAME = 'data.json.default'

if not os.path.exists(DATA_FILE_NAME):
    shutil.copyfile(DEFAULT_FILE_NAME, DATA_FILE_NAME)


def get_data():
    with open(DATA_FILE_NAME, 'rb') as f:
        return pickle.load(f)


def put_data(data):
    with open(DATA_FILE_NAME, 'wb') as f:
        pickle.dump(data, f)


pass
