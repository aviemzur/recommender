import json

import os
import shutil

DATA_FILE_NAME = 'data.json'
DEFAULT_FILE_NAME = 'data.json.default'

if not os.path.exists(DATA_FILE_NAME):
    shutil.copyfile(DEFAULT_FILE_NAME, DATA_FILE_NAME)


def get_data():
    with open(DATA_FILE_NAME) as f:
        return json.load(f)


def put_data(data):
    with open(DATA_FILE_NAME, 'w') as f:
        json.dump(data, f)


pass
