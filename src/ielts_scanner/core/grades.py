from ielts_scanner.config import MODIFIED_SUFFIX


def checkCEFR(examResult):
    if examResult.overall_band_score != "":
        avg = float(examResult.overall_band_score.strip(MODIFIED_SUFFIX))
        if examResult.cefr_level == "":
            if avg >= 7:
                examResult.cefr_level = "C1" + MODIFIED_SUFFIX
            elif avg >= 6:
                examResult.cefr_level = "B2" + MODIFIED_SUFFIX
            elif avg >= 5:
                examResult.cefr_level = "B1" + MODIFIED_SUFFIX
            elif avg >= 4:
                examResult.cefr_level = "A2" + MODIFIED_SUFFIX
            else:
                examResult.cefr_level = "A1" + MODIFIED_SUFFIX


def patchGrades(examResult, marksList):
    if len(marksList) == 5:
        total = sum([float(marksList[i]) for i in range(4)])
        avg = total / 4.0
        avg = avg if str(avg) == marksList[4] else None

        if examResult.listening_score == "":
            examResult.listening_score = marksList[0] + MODIFIED_SUFFIX
        if examResult.reading_score == "":
            examResult.reading_score = marksList[1] + MODIFIED_SUFFIX
        if examResult.writing_score == "":
            examResult.writing_score = marksList[2] + MODIFIED_SUFFIX
        if examResult.speaking_score == "":
            examResult.speaking_score = marksList[3] + MODIFIED_SUFFIX

        if avg != examResult.overall_band_score and avg is not None:
            examResult.overall_band_score = marksList[4] + MODIFIED_SUFFIX

    elif len(marksList) == 4:
        if examResult.overall_band_score != "":
            if examResult.overall_band_score.strip(MODIFIED_SUFFIX) == marksList[3]:
                emptyField = [
                    examResult.listening_score,
                    examResult.reading_score,
                    examResult.writing_score,
                    examResult.speaking_score,
                ]
                for i in range(len(emptyField)):
                    if emptyField[i] == "":
                        totalGrades = sum(
                            [float(marksList[j].strip(MODIFIED_SUFFIX)) for j in range(4) if j != i]
                        )
                        emptyField[i] = str(float(marksList[3].strip(MODIFIED_SUFFIX)) * 4 - totalGrades) + MODIFIED_SUFFIX
                        break
                examResult.listening_score = emptyField[0]
                examResult.reading_score = emptyField[1]
                examResult.writing_score = emptyField[2]
                examResult.speaking_score = emptyField[3]
        else:
            total = sum([float(i) for i in marksList])
            avg = total / 4.0
            examResult.overall_band_score = str(avg) + MODIFIED_SUFFIX

    checkCEFR(examResult)
