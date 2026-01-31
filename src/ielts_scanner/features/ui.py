import sys
from pathlib import Path

# Make sure src layout is importable when Streamlit runs this file directly.
SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

import os
import time
import uuid
import subprocess

import streamlit as st

from ielts_scanner.config import EXCEL_FILE_NAME, MAIN_DIR
from ielts_scanner.features.excel_export import excelWriter
from ielts_scanner.features.ocr import init_reader, process_images
from ielts_scanner.features.pdf_ingest import getPathes
from ielts_scanner.features.session_management import addReadyToBeDeleted, cleanup, clearOldSessions, handle_first_classes_date


def run_streamlit():
    absPATH = os.path.abspath(__file__)
    command = f"streamlit run '{absPATH}'"
    subprocess.run(command, shell=True)


def main():
    global EXCEL_FILE_NAME, MAIN_DIR
    os.makedirs(MAIN_DIR, exist_ok=True)
    clearOldSessions()
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "session_dir" not in st.session_state:
        st.session_state.session_dir = os.path.join(MAIN_DIR, st.session_state.session_id)
        os.makedirs(st.session_state.session_dir, exist_ok=True)
    if "totalApproximateTime" not in st.session_state:
        st.session_state.totalApproximateTime = 0
    if "reader" not in st.session_state:
        st.session_state.reader = None
        init_reader()
    if "total_fields" not in st.session_state:
        st.session_state.total_fields = 0
    if "blank_fields" not in st.session_state:
        st.session_state.blank_fields = 0
    if "excel_ready" not in st.session_state:
        st.session_state.excel_ready = False
    if "first_classes_date" not in st.session_state:
        st.session_state.first_classes_date = None

    st.title("Exam Result OCR Processor")
    handle_first_classes_date()
    st.write("Upload your exam result images (PNG, JPG, JPEG, PDF) to extract data and download as Excel.")

    uploaded_files = st.file_uploader("Choose files", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

    if st.button("Process Files"):
        if st.session_state.first_classes_date is None:
            st.error("Please set the first day of classes.")

        elif uploaded_files:
            cleanup(deepClean=False)
            startTime = time.time()
            programStartTime = time.time()

            pathes = getPathes(uploaded_files)
            startTime = time.time()
            examResults, rejected_examResults, faulty_examResults = process_images(pathes)
            print("time taken for ocr ", time.time() - startTime)

            startTime = time.time()
            if (examResults and examResults != []) or (rejected_examResults != [] and rejected_examResults):
                excelWriter(examResults, rejected_examResults, faulty_examResults)
            print("time taken for excel writing ", time.time() - startTime)
            print("total time taken ", time.time() - programStartTime)
            print("=" * 50)

            st.session_state.excel_ready = True
            addReadyToBeDeleted()
            st.success("Processing complete!")
            st.write(f"Time taken: {time.time() - programStartTime:.0f} seconds")

            total_fields = st.session_state.total_fields
            blank_fields = st.session_state.blank_fields

            filled_fields = total_fields - blank_fields
            filled_percentage = (filled_fields / total_fields) * 100 if total_fields > 0 else 0

            if len(rejected_examResults) > 0:
                st.warning(f"rejected certificates: {len(rejected_examResults)}")
            else:
                st.success("All certificates accepted.")
            if examResults and examResults != []:
                if filled_percentage > 90:
                    st.success(f"Filled Fields: {filled_percentage:.2f}%")
                elif filled_percentage > 70:
                    st.warning(f"Filled Fields: {filled_percentage:.2f}%")
                else:
                    st.error(f"Filled Fields: {filled_percentage:.2f}%")
        else:
            st.error("Please upload at least one file.")

    if st.session_state.excel_ready:
        excelPath = os.path.join(st.session_state.session_dir, EXCEL_FILE_NAME)

        if os.path.exists(excelPath):
            with open(excelPath, "rb") as file:
                st.download_button(label="Download Excel File", data=file, file_name=EXCEL_FILE_NAME)

    if st.button("Clear Session"):
        cleanup()
        st.success("Session cleared successfully.")
