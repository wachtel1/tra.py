def delEmptyLines(t):
    t = "\n".join([ll.rstrip() for ll in t.splitlines() if ll.strip()])
    return t


def delMultiSpaces(t):
    while "  " in t:
        t = t.replace("  ", " ")
    while "\r " in t:
        t = t.replace("\r ", "\r")
    while " \r" in t:
        t = t.replace(" \r", "\r")
    return t


def delNewLines(t, saveNewLinesAfterSpecialSymbols, specialSymbols):
    t = t.replace("\r\n", "\r").replace("\n", "\r")
    if saveNewLinesAfterSpecialSymbols:
        for symbol in specialSymbols:
            t = t.replace(symbol + "\r", "###" +
                          str(specialSymbols.index(symbol)) + "###")
        t = t.replace("\r", " ")
        for symbol in specialSymbols:
            t = t.replace(
                "###" + str(specialSymbols.index(symbol)) + "###", symbol + "\r")
    else:
        t = t.replace("\r", " ")
    t = delMultiSpaces(t)
    return t


def delSpaces(t):
    t = t.replace(" ", "").replace("    ", "").replace("　", "")
    return t


def basicCleanup(t):
    t = t.replace(" ", " ").replace("　", " ")
    t = t.replace("\r\n", "\r").replace("\n", "\r")
    t = delMultiSpaces(t)
    return t
