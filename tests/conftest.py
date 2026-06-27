import base64
import pytest

# A valid 1x1 PNG — enough for export tests that only need a real image file.
PNG_1x1 = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def frames(tmp_path):
    """Three slide dicts backed by real (tiny) PNG frames; slide 1 has no narration."""
    rows = []
    for i in range(3):
        f = tmp_path / f"frame-{i+1:02d}.png"
        f.write_bytes(PNG_1x1)
        rows.append({"frame": f, "narration": "" if i == 1 else f"Narration line {i}."})
    return rows
