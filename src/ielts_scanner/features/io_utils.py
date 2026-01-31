import json


def read_json_file(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def write_json_file(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f)
