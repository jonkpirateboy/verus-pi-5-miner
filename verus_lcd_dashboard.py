#!/usr/bin/env python3
import os
import time
import re
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH = 480
HEIGHT = 320
FB_PATH = "/dev/fb0"
LOG_PATH = Path("/tmp/verus_raw.log")

BG_COLOR = (0, 0, 0)
FG_MAIN = (0, 255, 0)        # hacker-grönt
FG_DIM = (0, 160, 0)
FG_GRAY = (100, 100, 100)
FG_WARN = (255, 165, 0)

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(s: str) -> str:
    """Ta bort ANSI-färgkoder."""
    return ANSI_RE.sub("", s)

def rgb888_to_rgb565(img):
    arr = np.array(img)
    r = (arr[:, :, 0] >> 3).astype(np.uint16)
    g = (arr[:, :, 1] >> 2).astype(np.uint16)
    b = (arr[:, :, 2] >> 3).astype(np.uint16)
    rgb565 = (r << 11) | (g << 5) | b
    return rgb565

def load_font(size):
    # Försök få monospace först
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def uptime_string(secs: int) -> str:
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def center_text(draw, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = (WIDTH - text_w) // 2
    draw.text((x, y), text, font=font, fill=fill)

def get_recent_accepted_lines(n=11):
    """Hämta de n senaste raderna som innehåller 'accepted:'."""
    if not LOG_PATH.exists():
        return []

    try:
        with LOG_PATH.open("r") as f:
            lines = f.readlines()
    except Exception:
        return []

    accepted = [ln.rstrip("\n") for ln in lines if "accepted:" in ln]
    return accepted[-n:]

def strip_timestamp(line: str) -> str:
    """
    Ta bort prefixet '[2025-12-09 11:37:41] ' om det finns.
    """
    if line.startswith("["):
        idx = line.find("]")
        if idx != -1:
            # hoppa över ']' + ev. mellanslag
            i = idx + 1
            if i < len(line) and line[i] == " ":
                i += 1
            return line[i:]
    return line

def parse_stats_from_line(line: str):
    """
    Parsar hashrate (kH/s) och shares från:
    [time] accepted: 252/253 (diff ...), 3679.97 kH/s yes!
    """
    m = re.search(r"accepted:\s+(\d+)/(\d+).*?,\s+([\d\.]+)\s+kH/s", line)
    if not m:
        return 0.0, 0, 0
    acc = int(m.group(1))
    tot = int(m.group(2))
    khs = float(m.group(3))
    return khs * 1000.0, acc, tot  # H/s

def main():
    font_title = load_font(20)
    font_data  = load_font(16)
    font_small = load_font(13)
    font_log   = load_font(13)

    start_time = time.time()

    while True:
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        uptime_secs = int(time.time() - start_time)
        uptime = uptime_string(uptime_secs)
        lines = get_recent_accepted_lines(n=11)

        hashrate_hs = 0.0
        acc = 0
        tot = 0

        if lines:
            hashrate_hs, acc, tot = parse_stats_from_line(lines[-1])

        hashrate_mhs = hashrate_hs / 1_000_000.0
        rej = max(tot - acc, 0)

        # Shares per minut (bara som kul siffra)
        spm = 0.0
        if uptime_secs > 0:
            spm = acc / (uptime_secs / 60.0)

        # Header
        center_text(draw, 2, "VERUS MINER // PI5", font_title, FG_MAIN)
        center_text(draw, 20, "POOL: sg.vipor.net", font_small, FG_DIM)

        # Divider
        draw.line((10, 36, WIDTH - 10, 36), fill=FG_DIM, width=1)

        if not LOG_PATH.exists() or not lines:
            center_text(draw, 80, "WAITING FOR MINER OUTPUT", font_data, FG_WARN)
            center_text(draw, 100, "Start ccminer with tee /tmp/verus_raw.log", font_small, FG_GRAY)
        else:
            # Data-ruta
            draw.text((10, 40), f"HR : {hashrate_mhs:5.2f} MH/s", font=font_data, fill=FG_MAIN)
            draw.text((10, 56), f"SH : {acc:4d}/{tot:<4d}  REJ: {rej}", font=font_data, fill=FG_MAIN)
            draw.text((10, 72), f"UP : {uptime}", font=font_data, fill=FG_MAIN)
            draw.text((10, 88), f"SPM: {spm:5.2f} shares/min", font=font_data, fill=FG_MAIN)

            # Divider
            draw.line((10, 106, WIDTH - 10, 106), fill=FG_DIM, width=1)

            # Log-del – fyll resten av skärmen
            draw.text((10, 110), "LOG:", font=font_small, fill=FG_GRAY)

            y = 126
            max_chars = 60
            for ln in lines:
                # städa ANSI + timestamp
                ln2 = strip_ansi(ln)
                ln_clean = strip_timestamp(ln2)
                if len(ln_clean) > max_chars:
                    ln_disp = ln_clean[:max_chars] + "…"
                else:
                    ln_disp = ln_clean
                draw.text((10, y), "> " + ln_disp, font=font_log, fill=FG_MAIN)
                y += 16
                if y > HEIGHT - 8:
                    break

        # Skriv till framebuffer
        rgb565 = rgb888_to_rgb565(img)
        with open(FB_PATH, "wb") as f:
            f.write(rgb565.tobytes())

        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
