import os
import time

import streamlit as st
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter


def split_pdf_to_single_pages(pdf_path, output_dir):
    pdf_reader = PdfReader(pdf_path)
    single_page_paths = []

    for page_num in range(len(pdf_reader.pages)):
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[page_num])

        single_page_pdf_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{page_num + 1}.pdf")
        with open(single_page_pdf_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)

        single_page_paths.append(single_page_pdf_path)

    return single_page_paths


def getPathes(uploaded_files):
    startTime = time.time()
    statusContainer = st.empty()
    counterContainer = st.empty()
    statusContainer.text("Converting files to certificates...")

    session_dir = st.session_state.session_dir
    imgPathes = []

    for index, uploaded_file in enumerate(uploaded_files):
        file_path = os.path.join(session_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_files[index].getbuffer())
        newFilePath = os.path.join(session_dir, uploaded_file.name.replace(" ", "_"))
        os.rename(file_path, newFilePath)
        imgPathes.append(newFilePath)

    imgPathes = list(set(imgPathes))

    pathes = []
    count = 0
    totalCertsNum = len(imgPathes)

    for imgPath in imgPathes:
        ext = os.path.splitext(imgPath)[1].lower()

        if ext in [".png", ".jpg", ".jpeg", ".pdf"]:
            if ext == ".pdf":
                single_page_pdfs = split_pdf_to_single_pages(imgPath, session_dir)
                totalCertsNum += len(single_page_pdfs) - 1

                for single_page_pdf in single_page_pdfs:
                    count += 1
                    counterContainer.text(f"Converting certificate {count}/{totalCertsNum}")
                    page_size = os.path.os.path.getsize(single_page_pdf) / 1000  # size in KB
                    # page_dpi=1000 if page_size < 600 else 500
                    pages = convert_from_path(single_page_pdf, dpi=page_size)
                    for page in pages:
                        new_image_path = os.path.splitext(single_page_pdf)[0] + ".jpg"
                        if new_image_path not in pathes:
                            page.save(new_image_path, "JPEG")
                            pathes.append(new_image_path)
            else:
                # new_image_path = os.path.splitext(imgPath)[0] + '.jpg'
                # if new_image_path not in pathes:
                pathes.append(imgPath)

    counterContainer.text("")
    statusContainer.text("Files converted successfully.\nProcessing files...")
    print("time taken for conversion", time.time() - startTime)
    return pathes
