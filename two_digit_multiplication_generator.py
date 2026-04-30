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

# =========================================================
# SETTINGS
# =========================================================
INCLUDE_ANSWER_KEY = True

# =========================================================
# COLORS / PAGE
# =========================================================
BLUE_ACCENT = colors.HexColor("#4A90E2")
PAGE_WIDTH, PAGE_HEIGHT = letter

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
IMAGES_DIR = ASSETS_DIR / "images"

TITLE_FONT_PATH = FONTS_DIR / "KGRedHands.ttf"
#PROBLEM_FONT_PATH = FONTS_DIR / "KGNeatlyPrintedSpaced.ttf"
PROBLEM_FONT_PATH = FONTS_DIR / "KGPrimaryPenmanship.ttf"

COLOR_IMAGE_PATH = IMAGES_DIR / "Math_Stars_Color.png"
BW_IMAGE_PATH = IMAGES_DIR / "Math_Stars_BW.png"

ANSWER_FONT_PATH = FONTS_DIR / "KGPrimaryPenmanship.ttf"
ANSWER_FONT_NAME = "KGPrimary"

TITLE_FONT_NAME = "KGRedHands"
#PROBLEM_FONT_NAME = "KGNeatlyPrintedSpaced"
PROBLEM_FONT_NAME = "KGPrimary"




# =========================================================
# FONT HELPERS
# =========================================================
def safe_font_register() -> None:
    global TITLE_FONT_NAME, PROBLEM_FONT_NAME, ANSWER_FONT_NAME

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

    try:
        if ANSWER_FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont(ANSWER_FONT_NAME, str(ANSWER_FONT_PATH)))
        else:
            ANSWER_FONT_NAME = "Helvetica-Bold"
    except Exception:
        ANSWER_FONT_NAME = "Helvetica-Bold"


def slug_part(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# =========================================================
# PROBLEM GENERATION
# =========================================================
def is_no_regrouping_problem(a: int, b: int) -> bool:
    a_ones = a % 10
    a_tens = a // 10
    b_ones = b % 10
    b_tens = b // 10

    return (
        a_ones * b_ones < 10
        and a_tens * b_ones < 10
        and a_ones * b_tens < 10
        and a_tens * b_tens < 10
    )


def generate_two_digit_multiplication_problems(
    count: int,
    problem_type: str = "mixed",
) -> List[Tuple[int, int]]:

    problems: List[Tuple[int, int]] = []
    seen = set()

    attempts = 0
    max_attempts = count * 5000

    while len(problems) < count and attempts < max_attempts:
        attempts += 1

        a = random.randint(10, 99)
        b = random.randint(10, 99)

        if (a, b) in seen:
            continue

        no_regroup = is_no_regrouping_problem(a, b)

        if problem_type == "no-regrouping" and not no_regroup:
            continue

        if problem_type == "with-regrouping" and no_regroup:
            continue

        seen.add((a, b))
        problems.append((a, b))

    if len(problems) < count:
        raise ValueError(
            f"Could only generate {len(problems)} problems for type={problem_type}."
        )

    return problems


# =========================================================
# DRAW HELPERS
# =========================================================
def draw_outer_border(c: canvas.Canvas, image_style: str) -> None:
    margin = 10
    border_width = 2.5

    c.setLineWidth(border_width)
    c.setStrokeColor(BLUE_ACCENT if image_style == "color" else colors.black)
    c.rect(margin, margin, PAGE_WIDTH - 2 * margin, PAGE_HEIGHT - 2 * margin)
    c.setStrokeColor(colors.black)


def draw_header(
    c: canvas.Canvas,
    title: str,
    subtitle: str,
    image_style: str,
    subtitle_color=None,
) -> None:
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

    c.setFont(TITLE_FONT_NAME, 26)
    c.setFillColor(colors.black)
    c.drawCentredString(PAGE_WIDTH / 2, top, title)

    # Subtitle: keep "Solve each problem." black,
    # make only "Answer key." or "Worked solutions." red.
    c.setFont(TITLE_FONT_NAME, 14)

    if "Answer key." in subtitle:
        main_text = subtitle.replace(" Answer key.", "")
        label_text = "Answer key."
    elif "Worked solutions." in subtitle:
        main_text = subtitle.replace(" Worked solutions.", "")
        label_text = "Worked solutions."
    else:
        main_text = subtitle
        label_text = ""

    y = top - 28

    if label_text:
        space = " "
        main_width = c.stringWidth(main_text + space, TITLE_FONT_NAME, 14)
        label_width = c.stringWidth(label_text, TITLE_FONT_NAME, 14)
        start_x = (PAGE_WIDTH / 2) - ((main_width + label_width) / 2)

        c.setFillColor(colors.black)
        c.drawString(start_x, y, main_text + space)

        c.setFillColor(colors.red)
        c.drawString(start_x + main_width, y, label_text)
    else:
        c.setFillColor(BLUE_ACCENT if image_style == "color" else colors.black)
        c.drawCentredString(PAGE_WIDTH / 2, y, subtitle)

    c.setFillColor(colors.black)

    c.setFont("Helvetica", 12)
    name_x = PAGE_WIDTH - 170
    name_y = PAGE_HEIGHT - 35
    c.drawString(name_x, name_y, "Name")
    c.setLineWidth(0.8)
    c.line(name_x + 45, name_y - 2, name_x + 130, name_y - 2)


def draw_two_digit_vertical_problem(
    c: canvas.Canvas,
    index: int,
    a: int,
    b: int,
    cell_x: float,
    cell_y: float,
    cell_w: float,
    cell_h: float,
) -> None:
    number_font_size = 10
    equation_font_size = 20

    c.setFillColor(colors.black)

    c.setFont("Helvetica-Bold", number_font_size)
    c.drawString(cell_x + 8, cell_y + cell_h - 18, f"{index}.")

    center_x = cell_x + (cell_w / 2)
    top_y = cell_y + cell_h - 40

    c.setFont(PROBLEM_FONT_NAME, equation_font_size)

    digit_gap = 14
    ones_x = center_x + 12
    tens_x = ones_x - digit_gap

    symbol_x = tens_x - 18

    a_tens, a_ones = divmod(a, 10)
    b_tens, b_ones = divmod(b, 10)

    c.drawCentredString(tens_x, top_y, str(a_tens))
    c.drawCentredString(ones_x, top_y, str(a_ones))

    c.drawString(symbol_x, top_y - 20, "×")
    c.drawCentredString(tens_x, top_y - 20, str(b_tens))
    c.drawCentredString(ones_x, top_y - 20, str(b_ones))

    c.setLineWidth(1.2)
    c.line(tens_x - 18, top_y - 26, ones_x + 18, top_y - 26)


def draw_problems(
    c: canvas.Canvas,
    problems: List[Tuple[int, int]],
    layout: str = "vertical-3x4",
) -> None:
    if layout != "vertical-3x4":
        raise ValueError("Only vertical-3x4 layout is supported.")

    cols = 3
    rows = 4

    top_y = PAGE_HEIGHT - 125
    bottom_y = 55
    left_margin = 22
    right_margin = 22

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

    for i, (a, b) in enumerate(problems[: cols * rows]):
        row = i // cols
        col = i % cols

        cell_x = grid_x + col * col_w
        cell_y = top_y - (row + 1) * row_h

        draw_two_digit_vertical_problem(
            c=c,
            index=i + 1,
            a=a,
            b=b,
            cell_x=cell_x,
            cell_y=cell_y,
            cell_w=col_w,
            cell_h=row_h,
        )


def draw_answer_key_page(
    c: canvas.Canvas,
    problems: List[Tuple[int, int]],
    problem_type: str,
    image_style: str,
    layout: str = "vertical-3x4",
) -> None:
    c.showPage()

    title, subtitle = build_title_and_subtitle(problem_type)
    answer_subtitle = subtitle + " Answer key."

    draw_header(c, title, answer_subtitle, image_style, subtitle_color=colors.red)
    draw_outer_border(c, image_style)
    draw_problems(c, problems, layout)

    cols = 3
    rows = 4

    top_y = PAGE_HEIGHT - 125
    left_margin = 22
    right_margin = 22

    usable_w = PAGE_WIDTH - left_margin - right_margin
    col_w = usable_w / cols
    row_h = (top_y - 55) / rows

    grid_x = left_margin

    for i, (a, b) in enumerate(problems[: cols * rows]):
        row = i // cols
        col = i % cols

        cell_x = grid_x + col * col_w
        cell_y = top_y - (row + 1) * row_h

        center_x = cell_x + (col_w / 2)
        problem_top_y = cell_y + row_h - 40

        # SAME column alignment as problem
        digit_gap = 14
        ones_x = center_x + 12
        tens_x = ones_x - digit_gap

        # -----------------------------
        # ✅ NEW ANSWER DRAWING (REPLACED)
        # -----------------------------
        answer = a * b

        c.setFont(ANSWER_FONT_NAME, 20)
        c.setFillColor(colors.red)

        answer_y = problem_top_y - 50

        digits = list(str(answer))

        digit_spacing = 14
        right_x = ones_x

        for j, digit in enumerate(reversed(digits)):
            x = right_x - j * digit_spacing

            # bold effect
            for offset in [0, 0.35]:
                c.drawCentredString(x + offset, answer_y, digit)

        c.setFillColor(colors.black)

    draw_footer(c)

def draw_worked_answer_key_page(
    c: canvas.Canvas,
    problems: List[Tuple[int, int]],
    problem_type: str,
    image_style: str,
    layout: str = "vertical-3x4",
) -> None:
    c.showPage()

    title, subtitle = build_title_and_subtitle(problem_type)
    subtitle = subtitle + " Worked solutions."

    draw_header(c, title, subtitle, image_style, subtitle_color=colors.red)
    draw_outer_border(c, image_style)
    draw_problems(c, problems, layout)

    cols = 3
    rows = 4

    top_y = PAGE_HEIGHT - 125
    left_margin = 22
    right_margin = 22

    usable_w = PAGE_WIDTH - left_margin - right_margin
    col_w = usable_w / cols
    row_h = (top_y - 55) / rows

    grid_x = left_margin

    for i, (a, b) in enumerate(problems[: cols * rows]):
        row = i // cols
        col = i % cols

        cell_x = grid_x + col * col_w
        cell_y = top_y - (row + 1) * row_h

        center_x = cell_x + (col_w / 2)
        problem_top_y = cell_y + row_h - 40

        digit_spacing = 14
        ones_x = center_x + 12
        tens_x = ones_x - digit_spacing

        a_tens, a_ones = divmod(a, 10)
        b_tens, b_ones = divmod(b, 10)

        # Helper to draw bold red digits
        def draw_bold_digit(x: float, y: float, digit: str, size: int = 16) -> None:
            c.setFont(ANSWER_FONT_NAME, size)
            c.setFillColor(colors.red)
            for offset in [0, 0.3]:
                c.drawCentredString(x + offset, y, digit)

        # Helper: draw carry numbers ABOVE the original black top number
        def draw_carries_above_top_number(multiplier_digit: int, y: float) -> None:
            carry = 0
            a_digits_reversed = list(reversed(str(a)))

            for j, digit in enumerate(a_digits_reversed):
                val = int(digit) * multiplier_digit + carry
                new_carry = val // 10

                # Put carry above the next column to the left
                if new_carry > 0 and j < len(a_digits_reversed) - 1:
                    carry_x = ones_x - ((j + 1) * digit_spacing)
                    draw_bold_digit(carry_x, y, str(new_carry), size=10)

                carry = new_carry

        # Carry row positions above the black top number
        # Ones multiplier carry is closer to the top number.
        # Tens multiplier carry is slightly higher so both can show if needed.
        carry_y_ones = problem_top_y + 18
        carry_y_tens = problem_top_y + 30

        draw_carries_above_top_number(b_ones, carry_y_ones)
        draw_carries_above_top_number(b_tens, carry_y_tens)

        # ======================
        # Partial product rows
        # ======================
        y1 = problem_top_y - 48
        y2 = y1 - 20

        ones_partial = a * b_ones
        tens_partial = a * b_tens

        # Ones partial product
        for j, digit in enumerate(reversed(str(ones_partial))):
            x = ones_x - j * digit_spacing
            draw_bold_digit(x, y1, digit, size=16)

        # Tens partial product, shifted left one place
        for j, digit in enumerate(reversed(str(tens_partial))):
            x = (ones_x - digit_spacing) - j * digit_spacing
            draw_bold_digit(x, y2, digit, size=16)

        # Line under partial products
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(tens_x - 32, y2 - 6, ones_x + 18, y2 - 6)

        # Final answer
        y3 = y2 - 22
        final = a * b

        for j, digit in enumerate(reversed(str(final))):
            x = ones_x - j * digit_spacing
            draw_bold_digit(x, y3, digit, size=16)

        c.setFillColor(colors.black)

    draw_footer(c)

def draw_footer(c: canvas.Canvas) -> None:
    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_WIDTH - 18, 18, "free4classrooms.com - Free Printable Worksheets")


def build_title_and_subtitle(problem_type: str) -> Tuple[str, str]:
    title = "2-Digit Multiplication"

    if problem_type == "no-regrouping":
        subtitle = "Solve each problem. No regrouping."
    elif problem_type == "with-regrouping":
        subtitle = "Solve each problem. Regrouping practice."
    else:
        subtitle = "Solve each problem."

    return title, subtitle


def create_pdf(
    output_path: Path,
    problems: List[Tuple[int, int]],
    problem_type: str,
    image_style: str = "bw",
    layout: str = "vertical-3x4",
) -> None:
    title, subtitle = build_title_and_subtitle(problem_type)

    c = canvas.Canvas(str(output_path), pagesize=letter)

    draw_header(c, title, subtitle, image_style)
    draw_outer_border(c, image_style)
    draw_problems(c, problems, layout)
    draw_footer(c)

    if INCLUDE_ANSWER_KEY:
        draw_answer_key_page(c, problems, problem_type, image_style, layout)

    if problem_type in ["with-regrouping", "mixed"]:
        draw_worked_answer_key_page(c, problems, problem_type, image_style, layout)

    c.save()


# =========================================================
# CLI
# =========================================================
def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--problem-type",
        choices=["no-regrouping", "with-regrouping", "mixed"],
        default="mixed",
    )
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--image-style", choices=["bw", "color"], default="bw")
    parser.add_argument("--layout", choices=["vertical-3x4"], default="vertical-3x4")
    parser.add_argument("--filename", default="")

    args = parser.parse_args()

    problems = generate_two_digit_multiplication_problems(
        count=args.count,
        problem_type=args.problem_type,
    )

    if args.filename:
        filename = args.filename
    else:
        filename = f"2-digit-by-2-digit-multiplication-{slug_part(args.problem_type)}-{args.image_style}.pdf"

    output_path = GENERATED_DIR / filename

    create_pdf(
        output_path=output_path,
        problems=problems,
        problem_type=args.problem_type,
        image_style=args.image_style,
        layout=args.layout,
    )

    print(filename)


if __name__ == "__main__":
    safe_font_register()
    main()
