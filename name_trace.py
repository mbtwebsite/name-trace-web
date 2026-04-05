import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import OUTPUT_DIR, IMAGES_DIR, TRACE_FONT_PATH
from pdf_templates.base import create_canvas, draw_footer


def register_trace_font():
    font_name = "TraceFont"
    try:
        pdfmetrics.registerFont(TTFont(font_name, str(TRACE_FONT_PATH)))
        return font_name
    except Exception as e:
        print("⚠️ Font load failed, using Helvetica:", e)
        return "Helvetica"


def draw_dashed_page_border(c, x=25, y=25, width=562, height=742):
    c.setLineWidth(3)
    c.setDash(12, 8)
    c.roundRect(x, y, width, height, 10, stroke=1, fill=0)
    c.setDash()


def draw_guidelines(c, left_x, right_x, y_text, font_size):
    c.setLineWidth(1)

    top_y = y_text + font_size * 0.62
    mid_y = y_text + font_size * 0.32
    base_y = y_text

    c.line(left_x, top_y, right_x, top_y)

    c.setDash(4, 3)
    c.line(left_x, mid_y, right_x, mid_y)

    c.setDash()
    c.line(left_x, base_y, right_x, base_y)


def draw_trace_row(c, text, x, y, font_name, font_size, left_limit, right_limit):
    draw_guidelines(c, left_limit, right_limit, y, font_size)
    c.setFont(font_name, font_size)
    c.drawString(x, y, text)


def draw_blank_writing_row(c, left_x, right_x, y_text, guide_font_size):
    draw_guidelines(c, left_x, right_x, y_text, guide_font_size)


def draw_picture_box(c, left_x, bottom_y, width, height):
    c.setLineWidth(1.2)
    c.rect(left_x, bottom_y, width, height, stroke=1, fill=0)

    c.setFont("Helvetica", 16)
    c.drawString(left_x + 12, bottom_y + height - 22, "Draw a picture")


def choose_font_size_for_repeats(name, font_name, usable_width, per_row, gap="   "):
    for size in [72, 68, 64, 60, 56, 52, 48, 44, 40]:
        test_row = gap.join([name] * per_row)
        if pdfmetrics.stringWidth(test_row, font_name, size) <= usable_width:
            return size
    return 36


def choose_repeat_count(name):
    length = len(name.replace(" ", "").replace("-", "").replace("'", ""))

    if length >= 12:
        return 1
    elif length >= 5:
        return 2
    else:
        return 3


def build_trace_rows(name, row_count=3):
    per_row = choose_repeat_count(name)
    return ["   ".join([name] * per_row) for _ in range(row_count)], per_row


def generate_name_trace_pdf(name: str, image_name: str = "Star2_crayon.png") -> Path:
    name = name.strip()
    safe_name = name.lower().replace(" ", "-")
    pdf_path = OUTPUT_DIR / f"name-trace-{safe_name}.pdf"

    c = create_canvas(pdf_path)
    trace_font = register_trace_font()

    # ---------- page frame ----------
    border_x = 25
    border_y = 25
    border_w = 562
    border_h = 742

    draw_dashed_page_border(c, border_x, border_y, border_w, border_h)

    # ---------- header ----------
    title_y = 730
    subtitle_y = 690
    image_x = 470
    image_y = 650
    image_size = 115

    c.setFont("Helvetica-Bold", 30)
    c.drawString(40, title_y, "Name Tracing Practice")

    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, subtitle_y, f"Hi {name}!")

    c.setFont("Helvetica", 18)
    c.drawString(40, subtitle_y - 26, "Trace your name.")

    image_path = IMAGES_DIR / image_name
    if image_path.exists():
        c.drawImage(str(image_path), image_x, image_y, width=image_size, height=image_size, mask="auto")

    # ---------- content settings ----------
    left_x = 55
    right_x = 545
    usable_width = right_x - left_x

    trace_rows, per_row = build_trace_rows(name, row_count=3)
    trace_font_size = choose_font_size_for_repeats(name, trace_font, usable_width, per_row)
    guide_font_size = trace_font_size

    trace_row_count = len(trace_rows)
    blank_row_count = 1

    # ---------- vertical layout zones ----------
    tracing_top_y = 580
    trace_bottom_target_y = 430

    writing_label_y = 390
    blank_top_y = 340
    blank_bottom_target_y = 340

    picture_box_top = 320
    picture_box_bottom = 40

    footer_y = 15

    if trace_row_count > 1:
        trace_row_gap = (tracing_top_y - trace_bottom_target_y) / (trace_row_count - 1)
    else:
        trace_row_gap = 100

    if blank_row_count > 1:
        blank_row_gap = (blank_top_y - blank_bottom_target_y) / (blank_row_count - 1)
    else:
        blank_row_gap = 60

    # ---------- draw tracing rows ----------
    for i, row_text in enumerate(trace_rows):
        y = tracing_top_y - (i * trace_row_gap)
        draw_trace_row(
            c,
            row_text,
            left_x,
            y,
            font_name=trace_font,
            font_size=trace_font_size,
            left_limit=left_x,
            right_limit=right_x
        )

    # ---------- writing directions ----------
    c.setFont("Helvetica", 16)
    c.drawString(40, writing_label_y, "Write your name.")

    # ---------- draw blank writing row ----------
    for i in range(blank_row_count):
        y = blank_top_y - (i * blank_row_gap)
        draw_blank_writing_row(
            c,
            left_x,
            right_x,
            y,
            guide_font_size=guide_font_size
        )

    # ---------- picture box ----------
    picture_box_left = 55
    picture_box_right = 545
    picture_box_width = picture_box_right - picture_box_left
    picture_box_height = picture_box_top - picture_box_bottom

    draw_picture_box(
        c,
        picture_box_left,
        picture_box_bottom,
        picture_box_width,
        picture_box_height
    )

    draw_footer(c, text="Copyright © Free4Classrooms.com", x=215, y=footer_y)

    c.save()
    return pdf_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 name_trace.py Ava")
    else:
        name = sys.argv[1]
        pdf_path = generate_name_trace_pdf(name)
        print(f"Created: {pdf_path}")