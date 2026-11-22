import docx
import pypdf
from PIL import Image, ImageOps


def extract_pdf_text(uploaded_file) -> str:
    """Extract and concatenate text from all readable pages of a PDF file."""
    reader = pypdf.PdfReader(uploaded_file)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def extract_docx_text(uploaded_file) -> str:
    """Extract non-empty paragraph text from a Word (.docx) document."""
    doc = docx.Document(uploaded_file)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs).strip()


def process_image(uploaded_file) -> Image.Image:
    """Open an image file, normalize EXIF orientation, and return a PIL Image."""
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)
    return image


def parse_uploaded_file(uploaded_file):
    """Parse an uploaded file and return ('text', extracted_text) or ('image', pil_image)."""
    if uploaded_file is None or not getattr(uploaded_file, "name", None):
        raise ValueError("No file was provided. Please upload a valid file.")

    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        text = extract_pdf_text(uploaded_file)
        if not text:
            raise ValueError(
                "No readable text was found in this PDF. Please upload a text-based PDF or an image."
            )
        return "text", text

    if filename.endswith(".docx"):
        text = extract_docx_text(uploaded_file)
        if not text:
            raise ValueError("The uploaded DOCX document is empty.")
        return "text", text

    if filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        image = process_image(uploaded_file)
        return "image", image

    raise ValueError(
        "Unsupported file format. Please upload a PDF, DOCX, JPG, JPEG, PNG, or WEBP file."
    )