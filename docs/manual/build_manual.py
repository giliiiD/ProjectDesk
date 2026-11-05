"""User manual as PDF from the screenshots of make_screenshots.py

Needs the Python packages playwright (with its Chromium), pypdf and Pillow and the font Inter:
    python3 docs/manual/make_screenshots.py
    python3 docs/manual/build_manual.py
The result is docs/ProjectDesk_User_Manual.pdf.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright
from pypdf import PdfReader, PdfWriter

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))

from project_desk import APP_VERSION  # noqa: E402

BUILD = REPOSITORY / "docs" / "manual" / "build"
OUTPUT = REPOSITORY / "docs" / "ProjectDesk_User_Manual.pdf"
ICON = REPOSITORY / "projectdesk.ico"
EDITION = "November 2026"
ACCENT = "#0f6cbd"

CSS = """
@page { size: A4; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Inter', sans-serif; color: #1b1b1b; font-size: 10pt; line-height: 1.55; margin: 0; }
h1 { font-size: 22pt; font-weight: 700; margin: 0 0 6mm; letter-spacing: -0.01em; }
h2 { font-size: 15pt; font-weight: 650; color: #0f6cbd; margin: 0 0 3mm; padding-top: 2mm; break-after: avoid; letter-spacing: -0.005em; }
h3 { font-size: 11pt; font-weight: 650; margin: 5mm 0 1.5mm; break-after: avoid; }
p { margin: 0 0 2.5mm; }
ul, ol { margin: 0 0 3mm; padding-left: 5.5mm; }
li { margin: 0 0 1.2mm; }
section { break-before: page; }
section.flow { break-before: auto; margin-top: 9mm; }
.ui { font-weight: 600; }
kbd { font-family: 'Inter', sans-serif; font-size: 8.5pt; font-weight: 600; background: #f3f3f3; border: 1px solid #d0d0d0; border-bottom-width: 2px; border-radius: 3px; padding: 0 1.4mm; white-space: nowrap; }
figure { margin: 3mm 0 5mm; break-inside: avoid; }
figure .frame { position: relative; border: 1px solid #dcdcdc; border-radius: 2.5mm; overflow: hidden; box-shadow: 0 0.6mm 2.5mm rgba(0,0,0,0.08); }
figure img { display: block; width: 100%; }
figure.side { float: right; width: 36%; margin: 1mm 0 4mm 7mm; }
figcaption { font-size: 8.5pt; color: #6b6b6b; margin-top: 1.8mm; }
.callout { position: absolute; width: 6.2mm; height: 6.2mm; margin: -3.1mm 0 0 -3.1mm; border-radius: 50%; background: #0f6cbd; color: #fff; font-size: 8.5pt; font-weight: 700; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 0.6mm #fff; }
.legend { display: grid; grid-template-columns: 6.2mm 1fr; gap: 1.6mm 3mm; margin: 2mm 0 4mm; align-items: start; }
.legend .num { width: 6.2mm; height: 6.2mm; border-radius: 50%; background: #0f6cbd; color: #fff; font-size: 8.5pt; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.tip { background: #ebf3fc; border-left: 1mm solid #0f6cbd; border-radius: 1.5mm; padding: 2.5mm 4mm; margin: 3mm 0 4mm; break-inside: avoid; }
.tip b { color: #0f6cbd; }
table { border-collapse: collapse; width: 100%; margin: 2mm 0 4mm; font-size: 9.5pt; }
th { text-align: left; font-weight: 650; color: #6b6b6b; font-size: 8.5pt; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid #d0d0d0; padding: 1.5mm 2mm; }
td { border-bottom: 1px solid #ececec; padding: 1.8mm 2mm; vertical-align: top; }
td:first-child { width: 42%; }
.toc { list-style: none; padding: 0; margin: 4mm 0 0; }
.toc li { display: flex; align-items: baseline; margin: 0 0 2.6mm; font-size: 10.5pt; }
.toc .title { white-space: nowrap; }
.toc .dots { flex: 1; border-bottom: 1px dotted #b8b8b8; margin: 0 2mm; transform: translateY(-1mm); }
.toc .num { color: #6b6b6b; min-width: 6mm; text-align: right; }
"""

COVER_CSS = """
@page { margin: 0; }
body { height: 297mm; }
.cover { height: 297mm; display: flex; flex-direction: column; justify-content: center; padding: 0 24mm; background: linear-gradient(180deg, #ffffff 0%, #ffffff 62%, #ebf3fc 100%); }
.cover img { width: 30mm; height: 30mm; margin-bottom: 10mm; }
.cover .name { font-size: 40pt; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
.cover .sub { font-size: 18pt; color: #0f6cbd; font-weight: 500; margin-top: 3mm; }
.cover .meta { margin-top: 18mm; color: #6b6b6b; font-size: 10.5pt; line-height: 1.7; }
"""

FOOTER = """<div style="width:100%; font-family: Inter, sans-serif; font-size:7.5pt; color:#8a8a8a; padding: 0 18mm; display:flex; justify-content:space-between;"><span>ProjectDesk User Manual</span><span class="pageNumber"></span></div>"""


class Manual:
    """Chapters with text and screenshots"""

    def __init__(self) -> None:
        callouts = json.loads((BUILD / "callouts.json").read_text(encoding="utf-8"))
        self.window_width, self.window_height = callouts.pop("size")
        self.callouts = callouts
        self.crops = json.loads((BUILD / "crops.json").read_text(encoding="utf-8"))
        self.titles: list[str] = []
        self.chapters: list[str] = []

    def figure(self, name: str, caption: str, marks: dict | None = None, size: int | None = None, side: bool = False) -> str:
        path = self._image(name)
        attributes = ' class="side"' if side else (f' style="width:{size}%"' if size else "")
        marks_html = ""
        for key, (x, y) in (marks or {}).items():
            marks_html += f'<div class="callout" style="left:{x / self.window_width * 100:.2f}%; top:{y / self.window_height * 100:.2f}%">{key}</div>'
        return f'<figure{attributes}><div class="frame"><img src="{path.as_uri()}">{marks_html}</div><figcaption>{caption}</figcaption></figure>'

    def _image(self, name: str) -> Path:
        # Details are cut from the full screenshot, the screenshot name without extension is the key
        key = name.removesuffix(".png")
        if key not in self.crops:
            return BUILD / name
        source = BUILD / ("overview.png" if key == "todo_details" else name)
        image = Image.open(source)
        scale = image.width / self.window_width
        x, y, width, height = self.crops[key]
        box = (round(x * scale), round(max(0, y) * scale), round(min(x + width, self.window_width) * scale), round(min(y + height, self.window_height) * scale))
        target = BUILD / f"crop_{key}.png"
        image.crop(box).save(target)
        return target

    def chapter(self, title: str, body: str, flow: bool = False) -> None:
        self.titles.append(title)
        attributes = ' class="flow"' if flow else ""
        self.chapters.append(f"<section{attributes}><h2>{title}</h2>{body}</section>")

    def html(self, pages: dict[str, int]) -> str:
        items = ""
        for title in self.titles:
            items += f'<li><span class="title">{title}</span><span class="dots"></span><span class="num">{pages.get(title, "")}</span></li>'
        contents = f'<section style="break-before:auto"><h1>Contents</h1><ul class="toc">{items}</ul></section>'
        return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{contents}{''.join(self.chapters)}</body></html>"


def keys(*names: str) -> str:
    return "+".join(f"<kbd>{name}</kbd>" for name in names)


def ui(text: str) -> str:
    return f'<span class="ui">{text}</span>'


def write_chapters(manual: Manual) -> None:
    manual.chapter("The Main Window", f"""
<p>ProjectDesk keeps everything that belongs to a project in one place: todos, notes and links. The window has three columns: your projects on the left, the entries of the open project in the middle and the details of the selected entry on the right.</p>
{manual.figure("overview.png", "The main window with the todos of a project", manual.callouts)}
<div class="legend">
<div class="num">1</div><div>{ui("Projects")}: the fixed project {ui("General")}, your projects and the archive. The number shows the open todos, a red flag shows flagged todos.</div>
<div class="num">2</div><div>{ui("Tabs")}: every project has todos, notes and links. Tabs you do not need can be hidden in the settings.</div>
<div class="num">3</div><div>{ui("Input field")}: type and press <kbd>Enter</kbd> to add a new entry.</div>
<div class="num">4</div><div>{ui("Group")}: entries can be sorted into groups. The {ui("+")} adds an entry directly to the group.</div>
<div class="num">5</div><div>{ui("Details")} of the selected entry: text, attachments, fields and dates. The icon at the top right enlarges this column to the whole window.</div>
<div class="num">6</div><div>{ui("Settings")}: mode, language, zoom, tabs, storage location and backups.</div>
</div>
<div class="tip"><b>Good to know.</b> Almost every action is in the right-click menu. Rename anything with a double-click. Changes are saved automatically, and {keys("Ctrl", "Z")} undoes every change.</div>
""")

    manual.chapter("Installation and First Start", f"""
<h3>Install</h3>
<ol>
<li>Download {ui("ProjectDesk_Setup.exe")} from the Releases page of the ProjectDesk repository.</li>
<li>Run it. No administrator rights are needed.</li>
<li>If Windows shows a SmartScreen warning, click {ui("More info")} and then {ui("Run anyway")}.</li>
</ol>
<h3>First start</h3>
<p>ProjectDesk asks for a folder in which all data is stored. A folder in your OneDrive is a good choice because OneDrive backs it up automatically. The folder can be changed later (see {ui("Storage Location")}).</p>
<h3>Update</h3>
<p>Download the new setup and run it over the installed version. Your data and settings are kept. An existing installation of the predecessor {ui("ToDo")} is updated to ProjectDesk the same way.</p>
<p>Only one ProjectDesk window runs at a time. Starting it again brings the open window to the front.</p>
""")

    manual.chapter("Projects", f"""
<p>The project {ui("General")} is always at the top. Use it for everything that does not belong to a project.</p>
<ul>
<li>{ui("New project")}: click {ui("+")} next to {ui("Projects")}, or right-click the free space below the projects. Type the name and press <kbd>Enter</kbd>.</li>
<li>{ui("Rename")}: double-click the project, or right-click and choose {ui("Rename")}.</li>
<li>{ui("Color")}: right-click and choose a color for the dot.</li>
<li>{ui("Order")}: drag a project up or down.</li>
<li>{ui("Archive")}: right-click and choose {ui("Archive")}, or drag the project onto the {ui("Archive")} row. A click on {ui("Archive")} shows the archived projects. Right-click one and choose {ui("Restore")} to bring it back.</li>
<li>{ui("Delete")}: right-click and choose {ui("Delete")}, or press <kbd>Delete</kbd>. ProjectDesk asks before deleting.</li>
<li>{ui("More space")}: the button {ui("«")} collapses the project column to a narrow strip, {ui("»")} opens it again.</li>
</ul>
{manual.figure("project_menu.png", "Right-click menu of a project with the colors", size=60)}
""")

    manual.chapter("Tabs and Groups", f"""
<p>Every project has the tabs {ui("Todos")}, {ui("Notes")} and {ui("Links")}. Each tab has its own groups, for example {ui("Design")} and {ui("Content")} for todos. Groups are optional, entries without a group are shown at the top.</p>
<ul>
<li>{ui("New group")}: right-click the free space in the list and choose {ui("New group")}.</li>
<li>{ui("Collapse or expand")}: click the group header.</li>
<li>{ui("Rename")}: double-click the group header.</li>
<li>{ui("Order")}: drag the group header up or down.</li>
<li>{ui("Delete")}: right-click the header and choose {ui("Delete")}. The entries stay, they are shown without a group.</li>
</ul>
<h3>Adding entries to a group</h3>
<p>Click the {ui("+")} on the group header and type the name. <kbd>Enter</kbd> saves it and opens the next entry, so several entries can be typed one after another. <kbd>Esc</kbd> ends. In the notes tab, <kbd>Enter</kbd> continues in the text of the new note.</p>
{manual.figure("quick_add.png", "A new todo is typed directly into the group Content", size=72)}
<h3>Moving entries</h3>
<p>Drag an entry to another place, into another group or onto a collapsed group header. Dropping it onto a project on the left moves it into that project.</p>
""")

    manual.chapter("Todos", f"""
{manual.figure("todo_details.png", "Details of a todo with description and attachment", side=True)}
<ul>
<li>{ui("Add")}: type into {ui("Add new todo")} and press <kbd>Enter</kbd>.</li>
<li>{ui("Done")}: click the checkbox. The todo moves to the section {ui("Done")} at the end of the list and its flag is removed. Clicking the checkbox again reopens it.</li>
<li>{ui("Flag")}: right-click an open todo and choose {ui("Flag")} for important todos. They get a yellow background and the project shows a red flag. A click on the flag removes it.</li>
<li>{ui("Rename")}: double-click the todo in the list, or edit the title on the right.</li>
</ul>
<h3>Description</h3>
<p>Descriptions, notes and the notes of links share the same toolbar:</p>
{manual.figure("toolbar.png", "The toolbar for formatting text", size=45)}
<ul>
<li><b>Bold</b> ({keys("Ctrl", "B")}), <i>italic</i> ({keys("Ctrl", "I")}), <u>underline</u> ({keys("Ctrl", "U")}) and <s>strikethrough</s>.</li>
<li>{ui("Font size")}: Small, Normal, Large or Extra large, for example for headings. The sizes grow and shrink with the zoom.</li>
<li>{ui("Highlight")}: marks the selected text in yellow.</li>
<li>{ui("Bullet list")} and {ui("Numbered list")}. <kbd>Tab</kbd> moves a list line one level in, {keys("Shift", "Tab")} one level out. A dash followed by a space at the start of a line starts a bullet list.</li>
</ul>
<p>Web addresses and network paths become links automatically, a click opens them.</p>
<h3>Attachments</h3>
<p>Drop files onto {ui("Drop files here, click or Ctrl+V")}, click it to choose files, or paste files and screenshots with {keys("Ctrl", "V")}. Images and PDF files show a preview. The icons next to the file name open it with the default program or remove it.</p>
<div class="tip"><b>Note.</b> Attachments are copied into the storage folder. The original file can be moved or deleted afterwards.</div>
""")

    manual.chapter("Notes", f"""
<ul>
<li>{ui("Add")}: type a title into {ui("Add new note")} and press <kbd>Enter</kbd>. <kbd>Enter</kbd> in the empty field creates a note named with today's date.</li>
<li>{ui("Text")}: the same formatting as todo descriptions, including font sizes, highlight, lists and clickable links.</li>
<li>{ui("Images")}: paste screenshots with {keys("Ctrl", "V")}. Every image gets a line of its own and fits the width of the note. A double-click shows it large.</li>
<li>{ui("PDF")}: right-click the note in the list and choose {ui("Export as PDF")}.</li>
</ul>
{manual.figure("notes.png", "A note with bullet list, link and image", size=88)}
<h3>Turning lines into todos</h3>
<p>Select one or more lines, or place the cursor in a line, right-click and choose {ui("Turn into todo")}. The lines become todos of the same project and get a check mark in the note, so they are not taken over twice.</p>
{manual.figure("note_menu.png", "Turn into todo in the right-click menu of a note", size=52)}
<h3>Writing with more space</h3>
<p>The icon at the top right of the right column enlarges it to the whole window, for example for long notes. The same icon brings back the normal view.</p>
{manual.figure("maximized.png", "A note across the whole window", size=88)}
""")

    manual.chapter("Links", f"""
<p>Links collect the places that belong to a project: web pages, shared files, folders on network drives and tools.</p>
<ul>
<li>{ui("Add")}: paste an address into {ui("Add new link")} and press <kbd>Enter</kbd>. The name is taken from the address and can be changed. If you type a name instead, enter the address on the right.</li>
<li>Web addresses, {ui("www.")} addresses, network paths like {ui("&#92;&#92;server&#92;share")} and local paths like {ui("C:&#92;Tools")} are supported.</li>
<li>{ui("Open")}: click the icon on the right of the link, or right-click and choose {ui("Open")}. Web pages open in the browser, folders in the Explorer and files with their program. {ui("Copy address")} copies the address to the clipboard.</li>
<li>The field {ui("Note")} holds additional information.</li>
</ul>
{manual.figure("links.png", "Links in groups with address and note")}
""")

    manual.chapter("Selecting Several Entries", f"""
<ul>
<li><kbd>Ctrl</kbd>+click adds an entry to the selection or removes it.</li>
<li><kbd>Shift</kbd>+click selects all entries between the selected one and the clicked one.</li>
<li>{keys("Ctrl", "A")} selects all entries of the tab, <kbd>Esc</kbd> clears the selection.</li>
<li>{ui("Move")}: drag one of the selected entries. All selected entries move along, into a group or onto a project.</li>
<li>{ui("Export or delete")}: right-click one of the selected entries. <kbd>Delete</kbd> deletes the selection after a question.</li>
</ul>
{manual.figure("multi_select.png", "Three selected todos with their right-click menu")}
""")

    manual.chapter("Undo and Redo", f"""
<p>{keys("Ctrl", "Z")} undoes the last change, {keys("Ctrl", "Y")} or {keys("Ctrl", "Shift", "Z")} redoes it. This works for everything: deleting, moving, renaming, checking off, imports and restored backups. Deleted attachments and images come back as well.</p>
<p>While you are typing in a text field, {keys("Ctrl", "Z")} first undoes the typing in that field. The last 50 changes can be undone. When ProjectDesk is closed, the undo history is cleared, the backups remain.</p>
""", flow=True)

    manual.chapter("Sharing with Colleagues", f"""
<h3>Export</h3>
<p>Right-click an entry, a group, a project or several selected entries and choose {ui("Export …")}. ProjectDesk creates a {ui(".pdesk")} file that contains everything including attachments and images. Send it by email, Teams or a shared drive.</p>
<h3>Import</h3>
<ul>
<li>Double-click the {ui(".pdesk")} file in the Explorer,</li>
<li>drop it onto the ProjectDesk window, or</li>
<li>right-click the free space in a list or in the project column and choose {ui("Import …")}.</li>
</ul>
<p>Before anything changes, ProjectDesk shows what the file contains and where it goes. Entries and groups go into the open project, always into the matching tab. A project is added as a new project. A hidden tab is shown again when entries are imported into it.</p>
{manual.figure("import_dialog.png", "The import asks what to do with entries that already exist", size=88)}
<p>If entries already exist, choose {ui("Skip")} to keep yours or {ui("Replace")} to take over the imported version. Entries count as existing if they are the same entry or links with the same address. A backup is made before every import, and {keys("Ctrl", "Z")} undoes it.</p>
""")

    manual.chapter("Backups", f"""
<p>ProjectDesk backs up your data automatically: once a day, and additionally before every import, before moving the data and before restoring a backup. The 30 newest backups are kept.</p>
{manual.figure("settings_backups.png", "Settings, Backups, Restore", size=70)}
<ul>
<li>{ui("Back up automatically")}: switches the automatic backup on or off. It is on by default.</li>
<li>{ui("Back up now")}: creates a backup immediately.</li>
<li>{ui("Restore")}: lists all backups with date and reason. Choosing one asks first and backs up the current state before restoring, so nothing gets lost. {keys("Ctrl", "Z")} undoes the restore.</li>
<li>{ui("Open folder")}: shows the backup files in the Explorer.</li>
</ul>
<p>Short confirmations like {ui("Backup created")} appear in a blue bar at the bottom of the window.</p>
{manual.figure("banner.png", "Confirmation at the bottom of the window")}
""")

    manual.chapter("Storage Location", f"""
<p>{ui("Settings")}, {ui("Storage location")} shows the folder with your data.</p>
<ul>
<li>{ui("Open in Explorer")}: opens the folder.</li>
<li>{ui("Move data …")}: moves all data, attachments, images and backups to a new, empty folder. The copy is checked before the old files are removed.</li>
<li>{ui("Open other storage location …")}: switches to a folder that already contains ProjectDesk data, for example after setting up a new computer.</li>
</ul>
<div class="tip"><b>Important.</b> A storage folder should only be used by one ProjectDesk at a time. To share content with colleagues, use export and import.</div>
""")

    manual.chapter("Settings", f"""
{manual.figure("settings_tabs.png", "Settings, Tabs", side=True)}
<ul>
<li>{ui("Mode")}: {ui("Same as Windows")}, {ui("Light")} or {ui("Dark")}.</li>
<li>{ui("Language")}: Deutsch or English.</li>
<li>{ui("Zoom")}: makes everything larger or smaller, also with {keys("Ctrl", "+")}, {keys("Ctrl", "-")}, {keys("Ctrl", "0")} or <kbd>Ctrl</kbd> and the mouse wheel.</li>
<li>{ui("Tabs")}: shows or hides {ui("Todos")}, {ui("Notes")} and {ui("Links")}. Hidden tabs keep their entries. At least one tab stays, and with only one tab the tab row disappears.</li>
<li>{ui("Storage location")} and {ui("Backups")}: see the previous chapters.</li>
<li>The installed version is shown at the bottom of the menu.</li>
</ul>
""", flow=True)

    shortcuts = [
        ("Add entry from the input field", keys("Enter")),
        ("Rename the selected entry", "Double-click or " + keys("F2")),
        ("Cancel renaming", keys("Esc")),
        ("Delete the selected entries or project", keys("Delete")),
        ("Undo", keys("Ctrl", "Z")),
        ("Redo", keys("Ctrl", "Y") + " or " + keys("Ctrl", "Shift", "Z")),
        ("Add an entry to the selection", keys("Ctrl") + "+click"),
        ("Select a range", keys("Shift") + "+click"),
        ("Select all entries of the tab", keys("Ctrl", "A")),
        ("Clear the selection", keys("Esc")),
        ("Paste attachments, screenshots and images", keys("Ctrl", "V")),
        ("Bold, italic, underline", keys("Ctrl", "B") + ", " + keys("Ctrl", "I") + ", " + keys("Ctrl", "U")),
        ("List line one level in or out", keys("Tab") + ", " + keys("Shift", "Tab")),
        ("Zoom in, zoom out, reset", keys("Ctrl", "+") + ", " + keys("Ctrl", "-") + ", " + keys("Ctrl", "0")),
    ]
    rows = "".join(f"<tr><td>{action}</td><td>{combination}</td></tr>" for action, combination in shortcuts)
    manual.chapter("Keyboard Shortcuts", f"<table><tr><th>Action</th><th>Keys</th></tr>{rows}</table>")


def cover_html() -> str:
    icon = BUILD / "icon.png"
    image = Image.open(ICON)
    image.size = (256, 256)
    image.load()
    image.save(icon)
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{CSS}{COVER_CSS}</style></head><body><div class="cover">
<img src="{icon.as_uri()}">
<div class="name">ProjectDesk</div>
<div class="sub">User Manual</div>
<div class="meta">Version {APP_VERSION}<br>{EDITION}</div>
</div></body></html>"""


def render(page: Page, html: str, path: Path, footer: bool) -> None:
    # Loaded from a file so the local images are allowed
    source = path.with_suffix(".html")
    source.write_text(html, encoding="utf-8")
    page.goto(source.as_uri(), wait_until="networkidle")
    margin = {"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"} if footer else {"top": "0", "bottom": "0", "left": "0", "right": "0"}
    page.pdf(path=str(path), format="A4", print_background=True, margin=margin, display_header_footer=footer, header_template="<div></div>", footer_template=FOOTER if footer else "<div></div>")


def chapter_pages(path: Path, titles: list[str]) -> dict[str, int]:
    # The first page after the contents on which a chapter title stands alone in a line
    pages: dict[str, int] = {}
    for number, pdf_page in enumerate(PdfReader(str(path)).pages, start=1):
        lines = [line.strip() for line in (pdf_page.extract_text() or "").splitlines()]
        for title in titles:
            if title not in pages and number > 1 and title in lines:
                pages[title] = number
    return pages


def main() -> int:
    manual = Manual()
    write_chapters(manual)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        render(page, cover_html(), BUILD / "cover.pdf", False)
        render(page, manual.html({}), BUILD / "body.pdf", True)
        render(page, manual.html(chapter_pages(BUILD / "body.pdf", manual.titles)), BUILD / "body.pdf", True)
        browser.close()

    writer = PdfWriter()
    for part in ("cover.pdf", "body.pdf"):
        for pdf_page in PdfReader(str(BUILD / part)).pages:
            writer.add_page(pdf_page)
    writer.add_metadata({"/Title": "ProjectDesk User Manual", "/Subject": f"ProjectDesk {APP_VERSION}"})
    with OUTPUT.open("wb") as file:
        writer.write(file)
    print("Manual written to", OUTPUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
