import os
import sys

# Ensure the src layout is importable when running the entry script directly.
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st

from ielts_scanner.features.ui import main, run_streamlit


if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        run_streamlit()
