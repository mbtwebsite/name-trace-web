from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_canvas(pdf_path):
    return canvas.Canvas(str(pdf_path), pagesize=letter)


def draw_name_line(c, x=72, y=740, width=220):
    c.setFont("Helvetica", 14)
    c.drawString(x, y, "Name")
    c.line(x + 42, y - 2, x + width, y - 2)


def draw_centered_title(c, title, page_width=612, y=690):
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(page_width / 2, y, title)


def draw_instruction(c, text, page_width=612, y=665):
    c.setFont("Helvetica", 14)
    c.drawCentredString(page_width / 2, y, text)


def draw_footer(c, text="Copyright © Free4Classrooms.com", x=72, y=40):
    c.setFont("Helvetica", 10)
    c.drawString(x, y, text)