"""Genera el informe PDF del caso a partir del markdown curado.

Uso:
    python make_pdf.py

Requiere: markdown y weasyprint (o cae a reportlab). El PDF se escribe en
assets/informe_caso_rca.pdf y es autocontenido (imágenes embebidas).
"""
from __future__ import annotations

import base64
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "caso_residencial_veredas_plaza.md"
OUT = ROOT / "assets" / "informe_caso_rca.pdf"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; color: #1a2233;
       font-size: 10.5pt; line-height: 1.5; }
h1 { font-size: 20pt; color: #0b3a66; margin: 0 0 4px 0; }
h2 { font-size: 13pt; color: #0b6b6b; border-bottom: 2px solid #0b6b6b;
     padding-bottom: 3px; margin-top: 20px; }
h3 { font-size: 11pt; color: #0b3a66; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9.5pt; }
th, td { border: 1px solid #b9c4d4; padding: 5px 7px; text-align: left;
         vertical-align: top; }
th { background: #0b3a66; color: #fff; }
tr:nth-child(even) td { background: #f2f6fb; }
code { background: #eef2f7; padding: 1px 4px; border-radius: 3px;
       font-family: 'DejaVu Sans Mono', monospace; font-size: 9pt; }
blockquote { border-left: 3px solid #0b6b6b; margin: 8px 0; padding: 2px 10px;
             color: #445; background: #f7fafc; }
img { max-width: 100%; border: 1px solid #b9c4d4; border-radius: 4px; }
hr { border: none; border-top: 1px solid #ccd6e3; margin: 16px 0; }
"""


def _embed_images(html: str) -> str:
    """Reemplaza rutas locales de <img src> por data URI base64."""
    import re

    def repl(match: "re.Match[str]") -> str:
        src = match.group(1)
        path = ROOT / src
        if not path.exists():
            return match.group(0)
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return match.group(0).replace(src, f"data:{mime};base64,{data}")

    return re.sub(r'src="([^"]+)"', repl, html)


def build_html() -> str:
    text = SRC.read_text(encoding="utf-8")
    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"]
    )
    body = _embed_images(body)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = build_html()
    try:
        from weasyprint import HTML

        HTML(string=html, base_url=str(ROOT)).write_pdf(str(OUT))
    except Exception as exc:  # noqa: BLE001
        print(f"[..] weasyprint no disponible ({exc}); uso wkhtmltopdf")
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
            fh.write(html)
            tmp = fh.name
        subprocess.run(["wkhtmltopdf", "--quiet", tmp, str(OUT)], check=True)
    print(f"[ok] {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
