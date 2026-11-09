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
INSTALLATION = (
    "1. Download ProjectDesk_Setup.exe.\n"
    "2. If Windows blocks the file, right-click it, choose **Properties**, select **Unblock** on the **General** tab and click **OK**.\n"
    "3. Run the setup. No administrator rights are required. If SmartScreen shows a warning, click **More info** and then **Run anyway**.\n"
    "\n"
    "New versions install over the existing one. Data and settings are kept. The user manual is attached as PDF."
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

    # Changes first, then how to install
    notes = "### What's new\n\n" + section.group(1).strip() + "\n\n### Installation\n\n" + INSTALLATION + "\n"
    notes_file.write_text(notes, encoding="utf-8")
    print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
