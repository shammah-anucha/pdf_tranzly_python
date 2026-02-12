from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


WHITE = fitz.pdfcolor["white"]
TEXTFLAGS = fitz.TEXT_DEHYPHENATE


def translate_pdf_bytes(
    pdf_bytes: bytes, source: str, target: str, layer_name: str
) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Optional content group (layer) to hold translated text
    ocg = doc.add_ocg(layer_name, on=True)

    translator = GoogleTranslator(source=source, target=target)

    for page in doc:
        blocks = page.get_text("blocks", flags=TEXTFLAGS)
        for block in blocks:
            bbox = block[:4]
            text = block[4]

            # skip empty/whitespace
            if not text or not isinstance(text, str) or not text.strip():
                continue

            try:
                translated = translator.translate(text)
            except Exception:
                continue

            if (
                not translated
                or not isinstance(translated, str)
                or not translated.strip()
            ):
                continue

            # white-out old text block and insert translated
            page.draw_rect(bbox, color=None, fill=WHITE, oc=ocg)
            page.insert_htmlbox(
                bbox,
                translated,
                css="* {font-family: sans-serif; font-size: 10pt;}",
                oc=ocg,
            )

    doc.subset_fonts()
    out = doc.tobytes(deflate=True)
    doc.close()
    return out


@app.post("/translate")
async def translate_endpoint(
    file: UploadFile = File(...),
    source: str = Form(...),  # e.g. "de"
    target: str = Form(...),  # e.g. "en"
):
    pdf_bytes = await file.read()

    # Build output filename: "name-translated.pdf"
    original = file.filename or "document.pdf"
    if original.lower().endswith(".pdf"):
        base = original[:-4]
    else:
        base = original
    out_name = f"{base}-translated.pdf"

    translated_bytes = translate_pdf_bytes(
        pdf_bytes=pdf_bytes,
        source=source,
        target=target,
        layer_name=target.upper(),
    )

    return Response(
        content=translated_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
