# Project Desk Developer Documentation

This document describes the architecture, data format, design rules and release process of Project Desk. It is written so that a new chat or a new developer can continue development quickly. Start with "Quick Start for a New Chat".

The product name is "Project Desk". File names, the executable, the repository and code identifiers use "ProjectDesk" without a space.

## Quick Start for a New Chat

Provide these files together with the change request:

| Change | Files |
|---|---|
| Features and user interface | `DEVELOPMENT.md`, `project_desk.py` |
| Build or installer | additionally `build.bat`, `ProjectDesk.iss`, `requirements.txt` |
| User manual or README screenshot | additionally `docs/manual/make_screenshots.py`, `docs/manual/build_manual.py` |

Architecture in brief:
1. The entire program is in `project_desk.py`, ordered as described in "Code Structure".
2. The data model consists of dataclasses (`Todo`, `Note`, `Link`, `ItemGroup`, `Project`) held by `AppData`. `Storage` loads and saves them as `data.json` in the storage folder.
3. `MainWindow` shows three columns: the projects (`ProjectListWidget`), the entries of the open tab (`ItemListWidget`, painted by `ItemDelegate`) and the details of the selected entry (`TodoPanel`, `NotePanel`, `LinkPanel`).
4. After every change the window is rendered from the data: `_render_all` calls `_render_projects`, `_render_header`, `_render_input`, `_render_items` and `_render_detail`.
5. Every data change calls `_checkpoint()` first for undo and `_schedule_save()` afterwards.

Checklist for new features:
- Call `_checkpoint()` before changing data and `_schedule_save()` afterwards
- Read new data fields with a default value in `from_dict`, so older files still load
- Pass every visible text through `tr("German text")` and add the English text to `TRANSLATIONS`
- Use `px` or `ipx` for pixel sizes and constants at the top of the file for fixed values
- Use `create_menu` for menus, `create_line_icon` for icons and `show_message`, `confirm` or `ask` for dialogs
- Follow "User Interface and Design Rules"
- Test in offscreen mode (see "Testing") and show screenshots before delivering
- If visible behavior changes, update the user manual and this document and add an entry to the version history

Where to start:

| Change | Code |
|---|---|
| New field of an entry | Dataclass (`create`, `from_dict`), panel of the right column, `ItemDelegate` if the field appears in the list |
| New right-click menu entry | `MainWindow._show_item_menu` for entries, groups and empty space, `MainWindow._show_project_menu` for projects |
| New setting | `MainWindow._fill_settings_menu`, stored with `QSettings` (see "Data Storage") |
| New tab type | `ITEM_TYPES` and the per-type dictionaries among the constants, dataclass, panel, `ItemDelegate`, export and import |
| Cards and group headers | `ItemDelegate` and the size constants |
| Colors | `create_palette` and `Theme` |

## Overview

Project Desk is a Windows app for project-based work with a look based on Microsoft Outlook. Up to version 1.2.0 it was called ToDo. It is used alongside Outlook, Teams and the browser and holds only what belongs to a project: todos, notes and links.

- Projects on the left, each with a color dot, plus the fixed project "General" and an archive
- Three tabs per project: todos, notes and links, each with optional groups. Tabs can be hidden in the settings
- Entries in the middle, sortable by drag and drop. Details of the selected entry on the right, the right column can be maximized
- Todos with a condition: "Until" or "From", with a date or a text
- Formatted text with font sizes, highlight, bullet lists and numbered lists in all text fields
- Notes with inline images and PDF export. Lines of a note can be turned into todos
- Export and import of entries, groups and projects as `.pdesk` files
- Automatic backups, undo and redo for every change
- Notice of new versions, checked on GitHub once per start
- Light and dark mode, zoom, German and English user interface
- Installer for the current user, no administrator rights required

## Project Files

| File | Content |
|---|---|
| `project_desk.py` | The entire program |
| `build.bat` | Builds the program and the installer |
| `requirements.txt` | Python packages: PySide6, pyinstaller |
| `ProjectDesk.iss` | Installer script for Inno Setup |
| `projectdesk.ico` | Application icon |
| `README.md` | Start page of the repository |
| `DEVELOPMENT.md` | This document |
| `docs/screenshot.png` | Screenshot in the README, created by `make_screenshots.py` |
| `docs/ProjectDesk_User_Manual.pdf` | User manual, created by `build_manual.py` |
| `docs/manual/make_screenshots.py` | Creates the screenshots with neutral example data |
| `docs/manual/build_manual.py` | Text of the user manual and the PDF build |
| `.github/workflows/release.yml` | GitHub workflow Release: builds the installer and publishes the release |
| `.github/release_notes.py` | Reads the version and writes the release notes for the workflow |
| `.gitignore` | Keeps build output and personal data out of the repository |

Build output (`installer\`, `build\`, `dist\`, `*.spec`, `__pycache__\`, `docs\manual\build\`) is never committed. `.gitignore` also excludes personal data (`data.json`, `data_v1_backup.json`, `attachments\`, `images\`, `backups\`) in case the storage folder is the project folder.

Screenshots in the repository and in the manual show neutral example content only.

## Releasing a New Version

1. Increase `APP_VERSION` in `project_desk.py` and the version line at the end of `README.md`. `build.bat` passes the version to the installer.
2. Add a section `### <version>` to the version history at the end of this document. Its lines become the "What's new" part of the release notes.
3. If visible behavior changed, update the user manual (see "User Manual").
4. Commit the changes to `main`.
5. On GitHub open **Actions**, choose **Release** and click **Run workflow**. Pushing a tag such as `v2.3.1` also starts it.

The workflow runs on a Windows machine of GitHub. It checks that the version history has a section for `APP_VERSION` and that no release of this version exists, installs Inno Setup, runs `build.bat` and publishes the release "Project Desk <version>" with the tag `v<version>`, `ProjectDesk_Setup.exe` and `docs/ProjectDesk_User_Manual.pdf`. If a step fails, nothing is published and the log in **Actions** shows the reason.

Colleagues download the setup from the latest release and install it over their version. Their data is kept.

Local build for testing: run `build.bat`. The result is `installer\ProjectDesk_Setup.exe`. Requirements:
- Python 3 (tested with 3.13), installed with "Add to PATH"
- Inno Setup 6 or 7, "Install for me only" is sufficient

Build notes:
- PyInstaller works in `%LOCALAPPDATA%\ProjectDeskBuild` instead of the project folder. OneDrive locks build folders and PyInstaller then fails with "access denied".
- `build.bat` finds Inno Setup 6 and 7 through the registry and the default folders.
- `build.bat` ends with `pause`. The workflow passes `NUL` as input, so it does not wait.
- The installer is not signed. A downloaded setup may be blocked by Windows: right-click it, choose **Properties**, select **Unblock** and click **OK**. SmartScreen may warn on the first start, which is confirmed with **More info** and **Run anyway**.

## Maintaining the Repository in the Browser

Without Git, the repository can be maintained on github.com:
- **Upload files:** **Add file**, **Upload files**, drag the changed files into the window, enter a commit message and click **Commit changes**. Files with the same path are replaced. For files in `docs`, open that folder first or drag the whole folder.
- **Delete a file:** open it, then **…** and **Delete file**.
- **Create a release:** see "Releasing a New Version".

The browser accepts files up to 25 MiB. It ignores `.gitignore`, so never upload `data.json`, attachments, images or backups.

## User Manual

The manual and the README screenshot are generated by scripts and can be rebuilt after every change of the user interface. Both run on Linux without a display, for example in a Claude chat:

```bash
pip install PySide6 playwright pypdf Pillow
playwright install chromium
python3 docs/manual/make_screenshots.py
python3 docs/manual/build_manual.py
```

The font Inter must be installed. The results are `docs/screenshot.png` and `docs/ProjectDesk_User_Manual.pdf`. Intermediate files are written to `docs/manual/build/`.

- `make_screenshots.py` creates neutral example data in `docs/manual/build/data` (projects "Website Relaunch", "Office Move", "Summer Event" and the archived "Trade Fair 2025"), opens the main window offscreen at zoom 2 and saves the screenshots. Context menus are opened and painted onto the window image. The script also writes `callouts.json` (positions of the numbered marks in the overview) and `crops.json` (areas cut from screenshots, in window coordinates).
- `build_manual.py` contains the text of all chapters (`write_chapters`). It renders the cover and the body from HTML to PDF with Chromium, fills in the page numbers of the table of contents in a second pass and merges both parts.
- `manual.chapter(title, html)` adds a chapter, `flow=True` continues on the same page. `manual.figure(name, caption, marks, size, side)` adds a screenshot, `side=True` places it to the right of the text.
- After a build, check every page as an image, for example with `pdftoppm -r 50 -png`.

## Technology

- Python 3 and PySide6 (Qt 6), style "Fusion" with a custom palette and style sheet
- PDF export with `QPdfWriter`, PDF preview of attachments with QtPdf
- PyInstaller in folder mode (`--onedir`), which starts faster than a single executable
- Inno Setup installs per user to `%LOCALAPPDATA%\Programs\ProjectDesk`, with a start menu entry, an optional desktop shortcut and uninstallation through the Windows settings
- The installer ID (AppId) in `ProjectDesk.iss` must never change. It is still the AppId of ToDo, so existing installations are updated in place. `[InstallDelete]` removes files and shortcuts of older versions
- The installer registers the file type `.pdesk` for the current user. A double-click on a `.pdesk` file starts `ProjectDesk.exe "<file>"`
- Only one instance runs per Windows user. A second start passes its `.pdesk` argument through a `QLocalServer` named `ProjectDesk-<user name>` to the running window, which comes to the front and imports the file

## Data Storage

On the first start each user chooses a storage folder, for example in OneDrive.

- `data.json`: all projects with their todos, notes and links
- `attachments\`: copies of todo attachments, named `<12-character id>_<original name>`
- `images\`: images in notes, named `<16-character id>.png` and referenced in the note HTML as `images/<name>.png`
- `backups\`: copies of `data.json`, named `backup_<YYYY-MM-DD_HH-MM-SS>[-<counter>]_<reason>.json`
- `backups\files\`: attachments and note images of deleted entries while a backup still references them
- `data_v1_backup.json`: copy of version 1 data, written once before the conversion

Structure of `data.json` (version 2):

```json
{
  "version": 2,
  "projects": [
    {
      "id": "…",
      "name": "Website Relaunch",
      "general": false,
      "archived": false,
      "done_collapsed": false,
      "color": "#0f6cbd",
      "todos": [
        {
          "id": "…",
          "title": "Review homepage draft",
          "description": "Plain text",
          "description_html": "Formatted text as Qt HTML",
          "done": false,
          "flagged": false,
          "done_at": null,
          "created": 1762250000.0,
          "modified": 1762250000.0,
          "group_id": "…",
          "attachments": [{"id": "…", "name": "Image.png", "file": "…_Image.png", "added": 1762250000.0}],
          "condition": "until",
          "condition_date": "2026-11-14",
          "condition_text": ""
        }
      ],
      "notes": [{"id": "…", "title": "…", "text": "…", "html": "…", "created": 0.0, "modified": 0.0, "group_id": null}],
      "links": [{"id": "…", "title": "…", "url": "…", "note": "…", "note_html": "…", "created": 0.0, "modified": 0.0, "group_id": null}],
      "groups": {
        "todo": [{"id": "…", "name": "Design", "collapsed": false}],
        "note": [],
        "link": []
      }
    }
  ],
  "active_project_id": "…"
}
```

Data rules:
- `from_dict` reads every field with a default value, so older files keep working
- Exactly one project has `general` set. It is always first, cannot be renamed, archived or deleted and is shown as "Allgemein" or "General"
- Groups are optional and separate per tab. Entries with `group_id` null, or with a missing group, appear above the groups
- Deleting a group keeps its entries without a group
- Done todos appear in the section "Done" at the end of the todo tab and keep their group for when they are reopened
- Done todos are never flagged. Checking a todo removes its flag, also after reopening. `Todo.from_dict` drops the flag of done todos
- `condition` is empty, `until` or `from`. `condition_date` holds an ISO date or is empty, `condition_text` is used without a date. `Todo.from_dict` drops unknown kinds and invalid dates
- Projects without a color get the next free color of `PROJECT_COLORS` (`AppData.normalize`), the general project starts gray
- `touch` sets `modified` when the content of an entry changes in the right column. The footer shows "Created" and, after a change, "Changed"
- Data is saved 300 ms after every change, through a temporary file and `os.replace`

Conversion of older data:
- Version 1 (`AppData.from_groups`, used when `data.json` has `groups` but no `projects`): top-level groups become projects with the same id, subgroups become todo groups. Subgroups named "Allgemein" or "General" become todos without a group. The first open top-level group named "Allgemein" or "General" becomes the general project, otherwise a new one is created. `Storage.load` writes `data_v1_backup.json` once before converting
- Contacts of early 2.0.0 test versions: `contacts_note` turns them into a note "Kontakte" or "Contacts" at the top of the notes, one line per contact. Contact groups are dropped

Files of deleted entries:
- Deleting an entry keeps its files, so undo can restore them
- When the program closes, `Storage.collect_garbage` moves attachments and note images that `data.json` no longer references to `backups\files\`. Files there that neither a backup nor `data_v1_backup.json` references are deleted
- `Storage.restore_files` moves files back after undo, redo or restoring a backup

Personal settings are stored in the registry under `HKEY_CURRENT_USER\Software\ToDo\ToDo` (QSettings, the old name keeps existing settings): `dataFolder`, `geometry`, `splitter`, `archiveExpanded`, `colorMode`, `zoom`, `language`, `activeTab`, `enabledTabs`, `sidebarCollapsed`, `sidebarWidth`, `pdfFolder`, `autoBackup`, `exchangeFolder`. Without `sidebarCollapsed`, the project column starts collapsed when only the general project exists. `enabledTabs` lists the visible tabs separated by spaces, for example `todo note`. Without it, all tabs are visible.

## Todo Conditions

- A todo can have a condition: "Until" (`CONDITION_UNTIL`) for a deadline or "From" (`CONDITION_FROM`) for the earliest start
- In the right column (`TodoPanel`) the row "Condition" has a button for the kind (None, Until, From), a field for a date or a text and a calendar icon. With "None" the field and the calendar are hidden but keep their space, so the layout does not move. Choosing "None" clears date and text
- `parse_condition_date` accepts `14.11.2026`, `14.11.26`, `14.11.`, `14.11` and `2026-11-14`. Anything else is stored as text. A date without a year that lies more than half a year in the past (`CONDITION_NEXT_YEAR_DAYS`) refers to the next year. When the field loses focus, a date is shown in the date format of the language
- The calendar (`TodoPanel._show_calendar`) opens below its icon in the colors of the app. A click selects the day
- In the list the condition appears on the right of the first line, left of the flag and the attachment count (`todo_condition`, `CONDITION_ROLE`), for example "Until 14.11.2026" or "From design approval". The card keeps its height. Long texts are shortened with an ellipsis and take at most `CONDITION_MAX_SHARE` of the width. Today, tomorrow and yesterday are shown as words
- Colors (`STATE_ROLE`): red when an "Until" date is today or past, blue when a "From" date is reached, otherwise gray. Done todos and text conditions are always gray. There is no additional text such as "overdue"
- `MainWindow._check_day` checks every minute (`DAY_CHECK_MS`) whether the date has changed and updates the cards, also after the computer was asleep
- Choosing the kind and choosing a day in the calendar are separate undo steps (`ItemPanel.step_started`). Typing in the field is one step per entry

## Update Notice

- Once per start, 3 seconds after the window opens (`UPDATE_CHECK_DELAY_MS`), `UpdateChecker` requests the latest release from the GitHub API (`UPDATE_API_URL`) in a background thread with `urllib`. Only this request is sent, with the user agent `ProjectDesk/<version>`
- `UpdateState` keeps the result for the entire run. A window rebuilt after a language change does not request again and still shows the notice
- If the release is newer (`is_newer_version` compares `tag_name` with `APP_VERSION`), a blue bar shows "Update available, see Settings" once and the settings icon and the info icon of the version line get a blue dot (`add_badge`, `_update_settings_icons`). The version line reads "Version x.y.z (update available)" and opens the release page
- The dot remains until the new version is installed. The check cannot be switched off
- Without a connection, behind a blocking proxy, on errors or after the timeout (`UPDATE_TIMEOUT_SECONDS`) nothing is shown
- Without login the GitHub API allows 60 requests per hour and IP address, far more than one request per start needs
- The repository must remain public under its name, otherwise `UPDATE_API_URL` and `RELEASES_URL` must be changed

## Tabs Setting

- **Settings > Tabs** shows or hides todos, notes and links per user. Hidden tabs keep their data
- At least one tab remains visible, its menu entry is disabled while it is the last one
- With only one visible tab the tab row is hidden
- With the todo tab hidden, projects show no counts and flags, and notes offer no "Turn into todo" (`NotePanel.todos_enabled`)
- Importing into a hidden tab shows the tab again and reports it in the blue bar
- Code: `MainWindow._enabled_tabs`, `_load_enabled_tabs`, `_set_tab_enabled`, `_apply_enabled_tabs`

## Backups

- **Settings > Backups**: "Back up automatically" (on by default), "Back up now", "Restore" with the list of backups and "Open folder"
- Automatically once a day: before the first save of a day, the last saved `data.json` is copied unless a backup of that day exists
- Additionally before every import, before moving the data and before restoring a backup
- The 30 newest backups are kept (`BACKUP_KEEP`)
- Restoring backs up the current state first and can be undone with Ctrl+Z
- List labels: "Today 14:32", "Yesterday 09:10" or the date, plus the reason in parentheses except for automatic backups

## Moving the Data

**Settings > Storage location > Move data …** copies `data.json`, `attachments`, `images`, `backups` and `data_v1_backup.json` to an empty folder, loads the copy as a check and only then removes the old files. The new folder must not be inside the old one and must not contain a `data.json`. **Open other storage location …** switches to a folder that already contains data without moving anything.

## Export and Import

The right-click menu exports an entry, several selected entries, a group or a project (**Export …**). The file is a ZIP archive with the extension `.pdesk`:

```
content.json
files/attachments/<file>
files/images/<file>.png
```

`content.json`:

```json
{
  "format": "projectdesk-export",
  "format_version": 1,
  "app_version": "2.3.1",
  "kind": "items | group | project",
  "item_type": "todo | note | link, null for a project",
  "name": "…",
  "created": 1762250000.0,
  "groups": [{"id": "…", "name": "…", "collapsed": false}],
  "items": [{"…": "entries as in data.json"}],
  "project": {"…": "only for the kind project, structure as in data.json"}
}
```

Import:
- Through **Import …** in the right-click menu of the empty space in the project list or the middle list, by dropping a `.pdesk` file onto the window, or by double-clicking the file in Explorer
- A dialog shows the content and the target first. If entries already exist, it offers "Skip", "Replace" and "Cancel", otherwise "Import" and "Cancel"
- Entries and groups go into the active project, always into the tab of their type. The view switches to that tab
- A project is added as a new project. If its id already exists, missing entries are added to that project. Name conflicts get " (2)", " (3)" and so on
- Duplicates (`_find_duplicate`): the same id in the target project, or links with the same address (ignoring case and a trailing slash)
- Groups are matched by name, ignoring case. Missing groups are created
- Ids already used elsewhere get a new id. Attachments and note images get new file names
- All entries are checked before anything changes. A damaged file, a newer format version or an error during the import changes nothing and removes files already copied
- Missing files in the package are listed in the result, the entries are imported without them
- The result lists imported, replaced and skipped entries, per project for a project import
- Packages of early 2.0.0 test versions: contacts inside a project are ignored, a package of contacts is rejected as damaged
- Every import creates a backup first and can be undone with Ctrl+Z
- The folder of the last export or import is stored as `exchangeFolder`

## Undo and Redo

- Ctrl+Z undoes, Ctrl+Y or Ctrl+Shift+Z redoes, without a message
- Snapshots: `MainWindow._checkpoint()` stores the entire data (`AppData.to_dict`) and the view (tab, selected entries) before a change
- 50 steps (`UNDO_LIMIT`). A new change clears the redo steps
- While a text field has focus, Ctrl+Z and Ctrl+Y act on that field
- Typing in the right column is one step per entry (`ItemPanel.edit_started`, `_editing_key`). Selecting another entry starts a new step
- Choices in the right column, such as the kind of a condition or a day in the calendar, are separate steps (`ItemPanel.step_started`, `MainWindow._on_step_started`)
- Creating and naming a project, group or entry is one step, moving or deleting several selected entries as well
- If the restored view refers to a hidden tab, the first visible tab is shown
- Opening another storage location clears all steps

## Multi Selection

- Only in the middle list: Ctrl+click adds or removes an entry, Shift+click selects a range, Ctrl+A selects all entries of the tab, Esc clears the selection
- A click into a selection keeps it until the mouse button is released, so the selection can be dragged. Releasing without dragging selects only the clicked entry
- Dragging a selected entry moves all selected open entries, into a group, out of a group or onto a project, in their order. The drag image shows their number
- Right-click on a selection: "Export …" (one file) and "Delete" (one confirmation)
- The Delete key deletes the selection or the selected entry
- With several entries selected, the right column shows only "3 todos selected"
- `MainWindow._selection` holds the selected ids in list order, `_selected[tab]` the entry shown on the right. `_render_items` restores the selection after every change
- Dragging with the mouse never selects a range, it always moves

## Maximized Right Column

- The icon at the top right of the right column enlarges it to the entire window and back. Tooltips: "Maximize" and "Normal size"
- `MainWindow._set_detail_maximized` hides the project column and the middle column and stores the splitter sizes in `_normal_sizes`
- The icon is visible only while an entry is shown. Without an entry, for example after deleting it, the normal view returns
- The state is not stored, the program always starts in the normal view

## Dialogs and Messages

- All dialogs use `show_message`, `confirm` and `ask`, never `QMessageBox`
- Layout like Windows message boxes: text with an icon in the content area, buttons right-aligned in a gray bar below. Windows adds the title bar "Project Desk" and the rounded corners
- Icons (`DialogIcon`): info for hints and questions such as import or moving data, warning for deleting, removing, restoring and closing without saving, error for failures
- "Cancel" is the default button of questions
- Short messages appear in a blue bar across the full window width, as high as the footers (`StatusBanner`). It slides in from the bottom and back after 2.5 seconds
- Messages appear only for results that are not visible otherwise: backup created, backup restored, todos created from a note, a hidden tab shown by an import, update available. Undo, redo and ordinary changes show no message

## Code Structure

Order in `project_desk.py`:

| Section | Content |
|---|---|
| Constants | Names, version, sizes, colors, item roles and types, texts per tab, backup, export and PDF settings |
| Helpers | `UiScale`, `px`, `ipx`, `Language`, `TRANSLATIONS`, `tr`, `PopupMenu`, `create_menu`, color palettes |
| Dialogs | `DialogIcon`, `create_message_dialog`, `add_dialog_button`, `show_message`, `confirm`, `ask` |
| `Theme` | Colors derived from the palette and the style sheet |
| Links and clipboard | `open_link`, `looks_like_address`, `link_title_from_url`, `parse_link_input`, `note_preview`, `package_paths`, `image_from_mime` |
| Data model | `Attachment`, `Todo`, `Note`, `Link`, `touch`, `item_title`, `contacts_note`, `ItemGroup`, `Project`, `AppData` |
| `Storage` | Loading, saving, attachments, note images, moving, backups, files of deleted entries |
| `item_payload`, `parse_item_payload` | Dragged entries as "type:id,id,id" |
| `ProjectDelegate` | Project rows: color dot, name, flag, count and the archive row |
| `ItemDelegate` | Cards of all types, group and done headers, add icon of groups, inline editor |
| `ProjectListWidget` | Left list: archive, right-click menu, drag and drop of projects and entries |
| `ItemListWidget` | Middle list: checkbox and icon clicks, groups, add icon, renaming, multi selection, right-click menu, drag and drop |
| `highlight_color`, `tabular_figures`, `is_bullet_list`, `link_ranges` | Helpers of the text editor |
| Update notice | `version_numbers`, `is_newer_version`, `UpdateState`, `UpdateChecker` |
| `TitleEdit`, `ElidedLabel`, `DropZone`, `StatusBanner`, `RichTextEdit`, `DescriptionEditor` | Text editing with formats, sizes, highlight and lists, links, inline images, editor menu, toolbar, attachment drop zone, blue bar |
| `ScaledImage`, `ImageViewer`, `AttachmentCard` | Attachments with preview of images and PDF files |
| Icon functions | `create_..._icon`, line icons drawn with `create_line_icon`, `add_badge` for the blue dot |
| Formatting | `backup_label`, `format_date`, `iso_date`, `parse_condition_date`, `format_condition_date`, `todo_condition`, `format_timestamp`, `count_text`, `entries_text`, `format_size` |
| Export package | `PackageError`, `package_files`, `write_package`, `ImportPackage` |
| `write_note_pdf` | PDF export of a note |
| `ItemPanel` | Base of the right column: title, maximize icon, content, footer with dates |
| `TodoPanel`, `NotePanel`, `LinkPanel` | Right column per tab. `TodoPanel` holds condition, description and attachments |
| `TabBar` | Tabs of the middle column |
| `InputFilter` | Ctrl+V for attachments and note images, Ctrl and mouse wheel for zoom |
| `MainWindow` | Layout, rendering, menus, actions, export, import, undo, backups, settings, saving |
| Startup | `choose_folder`, `open_initial_storage`, `instance_server_name`, `send_to_running_instance`, `InstanceServer`, `main` |

## User Interface and Design Rules

These decisions are fixed.

General:
- Look and feel of Microsoft Outlook, clean and professional
- Only what a project needs. No contacts, they belong in Outlook
- Actions are in right-click menus. Hovering only highlights and shows no icons
- Always visible in the lists: checkbox and set flag of todos, open icon of links, add icon of group headers. A click on a set flag removes it
- The header of the right column shows the title and the maximize icon, no other buttons
- Renaming by double-click or through "Rename" in the right-click menu
- Deleting always asks through `confirm` (warning icon, buttons "Delete" and "Cancel")
- Questions with more than two answers use `ask`
- Menus are always created with `create_menu`, for rounded corners and submenus next to their parent. Menu entries have line icons where available
- Icons are line icons drawn with `create_line_icon`, no emojis and no Qt standard icons. Only the dialog icons info, warning and error are filled, as in Windows
- Buttons show an icon with a tooltip instead of text. The only exception is "Settings" at the bottom left
- The "Settings" button holds mode, language, zoom, tabs, storage location, backups and the version

Right-click menus:
- Project: Rename, Color, Archive or Restore, Export, Delete. The general project has only Color and Export
- Empty space in the project list: New project, Import
- Several selected entries: Export, Delete
- Todo: Flag or Remove flag (open todos only), Export, Delete
- Note: Export as PDF, Export, Delete
- Link: Open, Copy address, Export, Delete
- Group header: Rename, Export, Delete
- Empty space in the middle list: New group, Import. The list always ends with empty space (`KIND_SPACER` row)
- Text editors: own German or English menu with undo, redo, cut, copy, paste and select all. On a link also "Open link" and "Copy link", in notes also "Turn into todo" while the todo tab is visible

Projects:
- No icons, a color dot per project from `PROJECT_COLORS`
- « collapses the project column to a narrow strip with » and the settings icon
- Projects are reordered by drag and drop and archived by dropping them onto the archive row

Middle list:
- Entries without a group first, then the groups with a collapsible header, add icon and count
- A click on a group header collapses or expands it, a double-click renames it
- The add icon of a group creates an entry in that group and opens its name for editing. Enter saves and opens the next one, in the notes tab Enter continues in the note text. Esc or an empty name removes the new entry
- The inline editor has the same height for all entry types and never covers the second line
- Drag and drop sorts entries, moves them into another group (also onto a collapsed group header) or onto a project
- Group headers can be dragged to change the order of groups
- New todos and links are added at the end, new notes at the top
- Enter in the empty note field creates a note named with today's date
- A pasted address in the link field creates a link named after its host
- Notes and links have a large round icon on the left. On a selected card the circle is white, in dark mode dark
- Group headers have a highlight band with space around the add icon (`SECTION_BAND_PADDING`)
- The open icon of links is vertically centered on the card
- The scroll bar keeps a gap to the cards (style sheet of `QListWidget#itemList`). The mouse wheel scrolls in small steps (`LIST_SCROLL_STEP`, scaled with the zoom)

Colors:
- Projects: hover light blue, selected gray, no accent bar
- Cards: hover light blue with a blue accent bar on the left, selected darker blue, also for every entry of a multi selection
- Flagged todos: yellow background and red title, darker yellow when selected
- The icons on the right of todo cards align to the right edge: the attachment count at the edge, the flag to its left, or the flag at the edge without attachments. No space is reserved for hidden icons

Text editing:
- Toolbar (`DescriptionEditor`) for todo descriptions, notes and link notes: bold, italic, underline, strikethrough | font size, highlight | bullet list, numbered list. Thin lines separate the groups. The toolbar never widens the column (size policy `Ignored`)
- Font sizes are four steps relative to the editor font: Small, Normal, Large, Extra large (`FONT_SIZE_STEPS`). They are stored as `FontSizeAdjustment` (-1, 0, 1, 2), in the HTML as `font-size:small`, `large` and `x-large`, and follow the zoom. Explicit point sizes and font families are removed
- Highlight is a background in `HIGHLIGHT_LIGHT` or `HIGHLIGHT_DARK` (`highlight_color`). When text is loaded, every background takes the color of the current mode
- Bullet lists use `ListStyleUndefined` and are painted by `RichTextEdit.paintEvent`: dot, ring and square per level. Numbered lists use `ListDecimal` and are painted by Qt. Other list styles from older or pasted text are converted to these two
- Numbered lists use digits of equal width (`tabular_figures`, OpenType feature `tnum`), so the numbers line up. The editor applies this to the document font, the PDF only to the list numbers, because Qt's PDF output loses the text of digits with this feature
- Tab and Shift+Tab move list lines one level in or out (`RichTextEdit.focusNextPrevChild`, `change_list_level`), up to `LIST_MAX_INDENT` levels. A line joins the list of its new level above it, so numbering continues. Outside lists Tab moves the focus
- The list buttons create a list, remove a list of the same kind or switch the selected lines to the other kind
- Format changes across several fragments are collected first and applied afterwards. Changing formats while iterating the fragments of a block crashes when Qt merges fragments
- A dash or asterisk followed by a space at the start of a line starts a bullet list
- `RichTextEdit` paints the placeholder, which an empty bullet also hides
- Web addresses, `www.` addresses and network paths become links while typing (`LINK_PATTERN`). A click opens them
- Pasted text is inserted without foreign fonts and colors
- Images in notes get a line of their own with space above and below and a thin frame, are scaled to the note width and open large on double-click
- Lines turned into todos get a check mark at the start and are not taken over twice

PDF export of notes:
- A4 at 300 dpi, 20 mm margins, title and creation date at the top, "Page x of y" in the footer
- `write_note_pdf` lays out the pages. Images get explicit sizes and never exceed the page width or 90 % of the page height
- Bullets become disc, circle and square per level (`PDF_BULLET_STYLES`), highlight is printed in `HIGHLIGHT_LIGHT`, the indent per list level is `PDF_LIST_INDENT`
- The root frame has a small top and bottom margin (`PDF_PAGE_GAP_INCH`). Without it the first pixel row of an image on the next page appears at the bottom of a page

## Translations

- The user interface is German and English, German is the default
- Every visible text uses `tr("German text")`, the German text is the key
- Placeholders: `tr("ToDo \"{title}\" löschen?", title=title)`
- Every new text needs its English version in `TRANSLATIONS`
- A language change rebuilds the main window (`MainWindow._set_language`), so texts are set while building the window

## Zoom

- All pixel sizes use `px(value)` (float) or `ipx(value)` (integer)
- Fonts follow the application font, headings use `header_font`
- After a zoom change `MainWindow._apply_zoom` updates the sizes and reapplies the style sheet, so all widgets take the new font
- New widgets with fixed sizes must be added to `_apply_zoom` or to their own `apply_zoom`

## Code Style

- PEP 8: classes in PascalCase, functions and variables in snake_case, private members start with `_`
- Type hints for parameters and return values
- Explicit boolean checks, for example `if todo.done is False`
- Comments in English above the code, starting with a capital letter, without a trailing period. Comments and tooltips describe only what something is or does, without reasoning
- Fixed values as constants at the top of the file
- Plain loops instead of nested one-liners

## Testing

The user interface can be tested on Linux in offscreen mode and saved as images:

```bash
pip install PySide6
QT_QPA_PLATFORM=offscreen python3 test_script.py
```

A test script imports `project_desk`, creates a `MainWindow` with a temporary `Storage` and its own `QSettings` file, calls actions directly (for example `_add_item`, `_create_item`, `_on_item_dropped`, `_on_project_dropped`, `_set_project_archived`, `_export_section`, `import_file`, `undo`, `redo`, `_restore_backup`, `_set_tab_enabled`, `_set_detail_maximized`) and saves screenshots with `window.grab().save(...)`. Dialogs are skipped by replacing `project_desk.confirm`, `project_desk.ask`, `project_desk.show_message` and `QFileDialog.getSaveFileName`. Multi selection is tested with `QTest.mouseClick` and `ControlModifier` or `ShiftModifier` on the list viewport. Right-click menus are opened by sending a `QContextMenuEvent` to the list viewport and read through `QApplication.activePopupWidget()`. `docs/manual/make_screenshots.py` is a complete example.

Check on Windows after related changes, since offscreen mode cannot show them:
- drag and drop with the mouse, also of `.pdesk` files from Explorer
- rounded menu corners and window behavior
- "Same as Windows" while Windows is in dark mode
- pasting screenshots from the Snipping Tool into notes
- double-clicking a `.pdesk` file, with and without a running instance
- title bar and rounded corners of dialogs
- the animation of the blue bar and scrolling with the mouse wheel
- updating an existing installation
- the calendar of conditions and the change of day while the program stays open
- the update notice in the company network

## Working on Change Requests

1. For several or larger requests, first a short concept: current state and planned change per item
2. If something is unclear, ask one targeted question instead of guessing
3. Implement and test in offscreen mode
4. Show screenshots before releasing
5. After approval, commit to `main` and run the workflow Release
6. Summarize the changes per file, class and method
7. Increase `APP_VERSION` and extend the version history for every release

## Known Limitations

- Groups have one level and are separate per tab
- A storage folder must not be used by several people at the same time, there is no locking or synchronization. Sharing works through `.pdesk` files
- Undo steps are lost when the program closes
- Data of version 2 cannot be opened with version 1.x
- No search
- The installer is not signed

## Version History

### 2.3.1
- The program is named "Project Desk" in the window, dialogs, start menu, installer and documentation
- The condition appears to the right of the todo title, so the card keeps its height
- Choosing a condition no longer moves the content of the right column
- Installation notes explain how to unblock the downloaded setup

### 2.3.0
- Notice of new versions: once per start Project Desk checks GitHub for a newer version. A blue bar reports it once, the settings icon shows a blue dot and the version line in the settings opens the download page

### 2.2.0
- Todos can have a condition: "Until" for a deadline or "From" for the earliest start, with a date or a text
- Dates can be typed, for example 14.11., or selected in a calendar
- The condition appears below the todo title, red when a deadline is today or past, blue when a start date is reached
- The cards follow the date while the program stays open
- Selecting another entry starts a new undo step for typing in the right column

### 2.1.0
- Text formatting: strikethrough, four font sizes, highlight and numbered lists in addition to bold, italic, underline and bullet lists
- Tab and Shift+Tab move list lines one level in or out, numbering continues
- The numbers of numbered lists line up, also in the PDF export
- Highlight follows light and dark mode. The PDF export shows list levels, numbers and highlight
- Checking a todo removes its flag, done todos cannot be flagged
- Flag and attachment count align to the right edge of todo cards
- Releases are built and published by the GitHub workflow Release

### 2.0.0
- New name ProjectDesk with a new icon, existing ToDo installations and settings are taken over
- Projects instead of groups and subgroups, with the fixed project "General" and a color dot per project
- Tabs for todos, notes and links, each with optional groups. Tabs can be hidden, with one tab the tab row disappears
- Notes with inline images, PDF export and "Turn into todo"
- Links with address and note for web pages, files, folders and network paths
- Maximizable right column
- Right-click menus instead of icons on hover
- Add icon on every group header
- Created and changed date in the footer of every entry
- Export and import of entries, groups and projects as `.pdesk` files, also by double-click in Explorer
- Automatic backups with restore, backups before import, moving and restoring
- Undo and redo with Ctrl+Z and Ctrl+Y for every change
- Multi selection with Ctrl, Shift and Ctrl+A to move, export and delete several entries
- Dialogs in Windows style with info, warning and error icons, short messages in a blue bar
- Moving the data to another folder
- Files of deleted entries are kept for undo and backups
- New PDF export with page numbers and correctly scaled images
- Smoother scrolling and more space between the cards and the scroll bar
- Collapsible project column, collapsed for new users
- Renaming entries by double-click in the list
- Clickable links in all text fields, "- " starts a bullet list
- Collapsible "Done" section
- Automatic conversion of version 1 data with a backup copy
- User manual as PDF, generated by scripts in `docs/manual`

### 1.2.0
- Version information in the settings menu
- Version number defined only in `APP_VERSION`, `build.bat` passes it to the installer
- Build script, installer, README and developer documentation in English
- Repository prepared for GitHub with README, `.gitignore` and screenshot
- Divider between the attachment header and its preview
- Attachment buttons as icons instead of text
- First version shared with colleagues

### 1.1.0
- Installer with Inno Setup, application icon
- Outlook style, light and dark mode
- Subgroups, archive, drag and drop for groups and todos
- Flags, formatted description, attachments with preview
- Settings with mode, language (German, English), zoom and storage location

### 1.0.0
- First version: groups, todos, checkboxes, sorting, attachments
