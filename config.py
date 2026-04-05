from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "generated"
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
FONTS_DIR = ASSETS_DIR / "fonts"
TRACE_FONT_PATH = FONTS_DIR / "Print_Dashed.ttf"

OUTPUT_DIR.mkdir(exist_ok=True)