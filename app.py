import re
import time
import threading
import subprocess
from pathlib import Path

import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"


def is_valid_name(name):
    pattern = r"^[A-Za-z\s\-']{1,20}$"
    return re.match(pattern, name)


def slugify_name(name):
    safe = name.strip().lower().replace(" ", "-")
    safe = safe.replace("'", "").replace('"', "")
    return safe


def cleanup_old_files(folder, max_age_seconds=3600):
    now = time.time()
    for file in folder.glob("*"):
        if file.is_file():
            try:
                if now - file.stat().st_mtime > max_age_seconds:
                    file.unlink()
                    print(f"Deleted old file: {file}")
            except Exception as e:
                print(f"Could not delete {file}: {e}")


def delete_file_later(path, delay=10):
    def delete():
        time.sleep(delay)
        try:
            if path.exists():
                path.unlink()
                print(f"Deleted: {path}")
        except Exception as e:
            print(f"Could not delete {path}: {e}")

    threading.Thread(target=delete, daemon=True).start()


def create_preview_image(pdf_path, output_image_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)

    matrix = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    pix.save(str(output_image_path))

    doc.close()


@app.route("/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def home():
    entered_name = ""
    error = ""
    success = ""
    pdf_filename = ""
    preview_filename = ""

    if request.method == "POST":
        cleanup_old_files(GENERATED_DIR)

        entered_name = request.form.get("name", "").strip()

        if not entered_name:
            error = "Please enter a name."
        elif not is_valid_name(entered_name):
            error = "Only letters, spaces, hyphens, apostrophes, max 20 characters."
        else:
            try:
                result = subprocess.run(
                    ["python3", "name_trace.py", entered_name],
                    capture_output=True,
                    text=True,
                    check=True
                )

                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)

                slug = slugify_name(entered_name)
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

    return render_template(
        "index.html",
        entered_name=entered_name,
        error=error,
        success=success,
        pdf_filename=pdf_filename,
        preview_filename=preview_filename
    )


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
    app.run(debug=True)