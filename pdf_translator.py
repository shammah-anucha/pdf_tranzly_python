import pymupdf

from deep_translator import GoogleTranslator

WHITE = pymupdf.pdfcolor["white"]

textflags = pymupdf.TEXT_DEHYPHENATE

to_german = GoogleTranslator(source="de", target="en")

doc = pymupdf.open("Regatta_52Nord_Muster-MV (Stellplatz)_Draft_CBRE IM (5).pdf")

ocg = doc.add_ocg("English", on=True)

for page in doc:
    blocks = page.get_text("blocks", flags=textflags)
    for block in blocks:
        bbox = block[:4]
        text = block[4]
        try:
            english = to_german.translate(text)
        except Exception:
            continue

        if not english or not isinstance(english, str):
            continue
        page.draw_rect(bbox, color=None, fill=WHITE, oc=ocg)
        page.insert_htmlbox(bbox, english, css="* {font-family: sans-serif;}", oc=ocg)

doc.subset_fonts()
doc.ez_save(
    "translated-english-Regatta_52Nord_Muster-MV (Stellplatz)_Draft_CBRE IM (5).pdf"
)
