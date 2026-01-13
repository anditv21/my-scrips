#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
import datetime
import urllib.request
import urllib.error
import getpass
from typing import List, Tuple, Dict, Optional

DEFAULT_WEBHOOK: Optional[str] = ""  # updated from your request

DEFAULT_SAB_ICON = "https://github.com/sabnzbd.png"
DEFAULT_USERNAME = "SABnzbd"
DEFAULT_AVATAR: Optional[str] = "https://github.com/sabnzbd.png"
g
DEFAULT_DEBUG = False



# Map SABnzbd event types to (human label, emoji, color)
EVENT_MAP: Dict[str, Tuple[str, str, int]] = {
    "download": ("Added NZB", "📥", 0xF39C12),  # orange
    "complete": ("Job finished", "✅", 0x2ECC71),  # green
    "failed": ("Job failed", "❌", 0xE74C3C),  # red
    "error": ("Error", "🛑", 0xE74C3C),  # red
    "warning": ("Warning", "⚠️", 0xF1C40F),  # yellow
    "queue_done": ("Queue finished", "ℹ️", 0x3498DB),  # blue
    "startup": ("Startup/Shutdown", "ℹ️", 0x3498DB),
    "pause_resume": ("Pause/Resume", "⏸️", 0x3498DB),
    "pp": ("Post-processing started", "🔧", 0x3498DB),
    "disk_full": ("Disk full", "💥", 0xF1C40F),
    "other": ("Other", "ℹ️", 0x3498DB),
}


def masked_len(s: Optional[str]) -> str:
    """Return a masked description of a secret (do not print the secret)."""
    if not s:
        return "not set"
    return f"length={len(s)}"


def maybe_warn_line_endings() -> None:
    """Warn if this file likely has CRLF line endings which break Linux shebangs."""
    try:
        with open(__file__, "rb") as fh:
            head = fh.read(4096)
            if b"\r\n" in head:
                print("WARNING: script contains Windows (CRLF) line endings; run dos2unix on the file to avoid '/usr/bin/env: 'python3\\r': No such file or directory' errors.", file=sys.stderr)
    except Exception:
        pass






def split_urls(url_args: List[str]) -> List[str]:
    if not url_args:
        return []
    out: List[str] = []
    for u in url_args:
        parts = [x.strip() for x in u.split(",") if x.strip()]
        out.extend(parts)
    return out


def extract_fields_from_message(msg: str) -> Tuple[str, Dict[str, str]]:
    fields: Dict[str, str] = {}
    lines: List[str] = msg.splitlines()
    keep_lines: List[str] = []
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            k0 = k.strip().lower()
            v0 = v.strip()
            if k0 in ("category", "download status", "status"):
                fields[k0] = v0
                continue
        keep_lines.append(line)

    cleaned = "\n".join(keep_lines).strip()
    return cleaned, fields


def color_emoji_for_color(color: int) -> str:
    # Map approximate color to a colored circle emoji
    # orange, green, red, yellow, blue fallback
    if color == 0xF39C12 or (0xF00000 <= color <= 0xFFFF00):
        return "🟠"
    if color == 0x2ECC71 or (0x00FF00 <= color <= 0x33FF33):
        return "🟢"
    if color == 0xE74C3C or (0xFF0000 <= color <= 0xFF5555):
        return "🔴"
    if color == 0xF1C40F:
        return "🟡"
    if color == 0x3498DB:
        return "🔵"
    return "▫️"


def make_embed(ntype: str, title: str, body: str, urls: List[str]) -> Dict:
    # Find mapping or fallback
    map_entry = EVENT_MAP.get(ntype, (ntype.capitalize(), "ℹ️", 0x3498DB))
    label, emoji, color = map_entry

    description, parsed_fields = extract_fields_from_message(body)

    # Set Category and Download Status fields
    category = parsed_fields.get("category") or ntype
    download_status = parsed_fields.get("download status") or parsed_fields.get("status") or ntype

    # Add emoji to title and field values
    circle = color_emoji_for_color(color)
    title_text = f"SABnzbd: {emoji} {label}"
    category_value = f"{circle} {category}"
    download_status_value = f"{emoji} {download_status}"

    # Convert requested HSLA (37deg, 100% sat, 50% light) to integer color
    def hsl_to_rgb_int(h: float, s: float, l: float) -> int:
        # h in degrees [0,360), s,l in [0,1]
        c = (1 - abs(2 * l - 1)) * s
        hp = h / 60.0
        x = c * (1 - abs((hp % 2) - 1))
        r1 = g1 = b1 = 0.0
        if 0 <= hp < 1:
            r1, g1, b1 = c, x, 0
        elif 1 <= hp < 2:
            r1, g1, b1 = x, c, 0
        elif 2 <= hp < 3:
            r1, g1, b1 = 0, c, x
        elif 3 <= hp < 4:
            r1, g1, b1 = 0, x, c
        elif 4 <= hp < 5:
            r1, g1, b1 = x, 0, c
        else:
            r1, g1, b1 = c, 0, x
        m = l - c / 2
        r = int(round((r1 + m) * 255))
        g = int(round((g1 + m) * 255))
        b = int(round((b1 + m) * 255))
        return (r << 16) + (g << 8) + b

    hsla_color_int = hsl_to_rgb_int(37.0, 1.0, 0.5)
    final_color = color or hsla_color_int

    embed = {
        "title": title_text,
        "description": description or title,
        "color": final_color,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "author": {"name": "SABnzbd", "icon_url": DEFAULT_SAB_ICON},
        "fields": [
            {"name": "Category", "value": category_value, "inline": True},
            {"name": "Download Status", "value": download_status_value, "inline": True},
        ],
        "footer": {"text": "SABnzbd Notification"},
    }

    # If there are URLs, include the first as a thumbnail
    if urls:
        embed["thumbnail"] = {"url": urls[0]}

    return embed


def send_webhook(webhook_url: str, username: Optional[str], avatar_url: Optional[str], embed: Dict, debug: bool = False) -> bool:
    payload: Dict = {"embeds": [embed]}
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url

    data = json.dumps(payload).encode("utf-8")

    if debug:
        print("DEBUG: webhook payload:")
        print(json.dumps(payload, indent=2))
        return True


    # Log an unobtrusive notice before sending so SABnzbd logs show we attempted delivery
    print(f"NOTICE: sending webhook ({masked_len(webhook_url)})", file=sys.stderr)

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
        "Accept": "application/json",
    }

    req = urllib.request.Request(webhook_url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = resp.getcode()
            if 200 <= code < 300:
                print(f"NOTICE: webhook POST succeeded (HTTP {code})", file=sys.stderr)
                return True
            print(f"Discord responded with HTTP {code}", file=sys.stderr)
            return False
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}", file=sys.stderr)
        try:
            body = e.read().decode()
            if body:
                print(body, file=sys.stderr)
        except Exception:
            body = ''
        # Helpful hint on common failure modes
        if e.code == 403:
            print(
                "ERROR: Discord returned 403 Forbidden. This usually means the webhook URL is invalid or has been deleted.\n" \
                "Please regenerate the webhook in your Discord channel and update the script's DEFAULT_WEBHOOK or the DISCORD_WEBHOOK_URL environment variable.",
                file=sys.stderr,
            )
        return False
    except Exception as e:
        print(f"Error sending webhook: {e}", file=sys.stderr)
        return False


def main(argv: List[str]) -> int:
    maybe_warn_line_endings()

    # Single-file configuration only: prefer the built-in DEFAULT_WEBHOOK.
    if DEFAULT_WEBHOOK:
        print(f"NOTICE: using built-in DEFAULT_WEBHOOK ({masked_len(DEFAULT_WEBHOOK)})", file=sys.stderr)

    final_webhook = DEFAULT_WEBHOOK

    # Mask any webhook appearing in argv so we don't leak secrets in logs
    safe_argv = ["<WEBHOOK_REDACTED>" if isinstance(a, str) and "discord.com/api/webhooks" in a else a for a in sys.argv]

    try:
        who = getpass.getuser()
    except Exception:
        who = "unknown"
    print(f"DEBUG INFO: user={who} cwd={os.getcwd()} argv={safe_argv}", file=sys.stderr)

    if not final_webhook:
        print("ERROR: No webhook configured. Edit this file and set DEFAULT_WEBHOOK to your webhook URL (single-file configuration).", file=sys.stderr)
        return 2

    # Expect positional args: <type> <title> <message> [url1,url2,...]
    if len(argv) < 3:
        print("ERROR: Not enough arguments. Expect: <type> <title> <message> [urls...]", file=sys.stderr)
        return 1

    ntype = argv[0].strip().lower()
    title = argv[1]
    message = argv[2]
    urls = []
    if len(argv) > 3:
        for u in argv[3:]:
            for p in u.split(','):
                p = p.strip()
                if p:
                    urls.append(p)

    print(f"NOTICE: received notification type: {ntype}", file=sys.stderr)

    embed = make_embed(ntype, title, message, urls)

    debug_flag = DEFAULT_DEBUG

    ok = send_webhook(final_webhook, DEFAULT_USERNAME, DEFAULT_AVATAR, embed, debug=debug_flag)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
