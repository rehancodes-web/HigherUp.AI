"""Small, bounded text extraction helpers for candidate PDF documents."""

from io import BytesIO
import re

from pypdf import PdfReader


MAX_PDF_PAGES = 50
MAX_EXTRACTED_CHARACTERS = 100_000


class PDFTextExtractionError(ValueError):
    """Raised when a PDF cannot be converted to selectable text."""


def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, int]:
    """Return selectable text and page count from PDF bytes.

    This does not perform OCR. Scanned/image-only PDFs need an OCR step.
    """
    if not pdf_bytes:
        raise PDFTextExtractionError("The PDF is empty.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=False)
        if reader.is_encrypted:
            raise PDFTextExtractionError("Password-protected PDFs are not supported.")
        page_count = len(reader.pages)
        if page_count > MAX_PDF_PAGES:
            raise PDFTextExtractionError(
                f"PDF has too many pages; the limit is {MAX_PDF_PAGES}."
            )
        page_text = [(page.extract_text() or "").strip() for page in reader.pages]
    except PDFTextExtractionError:
        raise
    except Exception as exc:
        raise PDFTextExtractionError("Could not read this PDF.") from exc

    text = "\n\n".join(part for part in page_text if part)
    text = re.sub(r"[ \t]+\n", "\n", text).replace("\x00", "").strip()
    if not text:
        raise PDFTextExtractionError(
            "No selectable text was found. This may be a scanned PDF and needs OCR."
        )
    if len(text) > MAX_EXTRACTED_CHARACTERS:
        raise PDFTextExtractionError(
            f"Extracted text is too long; the limit is {MAX_EXTRACTED_CHARACTERS} characters."
        )

    return text, page_count
