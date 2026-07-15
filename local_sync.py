#!/usr/bin/env python
"""Local companion to the cloud weekly routine.

Run weekly (via Windows Task Scheduler) after the cloud routine has pushed a
new report: pulls the repo, then converts any `reports/*.md` that doesn't yet
have a corresponding `.docx` under `local_reports/`, using the pandoc install
already present on this machine.
"""
import glob
import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")
LOCAL_REPORTS_DIR = os.path.join(PROJECT_DIR, "local_reports")
LOG_PATH = os.path.join(PROJECT_DIR, "local_sync.log")


def log(msg):
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def run(cmd):
    return subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True)


def main():
    log(f"\n=== local_sync run ===")

    pull = run(["git", "pull", "--ff-only", "origin", "main"])
    log(f"[git pull] rc={pull.returncode} stdout={pull.stdout.strip()} stderr={pull.stderr.strip()}")
    if pull.returncode != 0:
        log("[git pull] failed, aborting conversion step this run.")
        sys.exit(1)

    os.makedirs(LOCAL_REPORTS_DIR, exist_ok=True)

    md_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.md")))
    converted = 0
    for md_path in md_files:
        base = os.path.splitext(os.path.basename(md_path))[0]
        docx_path = os.path.join(LOCAL_REPORTS_DIR, base + ".docx")
        if os.path.exists(docx_path):
            continue
        result = run(["pandoc", md_path, "-o", docx_path])
        if result.returncode == 0:
            log(f"[pandoc] converted: {base}.md -> {base}.docx")
            converted += 1
        else:
            log(f"[pandoc] FAILED on {base}.md: {result.stderr.strip()}")

    log(f"Done. {converted} new report(s) converted to docx in {LOCAL_REPORTS_DIR}.")


if __name__ == "__main__":
    main()
