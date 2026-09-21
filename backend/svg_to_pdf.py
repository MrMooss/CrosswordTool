import tempfile
from pathlib import Path

from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg


def svg_to_pdf(svg) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        svg_path = Path(tmp) / "crossword.svg"
        pdf_path = Path(tmp) / "crossword.pdf"

        svg_content = str(svg)

        svg_path.write_text(
            svg_content,
            encoding="utf-8",
        )

        drawing = svg2rlg(str(svg_path))

        if drawing is None:
            raise ValueError("Az SVG nem renderelhető.")

        renderPDF.drawToFile(
            drawing,
            str(pdf_path),
        )

        return pdf_path.read_bytes()