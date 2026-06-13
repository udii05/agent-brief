import os
import subprocess
import sys


def send_via_node(briefing_path: str = "briefing.txt") -> bool:
    whatsapp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "whatsapp")
    index_js = os.path.join(whatsapp_dir, "index.js")

    if not os.path.exists(index_js):
        print(f"whatsapp/index.js not found at {index_js}")
        return False
    if not os.path.exists(briefing_path):
        print(f"Briefing file not found: {briefing_path}")
        return False

    env = os.environ.copy()
    env["BRIEFING_PATH"] = os.path.abspath(briefing_path)

    print("Sending via WhatsApp (Node.js)...")
    result = subprocess.run(
        ["node", "index.js"],
        cwd=whatsapp_dir,
        env=env,
        capture_output=True,
        text=True,
    )

    for line in result.stdout.splitlines():
        print(f"  {line}")
    if result.stderr:
        for line in result.stderr.splitlines():
            print(f"  ! {line}")

    if result.returncode == 0:
        print("WhatsApp send succeeded")
        return True
    else:
        print(f"WhatsApp send failed (exit code {result.returncode})")
        return False
