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


def safe_font_register() -> None:
    global TITLE_FONT_NAME, PROBLEM_FONT_NAME

    try:
        if TITLE_FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont(TITLE_FONT_NAME, str(TITLE_FONT_PATH)))
        else:
            TITLE_FONT_NAME = "Helvetica-Bold"

        if PROBLEM_FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont(PROBLEM_FONT_NAME, str(PROBLEM_FONT_PATH)))
        else:
            PROBLEM_FONT_NAME = "Helvetica"
    except Exception:
        TITLE_FONT_NAME = "Helvetica-Bold"
        PROBLEM_FONT_NAME = "Helvetica"


def slug_part(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def generate_multiplication_problems(count: int, fact_number: str) -> List[Tuple[int, int]]:
    problems = []

    if fact_number == "mixed":
        seen = set()

        while len(problems) < count:
            a = random.randint(0, 12)
            b = random.randint(0, 12)

            if (a, b) not in seen:
                seen.add((a, b))
                problems.append((a, b))

    else:
        fixed = int(fact_number)
        base_facts = [(fixed, b) for b in range(0, 13)]

        while len(problems) < count:
            shuffled = base_facts[:]
            random.shuffle(shuffled)
            problems.extend(shuffled)

        problems = problems[:count]

    return problems


def draw_outer_border(c: canvas.Canvas, image_style: str) -> None:
    margin = 10
    border_width = 2.5

    c.setLineWidth(border_width)

    if image_style == "color":
        c.setStrokeColor(BLUE_ACCENT)
    else:
        c.setStrokeColor(colors.black)

    c.rect(
        margin,
        margin,
        PAGE_WIDTH - 2 * margin,
        PAGE_HEIGHT - 2 * margin,
    )

    c.setStrokeColor(colors.black)


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

    c.setFont(TITLE_FONT_NAME, 28)
    c.setFillColor(colors.black)
    c.drawCentredString(PAGE_WIDTH / 2, top, title)

    c.setFont(TITLE_FONT_NAME, 15)
    if image_style == "color":
        c.setFillColor(BLUE_ACCENT)
    else:
        c.setFillColor(colors.black)

    c.drawCentredString(PAGE_WIDTH / 2, top - 28, subtitle)
    c.setFillColor(colors.black)

    c.setFont("Helvetica", 12)

    name_x = PAGE_WIDTH - 170
    name_y = PAGE_HEIGHT - 35

    c.drawString(name_x, name_y, "Name")
    c.setLineWidth(0.8)
    c.line(name_x + 45, name_y - 2, name_x + 130, name_y - 2)


def draw_horizontal_problem(
    c,
    index: int,
    a: int,
    b: int,
    cell_x: float,
    cell_y: float,
    cell_w: float,
    cell_h: float,
) -> None:
    number_font_size = 13
    equation_font_size = 27

    y = cell_y + (cell_h / 2) - 9

    c.setFillColor(colors.black)

    c.setFont("Helvetica-Bold", number_font_size)
    c.drawRightString(cell_x + 36, y + 3, f"{index}.")

    equation = f"{a} × {b} ="
    c.setFont(PROBLEM_FONT_NAME, equation_font_size)
    c.drawString(cell_x + 82, y, equation)

    box_w = 82
    box_h = 42
    box_x = cell_x + cell_w - box_w - 40
    box_y = cell_y + (cell_h / 2) - (box_h / 2)

    c.setLineWidth(1.4)
    c.rect(box_x, box_y, box_w, box_h)


def draw_vertical_problem(
    c,
    index: int,
    a: int,
    b: int,
    cell_x: float,
    cell_y: float,
    cell_w: float,
    cell_h: float,
) -> None:
    number_font_size = 10
    equation_font_size = 22

    c.setFillColor(colors.black)

    c.setFont("Helvetica-Bold", number_font_size)
    c.drawString(cell_x + 8, cell_y + cell_h - 18, f"{index}.")

    center_x = cell_x + (cell_w / 2)
    top_y = cell_y + cell_h - 34

    c.setFont(PROBLEM_FONT_NAME, equation_font_size)

    c.drawCentredString(center_x + 8, top_y, str(a))
    c.drawString(center_x - 28, top_y - 24, "×")
    c.drawCentredString(center_x + 8, top_y - 24, str(b))

    c.setLineWidth(1.2)
    c.line(center_x - 32, top_y - 34, center_x + 38, top_y - 34)


def draw_problems(c: canvas.Canvas, problems: List[Tuple[int, int]], layout: str = "horizontal") -> None:
    if layout == "vertical":
        cols = 6
        rows = 4
        top_y = PAGE_HEIGHT - 125
        bottom_y = 55
    else:
        cols = 2
        rows = 12
        top_y = PAGE_HEIGHT - 125
        bottom_y = 28

    left_margin = 18
    right_margin = 18

    usable_w = PAGE_WIDTH - left_margin - right_margin
    usable_h = top_y - bottom_y

    col_w = usable_w / cols
    row_h = usable_h / rows

    grid_x = left_margin
    grid_y = bottom_y

    c.setLineWidth(1.15)
    c.setStrokeColor(colors.black)

    c.rect(grid_x, grid_y, usable_w, usable_h)

    for col in range(1, cols):
        x = grid_x + col * col_w
        c.line(x, grid_y, x, grid_y + usable_h)

    for row in range(1, rows):
        y = grid_y + row * row_h
        c.line(grid_x, y, grid_x + usable_w, y)

    for i, (a, b) in enumerate(problems):
        if layout == "vertical":
            row = i // cols
            col = i % cols
        else:
            if i < 12:
                col = 0
                row = i
            else:
                col = 1
                row = i - 12

        display_index = i + 1
        cell_x = grid_x + col * col_w
        cell_y = top_y - (row + 1) * row_h

        if layout == "vertical":
            draw_vertical_problem(c, display_index, a, b, cell_x, cell_y, col_w, row_h)
        else:
            draw_horizontal_problem(c, display_index, a, b, cell_x, cell_y, col_w, row_h)


def draw_footer(c: canvas.Canvas) -> None:
    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_WIDTH - 18, 18, "free4classrooms.com")


def create_pdf(
    output_path: Path,
    problems: List[Tuple[int, int]],
    fact_number: str,
    image_style: str,
    layout: str = "horizontal",
) -> None:
    title = "Multiplication Facts"

    if fact_number == "mixed":
        subtitle = "Solve each multiplication equation below."
    else:
        subtitle = f"Multiply by {fact_number}s."

    c = canvas.Canvas(str(output_path), pagesize=letter)

    draw_header(c, title, subtitle, image_style)
    draw_outer_border(c, image_style)
    draw_problems(c, problems, layout)
    draw_footer(c)

    c.save()


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--fact-number", choices=["mixed"] + [str(i) for i in range(13)], default="mixed")
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--image-style", choices=["bw", "color"], default="bw")
    parser.add_argument("--layout", choices=["horizontal", "vertical"], default="horizontal")
    parser.add_argument("--filename", default="")

    args = parser.parse_args()

    fact_number = args.fact_number
    count = args.count
    image_style = args.image_style
    layout = args.layout

    problems = generate_multiplication_problems(count, fact_number)

    if args.filename:
        filename = args.filename
    else:
        filename = f"multiplication-facts-{slug_part(fact_number)}-{layout}-{image_style}.pdf"

    output_path = GENERATED_DIR / filename

    create_pdf(output_path, problems, fact_number, image_style, layout)

    print(filename)


if __name__ == "__main__":
    safe_font_register()
    main()