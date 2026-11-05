"""Version and release notes for the GitHub workflow Release

python .github/release_notes.py <notes file> [tag]
Prints APP_VERSION of project_desk.py and writes the notes of that version from the version history in DEVELOPMENT.md.
Fails if the tag does not match the version or the version history has no section for it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
INTRO = (
    "Download ProjectDesk_Setup.exe and run it, no administrator rights are needed. "
    "An installed version is updated and the data is kept. The user manual is attached as PDF."
)


def main() -> int:
    notes_file = Path(sys.argv[1])
    tag = sys.argv[2] if len(sys.argv) > 2 else ""

    source = (REPOSITORY / "project_desk.py").read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION = "([^"]+)"', source, re.MULTILINE)
    if match is None:
        print("APP_VERSION not found in project_desk.py", file=sys.stderr)
        return 1
    version = match.group(1)
    if tag and tag != f"v{version}":
        print(f"Tag {tag} does not match APP_VERSION {version}", file=sys.stderr)
        return 1

    history = (REPOSITORY / "DEVELOPMENT.md").read_text(encoding="utf-8")
    section = re.search(rf"^### {re.escape(version)}\n(.*?)(?=^### |^## |\Z)", history, re.MULTILINE | re.DOTALL)
    if section is None or not section.group(1).strip():
        print(f"The version history in DEVELOPMENT.md has no section ### {version}", file=sys.stderr)
        return 1

    notes_file.write_text(INTRO + "\n\n" + section.group(1).strip() + "\n", encoding="utf-8")
    print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
