"""Shared helpers: shell, HTTP (stdlib only), headless-Chrome screenshots."""
import json, shutil, subprocess, urllib.request, urllib.error
from pathlib import Path

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def which(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


CHROME = which("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
FFMPEG = which("ffmpeg")
FFPROBE = which("ffprobe")


def sh(cmd, quiet=True):
    subprocess.run(cmd, check=True,
                   stdout=subprocess.DEVNULL if quiet else None,
                   stderr=subprocess.DEVNULL if quiet else None)


def http_get(url, dest=None, headers=None, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        ctype = r.headers.get("Content-Type", "")
    if dest:
        Path(dest).write_bytes(data)
    return data, ctype


def http_post_json(url, payload, headers=None, timeout=180, accept="application/json"):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "User-Agent": UA, "Content-Type": "application/json", "Accept": accept,
        **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("Content-Type", "")


def screenshot(url, dest, width, height, wait_ms=3500):
    if not CHROME:
        raise RuntimeError("No Chrome/Chromium found — needed to render slide frames.")
    sh([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
        f"--window-size={width},{height}", "--force-color-profile=srgb",
        f"--virtual-time-budget={wait_ms}", f"--screenshot={dest}", url])


def ffprobe_duration(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0
