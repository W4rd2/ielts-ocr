import os

try:
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
except ImportError:
    Image = None

# Prevent PyTorch MPS memory watermark issues (no-op on non-MPS systems)
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

# Application constants
MAIN_DIR = "IELTS-Scanner_data_folder"

EXCEL_FILE_NAME = "output.xlsx"
FAULTY_FIELDS_SHEETNAME = "Faulty Fields"
REJECTED_CERTS_SHEETNAME = "Rejected Certificates"
MODIFIED_SUFFIX = "-modified"
DELETED_FLAG_FILE = "toBeDeleted.txt"
DATA_FILENAME = "data.txt"
ONE_SKILL_RETAKE_REASON = "-One Skill Retake"
ROW_EMPTY_BLANKS_THRESHOLD = 4
