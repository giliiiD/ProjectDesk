# ProjectDesk Developer Documentation

This is the project documentation of ProjectDesk. It is written so that a new chat or a new developer can get into the project quickly and extend it. Start with "Quick Start for a New Chat".

## Quick Start for a New Chat

Provide these files together with the change request:

| Change | Files to provide |
|---|---|
| Program features and user interface | `DEVELOPMENT.md`, `project_desk.py` |
| Build or installer | additionally `build.bat`, `ProjectDesk.iss`, `requirements.txt` |
| User manual or README screenshot | additionally `docs/manual/make_screenshots.py`, `docs/manual/build_manual.py` |

The program in five sentences:
1. Everything is in `project_desk.py`, ordered as described in "Code Structure".
2. The data model are dataclasses (`Todo`, `Note`, `Link`, `ItemGroup`, `Project`) inside `AppData`. `Storage` loads and saves them as `data.json` in the storage folder.
3. `MainWindow` builds three columns: projects (`ProjectListWidget`), entries of the open tab (`ItemListWidget` painted by `ItemDelegate`) and the details of the selected entry (`TodoPanel`, `NotePanel`, `LinkPanel`).
4. After a change the window renders again from the data: `_render_all` calls `_render_projects`, `_render_header`, `_render_input`, `_render_items` and `_render_detail`.
5. Every change of the data first calls `_checkpoint()` for undo and then `_schedule_save()`.

Checklist for a new feature:
- Call `_checkpoint()` before the data changes and `_schedule_save()` after it
- Read new data fields with a default value in `from_dict`, so older files keep working
- Every visible text through `tr("German text")` with an English entry in `TRANSLATIONS`
- Pixel sizes through `px` or `ipx`, fixed values as constants at the top of the file
- Menus through `create_menu`, icons through `create_line_icon`, dialogs through `show_message`, `confirm` and `ask`
- Keep the rules in "User Interface and Design Rules"
- Test in offscreen mode (see "Testing") and show screenshots before delivering
- If the visible behavior changes, update the user manual and this file, and extend the version history

Where to start for typical changes:

| Change | Place in the code |
|---|---|
| New field of an entry | Dataclass (`create`, `from_dict`, `to_dict`), the panel of the right column, `ItemDelegate` if it shows in the list |
| New entry in a right click menu | `MainWindow._show_item_menu` for entries, groups and free space, `MainWindow._show_project_menu` for projects |
| New setting | `MainWindow._fill_settings_menu`, stored in `QSettings` (see "Data Storage") |
| New tab type | `ITEM_TYPES` and the dictionaries per item type in the constants, dataclass, panel, `ItemDelegate`, export and import |
| Appearance of cards and group headers | `ItemDelegate` and the constants for sizes |
| Colors | `create_palette` and `Theme` |

## Purpose

ProjectDesk is a Windows application for project based work, visually based on Microsoft Outlook. Until version 1.2.0 it was called ToDo. It is used next to Outlook, Teams and the browser and only holds what belongs to a project: todos, notes and links.

- Projects on the left, each with a color dot, plus the fixed project "General" and an archive
- Every project has three tabs: todos, notes and links, each with optional groups. Tabs can be hidden in the settings
- List in the middle, sortable by drag and drop, details of the selected entry on the right, the right column can be maximized
- Todos with a condition: until or from, as a date or as a text
- Formatted text with font sizes, highlight, bullet and numbered lists in all text fields
- Notes with inline images, export as PDF, lines can be turned into todos
- Entries, groups and whole projects can be exported as `.pdesk` files and imported by colleagues
- Automatic backups, undo and redo for every change
- Light and dark mode, zoom, German and English user interface
- Distributed as a regular Windows program with an installer, no administrator rights needed

## Project Files

| File | Content |
|---|---|
| `project_desk.py` | The complete program in a single file |
| `build.bat` | Builds the program and the installer |
| `requirements.txt` | Python packages: PySide6, pyinstaller |
| `ProjectDesk.iss` | Installer script for Inno Setup |
| `projectdesk.ico` | Application icon (desk with a folder on a blue square) |
| `README.md` | Start page of the repository: short description, installation, manual, build, development, version, author |
| `DEVELOPMENT.md` | This file |
| `docs/screenshot.png` | Screenshot shown in the README, made by `make_screenshots.py` |
| `docs/ProjectDesk_User_Manual.pdf` | User manual for colleagues, in English, made by `build_manual.py` |
| `docs/manual/make_screenshots.py` | Screenshots with neutral example data for the manual and the README |
| `docs/manual/build_manual.py` | Text of the user manual and the PDF build |
| `.gitignore` | Keeps build output and personal data out of the repository |
| `.github/workflows/release.yml` | GitHub workflow Release: builds the installer on Windows and publishes the release |
| `.github/release_notes.py` | Reads the version and the release notes for the workflow |

Build output (`installer\`, `build\`, `dist\`, `*.spec`, `__pycache__\`, `docs\manual\build\`) is never committed. The installer is published as a GitHub release instead, built by the workflow Release. `.gitignore` also keeps personal data (`data.json`, `data_v1_backup.json`, `attachments\`, `images\`, `backups\`) out of the repository, in case the storage folder is the project folder.

Screenshots in the repository and in the manual only show neutral example content, never real projects.

## Building and Distributing a New Version

1. Increase the constant `APP_VERSION` in `project_desk.py`. `build.bat` reads it and passes it to the installer. Also update the version line at the end of `README.md`.
2. Add a section `### <version>` to the version history at the end of this file. Its lines become the description of the release. If the visible behavior changed, also update the user manual (see "User Manual").
3. Commit the changes to `main` on GitHub.
4. On GitHub open "Actions", choose "Release" and click "Run workflow". A pushed tag like `v2.1.0` starts it as well.
5. The workflow runs on a Windows machine of GitHub: it checks that the version history has a section for `APP_VERSION` and that no release of that version exists, installs Inno Setup, runs `build.bat` and publishes the release "ProjectDesk <version>" with the tag `v<version>`, `ProjectDesk_Setup.exe` and `docs/ProjectDesk_User_Manual.pdf`. If a step fails, nothing is published.
6. Colleagues download the installer from the latest release and install it over the old version, their data is kept. They do not need Python.

Local build for testing: run `build.bat`. Requirements:
- Python 3 (tested with 3.13), with "Add to PATH" enabled during setup
- Inno Setup 6 or 7, "Install for me only" is sufficient
- Result: `installer\ProjectDesk_Setup.exe`

Build notes:
- PyInstaller works in `%LOCALAPPDATA%\ProjectDeskBuild`, not in the project folder. Reason: if the project folder is inside OneDrive, OneDrive locks the build folders and PyInstaller fails with "access denied".
- `build.bat` searches Inno Setup in the registry and in the default folders, versions 6 and 7 are found.
- `build.bat` ends with `pause`. The workflow runs it with the input from `NUL`, so it does not wait.
- The installer is not signed. Windows may show a SmartScreen warning on first start, which is confirmed with "More info" and "Run anyway".

## GitHub in the Browser

The repository is maintained on github.com in the browser, without Git or GitHub Desktop.

First upload:
1. On github.com click "New" next to the repositories. Name `ProjectDesk`, a short description, choose Private or Public, do not add a README, `.gitignore` or license, they already exist. Click "Create repository".
2. Click "uploading an existing file". Drag all files and the folder `docs` from the unpacked release package into the browser window, folders keep their structure.
3. Enter a commit message, for example "ProjectDesk 2.0.0", and click "Commit changes".

Updating files:
1. In the repository click "Add file" and "Upload files".
2. Drag the changed files into the window. Files with the same path are replaced. To replace files inside `docs`, open the folder `docs` first and upload there, or drag the whole folder `docs`.
3. Enter a commit message and click "Commit changes".
4. A file that no longer belongs to the project is opened in the browser and deleted through the menu "…" and "Delete file".

The browser accepts files up to 25 MiB per file. Never upload `data.json`, attachments, images or backups, the browser upload does not use `.gitignore`.

Creating a release:
1. In the repository click "Actions", choose "Release" on the left and click "Run workflow", then the green button "Run workflow".
2. After a few minutes the release appears under "Releases" with the installer and the user manual. A red mark in "Actions" means a step failed, its log shows why.
3. The link to the latest release can be shared with colleagues.

## User Manual

The manual and the README screenshot are generated, so they can be updated after every change of the user interface. Both scripts run on Linux without a display, for example in a Claude chat:

```bash
pip install PySide6 playwright pypdf Pillow
playwright install chromium
python3 docs/manual/make_screenshots.py
python3 docs/manual/build_manual.py
```

The font Inter must be installed. Results: `docs/screenshot.png` and `docs/ProjectDesk_User_Manual.pdf`. Intermediate files go to `docs/manual/build/`.

- `make_screenshots.py` creates neutral example data in `docs/manual/build/data` (projects "Website Relaunch", "Office Move", "Summer Event", archived "Trade Fair 2025"), opens the main window offscreen at zoom 2 and saves the screenshots. Right click menus are opened for real and painted onto the window image. It also writes `callouts.json` (positions of the numbered marks in the overview) and `crops.json` (areas cut out of screenshots, in window coordinates).
- `build_manual.py` holds the text of all chapters (`write_chapters`). It renders the cover and the body as HTML with Chromium to PDF, fills the page numbers of the table of contents in a second pass and merges both parts.
- New chapter: `manual.chapter(title, html)`. `flow=True` continues on the same page instead of a new one. Figures: `manual.figure(name, caption, marks, size, side)`, `side=True` floats the figure on the right of the text.
- After building, check every page as an image, for example with `pdftoppm -r 50 -png`.

## Technology

- Python 3, PySide6 (Qt 6), style "Fusion" with a custom color palette and style sheet
- PDF export through `QPdfWriter`, PDF preview of attachments through QtPdf
- PyInstaller in folder mode (`--onedir`), which starts faster than a single file executable
- Inno Setup installs per user to `%LOCALAPPDATA%\Programs\ProjectDesk`, with a start menu entry, an optional desktop shortcut and uninstallation through the Windows settings
- Never change the installer identifier (AppId) in `ProjectDesk.iss`. It is still the AppId of ToDo, so an existing ToDo installation is updated in its previous folder. `[InstallDelete]` removes the old `ToDo.exe` and the old shortcuts
- The installer registers the file type `.pdesk` for the current user (`[Registry]`, `ChangesAssociations=yes`). A double click on a `.pdesk` file starts `ProjectDesk.exe "<file>"`
- Only one ProjectDesk runs per Windows user. A second start sends its `.pdesk` argument through a `QLocalServer` named `ProjectDesk-<user name>` to the running window, which comes to the front and imports the file

## Data Storage

On first start each user chooses a storage folder, for example a folder in OneDrive.

- `data.json`: all projects with their todos, notes and links
- `attachments\`: copies of todo attachments, file name `<12 character id>_<original name>`
- `images\`: images inside notes, file name `<16 character id>.png`, referenced in the note HTML as `images/<name>.png`
- `backups\`: copies of `data.json`, file name `backup_<YYYY-MM-DD_HH-MM-SS>[-<counter>]_<reason>.json`
- `backups\files\`: attachments and note images of deleted entries, as long as a backup still needs them
- `data_v1_backup.json`: copy of the version 1 data, written once before the conversion

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

Data model rules:
- New fields are always read with a default value in `from_dict`, so older files keep working
- Exactly one project has `general` set. It is always first, cannot be renamed, archived or deleted, and shows the translated name "Allgemein" or "General"
- Groups are optional and exist separately per tab. `group_id` null means the entry is shown without group above the groups. Entries of a missing group are shown without group
- Deleting a group keeps its entries, they are shown without group
- Done todos are shown in the section "Done" at the end of the todo tab, they keep their group for when they are opened again
- Done todos are never flagged. Checking a todo removes its flag, it stays removed when the todo is opened again. `Todo.from_dict` drops the flag of done todos
- `condition` is empty, `until` or `from`. `condition_date` is an ISO date or empty, `condition_text` is used when there is no date. `Todo.from_dict` drops unknown kinds and invalid dates
- Projects without color get the next free color of `PROJECT_COLORS` in `AppData.normalize`, the general project starts gray
- `modified` is set through `touch` whenever the content of an entry changes in the right column. The footer shows "Created" and, if changed later, "Modified"
- Saving happens automatically 300 ms after every change, through a temporary file and `os.replace`

Conversion of older data:
- Version 1 (`AppData.from_groups`, only when `data.json` has `groups` and no `projects`): top level groups become projects with the same id, subgroups become todo groups of that project. Subgroups named "Allgemein" or "General" become todos without group. The first open top level group named "Allgemein" or "General" becomes the general project, otherwise a new one is created. Before the conversion `Storage.load` writes `data_v1_backup.json` once
- Contacts of early 2.0.0 test versions (`contacts` in a project): `contacts_note` turns them into a note "Kontakte" or "Contacts" at the top of the notes, one line per contact. Contact groups are dropped

Files of deleted entries:
- Deleting an entry never deletes its files right away, so undo can bring them back
- When the program closes, `Storage.collect_garbage` moves attachments and note images that `data.json` no longer references to `backups\files\`. Files there that no backup and no `data_v1_backup.json` references anymore are deleted
- `Storage.restore_files` moves files back from `backups\files\` after undo, redo or restoring a backup

Personal settings are stored in the registry under `HKEY_CURRENT_USER\Software\ToDo\ToDo` (QSettings, the old name is kept so existing settings stay): `dataFolder`, `geometry`, `splitter`, `archiveExpanded`, `colorMode`, `zoom`, `language`, `activeTab`, `enabledTabs`, `sidebarCollapsed`, `sidebarWidth`, `pdfFolder`, `autoBackup`, `exchangeFolder`. Without `sidebarCollapsed` the project column starts collapsed when only the general project exists. `enabledTabs` holds the visible tabs separated by spaces, for example `todo note`. Without it all tabs are visible.

## Todo Conditions

- A todo can have a condition: "Until" (`CONDITION_UNTIL`) for a deadline, "From" (`CONDITION_FROM`) for the earliest start
- Right column of a todo (`TodoPanel`): the row "Condition" with a button for the kind (None, Until, From), a field for a date or a text and a calendar icon. With the kind None the field and the calendar are hidden, choosing None clears date and text
- The field takes a date or any text (`parse_condition_date`): `14.11.2026`, `14.11.26`, `14.11.`, `14.11` and `2026-11-14` are dates, everything else is stored as text. A date without year more than half a year ago (`CONDITION_NEXT_YEAR_DAYS`) means next year. When the field loses the focus, a date is shown in the date format of the language
- The calendar (`TodoPanel._show_calendar`) opens below its icon in the colors of the app, a click takes the day
- In the list the condition is the second line of the card (`todo_condition`): "Until 14.11.2026", "From design approval". Today, tomorrow and yesterday are written as words
- Colors (`STATE_ROLE`): red when an "Until" date is today or past, blue when a "From" date is reached, otherwise gray. Done todos and text conditions are always gray. The color is the only mark, there is no extra word
- `MainWindow._check_day` checks every minute (`DAY_CHECK_MS`) whether the date changed and updates the cards, also after the computer slept
- Choosing the kind and choosing a day in the calendar are undo steps of their own (`ItemPanel.step_started`), typing in the field is one step per entry

## Tabs Setting

- `Settings > Tabs` shows or hides todos, notes and links per user. Hidden tabs keep their data, nothing is deleted
- At least one tab stays visible, its menu entry is disabled while it is the last one
- With only one visible tab the tab row is hidden
- With the todo tab hidden, the counts and flags of the projects are not shown and notes have no "Turn into todo" (`NotePanel.todos_enabled`)
- An import into a hidden tab shows that tab again and says so in the message bar
- `MainWindow._enabled_tabs`, `_load_enabled_tabs`, `_set_tab_enabled`, `_apply_enabled_tabs`

## Backups

- `Settings > Backups`: "Automatic backup" (on by default), "Back up now", "Restore" with the list of backups, "Open folder"
- Automatic: once a day, before the first save of the day, the last saved `data.json` is copied, if no backup of that day exists yet
- Additionally before every import, before moving the data and before restoring a backup
- The 30 newest backups are kept (`BACKUP_KEEP`), older ones are deleted
- Restoring first backs up the current state, then loads the backup. It can be undone with Ctrl+Z
- Labels in the list: "Today 14:32", "Yesterday 09:10" or the date, plus the reason in brackets except for automatic backups

## Moving the Data

`Settings > Storage location > Move data …` copies `data.json`, `attachments`, `images`, `backups` and `data_v1_backup.json` to an empty folder, loads the copy as a check and only then removes the old files. The new folder must not be inside the old one and must not contain a `data.json`. "Open other storage location …" switches to a folder that already contains data, without moving anything.

## Export and Import

Export through the right click menu: an entry, several selected entries, a group or a whole project ("Export …"). The file is a ZIP archive with the extension `.pdesk`:

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
  "app_version": "2.0.0",
  "kind": "items | group | project",
  "item_type": "todo | note | link, null for a project",
  "name": "…",
  "created": 1762250000.0,
  "groups": [{"id": "…", "name": "…", "collapsed": false}],
  "items": [{"…": "entries as in data.json"}],
  "project": {"…": "only for kind project, structure as in data.json"}
}
```

Import:
- Through "Import …" in the right click menu of the free space in the project list or in the middle list, by dropping a `.pdesk` file on the window, or by a double click on the file in the Explorer
- Before importing, a dialog shows the content and the target. If entries already exist, it asks "Skip", "Replace" or "Cancel", otherwise "Import" or "Cancel"
- Entries and groups go into the active project, always into the tab of their type, independent of the open tab. The tab switches to the imported entries
- A project goes into a new project. If its id already exists, missing entries are added to that project. Name clashes get " (2)", " (3)" and so on
- Duplicates (`_find_duplicate`): same id in the target project, or links with the same address (case and a trailing slash ignored)
- Groups are matched by name, ignoring case. Missing groups are created
- Ids already used elsewhere get a new id. Attachments and note images get new file names
- Every entry is checked before anything changes. A damaged file, a file of a newer format version or an error during the import changes nothing and removes files that were already copied
- Missing files inside the package are listed in the result message, the entries are imported without them
- The result message lists imported, replaced and skipped entries, per project for a project import
- Packages of early 2.0.0 test versions with contacts: contacts inside a project package are ignored, a package of contacts or a contact group is rejected as damaged
- A backup is made before every import, and the import can be undone with Ctrl+Z
- The folder of the last export or import is remembered as `exchangeFolder`

## Undo and Redo

- Ctrl+Z undoes, Ctrl+Y or Ctrl+Shift+Z redoes, without a message
- Snapshot based: `MainWindow._checkpoint()` stores the whole data (`AppData.to_dict`) and the view (tab, selected entries) before a change. Every new change must call `_checkpoint` first
- 50 steps (`UNDO_LIMIT`). A new change clears the redo steps
- While a text field has the focus, Ctrl+Z and Ctrl+Y belong to the text field. Typing in the right column is one step per entry and field session (`ItemPanel.edit_started`, `_editing_key`). Showing another entry ends the session
- Choices in the right column, like the kind of a condition or a day in the calendar, are steps of their own (`ItemPanel.step_started`, `MainWindow._on_step_started`)
- Creating and naming a new project, group or entry is one step. Moving or deleting several selected entries is one step
- If the restored view points to a hidden tab, the first visible tab is shown
- Opening another storage location clears the steps

## Multi Selection

- Only in the middle list. Ctrl+click adds or removes an entry, Shift+click selects a range, Ctrl+A selects all entries of the tab, Esc clears the selection
- A plain click into a selection keeps it until the mouse is released, so the whole selection can be dragged. The release without dragging selects only that entry
- Dragging an entry of the selection takes all selected open entries along, into a group, out of a group or onto a project. Their order is kept. The drag image shows their number
- Right click on a selected entry: "Export …" (one file with all entries) and "Delete" (one question for all)
- The Delete key deletes the selection or the single selected entry
- With several selected entries the right column only shows "3 todos selected"
- `MainWindow._selection` holds the ids of the selected entries in list order, `_selected[tab]` the entry shown on the right. `_render_items` selects them again after every change
- Pressing the mouse and moving never selects a range, moving always drags

## Maximized Right Column

- The icon at the top right of the right column enlarges it to the whole window and back, tooltips "Maximize" and "Normal size"
- `MainWindow._set_detail_maximized` hides the project column and the middle column and stores the splitter sizes in `_normal_sizes` to restore them
- The icon is only visible while an entry is shown. Without an entry, for example after deleting it, the normal view comes back automatically
- The state is not stored, ProjectDesk always starts in the normal view

## Dialogs and Messages

- All dialogs go through `show_message`, `confirm` and `ask`, never through `QMessageBox`
- Layout like the message boxes of Windows: text with an icon in the content area, buttons right aligned in a gray bar below. Windows adds the title bar "ProjectDesk" and the rounded corners
- Icons (`DialogIcon`): info for hints and questions like import or moving the data, warning for deleting, removing, restoring and closing without saving, error for failures
- In questions "Cancel" is the default button
- Short messages appear in a blue bar over the full width of the window, as high as the footers (`StatusBanner`). It slides up from below and back down after 2.5 seconds
- Messages only for results that are not visible otherwise: backup created, backup restored, todos created from a note, a hidden tab shown by an import. No messages for undo, redo or ordinary changes

## Code Structure

Order inside `project_desk.py`:

| Section | Content |
|---|---|
| Constants | Sizes, colors, item roles, item types, texts per tab, backup, export and PDF settings, version number |
| Helpers | `UiScale`, `px`, `ipx`, `Language`, `TRANSLATIONS`, `tr`, `PopupMenu`, `create_menu`, color palettes |
| Dialogs | `DialogIcon`, `create_message_dialog`, `add_dialog_button`, `show_message`, `confirm`, `ask` |
| `Theme` | All colors derived from the palette, plus the style sheet |
| Links and clipboard | `open_link`, `looks_like_address`, `link_title_from_url`, `parse_link_input`, `note_preview`, `package_paths`, `image_from_mime` |
| Data model | `Attachment`, `Todo`, `Note`, `Link`, `touch`, `item_title`, `contacts_note`, `ItemGroup`, `Project`, `AppData` |
| `Storage` | Loading, saving, attachments, note images, moving, backups, files of deleted entries |
| `item_payload`, `parse_item_payload` | Dragged entries as "type:id,id,id" |
| `ProjectDelegate` | Paints a project row: color dot, name, flag, count, or the archive row |
| `ItemDelegate` | Paints the cards of all types and the group and done headers, the add icon of groups, inline rename editor |
| `ProjectListWidget` | Left list: archive toggling, right click menu, drag and drop for projects and items |
| `ItemListWidget` | Middle list: checkbox and icon clicks, group toggling, add icon, double click rename, multi selection, right click menu, drag and drop |
| `highlight_color`, `is_bullet_list`, `link_ranges` | Helpers of the text editor |
| `TitleEdit`, `ElidedLabel`, `DropZone`, `StatusBanner`, `RichTextEdit`, `DescriptionEditor` | Text editing with formats, sizes, highlight and lists, links, inline images, editor right click menu, formatting toolbar, attachment drop zone, blue message bar |
| `ScaledImage`, `ImageViewer`, `AttachmentCard` | Attachments with preview for images and PDF files |
| Icon functions | `create_..._icon`, all drawn as line icons through `create_line_icon` |
| Formatting | `backup_label`, `format_date`, `iso_date`, `parse_condition_date`, `format_condition_date`, `todo_condition`, `format_timestamp`, `count_text`, `entries_text`, `format_size` |
| Export package | `PackageError`, `package_files`, `write_package`, `ImportPackage` |
| `write_note_pdf` | PDF export of a note |
| `ItemPanel` | Base of the right column: title, maximize icon, content, footer with dates |
| `TodoPanel`, `NotePanel`, `LinkPanel` | Right column per tab, `TodoPanel` with condition, description and attachments |
| `TabBar` | Tabs of the middle column |
| `InputFilter` | Ctrl+V for attachments and note images, Ctrl + mouse wheel for zoom |
| `MainWindow` | Layout, rendering, menus, all actions, export, import, undo, backups, settings, saving |
| Startup | `choose_folder`, `open_initial_storage`, `instance_server_name`, `send_to_running_instance`, `InstanceServer`, `main` |

## User Interface and Design Rules

These decisions were made by the product owner and must be kept.

General:
- Look and feel like Microsoft Outlook, clean and professional
- As simple as possible, only what a project really needs. Contacts were removed on purpose, they are kept in Outlook
- Actions are in right click menus. No icons appear while hovering, hovering only highlights
- Always visible in the lists: checkbox and set flag of todos, open icon of links, add icon of group headers. A click on the set flag removes it
- The header of the right column shows the title and, on the right, the icon to maximize the column. No other buttons
- Rename by double click, or through "Rename" in the right click menu
- Deleting always asks for confirmation through `confirm` (warning icon, buttons "Delete" and "Cancel")
- Questions with more than two answers go through `ask`. Dialogs and messages are described in "Dialogs and Messages"
- Menus are always created through `create_menu`, so corners are rounded and submenus open next to the parent menu. Menu entries have line icons where an icon exists
- New icons are line icons drawn through `create_line_icon`, no emojis and no Qt standard icons. Only the info, warning and error icons of dialogs are filled like in Windows
- Buttons show icons with a tooltip instead of text. The only exception is the "Settings" button at the bottom left
- Settings live in the "Settings" button at the bottom left: mode, language, zoom, tabs, storage location, backups, version

Right click menus:
- Project: Rename, Color, Archive or Restore, Export, Delete. The general project only has Color and Export
- Free space in the project list: New project, Import
- Several selected entries: Export, Delete
- Todo: Flag or Remove flag (only open todos), Export, Delete
- Note: Export as PDF, Export, Delete
- Link: Open, Copy address, Export, Delete
- Group header: Rename, Export, Delete
- Free space in the middle list: New group, Import. The list always ends with free space (`KIND_SPACER` row)
- Text editors: own German or English menu with undo, redo, cut, copy, paste, select all. On a link additionally "Open link" and "Copy link", in notes additionally "Turn into todo" while the todo tab is visible

Projects:
- No icons, a color dot per project. Colors from `PROJECT_COLORS`
- The project column can be collapsed with « to a narrow strip with » and the settings icon
- Projects can be reordered by drag and drop and archived by dropping them on the archive row

Lists in the middle:
- Entries without group first, then the groups with collapsible header, add icon and count
- A click on a group header collapses or expands it, a double click renames it
- The add icon of a group creates an entry in that group and opens its name for editing in the list. Enter saves and opens the next one, in the note tab Enter continues in the note text. Esc or an empty name removes the new entry again
- The inline editor has the same height for every kind of entry and never covers the second line
- Drag and drop sorts, moves into another group (also onto a collapsed group header) or onto a project on the left
- Group headers can be dragged to change the order of the groups
- New todos are added at the end, new notes at the top, new links at the end
- Enter in the empty note field creates a note named with today's date
- A pasted address in the link field becomes a link named by its host
- Notes and links have a large round icon on the left. On a selected card the circle is white, in dark mode dark
- Group headers have a highlight band with space around the add icon (`SECTION_BAND_PADDING`)
- The open icon of links is vertically centered on the card
- The scroll bar has space to the cards (style sheet of `QListWidget#itemList`). The mouse wheel scrolls in small steps (`LIST_SCROLL_STEP`, scaled with the zoom)

Colors and highlighting:
- Projects on the left: hover light blue, selected gray, no accent bar
- Cards in the middle: hover light blue with a blue accent bar on the left, selected darker blue, also for every entry of a multi selection
- Flagged todos: yellow background, red title. Selected darker yellow
- Icons on the right of todo cards move together to the right edge: the attachment count at the edge and the flag left of it. Without attachments the flag sits at the edge. No space is reserved for icons that are not shown

Text editing:
- Toolbar (`DescriptionEditor`) for todo descriptions, notes and link notes: bold, italic, underline, strikethrough, then font size and highlight, then bullet list and numbered list. Thin lines separate the three groups. The toolbar never widens the column (size policy `Ignored`)
- Font sizes are four steps of the editor font: Small, Normal, Large, Extra large (`FONT_SIZE_STEPS`). They are stored as `FontSizeAdjustment` (-1, 0, 1, 2), in the HTML as `font-size:small`, `large` and `x-large`, and follow the zoom. Explicit point sizes and font families are always removed
- Highlight is a background in `HIGHLIGHT_LIGHT` or `HIGHLIGHT_DARK` (`highlight_color`). When a text is loaded, every background takes the color of the current mode
- Bullet lists use the style `ListStyleUndefined` and are painted by `RichTextEdit.paintEvent`: dot, ring and square per level. Numbered lists use `ListDecimal` and are painted by Qt. Other list styles from older or pasted text are converted to these two
- Numbered lists use digits of equal width (`tabular_figures`, OpenType feature `tnum`), so the numbers line up. In the editor this applies to the document font, in the PDF only to the list numbers, because Qt's PDF output loses the text of digits with this feature
- Tab and Shift+Tab move list lines one level in or out (`RichTextEdit.focusNextPrevChild`, `change_list_level`), up to `LIST_MAX_INDENT` levels. A line joins the list of its new level above it, so numbering continues. Outside lists Tab moves the focus
- The bullet and numbering buttons create a list, remove the list of the same kind or switch the selected lines to the other kind
- Format changes over several fragments are collected first and applied afterwards. Changing formats while iterating the fragments of a block crashes when Qt merges fragments
- A dash or star followed by a space at the start of a line starts a bullet list
- The placeholder is painted by `RichTextEdit` and is also hidden by an empty bullet
- Web addresses, `www.` addresses and network paths become links while typing (`LINK_PATTERN`). A click opens them
- Pasted text is inserted without foreign fonts and colors
- Images in notes get a line of their own with space above and below and a thin frame, are scaled down to the note width and open large on double click
- Lines turned into todos start with a check mark and are not taken over twice

PDF export of notes:
- A4 at 300 dpi, margins 20 mm, title and creation date at the top, "Page x of y" in the footer
- Pages are laid out by `write_note_pdf` itself, images get explicit sizes and never exceed the page width or 90 % of the page height
- Bullets become disc, circle and square per level (`PDF_BULLET_STYLES`), highlight is always printed in `HIGHLIGHT_LIGHT`, the indent per list level is `PDF_LIST_INDENT`
- The root frame has a small top and bottom margin (`PDF_PAGE_GAP_INCH`), otherwise the first pixel row of an image on the next page shows at the bottom of a page

## Translations

- The user interface supports German and English, German is the default
- Every visible text goes through `tr("German text")`. The German text is the key
- Placeholders work like this: `tr("ToDo \"{title}\" löschen?", title=title)`
- Every new text needs an entry with the English version in `TRANSLATIONS`
- When the language changes, the main window is rebuilt (`MainWindow._set_language`). Texts are therefore set while building the window and do not need live switching

## Zoom

- All pixel sizes go through `px(value)` (float) or `ipx(value)` (integer)
- Fonts follow the application font, headings use `header_font`
- After a zoom change `MainWindow._apply_zoom` updates the sizes and reapplies the style sheet, so every widget takes over the new font
- New widgets with fixed sizes must be added to `_apply_zoom` or to their own `apply_zoom`

## Code Style

- Python according to PEP 8: classes in PascalCase, functions and variables in snake_case, private members start with `_`
- Type hints for parameters and return values
- Explicit boolean checks, for example `if todo.done is False`
- Comments in English, above the code, starting with a capital letter and without a trailing period. Comments and tooltips only describe what something is or does, no reasoning
- Fixed values as constants at the top of the file, not scattered in the code
- Plain loops instead of nested one-liners

## Testing

Without Windows the user interface can be tested on Linux in offscreen mode and saved as images:

```bash
pip install PySide6
QT_QPA_PLATFORM=offscreen python3 test_script.py
```

In the test script import `project_desk`, create a `MainWindow` with a temporary `Storage` and its own `QSettings` file, call actions directly (for example `_add_item`, `_create_item`, `_on_item_dropped`, `_on_project_dropped`, `_set_project_archived`, `_export_section`, `import_file`, `undo`, `redo`, `_restore_backup`, `_set_tab_enabled`, `_set_detail_maximized`) and save screenshots with `window.grab().save(...)`. Dialogs can be skipped by replacing `project_desk.confirm`, `project_desk.ask`, `project_desk.show_message` and `QFileDialog.getSaveFileName`. Multi selection can be tested with `QTest.mouseClick` and `Qt.KeyboardModifier.ControlModifier` or `ShiftModifier` on the list viewport. Right click menus can be opened by sending a `QContextMenuEvent` to the list viewport and read through `QApplication.activePopupWidget()`. `docs/manual/make_screenshots.py` is a complete example.

Not testable in offscreen mode, check these on Windows after related changes:
- real drag and drop with the mouse, also of `.pdesk` files from the Explorer
- rounded menu corners and window behavior
- "Same as Windows" while Windows is in dark mode
- pasting screenshots from the Snipping Tool into notes
- double click on a `.pdesk` file, with and without a running ProjectDesk, and the window coming to the front
- title bar and rounded corners of dialogs
- the animation of the message bar and scrolling with the mouse wheel
- the update of an existing ToDo installation
- the calendar of conditions and the change of the day while ProjectDesk stays open

## Workflow for Change Requests

This way of working has proven itself:

1. For several or larger requests, first a short concept: current state and planned change per item
2. If something is unclear, ask exactly one targeted question instead of guessing
3. Implement and test in offscreen mode
4. Show screenshots before delivering a download
5. After approval, deliver a ZIP with all project files
6. Add a change overview: per change the file, class and method, followed by a code block with "before" and "after". For very large changes, a summary per class and the note to replace the whole file
7. For every new version increase `APP_VERSION` and extend the version history

## Known Limitations

- Groups are only one level deep and exist per tab
- Several people should not use the same storage folder at the same time, there is no locking and no synchronization. Sharing works through `.pdesk` files
- Undo steps are lost when the program closes
- Data of version 2 cannot be opened with version 1.x anymore
- No search yet
- The installer is not signed

## Version History

### 2.2.0
- Todos can have a condition: "Until" for a deadline or "From" for the earliest start, as a date or as a text
- Dates can be typed like 14.11. or picked in a calendar
- The condition is shown below the todo title, red when a deadline is today or past, blue when a start date is reached
- The cards follow the date while ProjectDesk stays open
- Showing another entry starts a new undo step for typing in the right column

### 2.1.0
- Text formatting with strikethrough, four font sizes, highlight and numbered lists, in addition to bold, italic, underline and bullet lists
- Tab and Shift+Tab move list lines one level in or out, numbering continues
- Numbers of numbered lists line up, also in the PDF export
- Highlight follows light and dark mode, the PDF export shows list levels, numbers and highlight
- Checking a todo removes its flag, done todos cannot be flagged
- Flag and attachment count move to the right edge of todo cards
- Releases are built and published by the GitHub workflow Release

### 2.0.0
- New name ProjectDesk with a new icon, existing ToDo installations and settings are taken over
- Projects instead of groups and subgroups, with the fixed project "General" and a color dot per project
- Tabs for todos, notes and links, each with optional groups. Tabs can be hidden in the settings, with one tab the tab row disappears
- Notes with inline images, PDF export and "Turn into todo" for lines
- Links with address and note for web pages, files, folders and network paths
- Right column can be maximized to the whole window
- Right click menus instead of icons while hovering
- Add icon on every group header for new entries directly in the group
- Created and modified date in the footer of every entry
- Export and import of entries, groups and projects as `.pdesk` files, also by double click in the Explorer
- Automatic backups with restore, backups before import, move and restore
- Undo and redo with Ctrl+Z and Ctrl+Y for every change
- Multi selection with Ctrl, Shift and Ctrl+A, to move, export and delete several entries at once
- Dialogs in the style of Windows with info, warning and error icon, short messages in a blue bar at the bottom
- Moving the data to another folder
- Files of deleted entries are kept for undo and backups
- New PDF export with page numbers and correctly scaled images
- Smoother scrolling and more space between the cards and the scroll bar
- Collapsible project column, collapsed for new users
- Rename todos and other entries by double click in the list
- Clickable links in all text fields, "- " starts a bullet list, placeholder hidden by empty bullets
- Collapsible "Done" section
- Automatic conversion of version 1 data with a backup copy
- User manual as PDF, generated from scripts in `docs/manual`

### 1.2.0
- Version information in the settings menu
- Version number only defined in `APP_VERSION`, `build.bat` passes it to the installer
- Build script, installer, readme and developer documentation in English
- Repository prepared for GitHub with README.md, .gitignore and screenshot
- Divider line between the attachment header and its preview
- Attachment buttons as icons (open with default program, remove) instead of text
- First version shared with colleagues

### 1.1.0
- Installer with Inno Setup, application icon
- Outlook style design, light and dark mode
- Subgroups, archive, drag and drop for groups and todos
- Flags, formatted description, attachments with preview
- Settings with mode, language (German, English), zoom and storage location

### 1.0.0
- First version: groups, todos, checkboxes, sorting, attachments
