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

BLUE_ACCENT = colors.HexColor("#4A90E2")

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
LONG_DIVISION_IMAGE_PATH = BASE_DIR / "static" / "long_division_3digit.png"

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


def generate_division_problems(count: int, fact_number: str) -> List[Tuple[int, int]]:
    problems = []

    if fact_number == "mixed":
        seen = set()

        while len(problems) < count:
            divisor = random.randint(1, 12)
            quotient = random.randint(1, 12)
            dividend = divisor * quotient

            if divisor == 0:
                continue

            problem = (dividend, divisor)

            if problem not in seen:
                seen.add(problem)
                problems.append(problem)

    else:
        divisor = int(fact_number)
        base_facts = [(divisor * quotient, divisor) for quotient in range(1, 13)]

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
            12,
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
    dividend: int,
    divisor: int,
    cell_x: float,
    cell_y: float,
    cell_w: float,
    cell_h: float,
) -> None:
    number_font_size = 14
    equation_font_size = 27

    y = cell_y + (cell_h / 2) - 9

    c.setFillColor(colors.black)

    # Problem number
    c.setFont("Helvetica-Bold", number_font_size)
    c.drawRightString(cell_x + 36, y + 3, f"{index})")

    # 🔥 Fixed column for equals sign
    equals_x = cell_x + cell_w - 120

    # Left side of equation (right-aligned to equals)
    left_text = f"{dividend} ÷ {divisor}"
    c.setFont(PROBLEM_FONT_NAME, equation_font_size)
    c.drawRightString(equals_x - 10, y, left_text)

    # Equals sign (fixed position)
    c.drawString(equals_x, y, "=")

    # Answer box (same position every time)
    box_w = 82
    box_h = 42
    box_x = equals_x + 20
    box_y = cell_y + (cell_h / 2) - (box_h / 2)

    c.setLineWidth(1.4)
    c.rect(box_x, box_y, box_w, box_h)


def draw_long_division_problem(
    c,
    index: int,
    dividend: int,
    divisor: int,
    cell_x: float,
    cell_y: float,
    cell_w: float,
    cell_h: float,
) -> None:
    c.setFillColor(colors.black)

    # Problem number
    c.setFont("Helvetica-Bold", 14)
    c.drawString(cell_x + 12, cell_y + cell_h - 22, f"{index})")

    # Center anchor
    center_x = cell_x + (cell_w / 2)
    center_y = cell_y + (cell_h / 2) + 18

    # Long division PNG size
    symbol_w = 102
    symbol_h = 48

    block_w = 185
    block_x = center_x - (block_w / 2)

    shift_right = 6

    # Base position used by the numbers
    symbol_x = block_x + 62 + shift_right
    symbol_y = center_y - (symbol_h / 2)

    # Move ONLY the PNG left, not the numbers
    symbol_shift_left = 12
    symbol_draw_x = symbol_x - symbol_shift_left

    if LONG_DIVISION_IMAGE_PATH.exists():
        c.drawImage(
            str(LONG_DIVISION_IMAGE_PATH),
            symbol_draw_x,
            symbol_y,
            width=symbol_w,
            height=symbol_h,
            preserveAspectRatio=True,
            mask="auto",
        )

    # Equation numbers
    c.setFont(PROBLEM_FONT_NAME, 34)

    # Outside number
    divisor_x = symbol_x - 6
    divisor_y = symbol_y + 14
    c.drawRightString(divisor_x, divisor_y, str(divisor))

    # Inside number
    dividend_x = symbol_x + 24
    dividend_y = symbol_y + 14
    c.drawString(dividend_x, dividend_y, str(dividend))


def draw_problems(c: canvas.Canvas, problems: List[Tuple[int, int]], layout: str = "horizontal") -> None:
    if layout == "long":
        cols = 3
        rows = 3
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

    for i, (dividend, divisor) in enumerate(problems):
        if layout == "long":
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

        if layout == "long":
            draw_long_division_problem(c, display_index, dividend, divisor, cell_x, cell_y, col_w, row_h)
        else:
            draw_horizontal_problem(c, display_index, dividend, divisor, cell_x, cell_y, col_w, row_h)


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
    title = "Division Facts"

    if layout == "long":
        subtitle = "Solve each long division problem (no remainders)."
    elif fact_number == "mixed":
        subtitle = "Solve each division equation below."
    else:
        subtitle = f"Divide by {fact_number}s."

    c = canvas.Canvas(str(output_path), pagesize=letter)

    draw_header(c, title, subtitle, image_style)
    draw_outer_border(c, image_style)
    draw_problems(c, problems, layout)
    draw_footer(c)

    c.save()


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--fact-number", choices=["mixed"] + [str(i) for i in range(1, 13)], default="mixed")
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--image-style", choices=["bw", "color"], default="bw")
    parser.add_argument("--layout", choices=["horizontal", "long"], default="horizontal")
    parser.add_argument("--filename", default="")

    args = parser.parse_args()

    fact_number = args.fact_number
    image_style = args.image_style
    layout = args.layout

    count = 9 if layout == "long" else args.count

    problems = generate_division_problems(count, fact_number)

    if args.filename:
        filename = args.filename
    else:
        filename = f"division-facts-{slug_part(fact_number)}-{layout}-{image_style}.pdf"

    output_path = GENERATED_DIR / filename

    create_pdf(output_path, problems, fact_number, image_style, layout)

    print(filename)


if __name__ == "__main__":
    safe_font_register()
    main()