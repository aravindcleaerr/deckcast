"""Assemble per-slide image+audio segments and concatenate into the final MP4."""
import os
from pathlib import Path
from .util import sh, FFMPEG, ffprobe_duration


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


def concat_xfade(segments, dest, transition, fps, abitrate, build_dir):
    """Concatenate with `transition`-second cross-dissolves between slides.
    Re-encodes (xfade needs decoded frames). Falls back to plain concat for 1 clip."""
    segments = list(segments)
    if len(segments) < 2:
        return concat(segments, dest, build_dir)
    durs = [ffprobe_duration(s) for s in segments]
    ins = []
    for s in segments:
        ins += ["-i", str(s)]
    chains, vprev, aprev, offset = [], "[0:v]", "[0:a]", durs[0] - transition
    for k in range(1, len(segments)):
        vout, aout = f"[v{k}]", f"[a{k}]"
        chains.append(f"{vprev}[{k}:v]xfade=transition=fade:"
                      f"duration={transition}:offset={offset:.3f}{vout}")
        chains.append(f"{aprev}[{k}:a]acrossfade=d={transition}{aout}")
        vprev, aprev = vout, aout
        offset += durs[k] - transition
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    sh([FFMPEG, "-y", *ins, "-filter_complex", ";".join(chains),
        "-map", vprev, "-map", aprev, "-r", str(fps),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", abitrate,
        "-movflags", "+faststart", str(dest)])
    return dest


def add_music(video_path, music, volume=0.12, fade=2.0):
    """Mix a looping background bed under the existing narration (in place)."""
    video_path = Path(video_path)
    dur = ffprobe_duration(video_path)
    tmp = video_path.with_suffix(".music.mp4")
    fc = (f"[1:a]volume={volume},afade=t=out:st={max(0.0, dur - fade):.2f}:d={fade}[bg];"
          f"[0:a][bg]amix=inputs=2:duration=first:normalize=0[a]")
    sh([FFMPEG, "-y", "-i", str(video_path), "-stream_loop", "-1", "-i", str(music),
        "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(tmp)])
    os.replace(tmp, video_path)
    return video_path
