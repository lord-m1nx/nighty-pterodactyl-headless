#!/usr/bin/env python3
"""log rotation utility for nighty-linux-headless.

Rotates log files in diagnostics/ and NIGHTY_HOME when they exceed a configurable
size threshold, keeping a bounded number of rotated backups.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


def rotate_log_file(log_path: Path, max_bytes: int = 10 * 1024 * 1024, max_backups: int = 3) -> bool:
    """Rotate a log file if its size exceeds max_bytes.

    Returns True if the log was rotated, False otherwise.
    """
    if not log_path.is_file():
        return False

    try:
        size = log_path.stat().st_size
    except OSError:
        return False

    if size < max_bytes:
        return False

    # Shift existing backups (.2 -> .3, .1 -> .2, etc.)
    for i in range(max_backups - 1, 0, -1):
        src = log_path.with_name(f"{log_path.name}.{i}")
        dst = log_path.with_name(f"{log_path.name}.{i + 1}")
        if src.is_file():
            try:
                if dst.is_file():
                    dst.unlink()
                src.rename(dst)
            except OSError:
                pass

    # Move primary log to .1
    target = log_path.with_name(f"{log_path.name}.1")
    try:
        if target.is_file():
            target.unlink()
        shutil.copyfile(log_path, target)
        with open(log_path, "r+b") as fh:
            fh.truncate(0)
        return True
    except OSError as e:
        print(f"[rotate_logs] Warning: Failed to rotate {log_path}: {e}", file=sys.stderr)
        return False


def wrapper_owned_logs(diag_path: Path, home_path: Path) -> list[Path]:
    log_names = ["backend.log", "bridge.log", "guard.log", "xvfb.log", "stub_webview.log", "nighty.log"]
    targets = []
    for name in log_names:
        p_diag = diag_path / name
        if p_diag.is_file():
            targets.append(p_diag)
        p_home = home_path / name
        if p_home.is_file() and p_home != p_diag:
            targets.append(p_home)
    return targets


def main() -> int:
    max_mb = float(os.environ.get("MAX_LOG_MB", "10"))
    max_bytes = int(max_mb * 1024 * 1024)
    max_backups = int(os.environ.get("MAX_LOG_BACKUPS", "3"))

    here_dir = Path(__file__).resolve().parents[1]
    diag_dir_env = os.environ.get("NIGHTY_DIAG_DIR")
    diag_path = Path(diag_dir_env) if diag_dir_env else (here_dir / "diagnostics")

    nighty_home = os.environ.get("NIGHTY_HOME") or os.path.expanduser("~/.local/share/nighty")
    home_path = Path(nighty_home)

    if len(sys.argv) > 1:
        targets = [Path(p) for p in sys.argv[1:]]
    else:
        targets = wrapper_owned_logs(diag_path, home_path)

    rotated_any = False
    for target in targets:
        if rotate_log_file(target, max_bytes=max_bytes, max_backups=max_backups):
            print(f"[rotate_logs] Rotated {target.name} (exceeded {max_mb} MB)")
            rotated_any = True

    return 0 if rotated_any else 0


if __name__ == "__main__":
    sys.exit(main())
