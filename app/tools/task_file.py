from __future__ import annotations

from datetime import datetime
from pathlib import Path


def append_group_message(file_path: str, group: str, sender: str, text: str) -> None:
    if not text:
        return

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if group:
        line = f"[{ts}] [{group}] {sender}: {text}\n"
    else:
        line = f"[{ts}] {sender}: {text}\n"

    with path.open("a", encoding="utf-8") as f:
        f.write(line)
