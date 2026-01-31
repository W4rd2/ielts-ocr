import gc
import json
import os
import time
from datetime import datetime

import cv2
import easyocr
import numpy as np
import streamlit as st
from skimage.morphology import disk, opening

from PIL import Image

from ielts_scanner.config import MAIN_DIR, MODIFIED_SUFFIX, ONE_SKILL_RETAKE_REASON, ROW_EMPTY_BLANKS_THRESHOLD
from ielts_scanner.core.grades import patchGrades
from ielts_scanner.core.utils import convertLettersToNumbers, isNum, isValidScore, safe_index
from ielts_scanner.models.exam_result import ExamResult


def clear_unused_objects():
    del st.session_state.reader
    init_reader()
    gc.collect()


def init_reader():
    st.session_state.reader = easyocr.Reader(["en"], gpu=True, model_storage_directory=os.path.join(MAIN_DIR, "models"))


def getText(path):
    texts = st.session_state.reader.readtext(path, detail=0, contrast_ths=0.7, blocklist="$@")
    accepted = True
    examResult = ExamResult()
    print(examResult.rejectance_reason)

    print(texts)
    startOfScanningNumbers = 0
    endOfScanningNumbers = safe_index(texts, "Administrator Comments")
    endOfScanningNumbers = 0 if endOfScanningNumbers == -1 else endOfScanningNumbers
    for i in range(1, len(texts)):
        text = texts[i]
        if len(text) == 18:
            if isNum(convertLettersToNumbers(text, 0, 2)[0:2]) and isNum(convertLettersToNumbers(text, 4, 10)[4:10]):
                text = convertLettersToNumbers(text, 0, 2)
                text = convertLettersToNumbers(text, 4, 10)
                text = convertLettersToNumbers(text, 14, 17)
                examResult.test_form_no = text
    formCenterNumber = examResult.test_form_no[2:4]
    formCandidtateNumber = examResult.test_form_no[4:10]
    formCandidateId = examResult.test_form_no[:2]
    formFamName = examResult.test_form_no[10:13]
    formFirstName = examResult.test_form_no[13:14]

    examResult.candidate_no = formCandidtateNumber

    marksList = []

    for i in range(1, len(texts)):
        text = texts[i]
        if "retake" in text.lower() and ONE_SKILL_RETAKE_REASON not in examResult.rejectance_reason:
            accepted = False
            examResult.rejectance_reason += ONE_SKILL_RETAKE_REASON

        if examResult.first_name != "" and examResult.family_name != "":
            text = text.replace("'", "").strip()
        if text in ["ACADEMIC", "GENERAL TRAINING"] and examResult.exam_type == "":
            examResult.exam_type = text
            if text == "GENERAL TRAINING":
                accepted = False
                examResult.rejectance_reason += "-General Training"
            if examResult.test_form_no != "":
                if examResult.test_form_no.strip(MODIFIED_SUFFIX)[-1] != text[0]:
                    examResult.test_form_no = examResult.test_form_no.strip(MODIFIED_SUFFIX)
                    examResult.test_form_no = examResult.test_form_no[:-1] + text[0] + MODIFIED_SUFFIX

        elif len(text) == 5 and (not isNum(text[0:2])) and "Centre Number" in texts[i - 1]:
            text = convertLettersToNumbers(text, start=2)
            examResult.center_no = text
            if len(examResult.test_form_no) == 18:
                numsOnly = "".join(filter(str.isdigit, text))
                charsOnly = "".join(filter(str.isalpha, text))
                old_form_no = examResult.test_form_no.strip(MODIFIED_SUFFIX)
                new_form_no = old_form_no[:2] + charsOnly + old_form_no[4:14] + text[2:] + old_form_no[17]

                if new_form_no != old_form_no:
                    new_form_no += MODIFIED_SUFFIX
                examResult.test_form_no = new_form_no

        elif len(text) == 11 and (text[2] == "/" or text[2] == "I") and (not isNum(text[3:6])) and (text[6] == "/" or text[6] == "I"):
            if "0" in text[3:6]:
                text = text[:3] + text[3:6].replace("0", "O") + text[6:]

            text = text.replace("I", "/")

            text = convertLettersToNumbers(text, start=0, end=2)
            text = convertLettersToNumbers(text, start=7)

            examResult.exam_date = text

        elif formCandidtateNumber in text and text != examResult.test_form_no and "Candidate Number" in texts[i - 1] and examResult.candidate_no == "":
            text = convertLettersToNumbers(text)
            temp = text.split(",")
            if len(temp) == 2:
                text = temp[0] + MODIFIED_SUFFIX
            examResult.candidate_no = text

        elif not isNum(text) and "Family Name" in texts[i - 1]:
            if "First Name" in text:
                text = ""
            examResult.family_name = text

        elif "First Name" in texts[i - 1] and not isNum(text):
            examResult.first_name = text

        elif (("Candidate ID" in texts[i - 1]) or ("Candidate [D" in texts[i - 1])) and isNum(text[-3:]):
            text = convertLettersToNumbers(text, start=1)
            examResult.candidate_id = text

        elif len(text) == 1 and text in ["M", "F"] and "Sex" in texts[i - 1]:
            examResult.sex = text

        elif texts[i - 1] == "Scheme Code" and not isNum(text):
            examResult.scheme_code = text

        elif isValidScore(text) != "":
            text = isValidScore(text)
            if startOfScanningNumbers <= i < endOfScanningNumbers:
                marksList.append(text)
            if texts[i - 1] == "Listening":
                examResult.listening_score = text
            elif texts[i - 1] == "Reading":
                examResult.reading_score = text
            elif texts[i - 1] == "Writing":
                examResult.writing_score = text
            elif texts[i - 1] == "Speaking":
                examResult.speaking_score = text
            elif "Band" in texts[i - 1]:
                examResult.overall_band_score = text

        elif text in ["A1", "A2", "B1", "B2", "C1", "C2"] and ("Level" in (texts[i - 1] + texts[i + 1]) or "CEFR" in texts[i - 1]):
            examResult.cefr_level = text

        elif len(text) == 10 and text[2] == "/" and text[5] == "/" and isNum(text[0:2]) and isNum(text[3:5]) and isNum(text[6:10]):
            examResult.issue_date = text

    patchGrades(examResult, marksList)

    if examResult.overall_band_score != "":
        if float(examResult.overall_band_score.strip(MODIFIED_SUFFIX)) < 5.5:
            accepted = False
            examResult.rejectance_reason += "-Overall below 5.5"

    if examResult.exam_date != "":
        try:
            exam_date = datetime.strptime(examResult.exam_date, "%d/%b/%Y")
            exam_date_plus_two_years = exam_date.replace(year=exam_date.year + 2)

            if exam_date_plus_two_years < datetime.strptime(st.session_state.first_classes_date, "%Y-%m-%d"):
                accepted = False
                examResult.rejectance_reason += "-Certificate Expired"
        except:
            examResult.exam_date += MODIFIED_SUFFIX

    return examResult, accepted


def apply_filters(imgPath):
    if imgPath.split("_")[-1] == "filtered.jpg":
        return imgPath

    black = 0
    white = 255
    threshold = 200

    img = Image.open(imgPath).convert("LA")
    pixels = np.array(img)[:, :, 0]

    # pixels[pixels > threshold] = white
    # pixels[pixels < threshold] = black

    blobSize = 1
    structureElement = disk(blobSize)
    pixels = np.invert(opening(np.invert(pixels), structureElement))

    nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(np.invert(pixels), connectivity=8)
    sizes = stats[1:, -1]
    nb_components -= 1

    minimum_size = 100
    newPixels = np.ones(pixels.shape) * 255

    for i in range(1, nb_components):
        if sizes[i] > minimum_size:
            newPixels[output == i + 1] = 0

    newImg = Image.fromarray(newPixels).convert("RGB")
    base, ext = os.path.splitext(imgPath)
    newPath = f"{base}_enhanced{ext}"
    newImg.save(newPath)

    return newPath


def process_images(pathes):
    global totalApproximateTime
    exam_results = []
    rejected_examResults = []
    faulty_examResults = []
    startTime = time.time()

    progress_bar = st.progress(0)
    totalApproximateTime_text = st.empty()
    totalCertificatedProcessed_text = st.empty()

    currentExamResult, accepted = getText(pathes[0])
    isFaulty = sum(1 for value in vars(currentExamResult).values() if value in [None, ""]) > ROW_EMPTY_BLANKS_THRESHOLD
    if accepted:
        if isFaulty:
            faulty_examResults.append(currentExamResult)
        else:
            exam_results.append(currentExamResult)
    else:
        rejected_examResults.append(currentExamResult)
    timeDiff = time.time() - startTime
    totalApproximateTime_text.text(f"Total approximate time left: {(timeDiff*len(pathes))/60:.2f} minutes")
    for index, path in enumerate(pathes[1:]):
        startTimeForOneImage = time.time()
        currentExamResult, accepted = getText(path)
        if accepted:
            exam_results.append(currentExamResult)
        else:
            rejected_examResults.append(currentExamResult)
        print("time taken for one image ", time.time() - startTimeForOneImage, "\n", path, "\n", "*" * 50)
        clear_unused_objects()
        index += 1
        print(index)
        timeDiff = time.time() - startTime
        progress_bar.progress(index / len(pathes))
        totalApproximateTime_text.text(f"Total approximate time left: {(timeDiff*(len(pathes)-index))/60:.2f} minutes")
        totalCertificatedProcessed_text.text(f"Certificates processed: {index}/{len(pathes)}")

        startTime = time.time()
    progress_bar.progress(1.0)
    totalApproximateTime_text.text("")
    totalCertificatedProcessed_text.text("")
    return exam_results, rejected_examResults, faulty_examResults
