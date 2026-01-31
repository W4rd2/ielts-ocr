import json
import os
import shutil
import time
from datetime import datetime

import streamlit as st

from ielts_scanner.config import DATA_FILENAME, DELETED_FLAG_FILE, MAIN_DIR
from ielts_scanner.features.io_utils import read_json_file, write_json_file


def addReadyToBeDeleted():
    with open(os.path.join(st.session_state.session_dir, DELETED_FLAG_FILE), "a") as f:
        f.write(st.session_state.session_dir + "\n")


def clearOldSessions():
    global MAIN_DIR
    for folder in os.listdir(MAIN_DIR):
        if os.path.isdir(os.path.join(MAIN_DIR, folder)) and folder != "models":
            folderPath = os.path.join(MAIN_DIR, folder)
            deleteFilePath = os.path.join(folderPath, DELETED_FLAG_FILE)
            if os.path.exists(deleteFilePath):
                if os.path.getatime(deleteFilePath) < time.time() - 60 * 60 * 12:
                    shutil.rmtree(folderPath)
            elif os.path.getatime(folderPath) < time.time() - 60 * 60 * 12:
                shutil.rmtree(folderPath)


def cleanup(deepClean=True):
    if os.path.exists(st.session_state.session_dir):
        if deepClean:
            shutil.rmtree(st.session_state.session_dir)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
        else:
            for file in os.listdir(st.session_state.session_dir):
                os.remove(os.path.join(st.session_state.session_dir, file))


def handle_first_classes_date():
    global DATA_FILENAME

    file_path = os.path.join(MAIN_DIR, DATA_FILENAME)
    json_data = read_json_file(file_path)

    if "first_classes_date" not in json_data.keys():
        json_data["first_classes_date"] = None
    else:
        st.session_state.first_classes_date = str(json_data["first_classes_date"])
    with st.form(key="date_form"):
        date_str = json_data["first_classes_date"]
        new_date = st.date_input("Set First Day of Classes", value=datetime.strptime(date_str, "%Y-%m-%d") if json_data["first_classes_date"] else None)
        submit = st.form_submit_button("Save")
        if submit:
            st.success(f"First Day of Classes set to {new_date}")
            json_data["first_classes_date"] = str(new_date)
            write_json_file(file_path, json_data)
            st.session_state.first_classes_date = str(new_date)
