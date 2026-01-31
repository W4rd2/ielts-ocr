from ielts_scanner.config import MODIFIED_SUFFIX


def contains(lst, value):
    return value in lst


def safe_index(lst, value, start=0):
    try:
        return lst.index(value, start)
    except ValueError:
        return -1


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def isNum(text):
    for char in text:
        if not (48 <= ord(char) <= 57 or ord(char) == 46 or char == "O" or char == "I"):
            return False
    return True


def convertLettersToNumbers(text, start=0, end=-1):
    if end == -1:
        end = len(text)
    for i in range(start, end):
        if text[i] == "O":
            text = text[:i] + "0" + text[i + 1 :]
        elif text[i] == "I":
            text = text[:i] + "1" + text[i + 1 :]
        elif text[i] == "S":
            text = text[:i] + "5" + text[i + 1 :]
        elif text[i] == "B":
            text = text[:i] + "8" + text[i + 1 :]
        elif text[i] == "Z":
            text = text[:i] + "2" + text[i + 1 :]
        elif text[i] == "G":
            text = text[:i] + "6" + text[i + 1 :]

    return text


def isValidScore(score):
    if score == "0":
        return ""

    newScore = ""
    if len(score) == 3:
        if score[1] in [".", ","]:
            for char in score:
                if char.isdigit() or char in [".", ","]:
                    newScore += "." if char == "," else char
                else:
                    return ""
            return newScore
    if len(score) == 1:
        if score.isdigit():
            newScore = score + ".0" + MODIFIED_SUFFIX
            return newScore
    return ""
