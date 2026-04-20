import sys
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import OUTPUT_DIR, FONTS_DIR
from pdf_templates.base import create_canvas


def register_font(font_name: str, font_path: Path, fallback: str = "Helvetica"):
    try:
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
        return font_name
    except Exception as e:
        print(f"⚠️ Font load failed for {font_name}, using {fallback}: {e}")
        return fallback


def register_fonts():
    heading_font = register_font(
        "HeadingFont",
        FONTS_DIR / "KGNeatlyPrintedSpaced.ttf"
    )

    directional_font = register_font(
        "DirectionalFont",
        FONTS_DIR / "KTDLFormFun-M.ttf"
    )

    dotted_font = register_font(
        "DottedFont",
        FONTS_DIR / "KTDLFFunDOTTED-M.ttf"
    )

    outline_font = register_font(
        "OutlineFont",
        FONTS_DIR / "KTDLFFunOUTLINE-M.ttf"
    )

    return {
        "heading": heading_font,
        "directional": directional_font,
        "dotted": dotted_font,
        "outline": outline_font,
    }


def safe_slug(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace(" ", "-")
        .replace("'", "")
        .replace('"', "")
    )


def text_width(text: str, font_name: str, font_size: float) -> float:
    return pdfmetrics.stringWidth(text, font_name, font_size)


def fit_font_size(text: str, font_name: str, max_width: float, sizes):
    for size in sizes:
        if text_width(text, font_name, size) <= max_width:
            return size
    return sizes[-1]


def draw_page_frame(c):
    c.setLineWidth(3)
    c.rect(2, 2, 608, 788, stroke=1, fill=0)

    c.line(2, 528, 610, 528)
    c.line(2, 264, 610, 264)


def draw_heading(c, text, x, y, font_name, size=24):
    c.setFont(font_name, size)
    c.drawString(x, y, text)


def draw_centered_word(c, text, font_name, font_size, center_x, baseline_y):
    width = text_width(text, font_name, font_size)
    x = center_x - (width / 2)
    c.setFont(font_name, font_size)
    c.drawString(x, baseline_y, text)


def draw_footer(c, text, font_name):
    font_size = 22
    y = 18
    right_margin_x = 575
    width = text_width(text, font_name, font_size)
    x = right_margin_x - width
    c.setFont(font_name, font_size)
    c.drawString(x, y, text)


def generate_name_trace_pdf(name: str) -> Path:
    name = name.strip()
    slug = safe_slug(name)
    pdf_path = OUTPUT_DIR / f"name-trace-{slug}.pdf"

    fonts = register_fonts()
    c = create_canvas(pdf_path)

    page_width = 612
    center_x = page_width / 2
    max_word_width = 500

    draw_page_frame(c)

    # Section labels
    draw_heading(c, "Write.", 28, 750, fonts["heading"], 24)
    draw_heading(c, "Trace it.", 28, 486, fonts["heading"], 24)
    draw_heading(c, "Color it.", 40, 235, fonts["heading"], 24)

    # Top section: directional/stroke-order font
    top_size = fit_font_size(
        name,
        fonts["directional"],
        max_word_width,
        [136, 128, 120, 112, 104, 96, 88, 80, 72]
    )
    draw_centered_word(c, name, fonts["directional"], top_size, center_x, 600)

    # Middle section: dotted trace font
    middle_size = fit_font_size(
        name,
        fonts["dotted"],
        max_word_width,
        [114, 106, 98, 90, 82, 74, 66, 58]
    )
    draw_centered_word(c, name, fonts["dotted"], middle_size, center_x, 350)

    # Bottom section: outline coloring font
    bottom_size = fit_font_size(
        name,
        fonts["outline"],
        max_word_width,
        [136, 128, 120, 112, 104, 96, 88, 80, 72]
    )
    draw_centered_word(c, name, fonts["outline"], bottom_size, center_x, 95)

    draw_footer(c, "Free4Classrooms.com", fonts["heading"])

    c.save()
    return pdf_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 name_trace.py Ava")
    else:
        entered_name = sys.argv[1]
        pdf_path = generate_name_trace_pdf(entered_name)
        print(f"Created: {pdf_path}")