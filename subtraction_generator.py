import argparse
import random
import re
from pathlib import Path
from typing import List, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ========= COLORS =========
BLUE_ACCENT = colors.HexColor("#4A90E2")

# ========= PAGE =========
PAGE_WIDTH, PAGE_HEIGHT = letter

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
IMAGES_DIR = ASSETS_DIR / "images"

TITLE_FONT_PATH = FONTS_DIR / "KGRedHands.ttf"
PROBLEM_FONT_PATH = FONTS_DIR / "KGNeatlyPrintedSpaced.ttf"

COLOR_IMAGE_PATH = IMAGES_DIR / "Math_Stars_Color.png"
BW_IMAGE_PATH = IMAGES_DIR / "Math_Stars_BW.png"

TITLE_FONT_NAME = "KGRedHands"
PROBLEM_FONT_NAME = "KGNeatlyPrintedSpaced"


# ========= FONT SETUP =========
def safe_font_register() -> None:
    try:
        if TITLE_FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont(TITLE_FONT_NAME, str(TITLE_FONT_PATH)))
        else:
            globals()["TITLE_FONT_NAME"] = "Helvetica-Bold"

        if PROBLEM_FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont(PROBLEM_FONT_NAME, str(PROBLEM_FONT_PATH)))
        else:
            globals()["PROBLEM_FONT_NAME"] = "Helvetica"
    except Exception:
        globals()["TITLE_FONT_NAME"] = "Helvetica-Bold"
        globals()["PROBLEM_FONT_NAME"] = "Helvetica"


# ========= HELPERS =========
def slug_part(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# ========= PROBLEM GENERATION =========
def generate_subtraction_problems(count: int, digits: int, regrouping: str) -> List[Tuple[int, int]]:
    problems = []
    seen = set()

    while len(problems) < count:
        if digits == 1:
            a = random.randint(0, 9)
            b = random.randint(0, 9)

            if b > a:
                a, b = b, a

        else:
            a = random.randint(10, 99)
            b = random.randint(10, 99)

            if b > a:
                a, b = b, a

            a_ones = a % 10
            b_ones = b % 10
            needs_regrouping = b_ones > a_ones

            if regrouping == "no" and needs_regrouping:
                continue

            if regrouping == "yes" and not needs_regrouping:
                continue

        if (a, b) not in seen:
            seen.add((a, b))
            problems.append((a, b))

    return problems


# ========= BORDER =========
def draw_outer_border(c: canvas.Canvas, image_style: str) -> None:
    margin = 10
    border_width = 2.5
    corner_radius = 12

    c.setLineWidth(border_width)

    if image_style == "color":
        c.setStrokeColor(BLUE_ACCENT)
    else:
        c.setStrokeColor(colors.black)

    c.roundRect(
        margin,
        margin,
        PAGE_WIDTH - 2 * margin,
        PAGE_HEIGHT - 2 * margin,
        corner_radius,
    )

    c.setStrokeColor(colors.black)


# ========= HEADER =========
def draw_header(c: canvas.Canvas, title: str, subtitle: str, image_style: str) -> None:
    top = PAGE_HEIGHT - 55

    img_path = COLOR_IMAGE_PATH if image_style == "color" else BW_IMAGE_PATH
    if img_path.exists():
        c.drawImage(
            str(img_path),
            32,
            PAGE_HEIGHT - 115,
            width=100,
            height=100,
            preserveAspectRatio=True,
            mask="auto",
        )

    c.setFont(TITLE_FONT_NAME, 30)
    c.setFillColor(colors.black)
    c.drawCentredString(PAGE_WIDTH / 2, top, title)

    c.setFont(TITLE_FONT_NAME, 15)

    if image_style == "color":
        c.setFillColor(BLUE_ACCENT)
    else:
        c.setFillColor(colors.black)

    c.drawCentredString(PAGE_WIDTH / 2, top - 28, subtitle)

    c.setFillColor(colors.black)

    c.setFont(TITLE_FONT_NAME, 14)

    margin = 18
    name_x = PAGE_WIDTH - 180
    name_y = PAGE_HEIGHT - margin - 20

    c.drawString(name_x, name_y, "Name")
    c.setLineWidth(0.8)
    c.line(name_x + 50, name_y - 1, name_x + 140, name_y - 1)


# ========= PROBLEM DRAWING =========
def draw_vertical_problem(c, a, b, x, y, digits, font_size):
    c.setFont(PROBLEM_FONT_NAME, font_size)

    vertical_gap = 18
    answer_line_gap = 22

    if digits == 1:
        center_x = x + 42
        minus_x = x + 22

        c.drawCentredString(center_x, y, str(a))
        c.drawString(minus_x, y - vertical_gap, "-")
        c.drawCentredString(center_x, y - vertical_gap, str(b))

        c.setLineWidth(0.8)
        c.line(center_x - 12, y - answer_line_gap, center_x + 12, y - answer_line_gap)

    else:
        ones_x = x + 55
        tens_x = ones_x - 12
        minus_x = x + 20

        def draw_number(num, y_pos):
            s = str(num)
            if len(s) == 2:
                c.drawCentredString(tens_x, y_pos, s[0])
                c.drawCentredString(ones_x, y_pos, s[1])
            else:
                c.drawCentredString(ones_x, y_pos, s)

        draw_number(a, y)

        c.drawString(minus_x, y - vertical_gap, "-")
        draw_number(b, y - vertical_gap)

        c.setLineWidth(0.8)
        c.line(x + 30, y - answer_line_gap, x + 64, y - answer_line_gap)


# ========= GRID =========
def draw_problems(c, problems, digits):
    cols = 4
    rows = 5

    font_size = 24 if digits == 1 else 23

    left_margin = 58
    right_margin = 58

    top_y = PAGE_HEIGHT - 185
    bottom_y = 90

    usable_w = PAGE_WIDTH - left_margin - right_margin
    usable_h = top_y - bottom_y

    col_w = usable_w / cols
    row_h = usable_h / rows

    for i, (a, b) in enumerate(problems):
        row = i // cols
        col = i % cols

        x = left_margin + col * col_w + 24
        y = top_y - row * row_h

        draw_vertical_problem(c, a, b, x, y, digits, font_size)


# ========= FOOTER =========
def draw_footer(c):
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_WIDTH / 2, 36, "© Free4Classrooms.com • Free Printable Worksheets")


# ========= PDF =========
def create_pdf(output_path, problems, digits, regrouping, image_style):
    title = "Subtraction"

    if digits == 1:
        subtitle = "1-Digit Subtraction Practice"
    else:
        if regrouping == "no":
            subtitle = "2-Digit Subtraction No Regrouping"
        elif regrouping == "yes":
            subtitle = "2-Digit Subtraction with Regrouping"
        else:
            subtitle = "2-Digit Subtraction Mixed Practice"

    c = canvas.Canvas(str(output_path), pagesize=letter)

    draw_header(c, title, subtitle, image_style)
    draw_outer_border(c, image_style)
    draw_problems(c, problems, digits)
    draw_footer(c)

    c.save()


# ========= MAIN =========
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--digits", choices=["1", "2"], default="1")
    parser.add_argument("--regrouping", choices=["no", "yes", "mixed"], default="mixed")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--image-style", choices=["bw", "color"], default="bw")
    parser.add_argument("--filename", default="")

    args = parser.parse_args()

    digits = int(args.digits)
    count = args.count
    image_style = args.image_style

    if digits == 1:
        regrouping = "mixed"
    else:
        regrouping = args.regrouping

    problems = generate_subtraction_problems(count, digits, regrouping)

    if args.filename:
        filename = args.filename
    else:
        filename = f"subtraction-{digits}-digit-{slug_part(regrouping)}-{image_style}.pdf"

    output_path = GENERATED_DIR / filename

    create_pdf(output_path, problems, digits, regrouping, image_style)

    print(filename)


if __name__ == "__main__":
    safe_font_register()
    main()