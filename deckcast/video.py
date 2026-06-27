"""Assemble per-slide image+audio segments and concatenate into the final MP4."""
from pathlib import Path
from .util import sh, FFMPEG


def segment(image, audio, dest, size, fps, dur, abitrate):
    """Render `image` held for `dur` seconds. `audio` may be None -> silent slide."""
    w, h = size
    cmd = [FFMPEG, "-y", "-loop", "1", "-i", str(image)]
    if audio and Path(audio).exists():
        cmd += ["-i", str(audio), "-af", "apad"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    cmd += ["-t", f"{dur:.2f}", "-r", str(fps),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                   f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p",
            "-c:a", "aac", "-b:a", abitrate, "-ar", "48000", str(dest)]
    sh(cmd)
    return dur


def concat(segments, dest, build_dir):
    listfile = Path(build_dir) / "segments.txt"
    listfile.write_text("".join(f"file '{Path(s).resolve()}'\n" for s in segments))
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    sh([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
        "-c", "copy", "-movflags", "+faststart", str(dest)])
    return dest
