import unittest

from ielts_scanner.config import MODIFIED_SUFFIX
from ielts_scanner.core.grades import checkCEFR, patchGrades
from ielts_scanner.core.utils import convertLettersToNumbers, isValidScore
from ielts_scanner.models.exam_result import ExamResult


class ExamResultTests(unittest.TestCase):
    def test_default_result_has_expected_export_fields(self):
        result = ExamResult()

        self.assertEqual("", result.test_form_no)
        self.assertEqual("", result.rejectance_reason)
        self.assertIn("overall_band_score", result.__dict__)

    def test_check_cefr_derives_level_from_overall_band(self):
        result = ExamResult()
        result.overall_band_score = "6.5"

        checkCEFR(result)

        self.assertEqual(f"B2{MODIFIED_SUFFIX}", result.cefr_level)

    def test_patch_grades_fills_missing_component_scores(self):
        result = ExamResult()

        patchGrades(result, ["6.0", "6.5", "7.0", "7.5", "6.75"])

        self.assertEqual(f"6.0{MODIFIED_SUFFIX}", result.listening_score)
        self.assertEqual(f"7.5{MODIFIED_SUFFIX}", result.speaking_score)
        self.assertEqual(f"6.75{MODIFIED_SUFFIX}", result.overall_band_score)

    def test_score_and_ocr_character_helpers_normalize_common_values(self):
        self.assertEqual("6.5", isValidScore("6,5"))
        self.assertEqual(f"7.0{MODIFIED_SUFFIX}", isValidScore("7"))
        self.assertEqual("012856", convertLettersToNumbers("OIZBSG"))


if __name__ == "__main__":
    unittest.main()
