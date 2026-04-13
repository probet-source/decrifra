from io import BytesIO

import docx2txt
import pdfplumber

SUPPORTED_TYPES = (".pdf", ".docx", ".txt", ".md")


def extract_text_from_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith(".pdf"):
        return extract_pdf_text(data)
    if name.endswith(".docx"):
        return extract_docx_text(data), None
    if name.endswith(".txt") or name.endswith(".md"):
        return data.decode("utf-8", errors="ignore"), None
    raise ValueError("Formato não suportado. Use PDF, DOCX, TXT ou MD.")



def extract_pdf_text(data: bytes):
    text_parts = []
    with pdfplumber.open(BytesIO(data)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
    text = "\n\n".join(text_parts).strip()
    notice = None
    if not text:
        notice = (
            "Este PDF parece escaneado em imagem. A V4 não traz OCR nativo para manter estabilidade no Streamlit Cloud. "
            "Converta para PDF pesquisável ou cole o texto manualmente."
        )
    return text, notice



def extract_docx_text(data: bytes):
    tmp = BytesIO(data)
    return docx2txt.process(tmp) or ""
