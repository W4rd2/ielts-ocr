class ExamResult:
    """Mutable OCR result record used by parser, grading, and Excel export steps."""

    fields = (
        "test_form_no",
        "center_no",
        "candidate_no",
        "family_name",
        "first_name",
        "candidate_id",
        "sex",
        "scheme_code",
        "exam_date",
        "exam_type",
        "listening_score",
        "reading_score",
        "writing_score",
        "speaking_score",
        "overall_band_score",
        "cefr_level",
        "issue_date",
        "rejectance_reason",
    )

    def __init__(self):
        for field in self.fields:
            setattr(self, field, "")
