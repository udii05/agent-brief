import sys

# Windows consoles default to cp1252 and can't print emoji in log lines.
# Make stdout/stderr UTF-8-safe so modules work standalone (not just via main.py).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
