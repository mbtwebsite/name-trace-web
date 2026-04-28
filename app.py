import os
import re
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime

import fitz
import requests
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    send_from_directory,
    make_response,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY")
TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "")

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"

NAME_TRACE_TEMPLATE = "name_trace.html"
COLOR_TRACE_TEMPLATE = "color_trace.html"
ADDITION_TEMPLATE = "addition_generator.html"
MULTIPLICATION_TEMPLATE = "multiplication.html"

NAME_TRACE_SCRIPT = "name_trace.py"
COLOR_TRACE_SCRIPT = "color_trace.py"
ADDITION_SCRIPT = "addition_generator.py"
MULTIPLICATION_SCRIPT = "multiplication_generator.py"


def is_valid_text(value: str):
    pattern = r"^[A-Za-z\s\-']{1,20}$"
    return re.match(pattern, value)


def slugify_text(value: str):
    safe = value.strip().lower().replace(" ", "-")
    safe = safe.replace("'", "").replace('"', "")
    return safe


def cleanup_old_files(folder: Path, max_age_seconds: int = 3600):
    now = time.time()
    folder.mkdir(exist_ok=True)

    for file in folder.glob("*"):
        if file.is_file():
            try:
                if now - file.stat().st_mtime > max_age_seconds:
                    file.unlink()
                    print(f"Deleted old file: {file}")
            except Exception as e:
                print(f"Could not delete {file}: {e}")


def delete_file_later(path: Path, delay: int = 10):
    def delete():
        time.sleep(delay)
        try:
            if path.exists():
                path.unlink()
                print(f"Deleted: {path}")
        except Exception as e:
            print(f"Could not delete {path}: {e}")

    threading.Thread(target=delete, daemon=True).start()


def create_preview_image(pdf_path: Path, output_image_path: Path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)

    matrix = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    pix.save(str(output_image_path))

    doc.close()


def verify_turnstile() -> bool:
    if not TURNSTILE_SECRET_KEY:
        return True

    token = request.form.get("cf-turnstile-response")

    if not token:
        return False

    try:
        verify_response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": TURNSTILE_SECRET_KEY,
                "response": token,
            },
            timeout=10,
        )
        result = verify_response.json()
        print("Turnstile result:", result)
        return result.get("success", False)
    except Exception as e:
        print("Turnstile verification error:", e)
        return False


def render_generator_page(template_name: str, generator_script: str):
    entered_name = ""
    error = ""
    success = ""
    pdf_filename = ""
    preview_filename = ""

    if request.method == "POST":
        cleanup_old_files(GENERATED_DIR)

        if not verify_turnstile():
            error = "Security check failed. Please try again."
        else:
            entered_name = request.form.get("name", "").strip()

            if not entered_name:
                error = "Please enter a name or word."
            elif not is_valid_text(entered_name):
                error = "Only letters, spaces, hyphens, apostrophes, max 20 characters."
            else:
                try:
                    result = subprocess.run(
                        ["python3", generator_script, entered_name],
                        cwd=str(BASE_DIR),
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)

                    slug = slugify_text(entered_name)
                    pdf_filename = f"name-trace-{slug}.pdf"
                    preview_filename = f"name-trace-{slug}.png"

                    pdf_path = GENERATED_DIR / pdf_filename
                    preview_path = GENERATED_DIR / preview_filename

                    if pdf_path.exists():
                        create_preview_image(pdf_path, preview_path)
                        success = f'Worksheet generated for "{entered_name}".'
                    else:
                        error = "The script ran, but no PDF was found."
                        pdf_filename = ""
                        preview_filename = ""

                    if not preview_path.exists():
                        preview_filename = ""

                except subprocess.CalledProcessError as e:
                    error = "There was a problem generating the worksheet."
                    print("STDOUT:", e.stdout)
                    print("STDERR:", e.stderr)

                except Exception as e:
                    error = f"Preview generation failed: {e}"
                    print("ERROR:", e)

    response = make_response(
        render_template(
            template_name,
            year=datetime.now().year,
            entered_name=entered_name,
            error=error,
            success=success,
            pdf_filename=pdf_filename,
            preview_filename=preview_filename,
            turnstile_site_key=TURNSTILE_SITE_KEY,
        )
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


def render_addition_generator_page():
    error = ""
    success = ""
    pdf_filename = ""
    preview_filename = ""

    digits = request.form.get("digits", "1") if request.method == "POST" else "1"
    regrouping = request.form.get("regrouping", "mixed") if request.method == "POST" else "mixed"
    count = request.form.get("count", "20") if request.method == "POST" else "20"
    image_style = request.form.get("image_style", "bw") if request.method == "POST" else "bw"

    if request.method == "POST":
        cleanup_old_files(GENERATED_DIR)

        if not verify_turnstile():
            error = "Security check failed. Please try again."
        elif digits not in {"1", "2"}:
            error = "Please choose 1-digit or 2-digit addition."
        elif regrouping not in {"mixed", "no", "yes"}:
            error = "Please choose a valid regrouping option."
        elif count != "20":
            error = "This first version supports 20 problems only."
        elif image_style not in {"bw", "color"}:
            error = "Please choose black and white or color."
        else:
            try:
                if digits == "1":
                    regrouping = "mixed"

                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                pdf_filename = f"addition-{digits}-digit-{regrouping}-{image_style}-{count}-{timestamp}.pdf"
                preview_filename = pdf_filename.replace(".pdf", ".png")

                result = subprocess.run(
                    [
                        "python3",
                        ADDITION_SCRIPT,
                        "--digits",
                        digits,
                        "--regrouping",
                        regrouping,
                        "--count",
                        count,
                        "--image-style",
                        image_style,
                        "--filename",
                        pdf_filename,
                    ],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    check=True,
                )

                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)

                pdf_path = GENERATED_DIR / pdf_filename
                preview_path = GENERATED_DIR / preview_filename

                if pdf_path.exists():
                    create_preview_image(pdf_path, preview_path)
                    success = "Addition worksheet generated."
                else:
                    error = "The script ran, but no PDF was found."
                    pdf_filename = ""
                    preview_filename = ""

                if not preview_path.exists():
                    preview_filename = ""

            except subprocess.CalledProcessError as e:
                error = "There was a problem generating the addition worksheet."
                print("STDOUT:", e.stdout)
                print("STDERR:", e.stderr)

            except Exception as e:
                error = f"Preview generation failed: {e}"
                print("ERROR:", e)

    response = make_response(
        render_template(
            ADDITION_TEMPLATE,
            year=datetime.now().year,
            digits=digits,
            regrouping=regrouping,
            count=count,
            image_style=image_style,
            error=error,
            success=success,
            pdf_filename=pdf_filename,
            preview_filename=preview_filename,
            turnstile_site_key=TURNSTILE_SITE_KEY,
        )
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


def render_multiplication_generator_page():
    error = ""
    success = ""
    pdf_filename = ""
    preview_filename = ""

    fact_number = request.form.get("fact_number", "mixed") if request.method == "POST" else "mixed"
    image_style = request.form.get("image_style", "bw") if request.method == "POST" else "bw"
    layout = request.form.get("layout", "horizontal") if request.method == "POST" else "horizontal"
    count = "24"

    valid_fact_numbers = {"mixed"} | {str(i) for i in range(13)}

    if request.method == "POST":
        cleanup_old_files(GENERATED_DIR)

        if not verify_turnstile():
            error = "Security check failed. Please try again."
        elif fact_number not in valid_fact_numbers:
            error = "Please choose mixed facts or a number from 0 to 12."
        elif image_style not in {"bw", "color"}:
            error = "Please choose black and white or color."
        elif layout not in {"horizontal", "vertical"}:
            error = "Please choose horizontal or vertical layout."
        else:
            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                pdf_filename = f"multiplication-facts-{fact_number}-{layout}-{image_style}-{count}-{timestamp}.pdf"
                preview_filename = pdf_filename.replace(".pdf", ".png")

                result = subprocess.run(
                    [
                        "python3",
                        MULTIPLICATION_SCRIPT,
                        "--fact-number",
                        fact_number,
                        "--count",
                        count,
                        "--image-style",
                        image_style,
                        "--layout",
                        layout,
                        "--filename",
                        pdf_filename,
                    ],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    check=True,
                )

                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)

                pdf_path = GENERATED_DIR / pdf_filename
                preview_path = GENERATED_DIR / preview_filename

                if pdf_path.exists():
                    create_preview_image(pdf_path, preview_path)
                    success = "Multiplication facts worksheet generated."
                else:
                    error = "The script ran, but no PDF was found."
                    pdf_filename = ""
                    preview_filename = ""

                if not preview_path.exists():
                    preview_filename = ""

            except subprocess.CalledProcessError as e:
                error = "There was a problem generating the multiplication worksheet."
                print("STDOUT:", e.stdout)
                print("STDERR:", e.stderr)

            except Exception as e:
                error = f"Preview generation failed: {e}"
                print("ERROR:", e)

    response = make_response(
        render_template(
            MULTIPLICATION_TEMPLATE,
            year=datetime.now().year,
            fact_number=fact_number,
            image_style=image_style,
            layout=layout,
            error=error,
            success=success,
            pdf_filename=pdf_filename,
            preview_filename=preview_filename,
            turnstile_site_key=TURNSTILE_SITE_KEY,
        )
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

DIVISION_TEMPLATE = "division.html"
DIVISION_SCRIPT = "division_generator.py"


def render_division_generator_page():
    error = ""
    success = ""
    pdf_filename = ""
    preview_filename = ""

    fact_number = request.form.get("fact_number", "mixed_100") if request.method == "POST" else "mixed_100"
    image_style = request.form.get("image_style", "bw") if request.method == "POST" else "bw"
    layout = request.form.get("layout", "horizontal") if request.method == "POST" else "horizontal"
    count = "24"

    valid_fact_numbers = {"mixed", "mixed_50", "mixed_100", "mixed_144"} | {str(i) for i in range(2, 13)}

    if request.method == "POST":
        cleanup_old_files(GENERATED_DIR)

        if not verify_turnstile():
            error = "Security check failed. Please try again."
        elif fact_number not in valid_fact_numbers:
            error = "Please choose a valid division option."
        elif image_style not in {"bw", "color"}:
            error = "Please choose black and white or color."
        elif layout not in {"horizontal", "long"}:
            error = "Please choose horizontal or long division layout."
        else:
            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                pdf_filename = f"division-facts-{fact_number}-{layout}-{image_style}-{count}-{timestamp}.pdf"
                preview_filename = pdf_filename.replace(".pdf", ".png")

                result = subprocess.run(
                    [
                        "python3",
                        DIVISION_SCRIPT,
                        "--fact-number",
                        fact_number,
                        "--count",
                        count,
                        "--image-style",
                        image_style,
                        "--layout",
                        layout,
                        "--filename",
                        pdf_filename,
                    ],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    check=True,
                )

                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)

                pdf_path = GENERATED_DIR / pdf_filename
                preview_path = GENERATED_DIR / preview_filename

                if pdf_path.exists():
                    create_preview_image(pdf_path, preview_path)
                    success = "Division facts worksheet generated."
                else:
                    error = "The script ran, but no PDF was found."
                    pdf_filename = ""
                    preview_filename = ""

                if not preview_path.exists():
                    preview_filename = ""

            except subprocess.CalledProcessError as e:
                error = "There was a problem generating the division worksheet."
                print("STDOUT:", e.stdout)
                print("STDERR:", e.stderr)

            except Exception as e:
                error = f"Preview generation failed: {e}"
                print("ERROR:", e)

    response = make_response(
        render_template(
            DIVISION_TEMPLATE,
            year=datetime.now().year,
            fact_number=fact_number,
            image_style=image_style,
            layout=layout,
            error=error,
            success=success,
            pdf_filename=pdf_filename,
            preview_filename=preview_filename,
            turnstile_site_key=TURNSTILE_SITE_KEY,
        )
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@app.route("/division-generator/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def division_generator():
    return render_division_generator_page()

def render_subtraction_generator_page():
    error = ""
    success = ""
    pdf_filename = ""
    preview_filename = ""

    digits = request.form.get("digits", "1") if request.method == "POST" else "1"
    regrouping = request.form.get("regrouping", "mixed") if request.method == "POST" else "mixed"
    image_style = request.form.get("image_style", "bw") if request.method == "POST" else "bw"

    if request.method == "POST":
        cleanup_old_files(GENERATED_DIR)

        if not verify_turnstile():
            error = "Security check failed. Please try again."
        elif digits not in {"1", "2"}:
            error = "Please choose 1-digit or 2-digit subtraction."
        elif regrouping not in {"mixed", "no", "yes"}:
            error = "Please choose a valid regrouping option."
        elif image_style not in {"bw", "color"}:
            error = "Please choose black and white or color."
        else:
            try:
                if digits == "1":
                    regrouping = "mixed"

                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                pdf_filename = f"subtraction-{digits}-digit-{regrouping}-{image_style}-{timestamp}.pdf"
                preview_filename = pdf_filename.replace(".pdf", ".png")

                result = subprocess.run(
                    [
                        "python3",
                        "subtraction_generator.py",
                        "--digits",
                        digits,
                        "--regrouping",
                        regrouping,
                        "--image-style",
                        image_style,
                        "--filename",
                        pdf_filename,
                    ],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    check=True,
                )

                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)

                pdf_path = GENERATED_DIR / pdf_filename
                preview_path = GENERATED_DIR / preview_filename

                if pdf_path.exists():
                    create_preview_image(pdf_path, preview_path)
                    success = "Subtraction worksheet generated."
                else:
                    error = "The script ran, but no PDF was found."
                    pdf_filename = ""
                    preview_filename = ""

                if not preview_path.exists():
                    preview_filename = ""

            except subprocess.CalledProcessError as e:
                error = "There was a problem generating the subtraction worksheet."
                print("STDOUT:", e.stdout)
                print("STDERR:", e.stderr)

            except Exception as e:
                error = f"Preview generation failed: {e}"
                print("ERROR:", e)

    response = make_response(
        render_template(
            "subtraction.html",
            year=datetime.now().year,
            digits=digits,
            regrouping=regrouping,
            image_style=image_style,
            error=error,
            success=success,
            pdf_filename=pdf_filename,
            preview_filename=preview_filename,
            turnstile_site_key=TURNSTILE_SITE_KEY,
        )
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/name-trace/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def name_trace():
    return render_generator_page(NAME_TRACE_TEMPLATE, NAME_TRACE_SCRIPT)


@app.route("/color-trace/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def color_trace():
    return render_generator_page(COLOR_TRACE_TEMPLATE, COLOR_TRACE_SCRIPT)


@app.route("/addition-generator/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def addition_generator():
    return render_addition_generator_page()


@app.route("/multiplication-generator/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def multiplication_generator():
    return render_multiplication_generator_page()


@app.route("/subtraction-generator/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def subtraction_generator():
    return render_subtraction_generator_page()


@app.route("/preview/<path:filename>")
def preview_file(filename):
    return send_from_directory(GENERATED_DIR, filename)


@app.route("/download/<path:filename>")
def download_file(filename):
    file_path = GENERATED_DIR / filename

    if not file_path.exists():
        return "File not found", 404

    response = send_file(file_path, as_attachment=True)
    delete_file_later(file_path, delay=10)
    return response


if __name__ == "__main__":
    GENERATED_DIR.mkdir(exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))