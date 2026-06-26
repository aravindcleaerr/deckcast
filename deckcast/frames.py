"""Render each slide to a 1920x1080 PNG frame.

  builtin : fill the bundled HTML template (image + title + subtitle + bullets) and
            screenshot it — works with NO external deck, in any project.
  deck    : screenshot an existing HTML deck that supports `?clean#N` navigation
            (like the KuboHomes deck), one frame per slide.
"""
import html as _html
from pathlib import Path
from .util import screenshot

TEMPLATE = (Path(__file__).parent / "templates" / "slide.html").read_text()

LIGHT_OVERLAY = ("linear-gradient(100deg, rgba(251,248,242,.97) 0%, rgba(251,248,242,.9) 38%, "
                 "rgba(251,248,242,.62) 70%, rgba(251,248,242,.3) 100%)")
DARK_OVERLAY = ("linear-gradient(100deg, rgba(18,40,35,.93) 0%, rgba(18,40,35,.82) 44%, "
                "rgba(18,40,35,.58) 100%)")


def _esc(s):
    return _html.escape(str(s or ""))


def builtin_frame(slide, idx, total, theme, image_path, dest, size):
    title = slide.get("title", "")
    titlesize = "118px" if len(title) < 28 else ("92px" if len(title) < 50 else "72px")
    dark = bool(slide.get("dark"))
    overlay = DARK_OVERLAY if dark else LIGHT_OVERLAY
    img_css = f", url('file://{Path(image_path).resolve()}')" if image_path and Path(image_path).exists() else ""

    sub = f'<p class="sub" style="{"color:rgba(255,255,255,.85)" if dark else ""}">{_esc(slide["subtitle"])}</p>' \
        if slide.get("subtitle") else ""
    bullets = ""
    if slide.get("bullets"):
        items = "".join(f"<li style=\"{'color:#eef3f1' if dark else ''}\">{_esc(b)}</li>"
                        for b in slide["bullets"])
        bullets = f"<ul>{items}</ul>"

    brand = theme.get("brand", "Deck")
    repl = {
        "%%ACCENT%%": theme.get("accent", "#1f6f63"), "%%ACCENT2%%": theme.get("accent2", "#d98a3d"),
        "%%BG%%": theme.get("bg", "#fbf8f2"), "%%INK%%": "#ffffff" if dark else theme.get("ink", "#1d2a27"),
        "%%OVERLAY%%": overlay, "%%IMG%%": img_css,
        "%%DARKCLASS%%": "dark" if dark else "",
        "%%INITIAL%%": _esc(brand[:1].upper()), "%%BRAND%%": _esc(brand),
        "%%EYEBROW%%": _esc(slide.get("eyebrow", "")),
        "%%TITLE%%": _esc(title), "%%TITLESIZE%%": titlesize,
        "%%SUBTITLE%%": sub, "%%BULLETS%%": bullets,
        "%%IDX%%": str(idx + 1), "%%TOTAL%%": str(total),
    }
    out_html = TEMPLATE
    for k, v in repl.items():
        out_html = out_html.replace(k, v)
    tmp = Path(dest).with_suffix(".html")
    tmp.write_text(out_html)
    screenshot(f"file://{tmp.resolve()}", dest, size[0], size[1])
    tmp.unlink(missing_ok=True)
    return dest


def deck_frame(deck_path, idx, dest, size):
    url = f"file://{Path(deck_path).resolve()}?clean#{idx + 1}"
    screenshot(url, dest, size[0], size[1])
    return dest
