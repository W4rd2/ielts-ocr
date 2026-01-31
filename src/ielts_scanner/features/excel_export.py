import os

import pandas as pd
import streamlit as st

from ielts_scanner.config import EXCEL_FILE_NAME, FAULTY_FIELDS_SHEETNAME, MODIFIED_SUFFIX, REJECTED_CERTS_SHEETNAME
from ielts_scanner.models.exam_result import ExamResult


def merge_exam_results(e1, e2):
    """
    Attempt to merge two examResult objects e1 and e2.
    - If both have the same non-empty value for a field, keep that value.
    - If one is empty, the non-empty one wins.
    - If both are non-empty but differ, return None (cannot merge).
    
    Returns:
        A new examResult object if merge is successful, or
        None if they cannot be merged due to conflicts.
    """
    e1_dict = e1.__dict__
    e2_dict = e2.__dict__

    merged_dict = {}

    # Union of all attributes
    all_keys = set(e1_dict.keys()) | set(e2_dict.keys())

    for key in all_keys:
        val1 = e1_dict.get(key, "")
        val2 = e2_dict.get(key, "")

        # If both are empty
        if not val1 and not val2:
            merged_dict[key] = ""
        # If val1 is empty, take val2
        elif not val1:
            merged_dict[key] = val2
        # If val2 is empty, take val1
        elif not val2:
            merged_dict[key] = val1
        else:
            # Both are non-empty. Must match exactly or we cannot merge
            if val1 == val2:
                merged_dict[key] = val1
            else:
                # Conflict: different non-empty values
                return None

    # Build a new examResult from merged_dict
    # Assumes examResult class can be constructed with no args
    new_e = e1.__class__()  # or e2.__class__()
    for k, v in merged_dict.items():
        setattr(new_e, k, v)

    return new_e


def remove_duplicates_keep_nonempty(examResults):
    """
    Remove duplicates in examResults by merging objects that differ
    only by empty-string vs. non-empty-string fields.
    
    Example logic:
      - Keep a 'unique_results' list.
      - For each new examResult e:
          1. Attempt to merge with existing results in 'unique_results'.
          2. If successfully merged, update that entry and stop.
          3. If it cannot merge with any, append e as a new unique object.
      - Return 'unique_results' at the end.
    """
    unique_results = []

    for e in examResults:
        merged_somewhere = False

        for i, existing in enumerate(unique_results):
            merged_obj = merge_exam_results(existing, e)
            if merged_obj is not None:
                # They merged successfully, update that entry
                unique_results[i] = merged_obj
                merged_somewhere = True
                break

        if not merged_somewhere:
            # No merge => a new unique result
            unique_results.append(e)

    return unique_results


def excelWriter(examResults, rejected_examResults=[], faulty_examResults=[]):
    global EXCEL_FILE_NAME, FAULTY_FIELDS_SHEETNAME, REJECTED_CERTS_SHEETNAME

    excelPath = os.path.join(st.session_state.session_dir, EXCEL_FILE_NAME)
    orange_color_format = {"bg_color": "#FFA500"}
    yellow_color_format = {"bg_color": "#FFDE64"}

    examResults = remove_duplicates_keep_nonempty(examResults)
    faulty_examResults = remove_duplicates_keep_nonempty(faulty_examResults)
    rejected_examResults = remove_duplicates_keep_nonempty(rejected_examResults)

    with pd.ExcelWriter(excelPath, engine="xlsxwriter") as writer:
        # --------------------------------------------------------------------
        # Handle Main (valid) exam results
        # --------------------------------------------------------------------
        if examResults:
            # Remove duplicates (so we don't repeatedly write the same data)
            old_examResults = examResults + []
            #extract all unique values and put them in examResults

            # Convert to dict if not already
            examResults = [
                {
                    k: v
                    for k, v in (
                        examResult.__dict__ if isinstance(examResult, ExamResult) else examResult
                    ).items()
                    if k != "rejectance_reason"
                }
                for examResult in examResults
            ]

            main_data = prepare_dataframe(examResults)
            update_session_state(main_data)
            _write_to_sheet(writer, main_data, "Main", orange_color_format, yellow_color_format)

        # --------------------------------------------------------------------
        # Handle faulty exam results
        # --------------------------------------------------------------------
        if faulty_examResults:
            faulty_examResults = list(set(faulty_examResults))
            # Convert to dict if not already
            faulty_examResults = [
                examResult if isinstance(examResult, dict) else examResult.__dict__
                for examResult in faulty_examResults
            ]

            faulty_data = prepare_dataframe(faulty_examResults)
            _write_to_sheet(writer, faulty_data, FAULTY_FIELDS_SHEETNAME, orange_color_format, yellow_color_format)

        # --------------------------------------------------------------------
        # Handle rejected exam results
        # --------------------------------------------------------------------
        if rejected_examResults:
            rejected_examResults = list(set(rejected_examResults))
            # Convert to dict if not already
            rejected_examResults = [
                examResult if isinstance(examResult, dict) else examResult.__dict__
                for examResult in rejected_examResults
            ]

            # We need a temporary DataFrame to figure out column order
            tmp_data = prepare_dataframe(rejected_examResults)
            # Reorder so 'Rejectance_reason' is first
            reorder = ["Rejectance_reason"] + [col for col in tmp_data.columns if col != "Rejectance_reason"]

            rejected_data = prepare_dataframe(rejected_examResults, reorder=reorder)
            _write_to_sheet(writer, rejected_data, REJECTED_CERTS_SHEETNAME, orange_color_format, yellow_color_format)


def prepare_dataframe(data, capitalize=True, reorder=None):
    """
    Convert data (which should already be a list of dictionaries) to a DataFrame,
    capitalize columns, drop duplicates, and reorder if necessary.
    """
    df = pd.DataFrame(data)

    if capitalize:
        df.columns = [col.capitalize() for col in df.columns]

    if reorder:
        df = df[reorder]

    df.drop_duplicates(inplace=True)
    return df


def update_session_state(data):
    """Update session state variables for total and blank fields."""
    st.session_state.total_fields = data.size
    st.session_state.blank_fields = data.isnull().sum().sum() + (data == "").sum().sum()


def _write_to_sheet(writer, data, sheet_name, emptyField_format, modifiedField_format):
    """Write DataFrame to an Excel sheet and apply formatting."""
    data.to_excel(writer, sheet_name=sheet_name, index=False)
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # Set column widths based on the max length of data in each column
    for i, column in enumerate(data.columns):
        max_len = max(data[column].astype(str).map(len).max(), len(column)) + 10
        worksheet.set_column(i, i, max_len)

    # Apply conditional formatting for blanks
    worksheet.conditional_format(
        f"A2:{chr(65 + len(data.columns) - 1)}{len(data) + 1}",
        {"type": "blanks", "format": workbook.add_format(emptyField_format)},
    )

    # Highlight modified fields (i.e., those ending with MODIFIED_SUFFIX)
    modified_suffix_len = len(MODIFIED_SUFFIX)
    for row_index, row in data.iterrows():
        for col_index, value in enumerate(row):
            if isinstance(value, str) and value.endswith(MODIFIED_SUFFIX):
                # Write the value without the MODIFIED_SUFFIX, with a highlight format
                worksheet.write(row_index + 1, col_index, value[:-modified_suffix_len], workbook.add_format(modifiedField_format))
            else:
                worksheet.write(row_index + 1, col_index, value)
