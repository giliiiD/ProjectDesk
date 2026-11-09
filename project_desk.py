"""Project manager with todos, notes and links, groups, drag and drop, formatted text and attachments"""

from __future__ import annotations

import copy
import getpass
import http.client
import json
import math
import os
import re
import shutil
import sys
import threading
import time
import urllib.request
import uuid
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from PySide6.QtCore import QByteArray, QDate, QEasingCurve, QEvent, QItemSelectionModel, QLocale, QMarginsF, QMimeData, QObject, QPoint, QPointF, QPropertyAnimation, QRect, QRectF, QSettings, QSize, QSizeF, QStandardPaths, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDesktopServices,
    QAction,
    QActionGroup,
    QDrag,
    QFont,
    QFontMetrics,
    QFontMetricsF,
    QGuiApplication,
    QIcon,
    QImage,
    QKeyEvent,
    QKeySequence,
    QPageLayout,
    QPageSize,
    QPainter,
    QPainterPath,
    QPalette,
    QPdfWriter,
    QPen,
    QPixmap,
    QShortcut,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextDocumentFragment,
    QTextFormat,
    QTextImageFormat,
    QTextLayout,
    QTextLength,
    QTextListFormat,
    QTextOption,
    QTransform,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCalendarWidget,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTextEdit,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from PySide6.QtNetwork import QLocalServer, QLocalSocket

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    PDF_PREVIEW_AVAILABLE = True
except ImportError:
    PDF_PREVIEW_AVAILABLE = False


# Constants
APP_NAME = "ProjectDesk"
APP_TITLE = "Project Desk"
APP_VERSION = "2.3.1"
UPDATE_API_URL = "https://api.github.com/repos/giliiiD/ProjectDesk/releases/latest"
RELEASES_URL = "https://github.com/giliiiD/ProjectDesk/releases/latest"
UPDATE_CHECK_DELAY_MS = 3000
UPDATE_TIMEOUT_SECONDS = 10
APP_USER_MODEL_ID = "ProjectDesk.App"
SETTINGS_ORGANIZATION = "ToDo"
SETTINGS_APPLICATION = "ToDo"
ICON_FILE_NAME = "projectdesk.ico"
DATA_FILE_NAME = "data.json"
DATA_VERSION = 2
BACKUP_FILE_NAME = "data_v1_backup.json"
ATTACHMENT_FOLDER_NAME = "attachments"
IMAGE_FOLDER_NAME = "images"
BACKUP_FOLDER_NAME = "backups"
KEPT_FILES_FOLDER_NAME = "files"
BACKUP_KEEP = 30
BACKUP_TIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
BACKUP_FILE_PATTERN = re.compile(r"backup_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})(?:-(\d+))?_([a-z]+)\.json")
BACKUP_AUTOMATIC = "auto"
BACKUP_MANUAL = "manual"
BACKUP_IMPORT = "import"
BACKUP_MOVE = "move"
BACKUP_RESTORE = "restore"
BACKUP_REASON_TEXTS = {
    BACKUP_MANUAL: "manuell",
    BACKUP_IMPORT: "vor Import",
    BACKUP_MOVE: "vor Verschieben",
    BACKUP_RESTORE: "vor Wiederherstellen",
}
DATA_ENTRY_NAMES = (DATA_FILE_NAME, BACKUP_FILE_NAME, ATTACHMENT_FOLDER_NAME, IMAGE_FOLDER_NAME, BACKUP_FOLDER_NAME)
SAVE_DELAY_MS = 300
PDF_PREVIEW_HEIGHT = 520
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
INVALID_FILE_NAME_CHARACTERS = '<>:"/\\|?*'
LOAD_ERRORS = (OSError, ValueError, KeyError, TypeError, AttributeError)
QWIDGETSIZE_MAX = 16777215

BASE_FONT_SIZE = 10.0
HEADER_FONT_SIZE = 12.5
HEADER_HEIGHT = 62
COLUMN_PADDING = 16
FOOTER_HEIGHT = 48
ICON_SIZE = 16

SIDEBAR_WIDTH = 240
SIDEBAR_MIN_WIDTH = 170
SIDEBAR_RAIL_WIDTH = 48
TAB_SPACING = 22

GROUP_PADDING_H = 16
GROUP_PADDING_V = 9
GROUP_ICON_SPACING = 6

CARD_GAP = 6
CARD_PADDING_H = 12
CARD_PADDING_V = 10
CARD_RADIUS = 6.0
CHECK_SIZE = 18.0
CHECK_SPACING = 10.0
AVATAR_SIZE = 30.0
SUBTITLE_SPACING = 4.0
INLINE_EDIT_PADDING = 3
META_SPACING = 10.0
META_ICON_SPACING = 3.0
FOLDER_ICON_GAP = 6
SECTION_TOP = 18
SECTION_BOTTOM = 10
SECTION_BAND_PADDING = 8
SECTION_CHEVRON_LEFT = 12
SECTION_TEXT_LEFT = 24
LIST_END_SPACE = 56
LIST_SCROLL_STEP = 18

ID_ROLE = Qt.ItemDataRole.UserRole
COUNT_ROLE = Qt.ItemDataRole.UserRole + 1
KIND_ROLE = Qt.ItemDataRole.UserRole + 2
ARCHIVED_ROLE = Qt.ItemDataRole.UserRole + 3
EXPANDED_ROLE = Qt.ItemDataRole.UserRole + 4
GENERAL_ROLE = Qt.ItemDataRole.UserRole + 5
TYPE_ROLE = Qt.ItemDataRole.UserRole + 6
FLAGGED_ROLE = Qt.ItemDataRole.UserRole + 7
SECTION_ROLE = Qt.ItemDataRole.UserRole + 8
SUBTITLE_ROLE = Qt.ItemDataRole.UserRole + 9
TITLE_ROLE = Qt.ItemDataRole.UserRole + 10
TARGET_ROLE = Qt.ItemDataRole.UserRole + 11
TOOLTIP_ROLE = Qt.ItemDataRole.UserRole + 12
DONE_ROLE = Qt.ItemDataRole.UserRole + 14
COLOR_ROLE = Qt.ItemDataRole.UserRole + 15
STATE_ROLE = Qt.ItemDataRole.UserRole + 16
CONDITION_ROLE = Qt.ItemDataRole.UserRole + 17

KIND_PROJECT = "project"
KIND_ARCHIVE_HEADER = "archive_header"
KIND_ITEM = "item"
KIND_SECTION = "section"
KIND_DONE = "done"
KIND_SPACER = "spacer"

ITEM_TODO = "todo"
ITEM_NOTE = "note"
ITEM_LINK = "link"
ITEM_TYPES = (ITEM_TODO, ITEM_NOTE, ITEM_LINK)
ITEM_LISTS = {ITEM_TODO: "todos", ITEM_NOTE: "notes", ITEM_LINK: "links"}

CHEVRON_SIZE = 3.5
ACTION_SIZE = 24
ACCENT_BAR_WIDTH = 3.0
ACCENT_LIGHT = "#0f6cbd"
ACCENT_DARK = "#479ef5"
ACCENT_HOVER_LIGHT = "#ebf3fc"
ACCENT_SELECTED_LIGHT = "#cfe4fa"
FLAG_LIGHT = "#c4314b"
FLAG_DARK = "#f1707b"
FLAG_BACKGROUND_LIGHT = "#fff4ce"
FLAG_BACKGROUND_DARK = "#433519"
FLAG_SELECTED_LIGHT = "#fce59a"
FLAG_SELECTED_DARK = "#5a4721"
SUBMENU_GAP = 2
BULLET_INDENT = 18
BULLET_MARKERS = ("-", "*")
LIST_MAX_INDENT = 4
CONDITION_UNTIL = "until"
CONDITION_FROM = "from"
CONDITION_KINDS = (("", "Keine"), (CONDITION_UNTIL, "Bis"), (CONDITION_FROM, "Ab"))
CONDITION_OVERDUE = "overdue"
CONDITION_DUE = "due"
CONDITION_STARTED = "started"
CONDITION_NEXT_YEAR_DAYS = 183
CONDITION_SPACING = 12.0
CONDITION_MAX_SHARE = 0.45
DAY_CHECK_MS = 60000
TOOLBAR_SEPARATOR_HEIGHT = 16
TABULAR_FIGURES_FEATURE = "tnum"
FONT_SIZE_STEPS = (("Klein", -1, 0.8), ("Normal", 0, 1.0), ("Groß", 1, 1.2), ("Sehr groß", 2, 1.5))
HIGHLIGHT_LIGHT = "#ffe97a"
HIGHLIGHT_DARK = "#6b5a10"
PDF_BULLET_STYLES = (QTextListFormat.Style.ListDisc, QTextListFormat.Style.ListCircle, QTextListFormat.Style.ListSquare)
COUNT_SLOT_TEXT = "99"
TODO_MARK = "✓"
OBJECT_REPLACEMENT_CHARACTER = "￼"

PDF_FONT_SIZE = 10.0
PDF_TITLE_SIZE = 16.0
PDF_FOOTER_SIZE = 8.0
PDF_MUTED_COLOR = "#6b6b6b"
PDF_MARGIN_MM = 20.0
PDF_RESOLUTION = 300
PDF_FOOTER_HEIGHT_INCH = 0.35
PDF_IMAGE_MAX_HEIGHT = 0.9
PDF_PAGE_GAP_INCH = 0.04
PDF_LIST_INDENT = 22

ZOOM_STEPS = (0.8, 0.9, 1.0, 1.1, 1.25, 1.4, 1.6, 1.8, 2.0)
LANGUAGE_GERMAN = "de"
LANGUAGE_ENGLISH = "en"

COLOR_MODE_SYSTEM = "system"
COLOR_MODE_LIGHT = "light"
COLOR_MODE_DARK = "dark"

PROJECT_MIME_TYPE = "application/x-projectdesk-project-id"
ITEM_MIME_TYPE = "application/x-projectdesk-item"
SECTION_MIME_TYPE = "application/x-projectdesk-section-id"
ARCHIVE_TARGET = "archive"
DROP_BEFORE = "before"
DROP_AFTER = "after"
DROP_ONTO = "onto"

GENERAL_PROJECT_NAME = "Allgemein"
GENERAL_NAMES = ("Allgemein", "General")

PROJECT_COLORS = (
    ("Blau", "#0f6cbd"),
    ("Grün", "#107c10"),
    ("Orange", "#ca5010"),
    ("Lila", "#8764b8"),
    ("Türkis", "#038387"),
    ("Rot", "#d13438"),
    ("Pink", "#c239b3"),
    ("Gelb", "#c19c00"),
    ("Braun", "#8e562e"),
    ("Grau", "#7a7574"),
)
GENERAL_COLOR = "#7a7574"
DOT_SIZE = 10.0
IMAGE_MARGIN = 6

LINK_PATTERN = re.compile(r"(?:https?://|file:///?|www\.)[^\s<>\"]+|\\\\[^\s<>\"\\]+\\[^\s<>\"]*")
LINK_TRAILING_CHARACTERS = ".,;:!?)]}'\""
NOTE_IMAGE_PATTERN = re.compile(IMAGE_FOLDER_NAME + r"/[0-9a-f]+\.png")

DIALOG_TEXT_WIDTH = 340
DIALOG_ICON_SIZE = 32
DIALOG_BUTTON_WIDTH = 88
DIALOG_INFO = "info"
DIALOG_WARNING = "warning"
DIALOG_ERROR = "error"
DIALOG_INFO_COLOR = "#0f6cbd"
DIALOG_WARNING_COLOR = "#ffc83d"
DIALOG_WARNING_MARK_COLOR = "#1b1b1b"
DIALOG_ERROR_COLOR = "#c42b1c"
UNDO_LIMIT = 50
EXPORT_EXTENSION = ".pdesk"
EXPORT_FORMAT = "projectdesk-export"
EXPORT_FORMAT_VERSION = 1
EXPORT_CONTENT_NAME = "content.json"
EXPORT_FILES_PREFIX = "files/"
EXPORT_PROJECT = "project"
EXPORT_GROUP = "group"
EXPORT_ITEMS = "items"
IMPORT_SKIP = "skip"
IMPORT_REPLACE = "replace"
IMPORT_ADD = "add"
IMPORT_MISSING_LIMIT = 10
INSTANCE_SERVER_PREFIX = "ProjectDesk-"
INSTANCE_TIMEOUT_MS = 500
SINGULAR_TITLES = {
    ITEM_TODO: "ToDo",
    ITEM_NOTE: "Notiz",
    ITEM_LINK: "Link",
}
STATUS_DURATION_MS = 2500
STATUS_SLIDE_MS = 220
STATUS_COLOR = "#0f6cbd"
STATUS_TEXT_COLOR = "#ffffff"

TAB_TITLES = {
    ITEM_TODO: "ToDos",
    ITEM_NOTE: "Notizen",
    ITEM_LINK: "Links",
}

INPUT_PLACEHOLDERS = {
    ITEM_TODO: "Neues ToDo hinzufügen",
    ITEM_NOTE: "Neue Notiz hinzufügen",
    ITEM_LINK: "Neuen Link hinzufügen",
}

EMPTY_TEXTS = {
    ITEM_TODO: "Noch keine ToDos",
    ITEM_NOTE: "Noch keine Notizen",
    ITEM_LINK: "Noch keine Links",
}

COUNT_TEXTS = {
    ITEM_TODO: ("1 ToDo", "{count} ToDos"),
    ITEM_NOTE: ("1 Notiz", "{count} Notizen"),
    ITEM_LINK: ("1 Link", "{count} Links"),
}

DELETE_MESSAGES = {
    ITEM_TODO: "ToDo \"{title}\" löschen?",
    ITEM_NOTE: "Notiz \"{title}\" löschen?",
    ITEM_LINK: "Link \"{title}\" löschen?",
}

SECTION_ADD_TOOLTIPS = {
    ITEM_TODO: "Neues ToDo in dieser Gruppe",
    ITEM_NOTE: "Neue Notiz in dieser Gruppe",
    ITEM_LINK: "Neuer Link in dieser Gruppe",
}

ITEM_ACTION_TOOLTIPS = {
    "open": "Link öffnen",
}


# Helpers
def new_id() -> str:
    return uuid.uuid4().hex


def safe_file_name(name: str) -> str:
    cleaned = "".join("_" if character in INVALID_FILE_NAME_CHARACTERS else character for character in name).strip()
    return cleaned if cleaned else "Datei"


def local_files_from_mime(mime: Optional[QMimeData]) -> list[Path]:
    if mime is None or mime.hasUrls() is False:
        return []

    files: list[Path] = []
    for url in mime.urls():
        if url.isLocalFile() is False:
            continue
        path = Path(url.toLocalFile())
        if path.is_file():
            files.append(path)
    return files


def open_with_default_program(path: Path) -> None:
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def resource_path(name: str) -> Path:
    base_folder = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_folder / name


def mix_colors(first: QColor, second: QColor, amount: float) -> QColor:
    return QColor(
        round(first.red() + (second.red() - first.red()) * amount),
        round(first.green() + (second.green() - first.green()) * amount),
        round(first.blue() + (second.blue() - first.blue()) * amount),
    )


class UiScale:
    """Zoom factor for fonts, sizes and spacing"""

    factor = 1.0


class Language:
    """Current user interface language"""

    current = LANGUAGE_GERMAN


TRANSLATIONS = {
    "%d.%m.%Y": "%Y-%m-%d",
    "%d.%m.%Y, %H:%M": "%Y-%m-%d %H:%M",
    "Ab": "From",
    "Version {version} (Update verfügbar)": "Version {version} (update available)",
    "Update verfügbar, siehe Einstellungen": "Update available, see Settings",
    "Art der Bedingung": "Kind of condition",
    "Bedingung": "Condition",
    "Bis": "Until",
    "Datum auswählen": "Choose date",
    "Datum oder Text": "Date or text",
    "Keine": "None",
    "gestern": "yesterday",
    "heute": "today",
    "morgen": "tomorrow",
    "1 Eintrag gibt es schon.": "1 entry already exists.",
    "1 Link": "1 link",
    "1 Notiz": "1 note",
    "1 ToDo": "1 todo",
    "1 ToDo erstellt": "1 todo created",
    "Abbrechen": "Cancel",
    "Adresse": "Address",
    "Adresse kopieren": "Copy address",
    "Alle Daten nach\n{folder}\nverschieben?": "Move all data to\n{folder}?",
    "Alles auswählen": "Select all",
    "Allgemein": "General",
    "Als PDF exportieren": "Export as PDF",
    "Als ToDo übernehmen": "Turn into todo",
    "Anderen Speicherort öffnen …": "Open other storage location …",
    "Anhang \"{name}\" entfernen?": "Remove attachment \"{name}\"?",
    "Anhang entfernen": "Remove attachment",
    "Anhänge": "Attachments",
    "Anhänge hinzufügen": "Add attachments",
    "Archiv": "Archive",
    "Archivieren": "Archive",
    "archiviert": "archived",
    "Aufzählung": "Bullet list",
    "Nummerierung": "Numbered list",
    "Durchgestrichen": "Strikethrough",
    "Schriftgröße": "Font size",
    "Klein": "Small",
    "Normal": "Normal",
    "Groß": "Large",
    "Sehr groß": "Extra large",
    "Hervorheben": "Highlight",
    "Aus Notiz \"{title}\"": "From note \"{title}\"",
    "Ausschneiden": "Cut",
    "Automatisch sichern": "Back up automatically",
    "Backup erstellt": "Backup created",
    "Backup fehlgeschlagen:\n{error}": "Backup failed:\n{error}",
    "Backups": "Backups",
    "Beschreibung": "Description",
    "Bild konnte nicht gespeichert werden": "Image could not be saved",
    "Bitte einen Ordner wählen, in dem alle Daten gespeichert werden.\n\nEin Ordner in OneDrive wird automatisch gesichert.": "Please choose a folder for all your data.\n\nA folder in OneDrive is backed up automatically.",
    "Blau": "Blue",
    "Braun": "Brown",
    "{count} Einträge gibt es schon.": "{count} entries already exist.",
    "{entries} ersetzt": "{entries} replaced",
    "{entries} importiert": "{entries} imported",
    "1 Eintrag": "1 entry",
    "{count} Einträge": "{count} entries",
    "{entries} ausgewählt": "{entries} selected",
    "{entries} löschen?": "Delete {entries}?",
    "{entries} mit {count} Anhängen löschen?": "Delete {entries} with {count} attachments?",
    "{count} Links": "{count} links",
    "{count} Notizen": "{count} notes",
    "{count} offen": "{count} open",
    "{count} ToDos": "{count} todos",
    "{count} ToDos erstellt": "{count} todos created",
    "{entries} übersprungen, weil schon vorhanden": "{entries} skipped, already present",
    "Das Backup konnte nicht geladen werden:\n{error}": "The backup could not be loaded:\n{error}",
    "Datei nicht gefunden": "File not found",
    "Dateien hierher ziehen, klicken oder Strg+V": "Drop files here, click or Ctrl+V",
    "Daten verschieben …": "Move data …",
    "Der neue Speicherort darf nicht im bisherigen Ordner liegen.": "The new storage location must not be inside the current folder.",
    "Der Speicherort\n{folder}\nwurde nicht gefunden. Bitte einen Ordner wählen.": "The storage location\n{folder}\nwas not found. Please choose a folder.",
    "Die Datei ist keine Project-Desk-Datei oder beschädigt.": "The file is not a Project Desk file or it is damaged.",
    "Die Datei stammt aus einer neueren Version von Project Desk. Bitte Project Desk aktualisieren.": "The file comes from a newer version of Project Desk. Please update Project Desk.",
    "Die Daten in\n{folder}\nkonnten nicht geladen werden:\n{error}": "The data in\n{folder}\ncould not be loaded:\n{error}",
    "Die Daten in\n{folder}\nkonnten nicht geladen werden:\n{error}\n\nBitte einen anderen Ordner wählen.": "The data in\n{folder}\ncould not be loaded:\n{error}\n\nPlease choose another folder.",
    "Die Daten konnten nicht verschoben werden:\n{error}\n\nEs wurde nichts verändert.": "The data could not be moved:\n{error}\n\nNothing was changed.",
    "Die Daten liegen jetzt in\n{folder}": "The data is now stored in\n{folder}",
    "Die Daten liegen jetzt in\n{folder}\n\nFolgende alte Dateien konnten nicht gelöscht werden:\n{files}": "The data is now stored in\n{folder}\n\nThe following old files could not be deleted:\n{files}",
    "Die kopierten Daten sind unvollständig.": "The copied data is incomplete.",
    "Die letzten Änderungen konnten nicht gespeichert werden. Trotzdem schließen?": "The latest changes could not be saved. Close anyway?",
    "Diese Dateien fehlen in der Importdatei:": "These files are missing in the import file:",
    "Dunkel": "Dark",
    "Einfügen": "Paste",
    "Einstellungen": "Settings",
    "Entfernen": "Remove",
    "Erledigt": "Done",
    "Ersetzen": "Replace",
    "Erstellt am {date}": "Created {date}",
    "Export fehlgeschlagen:\n{error}": "Export failed:\n{error}",
    "Exportieren": "Export",
    "Exportieren …": "Export …",
    "Exportiert nach\n{path}\n\nGröße: {size}": "Exported to\n{path}\n\nSize: {size}",
    "Farbe": "Color",
    "Fett (Strg+B)": "Bold (Ctrl+B)",
    "Folgende Anhänge konnten nicht hinzugefügt werden:": "The following attachments could not be added:",
    "Geändert am {date}": "Changed {date}",
    "Gelb": "Yellow",
    "Gestern": "Yesterday",
    "Grau": "Gray",
    "Grün": "Green",
    "Gruppe": "Group",
    "Gruppe \"{name}\" löschen?": "Delete group \"{name}\"?",
    "Gruppe \"{name}\" löschen? Die {count} Einträge bleiben ohne Gruppe erhalten.": "Delete group \"{name}\"? The {count} entries are kept without a group.",
    "Gruppe \"{name}\": {count}": "Group \"{name}\": {count}",
    "Hell": "Light",
    "Heute": "Today",
    "Im Explorer öffnen": "Open in Explorer",
    "Im gewählten Ordner liegen bereits Daten. Bitte einen leeren Ordner wählen oder ihn über \"Anderen Speicherort öffnen …\" öffnen.": "The chosen folder already contains data. Please choose an empty folder or open it through \"Open other storage location …\".",
    "Import fehlgeschlagen:\n{error}\n\nEs wurde nichts verändert.": "Import failed:\n{error}\n\nNothing was changed.",
    "Importieren": "Import",
    "Importieren …": "Import …",
    "Inhalt: {summary}": "Content: {summary}",
    "Jetzt sichern": "Back up now",
    "Kein Link ausgewählt": "No link selected",
    "Kein ToDo ausgewählt": "No todo selected",
    "Keine Backups vorhanden": "No backups yet",
    "Keine Notiz ausgewählt": "No note selected",
    "Keine Vorschau verfügbar": "No preview available",
    "Klicken zum Vergrößern": "Click to enlarge",
    "Kontakte": "Contacts",
    "Maximieren": "Maximize",
    "Normale Größe": "Normal size",
    "Reiter": "Tabs",
    "Reiter eingeblendet: {tabs}": "Tabs shown: {tabs}",
    "Kopieren": "Copy",
    "Kursiv (Strg+I)": "Italic (Ctrl+I)",
    "Lila": "Purple",
    "Link": "Link",
    "Link \"{title}\" löschen?": "Delete link \"{title}\"?",
    "Link kopieren": "Copy link",
    "Link öffnen": "Open link",
    "Links": "Links",
    "Löschen": "Delete",
    "manuell": "manual",
    "Markieren": "Flag",
    "Markierung entfernen": "Remove flag",
    "Mit dem Standardprogramm öffnen": "Open with the default program",
    "Modus": "Mode",
    "\"{name}\" kann nicht importiert werden:\n{error}": "\"{name}\" cannot be imported:\n{error}",
    "Neue Gruppe": "New group",
    "Neue Notiz hinzufügen": "Add new note",
    "Neue Notiz in dieser Gruppe": "New note in this group",
    "Neuen Link hinzufügen": "Add new link",
    "Neuen Speicherort wählen": "Choose new storage location",
    "Neuer Link in dieser Gruppe": "New link in this group",
    "Neues Projekt": "New project",
    "Neues ToDo hinzufügen": "Add new todo",
    "Neues ToDo in dieser Gruppe": "New todo in this group",
    "Noch keine Links": "No links yet",
    "Noch keine Notizen": "No notes yet",
    "Noch keine ToDos": "No todos yet",
    "Notiz": "Note",
    "Notiz \"{title}\" löschen?": "Delete note \"{title}\"?",
    "Notiz schreiben, Bilder mit Strg+V einfügen": "Write a note, paste images with Ctrl+V",
    "Notizen": "Notes",
    "Öffnen": "Open",
    "ohne Titel": "untitled",
    "Orange": "Orange",
    "Ordner öffnen": "Open folder",
    "PDF konnte nicht gespeichert werden:\n{error}": "The PDF could not be saved:\n{error}",
    "PDF-Dateien (*.pdf)": "PDF files (*.pdf)",
    "Pink": "Pink",
    "Project-Desk-Dateien (*.pdesk)": "Project Desk files (*.pdesk)",
    "Projekt": "Project",
    "Projekt \"{name}\"": "Project \"{name}\"",
    "Projekt \"{name}\" löschen?": "Delete project \"{name}\"?",
    "Projekt \"{name}\" mit allen ToDos, Notizen und Links löschen?": "Delete project \"{name}\" with all todos, notes and links?",
    "Projekte": "Projects",
    "Projektspalte ausklappen": "Expand project column",
    "Projektspalte einklappen": "Collapse project column",
    "Rot": "Red",
    "Rückgängig": "Undo",
    "Seite {page} von {count}": "Page {page} of {count}",
    "Speichern fehlgeschlagen:\n{error}": "Saving failed:\n{error}",
    "Speicherort": "Storage location",
    "Speicherort wählen": "Choose storage location",
    "Sprache": "Language",
    "Stand vom {date} wiederhergestellt": "State of {date} restored",
    "Stand vom {date} wiederherstellen?\n\nDer aktuelle Stand wird vorher gesichert.": "Restore the state of {date}?\n\nThe current state is backed up first.",
    "Titel": "Title",
    "ToDo": "Todo",
    "ToDo \"{title}\" löschen?": "Delete todo \"{title}\"?",
    "ToDo \"{title}\" mit {count} Anhängen löschen?": "Delete todo \"{title}\" with {count} attachments?",
    "ToDos": "Todos",
    "Trotzdem schließen": "Close anyway",
    "Türkis": "Teal",
    "Überspringen": "Skip",
    "Umbenennen": "Rename",
    "Unterstrichen (Strg+U)": "Underline (Ctrl+U)",
    "Vergrößern": "Zoom in",
    "Verkleinern": "Zoom out",
    "Verschieben": "Move",
    "Version {version}": "Version {version}",
    "vor Import": "before import",
    "vor Verschieben": "before moving",
    "vor Wiederherstellen": "before restoring",
    "Wie Windows": "Same as Windows",
    "Wiederherstellen": "Restore",
    "Wiederholen": "Redo",
    "Ziel: neues Projekt": "Target: new project",
    "Ziel: Projekt \"{project}\", Reiter {tab}": "Target: project \"{project}\", tab {tab}",
    "Ziel: vorhandenes Projekt \"{name}\", fehlende Einträge werden ergänzt": "Target: existing project \"{name}\", missing entries are added",
    "Zoom ({percent} %)": "Zoom ({percent} %)",
    "Zurücksetzen (100 %)": "Reset (100 %)",
}


def tr(text: str, **values) -> str:
    translated = TRANSLATIONS.get(text, text) if Language.current == LANGUAGE_ENGLISH else text
    return translated.format(**values) if values else translated


def apply_zoom_factor(factor: float) -> None:
    UiScale.factor = min(ZOOM_STEPS[-1], max(ZOOM_STEPS[0], factor))
    font = QApplication.font()
    font.setPointSizeF(BASE_FONT_SIZE * UiScale.factor)
    QApplication.setFont(font)


class PopupMenu(QMenu):
    """Menu with rounded corners whose submenus open next to it without overlapping"""

    def __init__(self, title: str, parent: QWidget) -> None:
        super().__init__(title, parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        parent_menu = self.parentWidget()
        if isinstance(parent_menu, QMenu) is False or parent_menu.isVisible() is False:
            return

        parent_geometry = parent_menu.geometry()
        x = parent_geometry.right() + 1 + ipx(SUBMENU_GAP)
        screen = parent_menu.screen().availableGeometry()
        if x + self.width() > screen.right():
            x = parent_geometry.left() - self.width() - ipx(SUBMENU_GAP)
        self.move(x, self.y())


def create_menu(parent: QWidget, title: str = "") -> QMenu:
    return PopupMenu(title, parent)


def shortcut_label(text: str, sequence: QKeySequence) -> str:
    return text + "\t" + sequence.toString(QKeySequence.SequenceFormat.NativeText)


def px(value: float) -> float:
    return value * UiScale.factor


def ipx(value: float) -> int:
    return round(value * UiScale.factor)


def header_font(base_font: QFont) -> QFont:
    font = QFont(base_font)
    font.setPointSizeF(px(HEADER_FONT_SIZE))
    font.setWeight(QFont.Weight.DemiBold)
    return font


def is_checked(value) -> bool:
    return value in (Qt.CheckState.Checked, Qt.CheckState.Checked.value)


class DialogIcon(QWidget):
    """Info, warning or error symbol of a message dialog in the style of Windows"""

    def __init__(self, kind: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._kind = kind
        self.setFixedSize(ipx(DIALOG_ICON_SIZE), ipx(DIALOG_ICON_SIZE))

    def paintEvent(self, event) -> None:
        size = float(self.width())
        center = size / 2
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self._kind == DIALOG_WARNING:
            # Yellow triangle with rounded corners and a dark exclamation mark
            stroke = size * 0.1
            triangle = QPainterPath()
            triangle.moveTo(center, size * 0.1)
            triangle.lineTo(size * 0.94, size * 0.86)
            triangle.lineTo(size * 0.06, size * 0.86)
            triangle.closeSubpath()
            painter.setPen(QPen(QColor(DIALOG_WARNING_COLOR), stroke, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.setBrush(QColor(DIALOG_WARNING_COLOR))
            painter.drawPath(triangle)
            mark = QColor(DIALOG_WARNING_MARK_COLOR)
            painter.setPen(QPen(mark, size * 0.09, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(center, size * 0.38), QPointF(center, size * 0.6))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(mark)
            painter.drawEllipse(QPointF(center, size * 0.74), size * 0.06, size * 0.06)
            painter.end()
            return

        # Filled circle with a white mark
        color = QColor(DIALOG_ERROR_COLOR if self._kind == DIALOG_ERROR else DIALOG_INFO_COLOR)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QRectF(size * 0.03, size * 0.03, size * 0.94, size * 0.94))
        white = QColor("#ffffff")
        if self._kind == DIALOG_ERROR:
            painter.setPen(QPen(white, size * 0.09, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(size * 0.36, size * 0.36), QPointF(size * 0.64, size * 0.64))
            painter.drawLine(QPointF(size * 0.64, size * 0.36), QPointF(size * 0.36, size * 0.64))
        else:
            painter.setBrush(white)
            painter.drawEllipse(QPointF(center, size * 0.29), size * 0.065, size * 0.065)
            painter.setPen(QPen(white, size * 0.11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(center, size * 0.46), QPointF(center, size * 0.72))
        painter.end()


def create_message_dialog(parent: Optional[QWidget], kind: str, text: str) -> tuple[QDialog, QHBoxLayout]:
    # Text with icon on top, buttons in a gray bar below, like the message boxes of Windows
    dialog = QDialog(parent)
    dialog.setWindowTitle(APP_TITLE)
    dialog.setObjectName("messageDialog")
    dialog.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    dialog.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

    content = QWidget()
    content.setObjectName("dialogContent")
    content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    content_layout = QHBoxLayout(content)
    content_layout.setContentsMargins(ipx(24), ipx(22), ipx(28), ipx(26))
    content_layout.setSpacing(ipx(16))
    content_layout.addWidget(DialogIcon(kind), 0, Qt.AlignmentFlag.AlignTop)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setMinimumWidth(ipx(DIALOG_TEXT_WIDTH))
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    content_layout.addWidget(label, 1, Qt.AlignmentFlag.AlignVCenter)

    bar = QFrame()
    bar.setObjectName("dialogButtonBar")
    buttons = QHBoxLayout(bar)
    buttons.setContentsMargins(ipx(24), ipx(14), ipx(24), ipx(14))
    buttons.setSpacing(ipx(8))
    buttons.addStretch()

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
    layout.addWidget(content, 1)
    layout.addWidget(bar)
    return dialog, buttons


def add_dialog_button(dialog: QDialog, buttons: QHBoxLayout, text: str, result: int, default: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setMinimumWidth(ipx(DIALOG_BUTTON_WIDTH))
    button.setAutoDefault(False)
    button.setDefault(default)
    button.clicked.connect(lambda checked=False: dialog.done(result))
    buttons.addWidget(button)
    if default:
        button.setFocus()
    return button


def show_message(parent: Optional[QWidget], text: str, kind: str = DIALOG_INFO) -> None:
    dialog, buttons = create_message_dialog(parent, kind, text)
    add_dialog_button(dialog, buttons, "OK", 1, True)
    dialog.exec()


def confirm(parent: Optional[QWidget], text: str, accept_text: str, kind: str = DIALOG_WARNING) -> bool:
    dialog, buttons = create_message_dialog(parent, kind, text)
    add_dialog_button(dialog, buttons, accept_text, 1)
    add_dialog_button(dialog, buttons, tr("Abbrechen"), 0, True)
    return dialog.exec() == 1


def ask(parent: Optional[QWidget], text: str, choices: list[tuple[str, str]], kind: str = DIALOG_INFO) -> Optional[str]:
    dialog, buttons = create_message_dialog(parent, kind, text)
    for position, (choice_text, value) in enumerate(choices):
        add_dialog_button(dialog, buttons, choice_text, position + 1)
    add_dialog_button(dialog, buttons, tr("Abbrechen"), 0, True)
    result = dialog.exec()
    return choices[result - 1][1] if 1 <= result <= len(choices) else None


# Color mode
LIGHT_COLORS = {
    QPalette.ColorRole.Window: "#f3f3f3",
    QPalette.ColorRole.WindowText: "#1b1b1b",
    QPalette.ColorRole.Base: "#ffffff",
    QPalette.ColorRole.AlternateBase: "#f7f7f7",
    QPalette.ColorRole.Text: "#1b1b1b",
    QPalette.ColorRole.Button: "#fbfbfb",
    QPalette.ColorRole.ButtonText: "#1b1b1b",
    QPalette.ColorRole.BrightText: "#ffffff",
    QPalette.ColorRole.Highlight: "#2563eb",
    QPalette.ColorRole.HighlightedText: "#ffffff",
    QPalette.ColorRole.ToolTipBase: "#ffffff",
    QPalette.ColorRole.ToolTipText: "#1b1b1b",
    QPalette.ColorRole.PlaceholderText: "#8a8a8a",
    QPalette.ColorRole.Light: "#ffffff",
    QPalette.ColorRole.Midlight: "#eeeeee",
    QPalette.ColorRole.Mid: "#c8c8c8",
    QPalette.ColorRole.Dark: "#a0a0a0",
    QPalette.ColorRole.Shadow: "#707070",
    QPalette.ColorRole.Link: "#2563eb",
}

DARK_COLORS = {
    QPalette.ColorRole.Window: "#202020",
    QPalette.ColorRole.WindowText: "#f0f0f0",
    QPalette.ColorRole.Base: "#2b2b2b",
    QPalette.ColorRole.AlternateBase: "#323232",
    QPalette.ColorRole.Text: "#f0f0f0",
    QPalette.ColorRole.Button: "#333333",
    QPalette.ColorRole.ButtonText: "#f0f0f0",
    QPalette.ColorRole.BrightText: "#ffffff",
    QPalette.ColorRole.Highlight: "#3b78e7",
    QPalette.ColorRole.HighlightedText: "#ffffff",
    QPalette.ColorRole.ToolTipBase: "#2b2b2b",
    QPalette.ColorRole.ToolTipText: "#f0f0f0",
    QPalette.ColorRole.PlaceholderText: "#9a9a9a",
    QPalette.ColorRole.Light: "#505050",
    QPalette.ColorRole.Midlight: "#404040",
    QPalette.ColorRole.Mid: "#555555",
    QPalette.ColorRole.Dark: "#1a1a1a",
    QPalette.ColorRole.Shadow: "#000000",
    QPalette.ColorRole.Link: "#6ea0ff",
}


def create_palette(dark: bool) -> QPalette:
    palette = QPalette()
    colors = DARK_COLORS if dark else LIGHT_COLORS
    for role, value in colors.items():
        palette.setColor(role, QColor(value))

    disabled_text = QColor(colors[QPalette.ColorRole.PlaceholderText])
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, disabled_text)
    return palette


def apply_color_mode(mode: str) -> None:
    schemes = {
        COLOR_MODE_LIGHT: Qt.ColorScheme.Light,
        COLOR_MODE_DARK: Qt.ColorScheme.Dark,
    }
    hints = QGuiApplication.styleHints()
    if hasattr(hints, "setColorScheme"):
        hints.setColorScheme(schemes.get(mode, Qt.ColorScheme.Unknown))

    # Same as Windows reads the system color scheme after the override is reset
    if mode in schemes:
        dark = mode == COLOR_MODE_DARK
    else:
        dark = hints.colorScheme() == Qt.ColorScheme.Dark
    QApplication.setPalette(create_palette(dark))


# Theme
@dataclass
class Theme:
    """Colors derived from the current system palette, works for light and dark mode"""

    base: QColor
    window: QColor
    text: QColor
    muted: QColor
    divider: QColor
    divider_strong: QColor
    hover: QColor
    selected: QColor
    list_background: QColor
    flag: QColor
    flag_background: QColor
    flag_selected: QColor
    accent: QColor
    accent_hover: QColor
    accent_selected: QColor
    button_border: QColor
    scroll_handle: QColor
    scroll_handle_hover: QColor

    @staticmethod
    def from_palette(palette: QPalette) -> Theme:
        base = palette.color(QPalette.ColorRole.Base)
        text = palette.color(QPalette.ColorRole.Text)
        dark = base.lightness() < 128
        accent = QColor(ACCENT_DARK if dark else ACCENT_LIGHT)
        return Theme(
            base=base,
            window=palette.color(QPalette.ColorRole.Window),
            text=text,
            muted=mix_colors(base, text, 0.55),
            divider=mix_colors(base, text, 0.11),
            divider_strong=mix_colors(base, text, 0.28),
            hover=mix_colors(base, text, 0.05),
            selected=mix_colors(base, text, 0.12),
            list_background=mix_colors(base, text, 0.035),
            flag=QColor(FLAG_DARK if dark else FLAG_LIGHT),
            flag_background=QColor(FLAG_BACKGROUND_DARK if dark else FLAG_BACKGROUND_LIGHT),
            flag_selected=QColor(FLAG_SELECTED_DARK if dark else FLAG_SELECTED_LIGHT),
            accent=accent,
            accent_hover=mix_colors(base, accent, 0.16) if dark else QColor(ACCENT_HOVER_LIGHT),
            accent_selected=mix_colors(base, accent, 0.32) if dark else QColor(ACCENT_SELECTED_LIGHT),
            button_border=mix_colors(base, text, 0.2),
            scroll_handle=mix_colors(base, text, 0.25),
            scroll_handle_hover=mix_colors(base, text, 0.42),
        )

    @property
    def is_dark(self) -> bool:
        return self.base.lightness() < 128

    def style_sheet(self) -> str:
        return f"""
QWidget#projectColumn, QWidget#detailColumn {{ background: {self.base.name()}; }}
QWidget#itemColumn {{ background: {self.list_background.name()}; }}
QDialog#messageDialog, QWidget#dialogContent {{ background: {self.base.name()}; }}
QFrame#dialogButtonBar {{ background: {self.window.name()}; border: none; border-top: 1px solid {self.divider.name()}; }}
QFrame#columnHeader {{ background: transparent; border: none; border-bottom: 1px solid {self.divider.name()}; }}
QFrame#columnFooter {{ background: transparent; border: none; border-top: 1px solid {self.divider.name()}; }}
QLabel#mutedLabel, QLabel#countLabel {{ color: {self.muted.name()}; }}
QLabel#sectionLabel {{ color: {self.muted.name()}; font-weight: 600; }}
QFrame#dropZone {{ background: {self.list_background.name()}; border: 1px solid {self.divider.name()}; border-radius: 6px; }}
QFrame#dropZone:hover, QFrame#dropZone[active="true"] {{ background: {self.accent_hover.name()}; border-color: {self.accent.name()}; }}
QLabel#dropZoneText, QLabel#dropZoneIcon {{ background: transparent; border: none; color: {self.muted.name()}; }}
QListWidget#projectList, QListWidget#itemList {{ background: transparent; border: none; outline: 0; }}
QLineEdit#titleEdit {{ background: transparent; border: none; padding: 0px; }}
QLineEdit#newItemEdit {{ background: {self.base.name()}; border: 1px solid {self.divider.name()}; border-radius: 6px; padding: 7px 10px; }}
QLineEdit#newItemEdit:focus, QLineEdit#fieldEdit:focus {{ border-color: {self.accent.name()}; }}
QLineEdit#fieldEdit {{ background: {self.base.name()}; border: 1px solid {self.divider.name()}; border-radius: 6px; padding: 5px 8px; }}
QToolButton#conditionButton {{ background: {self.base.name()}; border: 1px solid {self.divider.name()}; border-radius: 6px; padding: 5px 6px 5px 8px; }}
QToolButton#conditionButton:hover {{ background: {self.hover.name()}; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background: {self.base.name()}; }}
QCalendarWidget QToolButton {{ color: {self.text.name()}; font-weight: 600; }}
QCalendarWidget QAbstractItemView {{ background: {self.base.name()}; selection-background-color: {self.accent.name()}; selection-color: #ffffff; outline: none; }}
QLineEdit#inlineEdit {{ background: {self.base.name()}; color: {self.text.name()}; border: 1px solid {self.accent.name()}; border-radius: 4px; padding: 1px 4px; }}
QFrame#tabRow {{ background: transparent; border: none; border-bottom: 1px solid {self.divider.name()}; }}
QToolButton#tabButton {{ background: transparent; color: {self.muted.name()}; border: none; border-bottom: 2px solid transparent; border-radius: 0px; padding: 0px; }}
QToolButton#tabButton:hover {{ background: transparent; color: {self.text.name()}; }}
QToolButton#tabButton:checked {{ background: transparent; color: {self.text.name()}; border-bottom: 2px solid {self.accent.name()}; font-weight: 600; }}
QFrame#descriptionFrame {{ background: {self.base.name()}; border: 1px solid {self.divider.name()}; border-radius: 6px; }}
QFrame#toolbarLine {{ background: {self.divider.name()}; border: none; }}
QFrame#toolbarSeparator {{ background: {self.divider_strong.name()}; border: none; margin: 0px 3px; }}
QTextEdit#descriptionEdit {{ background: transparent; border: none; }}
QFrame#attachmentCard {{ background: {self.base.name()}; border: 1px solid {self.divider.name()}; border-radius: 6px; }}
QScrollArea#attachmentScroll {{ background: transparent; border: none; }}
QWidget#attachmentContainer {{ background: transparent; }}
QToolButton {{ background: transparent; border: none; border-radius: 4px; padding: 4px 6px; }}
QToolButton:hover {{ background: {self.hover.name()}; }}
QToolButton:pressed, QToolButton:checked {{ background: {self.selected.name()}; }}
QToolButton::menu-indicator {{ image: none; width: 0px; }}
QToolButton#iconButton {{ padding: 0px; }}
QSplitter::handle {{ background: {self.divider.name()}; }}
QPushButton {{ background: {self.base.name()}; color: {self.text.name()}; border: 1px solid {self.button_border.name()}; border-radius: 4px; padding: 5px 12px; }}
QPushButton:hover {{ background: {self.hover.name()}; }}
QPushButton:pressed {{ background: {self.selected.name()}; }}
QPushButton:disabled {{ color: {self.muted.name()}; }}
QPushButton:default {{ border-color: {self.accent.name()}; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 0px; }}
QScrollBar::handle:vertical {{ background: {self.scroll_handle.name()}; border-radius: 3px; min-height: 32px; margin: 2px 3px; }}
QScrollBar::handle:horizontal {{ background: {self.scroll_handle.name()}; border-radius: 3px; min-width: 32px; margin: 3px 2px; }}
QScrollBar::handle:hover {{ background: {self.scroll_handle_hover.name()}; }}
QListWidget#itemList QScrollBar:vertical {{ width: 20px; }}
QListWidget#itemList QScrollBar::handle:vertical {{ margin: 2px 3px 2px 11px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; border: none; background: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QMenu {{ background: {self.base.name()}; color: {self.text.name()}; border: 1px solid {self.button_border.name()}; border-radius: 6px; padding: 4px; }}
QMenu::item {{ padding: 6px 28px 6px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background: {self.accent_hover.name()}; color: {self.text.name()}; }}
QMenu::item:disabled {{ color: {self.muted.name()}; }}
QMenu::separator {{ height: 1px; background: {self.divider.name()}; margin: 4px 8px; }}
QToolTip {{ background: {self.base.name()}; color: {self.text.name()}; border: 1px solid {self.button_border.name()}; padding: 4px 6px; }}
"""


# Links and clipboard
def url_from_text(text: str) -> QUrl:
    value = text.strip()
    if value.startswith("\\\\") or re.match(r"^[a-zA-Z]:[\\/]", value):
        return QUrl.fromLocalFile(value)
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", value):
        return QUrl(value)
    return QUrl("https://" + value)


def open_link(text: str) -> None:
    if text.strip():
        QDesktopServices.openUrl(url_from_text(text))


def looks_like_address(text: str) -> bool:
    return re.match(r"^(https?://|file:|www\.|\\\\|[a-zA-Z]:[\\/])", text.strip()) is not None


def link_title_from_url(url: str) -> str:
    value = url.strip()
    if value.startswith("\\\\") or re.match(r"^[a-zA-Z]:[\\/]", value):
        parts = [part for part in re.split(r"[\\/]", value) if part]
        return parts[-1] if parts else value
    parsed = urlparse(value if "://" in value else "https://" + value)
    host = parsed.netloc
    if host.startswith("www."):
        host = host[4:]
    return host or value


def parse_link_input(text: str) -> tuple[str, str]:
    if looks_like_address(text):
        return link_title_from_url(text), text.strip()
    return text, ""


def note_preview(note: Note) -> str:
    for line in note.text.splitlines():
        cleaned = line.replace(OBJECT_REPLACEMENT_CHARACTER, "").strip()
        if cleaned and cleaned != note.title.strip():
            return cleaned
    return ""


def package_paths(mime: Optional[QMimeData]) -> list[Path]:
    return [path for path in local_files_from_mime(mime) if path.suffix.lower() == EXPORT_EXTENSION]


def image_from_mime(mime: QMimeData) -> QImage:
    data = mime.imageData()
    if isinstance(data, QImage):
        return data
    if isinstance(data, QPixmap):
        return data.toImage()
    return QImage()


# Data model
@dataclass
class Attachment:
    id: str
    name: str
    file: str
    added: float = 0.0

    @staticmethod
    def from_dict(values: dict) -> Attachment:
        return Attachment(
            id=str(values["id"]),
            name=str(values.get("name", values["file"])),
            file=str(values["file"]),
            added=float(values.get("added", 0.0)),
        )


def optional_id(value) -> Optional[str]:
    return str(value) if value else None


@dataclass
class Todo:
    id: str
    title: str
    description: str = ""
    description_html: str = ""
    done: bool = False
    flagged: bool = False
    done_at: Optional[float] = None
    created: float = 0.0
    modified: float = 0.0
    group_id: Optional[str] = None
    attachments: list[Attachment] = field(default_factory=list)
    condition: str = ""
    condition_date: str = ""
    condition_text: str = ""

    @staticmethod
    def create(title: str, group_id: Optional[str] = None) -> Todo:
        now = time.time()
        return Todo(id=new_id(), title=title, created=now, modified=now, group_id=group_id)

    @staticmethod
    def from_dict(values: dict) -> Todo:
        done_at = values.get("done_at")
        condition = str(values.get("condition", ""))
        condition_date = str(values.get("condition_date", "") or "")
        return Todo(
            id=str(values["id"]),
            title=str(values.get("title", "")),
            description=str(values.get("description", "")),
            description_html=str(values.get("description_html", "")),
            done=bool(values.get("done", False)),
            flagged=bool(values.get("flagged", False)) and bool(values.get("done", False)) is False,
            done_at=float(done_at) if done_at is not None else None,
            created=float(values.get("created", 0.0)),
            modified=float(values.get("modified", 0.0)),
            group_id=optional_id(values.get("group_id")),
            attachments=[Attachment.from_dict(entry) for entry in values.get("attachments", [])],
            condition=condition if condition in (CONDITION_UNTIL, CONDITION_FROM) else "",
            condition_date=condition_date if iso_date(condition_date) is not None else "",
            condition_text=str(values.get("condition_text", "")),
        )


@dataclass
class Note:
    id: str
    title: str
    text: str = ""
    html: str = ""
    created: float = 0.0
    modified: float = 0.0
    group_id: Optional[str] = None

    @staticmethod
    def create(title: str, group_id: Optional[str] = None) -> Note:
        now = time.time()
        return Note(id=new_id(), title=title, created=now, modified=now, group_id=group_id)

    @staticmethod
    def from_dict(values: dict) -> Note:
        return Note(
            id=str(values["id"]),
            title=str(values.get("title", "")),
            text=str(values.get("text", "")),
            html=str(values.get("html", "")),
            created=float(values.get("created", 0.0)),
            modified=float(values.get("modified", 0.0)),
            group_id=optional_id(values.get("group_id")),
        )


@dataclass
class Link:
    id: str
    title: str
    url: str = ""
    note: str = ""
    note_html: str = ""
    created: float = 0.0
    modified: float = 0.0
    group_id: Optional[str] = None

    @staticmethod
    def create(title: str, url: str = "", group_id: Optional[str] = None) -> Link:
        now = time.time()
        return Link(id=new_id(), title=title, url=url, created=now, modified=now, group_id=group_id)

    @staticmethod
    def from_dict(values: dict) -> Link:
        return Link(
            id=str(values["id"]),
            title=str(values.get("title", "")),
            url=str(values.get("url", "")),
            note=str(values.get("note", "")),
            note_html=str(values.get("note_html", "")),
            created=float(values.get("created", 0.0)),
            modified=float(values.get("modified", 0.0)),
            group_id=optional_id(values.get("group_id")),
        )


ITEM_FACTORIES = {
    ITEM_TODO: Todo.from_dict,
    ITEM_NOTE: Note.from_dict,
    ITEM_LINK: Link.from_dict,
}


def touch(item) -> None:
    item.modified = time.time()


def item_title(item) -> str:
    return item.title


def set_item_title(item, text: str) -> None:
    item.title = text


def contacts_note(entries: list) -> Optional[Note]:
    # Contacts of version 2.0 previews are kept as a note
    lines: list[str] = []
    for entry in entries:
        if isinstance(entry, dict) is False:
            continue
        parts = [str(entry.get(key, "")).strip() for key in ("name", "company", "role", "email", "phone")]
        line = " · ".join(part for part in parts if part)
        note_text = " ".join(str(entry.get("note", "")).split())
        if note_text:
            line = line + " · " + note_text if line else note_text
        if line:
            lines.append(line)
    if not lines:
        return None
    note = Note.create(tr("Kontakte"))
    note.text = "\n".join(lines)
    return note


@dataclass
class ItemGroup:
    """Optional group inside one tab of a project"""

    id: str
    name: str
    collapsed: bool = False

    @staticmethod
    def create(name: str) -> ItemGroup:
        return ItemGroup(id=new_id(), name=name)

    @staticmethod
    def from_dict(values: dict) -> ItemGroup:
        return ItemGroup(
            id=str(values["id"]),
            name=str(values.get("name", "")),
            collapsed=bool(values.get("collapsed", False)),
        )


def empty_groups() -> dict[str, list[ItemGroup]]:
    return {item_type: [] for item_type in ITEM_TYPES}


@dataclass
class Project:
    id: str
    name: str
    general: bool = False
    archived: bool = False
    done_collapsed: bool = False
    color: str = ""
    todos: list[Todo] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    groups: dict[str, list[ItemGroup]] = field(default_factory=empty_groups)

    @staticmethod
    def create(name: str, general: bool = False) -> Project:
        return Project(id=new_id(), name=name, general=general)

    @staticmethod
    def from_dict(values: dict) -> Project:
        groups = empty_groups()
        stored_groups = values.get("groups", {})
        if isinstance(stored_groups, dict):
            for item_type in ITEM_TYPES:
                groups[item_type] = [ItemGroup.from_dict(entry) for entry in stored_groups.get(item_type, [])]

        notes = [Note.from_dict(entry) for entry in values.get("notes", [])]
        stored_contacts = values.get("contacts", [])
        contacts = contacts_note(stored_contacts) if isinstance(stored_contacts, list) else None
        if contacts is not None:
            notes.insert(0, contacts)

        return Project(
            id=str(values["id"]),
            name=str(values.get("name", "")),
            general=bool(values.get("general", False)),
            archived=bool(values.get("archived", False)),
            done_collapsed=bool(values.get("done_collapsed", False)),
            color=str(values.get("color", "")),
            todos=[Todo.from_dict(entry) for entry in values.get("todos", [])],
            notes=notes,
            links=[Link.from_dict(entry) for entry in values.get("links", [])],
            groups=groups,
        )

    def display_name(self) -> str:
        return tr(GENERAL_PROJECT_NAME) if self.general else self.name

    def items(self, item_type: str) -> list:
        return getattr(self, ITEM_LISTS[item_type])

    def groups_of(self, item_type: str) -> list[ItemGroup]:
        return self.groups.setdefault(item_type, [])

    def find_item(self, item_type: str, item_id: Optional[str]):
        for item in self.items(item_type):
            if item.id == item_id:
                return item
        return None

    def find_group(self, item_type: str, group_id: Optional[str]) -> Optional[ItemGroup]:
        for group in self.groups_of(item_type):
            if group.id == group_id:
                return group
        return None

    def open_todos(self) -> list[Todo]:
        return [todo for todo in self.todos if todo.done is False]

    def done_todos(self) -> list[Todo]:
        finished = [todo for todo in self.todos if todo.done is True]
        finished.sort(key=lambda todo: todo.done_at or 0.0, reverse=True)
        return finished

    def has_flagged_todo(self) -> bool:
        for todo in self.todos:
            if todo.flagged and todo.done is False:
                return True
        return False

    def item_count(self) -> int:
        total = 0
        for item_type in ITEM_TYPES:
            total += len(self.items(item_type))
        return total


@dataclass
class AppData:
    projects: list[Project] = field(default_factory=list)
    active_project_id: Optional[str] = None

    @staticmethod
    def create_default() -> AppData:
        data = AppData()
        data.normalize()
        return data

    @staticmethod
    def from_dict(values: dict) -> AppData:
        if "projects" not in values and "groups" in values:
            return AppData.from_groups(values)

        data = AppData(
            projects=[Project.from_dict(entry) for entry in values.get("projects", [])],
            active_project_id=optional_id(values.get("active_project_id")),
        )
        data.normalize()
        return data

    @staticmethod
    def from_groups(values: dict) -> AppData:
        # Version 1 had groups with one level of subgroups: groups become projects, subgroups become todo groups
        stored_groups = [entry for entry in values.get("groups", []) if isinstance(entry, dict) and "id" in entry]
        by_id = {str(entry["id"]): entry for entry in stored_groups}

        def parent_id(entry: dict) -> Optional[str]:
            parent = optional_id(entry.get("parent_id"))
            if parent is None or parent not in by_id or by_id[parent].get("parent_id"):
                return None
            return parent

        projects: list[Project] = []
        for entry in stored_groups:
            if parent_id(entry) is not None:
                continue

            project = Project(
                id=str(entry["id"]),
                name=str(entry.get("name", "")),
                archived=bool(entry.get("archived", False)),
                todos=[Todo.from_dict(todo) for todo in entry.get("todos", [])],
            )
            for child in stored_groups:
                if parent_id(child) != project.id:
                    continue
                name = str(child.get("name", ""))
                group_id: Optional[str] = None
                if name not in GENERAL_NAMES:
                    group = ItemGroup(id=str(child["id"]), name=name)
                    project.groups_of(ITEM_TODO).append(group)
                    group_id = group.id
                for todo_values in child.get("todos", []):
                    todo = Todo.from_dict(todo_values)
                    todo.group_id = group_id
                    project.todos.append(todo)

            if project.name in GENERAL_NAMES and project.archived is False and not any(entry.general for entry in projects):
                project.general = True
            projects.append(project)

        active_id = optional_id(values.get("active_group_id"))
        if active_id in by_id and parent_id(by_id[active_id]) is not None:
            active_id = parent_id(by_id[active_id])

        data = AppData(projects=projects, active_project_id=active_id)
        data.normalize()
        return data

    def normalize(self) -> None:
        # Exactly one general project, always first and never archived
        general: Optional[Project] = None
        for project in self.projects:
            if project.general and general is None:
                general = project
            else:
                project.general = False
        if general is None:
            general = Project.create(GENERAL_PROJECT_NAME, general=True)
        else:
            self.projects.remove(general)
        general.archived = False
        self.projects.insert(0, general)

        # Items of missing groups are shown without group
        for project in self.projects:
            for item_type in ITEM_TYPES:
                group_ids = {group.id for group in project.groups_of(item_type)}
                for item in project.items(item_type):
                    if item.group_id is not None and item.group_id not in group_ids:
                        item.group_id = None

        # Projects without color get the next color of the palette
        if not general.color:
            general.color = GENERAL_COLOR
        for project in self.projects:
            if not project.color:
                project.color = self.next_color()

        if self.find_project(self.active_project_id) is None:
            self.active_project_id = general.id

    def to_dict(self) -> dict:
        return {
            "version": DATA_VERSION,
            "projects": [asdict(project) for project in self.projects],
            "active_project_id": self.active_project_id,
        }

    def next_color(self) -> str:
        used = [project.color for project in self.projects]
        candidates = [value for name, value in PROJECT_COLORS if value != GENERAL_COLOR]
        return min(candidates, key=lambda value: (used.count(value), candidates.index(value)))

    def find_project(self, project_id: Optional[str]) -> Optional[Project]:
        for project in self.projects:
            if project.id == project_id:
                return project
        return None

    def general_project(self) -> Project:
        return self.projects[0]

    def active_project(self) -> Project:
        project = self.find_project(self.active_project_id)
        return project if project is not None else self.general_project()

    def open_projects(self) -> list[Project]:
        return [project for project in self.projects if project.archived is False]

    def archived_projects(self) -> list[Project]:
        return [project for project in self.projects if project.archived is True]

    def find_item(self, item_type: str, item_id: str) -> Optional[tuple[Project, object]]:
        for project in self.projects:
            item = project.find_item(item_type, item_id)
            if item is not None:
                return project, item
        return None


def referenced_files(values: dict) -> set[str]:
    # Attachment and image files of data.json content or of a backup, relative to the data folder
    files: set[str] = set()
    projects = values.get("projects")
    if projects is None:
        projects = [{"todos": group.get("todos", [])} for group in values.get("groups", [])]
    for project in projects:
        for todo in project.get("todos", []):
            for attachment in todo.get("attachments", []):
                if attachment.get("file"):
                    files.add(ATTACHMENT_FOLDER_NAME + "/" + str(attachment["file"]))
        for note in project.get("notes", []):
            files.update(NOTE_IMAGE_PATTERN.findall(str(note.get("html", ""))))
    return files


# Storage
class Storage:
    """Reads and writes data.json, the attachment files and the note images of one data folder"""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.data_file = folder / DATA_FILE_NAME
        self.attachment_folder = folder / ATTACHMENT_FOLDER_NAME
        self.image_folder = folder / IMAGE_FOLDER_NAME

    def load(self) -> AppData:
        self.attachment_folder.mkdir(parents=True, exist_ok=True)
        if self.data_file.exists() is False:
            data = AppData.create_default()
            self.save(data)
            return data

        with self.data_file.open("r", encoding="utf-8") as file:
            values = json.load(file)

        # Data of version 1 is kept as a copy before it is converted
        if "projects" not in values and "groups" in values:
            backup_file = self.folder / BACKUP_FILE_NAME
            if backup_file.exists() is False:
                shutil.copy2(self.data_file, backup_file)
        return AppData.from_dict(values)

    def save(self, data: AppData) -> None:
        temporary_file = self.folder / (DATA_FILE_NAME + ".tmp")
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(data.to_dict(), file, ensure_ascii=False, indent=2)
        os.replace(temporary_file, self.data_file)

    def attachment_path(self, attachment: Attachment) -> Path:
        return self.attachment_folder / attachment.file

    def import_file(self, source: Path) -> Attachment:
        attachment_id = new_id()
        file_name = attachment_id[:12] + "_" + safe_file_name(source.name)
        shutil.copy2(source, self.attachment_folder / file_name)
        return Attachment(id=attachment_id, name=source.name, file=file_name, added=time.time())

    def import_image(self, image: QImage) -> Attachment:
        attachment_id = new_id()
        name = "Screenshot_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png"
        file_name = attachment_id[:12] + "_" + name
        if image.save(str(self.attachment_folder / file_name), "PNG") is False:
            raise OSError(tr("Bild konnte nicht gespeichert werden"))
        return Attachment(id=attachment_id, name=name, file=file_name, added=time.time())

    def import_note_image(self, image: QImage) -> str:
        self.image_folder.mkdir(parents=True, exist_ok=True)
        file_name = new_id()[:16] + ".png"
        if image.save(str(self.image_folder / file_name), "PNG") is False:
            raise OSError(tr("Bild konnte nicht gespeichert werden"))
        return IMAGE_FOLDER_NAME + "/" + file_name

    def note_image_path(self, name: str) -> Path:
        return self.folder / name

    def entries(self) -> list[Path]:
        return [self.folder / name for name in DATA_ENTRY_NAMES if (self.folder / name).exists()]

    def copy_to(self, target: Path) -> None:
        # Everything is copied or nothing stays behind in the target folder
        target.mkdir(parents=True, exist_ok=True)
        copied: list[Path] = []
        try:
            for entry in self.entries():
                destination = target / entry.name
                if entry.is_dir():
                    shutil.copytree(entry, destination)
                else:
                    shutil.copy2(entry, destination)
                copied.append(destination)
        except OSError:
            for destination in copied:
                if destination.is_dir():
                    shutil.rmtree(destination, ignore_errors=True)
                else:
                    destination.unlink(missing_ok=True)
            raise

    def remove_entries(self) -> list[str]:
        failed: list[str] = []
        for entry in self.entries():
            try:
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
            except OSError:
                failed.append(entry.name)
        return failed

    # Backups
    @property
    def backup_folder(self) -> Path:
        return self.folder / BACKUP_FOLDER_NAME

    @property
    def kept_files_folder(self) -> Path:
        return self.backup_folder / KEPT_FILES_FOLDER_NAME

    def list_backups(self) -> list[tuple[Path, datetime, str]]:
        # Newest first, backups of the same second are ordered by their counter
        entries: list[tuple[datetime, int, Path, str]] = []
        if self.backup_folder.is_dir() is False:
            return []
        for path in self.backup_folder.glob("backup_*.json"):
            match = BACKUP_FILE_PATTERN.fullmatch(path.name)
            if match is None:
                continue
            try:
                moment = datetime.strptime(match.group(1), BACKUP_TIME_FORMAT)
            except ValueError:
                continue
            counter = int(match.group(2)) if match.group(2) else 0
            entries.append((moment, counter, path, match.group(3)))
        entries.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        return [(path, moment, reason) for moment, counter, path, reason in entries]

    def latest_backup_time(self) -> Optional[datetime]:
        backups = self.list_backups()
        return backups[0][1] if backups else None

    def backup_data_file(self, reason: str) -> Optional[Path]:
        # The saved data.json is copied, the oldest backups beyond the limit are removed
        if self.data_file.exists() is False:
            return None
        self.backup_folder.mkdir(parents=True, exist_ok=True)
        # Backups of the same second get a counter so the order stays clear
        stamp = datetime.now().strftime(BACKUP_TIME_FORMAT)
        name = stamp
        counter = 1
        while any(self.backup_folder.glob(f"backup_{name}_*.json")):
            counter += 1
            name = f"{stamp}-{counter}"
        target = self.backup_folder / f"backup_{name}_{reason}.json"
        shutil.copy2(self.data_file, target)
        for path, moment, name in self.list_backups()[BACKUP_KEEP:]:
            path.unlink(missing_ok=True)
        return target

    def load_backup(self, path: Path) -> AppData:
        with path.open("r", encoding="utf-8") as file:
            return AppData.from_dict(json.load(file))

    # Files of deleted entries
    def restore_files(self, data: AppData) -> None:
        # Files needed again after undo or restore come back from the kept files
        for relative in referenced_files(data.to_dict()):
            target = self.folder / relative
            kept = self.kept_files_folder / relative
            if target.exists() is False and kept.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(kept), str(target))

    def collect_garbage(self, data: AppData) -> None:
        # Unused files are kept as long as a backup needs them, afterwards they are deleted
        current = referenced_files(data.to_dict())
        for folder_name in (ATTACHMENT_FOLDER_NAME, IMAGE_FOLDER_NAME):
            folder = self.folder / folder_name
            if folder.is_dir() is False:
                continue
            for path in folder.iterdir():
                relative = folder_name + "/" + path.name
                if path.is_file() is False or relative in current:
                    continue
                kept = self.kept_files_folder / relative
                kept.parent.mkdir(parents=True, exist_ok=True)
                if kept.exists():
                    path.unlink()
                else:
                    shutil.move(str(path), str(kept))

        needed: set[str] = set()
        backup_files = [path for path, moment, reason in self.list_backups()]
        if (self.folder / BACKUP_FILE_NAME).exists():
            backup_files.append(self.folder / BACKUP_FILE_NAME)
        for path in backup_files:
            try:
                with path.open("r", encoding="utf-8") as file:
                    needed |= referenced_files(json.load(file))
            except (OSError, ValueError):
                continue
        if self.kept_files_folder.is_dir() is False:
            return
        for path in self.kept_files_folder.rglob("*"):
            if path.is_file() and path.relative_to(self.kept_files_folder).as_posix() not in needed:
                path.unlink()


# List delegates
def item_payload(item_type: str, item_ids: list[str]) -> str:
    # Dragged entries as "type:id,id,id"
    return item_type + ":" + ",".join(item_ids)


def parse_item_payload(mime: QMimeData) -> tuple[str, list[str]]:
    item_type, _, ids = bytes(mime.data(ITEM_MIME_TYPE)).decode("utf-8").partition(":")
    return item_type, [item_id for item_id in ids.split(",") if item_id]


def paint_chevron(painter: QPainter, center: QPointF, expanded: bool, color: QColor) -> None:
    size = px(CHEVRON_SIZE)
    pen = QPen(color, px(1.4))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    if expanded:
        points = [
            QPointF(center.x() - size, center.y() - size / 2),
            QPointF(center.x(), center.y() + size / 2),
            QPointF(center.x() + size, center.y() - size / 2),
        ]
    else:
        points = [
            QPointF(center.x() - size / 2, center.y() - size),
            QPointF(center.x() + size / 2, center.y()),
            QPointF(center.x() - size / 2, center.y() + size),
        ]
    painter.drawPolyline(points)


def paint_action(painter: QPainter, rect: QRectF, icon: QIcon, active: bool, theme: Theme) -> None:
    if active:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(theme.button_border)
        painter.drawRoundedRect(rect, px(4), px(4))
    inset = (rect.width() - px(ICON_SIZE)) / 2
    icon.paint(painter, rect.adjusted(inset, inset, -inset, -inset).toRect())


def create_inline_editor(parent: QWidget) -> QLineEdit:
    editor = QLineEdit(parent)
    editor.setObjectName("inlineEdit")
    return editor


class ProjectDelegate(QStyledItemDelegate):
    """Project row with color dot or archive row with fixed flag and count places"""

    def __init__(self, view: ProjectListWidget, theme: Theme) -> None:
        super().__init__(view)
        self._view = view
        self.theme = theme

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, value: Theme) -> None:
        self._theme = value
        self._flag_icon = create_flag_icon(value.flag, True)

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        metrics = QFontMetrics(option.font)
        return QSize(self._view.viewport().width(), metrics.height() + ipx(GROUP_PADDING_V) * 2)

    def icon_rect(self, rect: QRect) -> QRect:
        size = ipx(ICON_SIZE)
        return QRect(rect.left() + ipx(GROUP_PADDING_H), round(rect.center().y() - size / 2 + 0.5), size, size)

    def text_left(self, rect: QRect) -> int:
        return rect.left() + ipx(GROUP_PADDING_H) + ipx(ICON_SIZE) + ipx(GROUP_ICON_SPACING) + ipx(2)

    def _count_rect(self, rect: QRect) -> QRectF:
        right = rect.right() - px(GROUP_PADDING_H)
        width = QFontMetricsF(self._view.font()).horizontalAdvance(COUNT_SLOT_TEXT)
        return QRectF(right - width, rect.top(), width, rect.height())

    def _flag_rect(self, rect: QRect) -> QRectF:
        count_rect = self._count_rect(rect)
        size = px(ICON_SIZE)
        return QRectF(count_rect.left() - px(GROUP_ICON_SPACING) - size, rect.center().y() - size / 2 + 0.5, size, size)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        rect = option.rect
        is_header = index.data(KIND_ROLE) == KIND_ARCHIVE_HEADER
        archived = bool(index.data(ARCHIVED_ROLE))
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver) and self._view.drag_active is False

        painter.save()
        if selected:
            painter.fillRect(rect, self.theme.selected)
        elif hovered:
            painter.fillRect(rect, self.theme.accent_hover)

        painter.setPen(QPen(self.theme.divider, 1))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Chevron for the archive, color dot for projects
        icon_rect = self.icon_rect(rect)
        if is_header:
            paint_chevron(painter, QPointF(icon_rect.center().x() + 0.5, rect.center().y() + 0.5), bool(index.data(EXPANDED_ROLE)), self.theme.muted)
        else:
            color = QColor(index.data(COLOR_ROLE) or GENERAL_COLOR)
            if archived:
                color = mix_colors(self.theme.base, color, 0.45)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(icon_rect.center().x() + 0.5, rect.center().y() + 0.5), px(DOT_SIZE) / 2, px(DOT_SIZE) / 2)

        # Count and flag keep fixed places on the right
        count = index.data(COUNT_ROLE) or 0
        if count:
            painter.setFont(option.font)
            painter.setPen(self.theme.muted)
            painter.drawText(self._count_rect(rect), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(count))
        flag_rect = self._flag_rect(rect)
        if index.data(FLAGGED_ROLE):
            self._flag_icon.paint(painter, flag_rect.toRect())
        text_right = flag_rect.left() - px(4)

        font = QFont(option.font)
        if selected:
            font.setWeight(QFont.Weight.DemiBold)
        metrics = QFontMetrics(font)
        text_left = self.text_left(rect)
        text_width = max(0, round(text_right) - text_left)
        name = metrics.elidedText(index.data(Qt.ItemDataRole.DisplayRole) or "", Qt.TextElideMode.ElideRight, text_width)
        painter.setFont(font)
        painter.setPen(self.theme.muted if is_header or archived else self.theme.text)
        painter.drawText(QRect(text_left, rect.top(), text_width, rect.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
        painter.restore()

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index) -> QWidget:
        return create_inline_editor(parent)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index) -> None:
        text_left = self.text_left(option.rect)
        rect = option.rect
        editor.setGeometry(QRect(text_left - ipx(5), rect.top() + ipx(4), rect.right() - ipx(GROUP_PADDING_H) - text_left + ipx(10), rect.height() - ipx(8)))


@dataclass
class CardGeometry:
    card: QRectF
    lead: QRectF
    text_origin: QPointF
    layout: QTextLayout
    title_rect: QRectF
    subtitle_rect: QRectF
    meta_rect: QRectF
    actions: dict[str, QRectF]
    condition_rect: QRectF


class ItemDelegate(QStyledItemDelegate):
    """Cards for todos, notes and links plus the header rows of groups and done todos"""

    def __init__(self, view: ItemListWidget, theme: Theme) -> None:
        super().__init__(view)
        self._view = view
        self.theme = theme

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, value: Theme) -> None:
        self._theme = value
        factories = {
            "flag": create_flag_icon,
            "open": create_open_icon,
            "add": create_add_icon,
        }
        self._icons = {name: (factory(value.muted), factory(value.text)) for name, factory in factories.items()}
        self._flag_icon_set = create_flag_icon(value.flag, True)
        self._attachment_icon = create_attachment_icon(value.muted)
        lead_color = value.text if value.is_dark else value.accent
        self._note_icon = create_note_icon(lead_color)
        self._link_icon = create_link_icon(lead_color)

    # Geometry
    @staticmethod
    def action_names(item_type: str) -> list[str]:
        if item_type == ITEM_TODO:
            return ["flag"]
        if item_type == ITEM_LINK:
            return ["open"]
        return []

    @staticmethod
    def action_visible(name: str, index) -> bool:
        if name == "flag":
            return bool(index.data(FLAGGED_ROLE))
        return bool(index.data(TARGET_ROLE))

    def card_geometry(self, rect: QRect, font: QFont, index) -> CardGeometry:
        item_type = index.data(TYPE_ROLE)
        done = item_type == ITEM_TODO and is_checked(index.data(Qt.ItemDataRole.CheckStateRole))
        metrics = QFontMetricsF(font)
        line_height = metrics.height()
        action_size = px(ACTION_SIZE)

        # Icons on the right, the rightmost shown icon sits at the edge
        right = rect.left() + rect.width() - px(CARD_PADDING_H)
        meta_rect = QRectF()
        meta_left = right
        meta_width = 0.0
        slot_right = right + px(4)
        count = index.data(COUNT_ROLE) or 0
        if item_type == ITEM_TODO and count:
            meta_width = px(ICON_SIZE) + px(META_ICON_SPACING) + metrics.horizontalAdvance(str(count))
            meta_left = right - meta_width
            slot_right = meta_left - px(META_SPACING) + px(4)

        action_lefts: dict[str, float] = {}
        for name in self.action_names(item_type):
            if self.action_visible(name, index) is False:
                continue
            action_lefts[name] = slot_right - action_size
            slot_right -= action_size + px(2)
        actions_left = slot_right + px(2)

        # Lead: checkbox, type icon or avatar
        lead_size = px(CHECK_SIZE if item_type == ITEM_TODO else AVATAR_SIZE)
        left = rect.left() + px(CARD_PADDING_H)
        text_left = left + lead_size + px(CHECK_SPACING)
        content_right = actions_left - px(6)
        text_width = max(px(40), content_right - text_left)

        # Condition of a todo on the right of the first line, the title takes the rest
        condition = (index.data(CONDITION_ROLE) or "") if item_type == ITEM_TODO else ""
        condition_width = 0.0
        if condition:
            condition_width = min(metrics.horizontalAdvance(condition) + 1.0, max(px(60), (content_right - text_left) * CONDITION_MAX_SHARE))
            text_width = max(px(40), content_right - condition_width - px(CONDITION_SPACING) - text_left)

        # Wrapped title
        title_font = QFont(font)
        title_font.setStrikeOut(done)
        layout = QTextLayout((index.data(Qt.ItemDataRole.DisplayRole) or "").replace("\n", " "), title_font)
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(text_option)
        layout.beginLayout()
        title_height = 0.0
        while True:
            line = layout.createLine()
            if line.isValid() is False:
                break
            line.setLineWidth(text_width)
            line.setPosition(QPointF(0.0, title_height))
            title_height += line.height()
        layout.endLayout()
        title_height = max(title_height, line_height)

        subtitle = index.data(SUBTITLE_ROLE) or ""
        subtitle_height = px(SUBTITLE_SPACING) + line_height if subtitle else 0.0
        text_height = title_height + subtitle_height

        # Notes and links are centered vertically, todos start at the first line
        if item_type != ITEM_TODO:
            content_height = max(text_height, lead_size)
            lead_offset = (content_height - lead_size) / 2
            text_offset = (content_height - text_height) / 2
        else:
            lead_offset = max(0.0, (line_height - lead_size) / 2)
            text_offset = max(0.0, (lead_size - line_height) / 2)
            content_height = max(text_offset + text_height, lead_offset + lead_size)

        height = math.ceil(content_height + px(CARD_PADDING_V) * 2 + px(CARD_GAP))
        card_top = rect.top() + px(CARD_GAP) / 2
        content_top = card_top + px(CARD_PADDING_V)
        text_top = content_top + text_offset
        if item_type != ITEM_TODO:
            action_center = content_top + content_height / 2
        else:
            action_center = text_top + line_height / 2

        actions = {}
        for name, action_left in action_lefts.items():
            actions[name] = QRectF(action_left, action_center - action_size / 2, action_size, action_size)

        if meta_width > 0:
            meta_rect = QRectF(meta_left, text_top, meta_width, line_height)
        condition_rect = QRectF(content_right - condition_width, text_top, condition_width, line_height) if condition_width > 0 else QRectF()

        return CardGeometry(
            card=QRectF(rect.left(), card_top, rect.width(), height - px(CARD_GAP)),
            lead=QRectF(left, content_top + lead_offset, lead_size, lead_size),
            text_origin=QPointF(text_left, text_top),
            layout=layout,
            title_rect=QRectF(text_left, text_top, text_width, title_height),
            subtitle_rect=QRectF(text_left, text_top + title_height + px(SUBTITLE_SPACING), text_width, line_height),
            meta_rect=meta_rect,
            actions=actions,
            condition_rect=condition_rect,
        )

    def header_band(self, rect: QRect, font: QFont) -> QRectF:
        line_height = QFontMetricsF(font).height()
        return QRectF(rect.left(), rect.top() + px(SECTION_TOP) - px(SECTION_BAND_PADDING), rect.width(), line_height + px(SECTION_BAND_PADDING) * 2)

    def _header_count_rect(self, band: QRectF, font: QFont) -> QRectF:
        width = QFontMetricsF(font).horizontalAdvance(COUNT_SLOT_TEXT)
        right = band.right() - px(CARD_PADDING_H)
        return QRectF(right - width, band.top(), width, band.height())

    def header_text_left(self, rect: QRect) -> float:
        return rect.left() + px(SECTION_TEXT_LEFT)

    def section_add_rect(self, rect: QRect, font: QFont) -> QRectF:
        band = self.header_band(rect, font)
        size = px(ACTION_SIZE)
        right = self._header_count_rect(band, font).left() - px(META_SPACING) + px(4)
        return QRectF(right - size, band.center().y() - size / 2, size, size)

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        width = self._view.viewport().width()
        if index.data(KIND_ROLE) == KIND_SPACER:
            return QSize(width, ipx(LIST_END_SPACE))
        if index.data(KIND_ROLE) in (KIND_SECTION, KIND_DONE):
            metrics = QFontMetrics(option.font)
            return QSize(width, metrics.height() + ipx(SECTION_TOP) + ipx(SECTION_BOTTOM))

        geometry = self.card_geometry(QRect(0, 0, width, 0), option.font, index)
        return QSize(width, math.ceil(geometry.card.bottom() + px(CARD_GAP) / 2))

    # Painting
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        if index.data(KIND_ROLE) == KIND_SPACER:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if index.data(KIND_ROLE) in (KIND_SECTION, KIND_DONE):
            self._paint_header(painter, option, index)
        else:
            self._paint_card(painter, option, index)
        painter.restore()

    def _paint_header(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        rect = option.rect
        is_done = index.data(KIND_ROLE) == KIND_DONE
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver) and self._view.drag_active is False
        band = self.header_band(rect, option.font)

        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.theme.hover if self.theme.is_dark else self.theme.divider)
            painter.drawRoundedRect(band, px(CARD_RADIUS), px(CARD_RADIUS))

        color = self.theme.muted if is_done else self.theme.text
        paint_chevron(painter, QPointF(rect.left() + px(SECTION_CHEVRON_LEFT), band.center().y() + 0.5), bool(index.data(EXPANDED_ROLE)), self.theme.muted)

        count = index.data(COUNT_ROLE) or 0
        count_rect = self._header_count_rect(band, option.font)
        if count:
            painter.setFont(option.font)
            painter.setPen(self.theme.muted)
            painter.drawText(count_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(count))
        text_right = count_rect.left() - px(META_SPACING)

        # Add icon of groups, always visible
        if is_done is False:
            add_rect = self.section_add_rect(rect, option.font)
            hover_pos = self._view.hover_pos if hovered else None
            active = hover_pos is not None and add_rect.contains(QPointF(hover_pos))
            paint_action(painter, add_rect, self._icons["add"][1 if active else 0], active, self.theme)
            text_right = add_rect.left() - px(6)

        font = QFont(option.font)
        font.setWeight(QFont.Weight.DemiBold)
        metrics = QFontMetrics(font)
        text_left = self.header_text_left(rect)
        text_width = max(0, round(text_right - text_left))
        text = metrics.elidedText(index.data(Qt.ItemDataRole.DisplayRole) or "", Qt.TextElideMode.ElideRight, text_width)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(QRectF(text_left, band.top(), text_width, band.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

    def _paint_card(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        item_type = index.data(TYPE_ROLE)
        done = item_type == ITEM_TODO and is_checked(index.data(Qt.ItemDataRole.CheckStateRole))
        geometry = self.card_geometry(option.rect, option.font, index)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver) and self._view.drag_active is False
        flagged = bool(index.data(FLAGGED_ROLE)) and done is False

        # Card with Outlook style highlight, accent bar while hovered
        if flagged:
            background = self.theme.flag_selected if selected else self.theme.flag_background
        elif selected:
            background = self.theme.accent_selected
        elif hovered:
            background = self.theme.accent_hover
        else:
            background = self.theme.base
        card = geometry.card.adjusted(0.5, 0.5, -0.5, -0.5)
        radius = px(CARD_RADIUS)
        painter.setPen(QPen(self.theme.divider, 1))
        painter.setBrush(background)
        painter.drawRoundedRect(card, radius, radius)

        if hovered:
            card_path = QPainterPath()
            card_path.addRoundedRect(card, radius, radius)
            painter.save()
            painter.setClipPath(card_path)
            painter.fillRect(QRectF(card.left(), card.top(), px(ACCENT_BAR_WIDTH), card.height()), self.theme.accent)
            painter.restore()

        self._paint_lead(painter, geometry.lead, item_type, done, selected, index)

        # Title and subtitle
        if done:
            painter.setPen(self.theme.muted)
        elif flagged:
            painter.setPen(self.theme.flag)
        else:
            painter.setPen(self.theme.text)
        geometry.layout.draw(painter, geometry.text_origin)

        subtitle = index.data(SUBTITLE_ROLE) or ""
        if subtitle:
            metrics = QFontMetrics(option.font)
            painter.setFont(option.font)
            painter.setPen(self.theme.muted)
            elided = metrics.elidedText(subtitle, Qt.TextElideMode.ElideRight, round(geometry.subtitle_rect.width()))
            painter.drawText(geometry.subtitle_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)

        # Condition of todos: red when overdue or due today, blue when the start is reached
        condition = index.data(CONDITION_ROLE) or ""
        if item_type == ITEM_TODO and condition and geometry.condition_rect.isNull() is False:
            state = index.data(STATE_ROLE) or ""
            if state in (CONDITION_OVERDUE, CONDITION_DUE):
                painter.setPen(self.theme.flag)
            elif state == CONDITION_STARTED:
                painter.setPen(self.theme.accent)
            else:
                painter.setPen(self.theme.muted)
            painter.setFont(option.font)
            elided = QFontMetrics(option.font).elidedText(condition, Qt.TextElideMode.ElideRight, round(geometry.condition_rect.width()))
            painter.drawText(geometry.condition_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, elided)

        # Attachment count of todos
        count = index.data(COUNT_ROLE) or 0
        if item_type == ITEM_TODO and count:
            meta_rect = geometry.meta_rect
            icon_size = ipx(ICON_SIZE)
            icon_top = round(meta_rect.top() + (meta_rect.height() - icon_size) / 2)
            self._attachment_icon.paint(painter, QRect(round(meta_rect.left()), icon_top, icon_size, icon_size))
            painter.setFont(option.font)
            painter.setPen(self.theme.muted)
            text_rect = meta_rect.adjusted(icon_size + px(META_ICON_SPACING), 0, 0, 0)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(count))

        # Actions in fixed places
        hover_pos = self._view.hover_pos if hovered else None
        for name, action_rect in geometry.actions.items():
            if self.action_visible(name, index) is False:
                continue
            active = hover_pos is not None and action_rect.contains(QPointF(hover_pos))
            if name == "flag" and index.data(FLAGGED_ROLE):
                icon = self._flag_icon_set
            else:
                icon = self._icons[name][1 if active else 0]
            paint_action(painter, action_rect, icon, active, self.theme)

    def _paint_lead(self, painter: QPainter, rect: QRectF, item_type: str, done: bool, selected: bool, index) -> None:
        # The circle behind the icon stands out from the selected card
        circle = self.theme.base if selected else self.theme.accent_selected
        if item_type == ITEM_TODO:
            check = rect.adjusted(px(0.75), px(0.75), -px(0.75), -px(0.75))
            check_radius = px(4)
            if done:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(self.theme.muted)
                painter.drawRoundedRect(check, check_radius, check_radius)
                check_pen = QPen(self.theme.base, px(2))
                check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(check_pen)
                painter.drawPolyline([
                    QPointF(check.left() + check.width() * 0.24, check.top() + check.height() * 0.52),
                    QPointF(check.left() + check.width() * 0.43, check.top() + check.height() * 0.70),
                    QPointF(check.left() + check.width() * 0.77, check.top() + check.height() * 0.32),
                ])
            else:
                painter.setPen(QPen(self.theme.muted, px(1.5)))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(check, check_radius, check_radius)
            return

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(circle)
        painter.drawEllipse(rect)
        icon = self._note_icon if item_type == ITEM_NOTE else self._link_icon
        size = ipx(ICON_SIZE)
        icon_rect = QRect(round(rect.center().x() - size / 2), round(rect.center().y() - size / 2), size, size)
        icon.paint(painter, icon_rect)

    # Inline renaming
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index) -> QWidget:
        return create_inline_editor(parent)

    def setEditorData(self, editor: QWidget, index) -> None:
        raw = index.data(TITLE_ROLE)
        editor.setText(raw if raw is not None else index.data(Qt.ItemDataRole.DisplayRole) or "")
        editor.selectAll()

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index) -> None:
        line_height = QFontMetricsF(option.font).height()
        if index.data(KIND_ROLE) == KIND_SECTION:
            left = self.header_text_left(option.rect) - px(5)
            right = self.section_add_rect(option.rect, option.font).left() - px(4)
            band = self.header_band(option.rect, option.font)
            top = band.center().y() - line_height / 2 - px(INLINE_EDIT_PADDING)
        else:
            # Same height for every kind of entry, the subtitle below stays visible
            geometry = self.card_geometry(option.rect, option.font, index)
            left = geometry.title_rect.left() - px(5)
            right = geometry.title_rect.right() + px(4)
            top = geometry.title_rect.top() - px(INLINE_EDIT_PADDING)
        editor.setGeometry(QRect(round(left), round(top), round(right - left), round(line_height + px(INLINE_EDIT_PADDING) * 2)))


# List widgets
class ProjectListWidget(QListWidget):
    """Project sidebar with archive, right click menu and drag and drop for projects and items"""

    context_requested = Signal(str, QPoint)
    archive_toggle_requested = Signal()
    project_dropped = Signal(str, str, str)
    item_dropped = Signal(str, list, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("projectList")
        self.setMouseTracking(True)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setDragEnabled(False)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(False)

        self.hover_pos: Optional[QPoint] = None
        self.drop_row = -1
        self.drop_zone = ""
        self.drag_active = False
        self.project_drop_validator = None
        self.item_drop_validator = None

        self._press_pos: Optional[QPoint] = None
        self._press_row = -1

    def _project_delegate(self) -> ProjectDelegate:
        return self.itemDelegate()

    def find_row(self, project_id: str) -> Optional[QListWidgetItem]:
        for row in range(self.count()):
            item = self.item(row)
            if item.data(KIND_ROLE) == KIND_PROJECT and item.data(ID_ROLE) == project_id:
                return item
        return None

    # Mouse handling
    def mousePressEvent(self, event) -> None:
        position = event.position().toPoint()
        self._press_pos = None
        self._press_row = -1

        index = self.indexAt(position)
        if event.button() == Qt.MouseButton.LeftButton and index.isValid():
            self._press_pos = position
            self._press_row = index.row()
            if index.data(KIND_ROLE) == KIND_ARCHIVE_HEADER:
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        position = event.position().toPoint()
        self.hover_pos = position
        self.viewport().update()

        if self._press_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if (position - self._press_pos).manhattanLength() >= QApplication.startDragDistance():
                item = self.item(self._press_row)
                self._press_pos = None
                if item is not None and item.data(KIND_ROLE) == KIND_PROJECT and not item.data(GENERAL_ROLE):
                    self._start_project_drag(item)
                    return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        position = event.position().toPoint()
        pressed_row = self._press_row
        was_pressed = self._press_pos is not None
        self._press_pos = None
        self._press_row = -1

        index = self.indexAt(position)
        if was_pressed and index.isValid() and index.row() == pressed_row and event.button() == Qt.MouseButton.LeftButton:
            if index.data(KIND_ROLE) == KIND_ARCHIVE_HEADER:
                QTimer.singleShot(0, self.archive_toggle_requested.emit)
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        index = self.indexAt(event.position().toPoint())
        if index.isValid() and index.data(KIND_ROLE) == KIND_ARCHIVE_HEADER:
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        index = self.indexAt(event.pos())
        global_pos = event.globalPos()
        if index.isValid() and index.data(KIND_ROLE) == KIND_PROJECT:
            self.setCurrentIndex(index)
            project_id = index.data(ID_ROLE)
            QTimer.singleShot(0, lambda: self.context_requested.emit(project_id, global_pos))
        elif index.isValid() is False:
            QTimer.singleShot(0, lambda: self.context_requested.emit("", global_pos))
        event.accept()

    def viewportEvent(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Leave:
            self.hover_pos = None
            self.viewport().update()
        return super().viewportEvent(event)

    # Drag and drop
    def _start_project_drag(self, item: QListWidgetItem) -> None:
        self.drag_active = True
        rect = self.visualItemRect(item)
        pixmap = self.viewport().grab(rect)

        mime = QMimeData()
        mime.setData(PROJECT_MIME_TYPE, QByteArray(item.data(ID_ROLE).encode("utf-8")))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(24, rect.height() // 2))
        drag.exec(Qt.DropAction.MoveAction)

        self.drag_active = False
        self._clear_drop()

    def _clear_drop(self) -> None:
        self.drop_row = -1
        self.drop_zone = ""
        self.viewport().update()

    def _drop_target(self, event) -> Optional[tuple[int, str, str]]:
        mime = event.mimeData()
        position = event.position().toPoint()
        index = self.indexAt(position)

        # Items land on projects
        if mime.hasFormat(ITEM_MIME_TYPE):
            if index.isValid() is False or index.data(KIND_ROLE) != KIND_PROJECT:
                return None
            item_type, item_ids = parse_item_payload(mime)
            if self.item_drop_validator is None or self.item_drop_validator(item_type, item_ids, index.data(ID_ROLE)) is False:
                return None
            return index.row(), DROP_ONTO, index.data(ID_ROLE)

        if mime.hasFormat(PROJECT_MIME_TYPE) is False or self.count() == 0 or self.project_drop_validator is None:
            return None
        dragged_id = bytes(mime.data(PROJECT_MIME_TYPE)).decode("utf-8")

        # Below the last row counts as after the last row
        if index.isValid() is False:
            index = self.model().index(self.count() - 1, 0)
            zone = DROP_AFTER
        else:
            rect = self.visualRect(index)
            relative = (position.y() - rect.top()) / max(1, rect.height())
            if index.data(KIND_ROLE) == KIND_ARCHIVE_HEADER:
                zone = DROP_BEFORE if relative < 0.25 else DROP_ONTO
            else:
                zone = DROP_BEFORE if relative < 0.5 else DROP_AFTER

        target_id = ARCHIVE_TARGET if index.data(KIND_ROLE) == KIND_ARCHIVE_HEADER else index.data(ID_ROLE)
        if self.project_drop_validator(dragged_id, target_id, zone):
            return index.row(), zone, target_id
        return None

    def dragEnterEvent(self, event) -> None:
        mime = event.mimeData()
        if mime.hasFormat(PROJECT_MIME_TYPE) or mime.hasFormat(ITEM_MIME_TYPE):
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        target = self._drop_target(event)
        if target is None:
            self._clear_drop()
            event.ignore()
            return
        self.drop_row = target[0]
        self.drop_zone = target[1]
        self.viewport().update()
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event) -> None:
        self._clear_drop()
        event.accept()

    def dropEvent(self, event) -> None:
        target = self._drop_target(event)
        self._clear_drop()
        if target is None:
            event.ignore()
            return

        mime = event.mimeData()
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        if mime.hasFormat(ITEM_MIME_TYPE):
            item_type, item_ids = parse_item_payload(mime)
            QTimer.singleShot(0, lambda: self.item_dropped.emit(item_type, item_ids, target[2]))
            return

        dragged_id = bytes(mime.data(PROJECT_MIME_TYPE)).decode("utf-8")
        QTimer.singleShot(0, lambda: self.project_dropped.emit(dragged_id, target[2], target[1]))

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        item = self.item(self.drop_row) if self.drop_row >= 0 else None
        if item is None:
            return

        delegate = self._project_delegate()
        row = self.visualItemRect(item)

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self.drop_zone == DROP_ONTO:
            painter.setPen(QPen(delegate.theme.accent, px(1.5)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(row).adjusted(px(3), px(2), -px(3), -px(2)), px(4), px(4))
        else:
            y = row.top() + 1 if self.drop_zone == DROP_BEFORE else row.bottom()
            left = delegate.text_left(row) - px(6)
            painter.setPen(QPen(delegate.theme.accent, px(2)))
            painter.drawLine(QPointF(left, y), QPointF(row.right() - px(GROUP_PADDING_H), y))
            painter.setBrush(delegate.theme.accent)
            painter.drawEllipse(QPointF(left, y), px(3), px(3))
        painter.end()


class ItemListWidget(QListWidget):
    """Middle list with cards, collapsible groups, inline renaming, multi selection, right click menu and drag and drop"""

    action_requested = Signal(str, str)
    section_add_requested = Signal(str)
    context_requested = Signal(str, str, QPoint)
    section_toggle_requested = Signal(str)
    section_rename_requested = Signal(str, bool)
    done_toggle_requested = Signal()
    item_dropped = Signal(list, str, str, bool)
    section_dropped = Signal(str, str, bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("itemList")
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setMouseTracking(True)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(ipx(LIST_SCROLL_STEP))
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setUniformItemSizes(False)
        self.setWordWrap(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(False)

        self.item_type = ITEM_TODO
        self.empty_text = ""
        self.hover_pos: Optional[QPoint] = None
        self.drag_active = False
        self._drop_line: Optional[tuple[float, float, float]] = None
        self._drop_band: Optional[QRectF] = None

        self._press_pos: Optional[QPoint] = None
        self._press_row = -1
        self._press_hit: Optional[tuple[str, str, str]] = None
        self._deferred_select = False
        self._last_toggle: tuple[str, float] = ("", 0.0)

    def relayout(self) -> None:
        self.scheduleDelayedItemsLayout()

    def _item_delegate(self) -> ItemDelegate:
        return self.itemDelegate()

    def find_row(self, kind: str, row_id: str) -> Optional[QListWidgetItem]:
        for row in range(self.count()):
            item = self.item(row)
            if item.data(KIND_ROLE) == kind and item.data(ID_ROLE) == row_id:
                return item
        return None

    def selected_ids(self) -> list[str]:
        # Selected entries in the order of the list
        ids: list[str] = []
        for row in range(self.count()):
            item = self.item(row)
            if item.isSelected() and item.data(KIND_ROLE) == KIND_ITEM:
                ids.append(item.data(ID_ROLE))
        return ids

    def hit_test(self, position: QPoint) -> tuple[str, str, str]:
        index = self.indexAt(position)
        if index.isValid() is False:
            return "", "", ""

        kind = index.data(KIND_ROLE)
        rect = self.visualRect(index)
        point = QPointF(position)
        delegate = self._item_delegate()
        if kind == KIND_SPACER:
            return "", "", ""
        if kind == KIND_DONE:
            return "done", "", ""
        if kind == KIND_SECTION:
            if delegate.section_add_rect(rect, self.font()).contains(point):
                return "section_add", "", index.data(ID_ROLE)
            return "section", "", index.data(ID_ROLE)

        geometry = delegate.card_geometry(rect, self.font(), index)
        item_id = index.data(ID_ROLE)
        for name, action_rect in geometry.actions.items():
            if action_rect.contains(point) and delegate.action_visible(name, index):
                return "action", name, item_id
        if index.data(TYPE_ROLE) == ITEM_TODO and geometry.lead.adjusted(-px(5), -px(5), px(5), px(5)).contains(point):
            return "action", "check", item_id
        if geometry.card.contains(point):
            return "item", "", item_id
        return "", "", ""

    # Mouse handling
    def mousePressEvent(self, event) -> None:
        position = event.position().toPoint()
        self._press_hit = None
        self._press_pos = None
        self._press_row = -1
        self._deferred_select = False

        if event.button() == Qt.MouseButton.LeftButton:
            hit = self.hit_test(position)
            if hit[0] in ("action", "section_add"):
                self._press_hit = hit
                event.accept()
                return

            index = self.indexAt(position)
            if hit[0] in ("section", "done"):
                self._press_pos = position
                self._press_row = index.row()
                event.accept()
                return
            if hit[0] == "item":
                self._press_pos = position
                self._press_row = index.row()

                # A click into a selection keeps it for dragging, the release selects the entry alone
                modifiers = event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
                if modifiers == Qt.KeyboardModifier.NoModifier and self.item(index.row()).isSelected() and len(self.selected_ids()) > 1:
                    self._deferred_select = True
                    self.setFocus()
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        position = event.position().toPoint()
        self.hover_pos = position
        self.viewport().update()

        if self._press_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if (position - self._press_pos).manhattanLength() >= QApplication.startDragDistance():
                item = self.item(self._press_row)
                self._press_pos = None
                if item is not None and item.data(KIND_ROLE) == KIND_SECTION:
                    self._start_drag(item, SECTION_MIME_TYPE, item.data(ID_ROLE))
                    return
                if item is not None and item.data(KIND_ROLE) == KIND_ITEM and item.flags() & Qt.ItemFlag.ItemIsDragEnabled:
                    item_ids = self._drag_ids(item)
                    self._start_drag(item, ITEM_MIME_TYPE, item_payload(item.data(TYPE_ROLE), item_ids), len(item_ids))
                    return

        # Moving with the pressed button drags entries, it never selects a range
        if self._press_hit is not None or event.buttons() & Qt.MouseButton.LeftButton:
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        position = event.position().toPoint()
        if self._press_hit is not None:
            hit = self._press_hit
            self._press_hit = None
            if self.hit_test(position) == hit:
                if hit[0] == "section_add":
                    QTimer.singleShot(0, lambda: self.section_add_requested.emit(hit[2]))
                else:
                    QTimer.singleShot(0, lambda: self.action_requested.emit(hit[1], hit[2]))
            event.accept()
            return

        pressed_row = self._press_row
        was_pressed = self._press_pos is not None
        deferred_select = self._deferred_select
        self._press_pos = None
        self._press_row = -1
        self._deferred_select = False

        index = self.indexAt(position)
        if was_pressed and index.isValid() and index.row() == pressed_row and event.button() == Qt.MouseButton.LeftButton:
            if deferred_select:
                self.setCurrentItem(self.item(index.row()), QItemSelectionModel.SelectionFlag.ClearAndSelect)
                event.accept()
                return
            if index.data(KIND_ROLE) == KIND_DONE:
                QTimer.singleShot(0, self.done_toggle_requested.emit)
                event.accept()
                return
            if index.data(KIND_ROLE) == KIND_SECTION:
                group_id = index.data(ID_ROLE)
                self._last_toggle = (group_id, time.monotonic())
                QTimer.singleShot(0, lambda: self.section_toggle_requested.emit(group_id))
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        # The release after a double click does not toggle or add again
        self._press_pos = None
        self._press_row = -1
        self._press_hit = None
        position = event.position().toPoint()
        kind, name, target = self.hit_test(position)
        if kind == "section":
            # A toggle by the first click of this double click is undone
            toggled_id, toggled_at = self._last_toggle
            undo_toggle = toggled_id == target and time.monotonic() - toggled_at < QApplication.doubleClickInterval() / 1000 + 0.2
            self._last_toggle = ("", 0.0)
            QTimer.singleShot(0, lambda: self.section_rename_requested.emit(target, undo_toggle))
        elif kind == "item":
            item = self.itemAt(position)
            if item is not None:
                self.setCurrentItem(item, QItemSelectionModel.SelectionFlag.ClearAndSelect)
                self.editItem(item)
        event.accept()

    def contextMenuEvent(self, event) -> None:
        kind, name, target = self.hit_test(event.pos())
        if kind == "action":
            kind = "item"
        elif kind == "section_add":
            kind = "section"
        if kind == "item":
            # A right click into a selection keeps it
            item = self.itemAt(event.pos())
            if item is not None and item.isSelected() is False:
                self.setCurrentItem(item, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        if kind in ("item", "section", ""):
            global_pos = event.globalPos()
            QTimer.singleShot(0, lambda: self.context_requested.emit(kind, target, global_pos))
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape and self.selectedItems():
            self.clearSelection()
            event.accept()
            return
        super().keyPressEvent(event)

    def viewportEvent(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Leave:
            self.hover_pos = None
            self.viewport().update()
        elif event.type() == QEvent.Type.ToolTip:
            tooltip = self._tooltip(event.pos())
            if tooltip:
                QToolTip.showText(event.globalPos(), tooltip, self.viewport())
            else:
                QToolTip.hideText()
            return True
        return super().viewportEvent(event)

    def _tooltip(self, position: QPoint) -> str:
        kind, name, target = self.hit_test(position)
        if kind == "section_add":
            return tr(SECTION_ADD_TOOLTIPS[self.item_type])
        if kind != "action":
            if kind == "item":
                index = self.indexAt(position)
                return index.data(TOOLTIP_ROLE) or ""
            return ""
        if name == "flag":
            return tr("Markierung entfernen")
        tooltip = ITEM_ACTION_TOOLTIPS.get(name, "")
        return tr(tooltip) if tooltip else ""

    # Drag and drop
    def _drag_ids(self, item: QListWidgetItem) -> list[str]:
        # An entry inside the selection takes all selected open entries along
        if item.isSelected() is False:
            return [item.data(ID_ROLE)]
        ids: list[str] = []
        for row in range(self.count()):
            entry = self.item(row)
            if entry.isSelected() and entry.data(KIND_ROLE) == KIND_ITEM and entry.flags() & Qt.ItemFlag.ItemIsDragEnabled:
                ids.append(entry.data(ID_ROLE))
        return ids

    def _start_drag(self, item: QListWidgetItem, mime_type: str, payload: str, count: int = 1) -> None:
        self.drag_active = True
        rect = self.visualItemRect(item)
        pixmap = self.viewport().grab(rect)
        offset = 0
        if count > 1:
            pixmap, offset = self._add_count_badge(pixmap, count)

        mime = QMimeData()
        mime.setData(mime_type, QByteArray(payload.encode("utf-8")))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(24, min(rect.height() // 2, 24) + offset))
        drag.exec(Qt.DropAction.MoveAction)

        self.drag_active = False
        self.setState(QAbstractItemView.State.NoState)
        self._clear_drop()

    def _add_count_badge(self, pixmap: QPixmap, count: int) -> tuple[QPixmap, int]:
        # Number of dragged entries as a badge on the top right corner of the card
        ratio = pixmap.devicePixelRatio()
        width = pixmap.width() / ratio
        height = pixmap.height() / ratio
        radius = px(11)
        offset = math.ceil(radius)
        canvas = QPixmap(round((width + offset) * ratio), round((height + offset) * ratio))
        canvas.setDevicePixelRatio(ratio)
        canvas.fill(Qt.GlobalColor.transparent)

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawPixmap(QPointF(0, offset), pixmap)
        center = QPointF(width - px(4), offset + px(CARD_GAP) / 2 + px(2))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._item_delegate().theme.accent)
        painter.drawEllipse(center, radius, radius)
        font = QFont(self.font())
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), Qt.AlignmentFlag.AlignCenter, str(count))
        painter.end()
        return canvas, offset

    def _clear_drop(self) -> None:
        self._drop_line = None
        self._drop_band = None
        self.viewport().update()

    def _is_open_item(self, item: QListWidgetItem) -> bool:
        return item.data(KIND_ROLE) == KIND_ITEM and item.data(DONE_ROLE) is not True

    def content_count(self) -> int:
        # The space at the end of the list is not content
        count = self.count()
        if count > 0 and self.item(count - 1).data(KIND_ROLE) == KIND_SPACER:
            count -= 1
        return count

    def _row_at(self, position: QPoint) -> int:
        row = self.indexAt(position).row()
        return row if row < self.content_count() else -1

    def _section_rows(self, group_id: str) -> tuple[int, int]:
        first = -1
        last = -1
        for row in range(self.count()):
            item = self.item(row)
            if item.data(KIND_ROLE) == KIND_SECTION and item.data(ID_ROLE) == group_id:
                first = row
                last = row
            elif first >= 0 and item.data(KIND_ROLE) == KIND_ITEM and item.data(SECTION_ROLE) == group_id:
                last = row
            elif first >= 0:
                break
        return first, last

    def _line_at(self, row: int, after: bool) -> tuple[float, float, float]:
        rect = self.visualItemRect(self.item(row))
        y = rect.bottom() + 1 if after else rect.top()
        return float(y), rect.left() + px(4), rect.right() - px(4)

    def _item_drop_target(self, event) -> Optional[tuple[str, str, bool]]:
        item_type, item_ids = parse_item_payload(event.mimeData())
        if item_type != self.item_type or not item_ids:
            return None

        position = event.position().toPoint()
        row = self._row_at(position)
        if row < 0:
            # Below the last row
            if self.content_count() == 0:
                self._drop_line = None
                self._drop_band = None
                return "", "", True
            row = self.content_count() - 1
            last = self.item(row)
            if last.data(KIND_ROLE) == KIND_SECTION:
                self._drop_band = self._item_delegate().header_band(self.visualItemRect(last), self.font())
                self._drop_line = None
                return last.data(ID_ROLE), "", True
            if self._is_open_item(last) is False:
                return None
            self._drop_line = self._line_at(row, True)
            self._drop_band = None
            return last.data(SECTION_ROLE) or "", last.data(ID_ROLE), True

        target = self.item(row)
        if target.data(KIND_ROLE) == KIND_SECTION:
            self._drop_band = self._item_delegate().header_band(self.visualItemRect(target), self.font())
            self._drop_line = None
            return target.data(ID_ROLE), "", True
        if self._is_open_item(target) is False:
            return None

        rect = self.visualItemRect(target)
        after = position.y() > rect.center().y()
        self._drop_line = self._line_at(row, after)
        self._drop_band = None
        return target.data(SECTION_ROLE) or "", target.data(ID_ROLE), after

    def _section_drop_target(self, event) -> Optional[tuple[str, str, bool]]:
        dragged_id = bytes(event.mimeData().data(SECTION_MIME_TYPE)).decode("utf-8")
        sections = [self.item(row).data(ID_ROLE) for row in range(self.count()) if self.item(row).data(KIND_ROLE) == KIND_SECTION]
        if len(sections) < 2:
            return None

        position = event.position().toPoint()
        row = self._row_at(position)
        target = self.item(row) if row >= 0 else None
        if target is None or target.data(KIND_ROLE) == KIND_DONE or target.data(DONE_ROLE) is True:
            group_id = sections[-1]
            after = True
        elif target.data(KIND_ROLE) == KIND_SECTION:
            group_id = target.data(ID_ROLE)
            first, last = self._section_rows(group_id)
            top = self.visualItemRect(self.item(first)).top()
            bottom = self.visualItemRect(self.item(last)).bottom()
            after = position.y() > (top + bottom) / 2
        elif not target.data(SECTION_ROLE):
            group_id = sections[0]
            after = False
        else:
            group_id = target.data(SECTION_ROLE)
            first, last = self._section_rows(group_id)
            top = self.visualItemRect(self.item(first)).top()
            bottom = self.visualItemRect(self.item(last)).bottom()
            after = position.y() > (top + bottom) / 2

        if group_id == dragged_id:
            return None
        first, last = self._section_rows(group_id)
        self._drop_line = self._line_at(last if after else first, after)
        self._drop_band = None
        return group_id, "", after

    def _drop_target(self, event) -> Optional[tuple[str, str, bool]]:
        mime = event.mimeData()
        if mime.hasFormat(ITEM_MIME_TYPE):
            return self._item_drop_target(event)
        if mime.hasFormat(SECTION_MIME_TYPE):
            return self._section_drop_target(event)
        return None

    def dragEnterEvent(self, event) -> None:
        mime = event.mimeData()
        if mime.hasFormat(ITEM_MIME_TYPE) or mime.hasFormat(SECTION_MIME_TYPE):
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        target = self._drop_target(event)
        if target is None:
            self._clear_drop()
            event.ignore()
            return
        self.viewport().update()
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event) -> None:
        self._clear_drop()
        event.accept()

    def dropEvent(self, event) -> None:
        target = self._drop_target(event)
        mime = event.mimeData()
        self._clear_drop()
        if target is None:
            event.ignore()
            return

        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        if mime.hasFormat(ITEM_MIME_TYPE):
            item_type, item_ids = parse_item_payload(mime)
            QTimer.singleShot(0, lambda: self.item_dropped.emit(item_ids, target[0], target[1], target[2]))
            return
        dragged_id = bytes(mime.data(SECTION_MIME_TYPE)).decode("utf-8")
        QTimer.singleShot(0, lambda: self.section_dropped.emit(dragged_id, target[0], target[2]))

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        theme = self._item_delegate().theme
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Hint while the list is empty
        if self.content_count() == 0 and self.empty_text:
            painter.setPen(theme.muted)
            painter.setFont(self.font())
            painter.drawText(QRectF(0, px(24), self.viewport().width(), px(40)), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.empty_text)

        if self._drop_band is not None:
            painter.setPen(QPen(theme.accent, px(1.5)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self._drop_band.adjusted(px(1), 0, -px(1), 0), px(CARD_RADIUS), px(CARD_RADIUS))
        elif self._drop_line is not None:
            y, left, right = self._drop_line
            painter.setPen(QPen(theme.accent, px(2)))
            painter.drawLine(QPointF(left + px(3), y), QPointF(right, y))
            painter.setBrush(theme.accent)
            painter.drawEllipse(QPointF(left + px(3), y), px(3), px(3))
        painter.end()

# Detail widgets
class TitleEdit(QLineEdit):
    """Borderless single line title that ends with an ellipsis while not edited"""

    title_changed = Signal(str)
    submitted = Signal()

    def __init__(self, placeholder: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("titleEdit")
        self.setFrame(False)
        self.setAcceptDrops(False)
        self.setPlaceholderText(placeholder)
        self.setFont(header_font(self.font()))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.textEdited.connect(self.title_changed.emit)
        self.returnPressed.connect(self.submitted.emit)

    def apply_zoom(self) -> None:
        self.setFont(header_font(QApplication.font()))

    def set_title(self, text: str) -> None:
        self.blockSignals(True)
        self.setText(text)
        self.setCursorPosition(0)
        self.blockSignals(False)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.setCursorPosition(0)

    def paintEvent(self, event) -> None:
        if self.hasFocus():
            super().paintEvent(event)
            return

        text = self.text()
        color_role = QPalette.ColorRole.Text if text else QPalette.ColorRole.PlaceholderText
        rect = self.contentsRect().marginsRemoved(self.textMargins()).adjusted(2, 0, -2, 0)
        elided = self.fontMetrics().elidedText(text if text else self.placeholderText(), Qt.TextElideMode.ElideRight, rect.width())

        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(color_role))
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)
        painter.end()


class ElidedLabel(QLabel):
    """Single line label that ends with an ellipsis when the space is too small"""

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))
        text = self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideRight, self.contentsRect().width())
        painter.drawText(self.contentsRect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        painter.end()


class DropZone(QFrame):
    """Area for attachments with paper clip icon that opens the file selection on click"""

    clicked = Signal()

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setProperty("active", False)

        self._icon = QLabel()
        self._icon.setObjectName("dropZoneIcon")
        self._text = ElidedLabel(text)
        self._text.setObjectName("dropZoneText")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addStretch()
        layout.addWidget(self._icon)
        layout.addWidget(self._text)
        layout.addStretch()

    def set_active(self, active: bool) -> None:
        if self.property("active") == active:
            return
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def apply_theme(self, theme: Theme) -> None:
        size = ipx(ICON_SIZE)
        self._icon.setPixmap(create_attachment_icon(theme.muted).pixmap(size, size))

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


def version_numbers(text: str) -> Optional[tuple[int, ...]]:
    try:
        return tuple(int(part) for part in text.strip().lstrip("vV").split("."))
    except ValueError:
        return None


def is_newer_version(candidate: str, current: str) -> bool:
    candidate_numbers = version_numbers(candidate)
    current_numbers = version_numbers(current)
    return candidate_numbers is not None and current_numbers is not None and candidate_numbers > current_numbers


class UpdateState:
    """Result of the update check, once per start of the program"""

    checked = False
    version = ""
    url = ""


class UpdateChecker(QObject):
    """Looks up the newest release on GitHub in the background"""

    found = Signal(str, str)

    def start(self) -> None:
        if UpdateState.checked:
            return
        UpdateState.checked = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        # Without connection, proxy or answer nothing happens
        request = urllib.request.Request(UPDATE_API_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": f"{APP_NAME}/{APP_VERSION}"})
        try:
            with urllib.request.urlopen(request, timeout=UPDATE_TIMEOUT_SECONDS) as response:
                values = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, http.client.HTTPException):
            return
        if not isinstance(values, dict):
            return
        version = str(values.get("tag_name", "")).strip().lstrip("vV")
        if is_newer_version(version, APP_VERSION):
            self.found.emit(version, str(values.get("html_url") or RELEASES_URL))


class StatusBanner(QWidget):
    """Short message in a blue bar that slides up over the bottom of the window and back down"""

    def __init__(self, anchor: QWidget, parent: QWidget) -> None:
        super().__init__(parent)
        self._anchor = anchor
        self._text = ""
        self._leaving = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self._slide = QPropertyAnimation(self, QByteArray(b"pos"), self)
        self._slide.setDuration(STATUS_SLIDE_MS)
        self._slide.finished.connect(self._on_slide_finished)
        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self._slide_out)
        anchor.installEventFilter(self)
        self.hide()

    def show_message(self, text: str) -> None:
        self._text = text
        self._leaving = False
        self._hold_timer.stop()
        self._slide.stop()
        self.resize(self._anchor.width(), ipx(FOOTER_HEIGHT))
        if self.isVisible() is False:
            self.move(self._hidden_pos())
            self.show()
        self.raise_()
        self.update()
        self._slide_to(self._shown_pos(), QEasingCurve.Type.OutCubic)
        self._hold_timer.start(STATUS_DURATION_MS)

    def _shown_pos(self) -> QPoint:
        # Same height as the footers, over the full width of the window content
        return self._anchor.mapTo(self.parentWidget(), QPoint(0, self._anchor.height() - self.height()))

    def _hidden_pos(self) -> QPoint:
        return self._anchor.mapTo(self.parentWidget(), QPoint(0, self._anchor.height()))

    def _slide_to(self, target: QPoint, easing: QEasingCurve.Type) -> None:
        self._slide.stop()
        self._slide.setEasingCurve(easing)
        self._slide.setStartValue(self.pos())
        self._slide.setEndValue(target)
        self._slide.start()

    def _slide_out(self) -> None:
        self._leaving = True
        self._slide_to(self._hidden_pos(), QEasingCurve.Type.InCubic)

    def _on_slide_finished(self) -> None:
        if self._leaving:
            self.hide()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._anchor and event.type() == QEvent.Type.Resize and self.isVisible():
            self._slide.stop()
            self.resize(self._anchor.width(), ipx(FOOTER_HEIGHT))
            if self._leaving:
                self.hide()
            else:
                self.move(self._shown_pos())
        return False

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(STATUS_COLOR))
        painter.setPen(QColor(STATUS_TEXT_COLOR))
        painter.setFont(self.font())
        text_rect = self.rect().adjusted(ipx(COLUMN_PADDING), 0, -ipx(COLUMN_PADDING), 0)
        text = QFontMetrics(self.font()).elidedText(self._text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.end()


def tabular_figures(font: QFont) -> QFont:
    # Digits of equal width, so the numbers of numbered lists line up
    tabular = QFont(font)
    tabular.setFeature(QFont.Tag.fromString(TABULAR_FIGURES_FEATURE), 1)
    return tabular


def highlight_color() -> QColor:
    dark = QApplication.palette().color(QPalette.ColorRole.Base).lightness() < 128
    return QColor(HIGHLIGHT_DARK if dark else HIGHLIGHT_LIGHT)


def is_bullet_list(text_list) -> bool:
    return text_list is not None and text_list.format().style() == QTextListFormat.Style.ListStyleUndefined


def link_ranges(text: str) -> list[tuple[int, int, str]]:
    ranges: list[tuple[int, int, str]] = []
    for match in LINK_PATTERN.finditer(text):
        value = match.group(0).rstrip(LINK_TRAILING_CHARACTERS)
        if len(value) <= len("www."):
            continue
        ranges.append((match.start(), match.start() + len(value), value))
    return ranges


def link_format(href: str, color: QColor) -> QTextCharFormat:
    char_format = QTextCharFormat()
    char_format.setAnchor(True)
    char_format.setAnchorHref(href)
    char_format.setForeground(color)
    char_format.setFontUnderline(True)
    return char_format


def without_link(char_format: QTextCharFormat) -> QTextCharFormat:
    cleared = QTextCharFormat(char_format)
    cleared.setAnchor(False)
    for property_id in (
        QTextFormat.Property.AnchorHref,
        QTextFormat.Property.ForegroundBrush,
        QTextFormat.Property.TextUnderlineStyle,
        QTextFormat.Property.FontUnderline,
    ):
        cleared.clearProperty(property_id)
    return cleared


class RichTextEdit(QTextEdit):
    """Text editor with character formats, font sizes, highlight, bullet and numbered lists, clickable links and optional inline images"""

    image_activated = Signal(str)

    def __init__(self, placeholder: str, images: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("descriptionEdit")
        self.setAcceptRichText(True)
        self.setAcceptDrops(images)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setTabChangesFocus(True)
        self.viewport().setMouseTracking(True)
        self.document().setDocumentMargin(8)
        self.document().setIndentWidth(BULLET_INDENT)
        self.document().setDefaultFont(tabular_figures(self.font()))
        self.document().contentsChange.connect(self._on_contents_change)

        self._placeholder = placeholder
        self._images = images
        self._storage: Optional[Storage] = None
        self.context_actions = None
        self._loading = False
        self._linkifying = False
        self._linkify_pending = False
        self._press_pos: Optional[QPoint] = None

    def set_storage(self, storage: Optional[Storage]) -> None:
        self._storage = storage

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange:
            self.document().setDefaultFont(tabular_figures(self.font()))

    # Content
    def load_content(self, html_text: str, plain_text: str) -> None:
        self._loading = True
        self.blockSignals(True)
        if html_text:
            self.setHtml(html_text)
        else:
            self.setPlainText(plain_text)
        self.normalize_document()
        self._linkify()
        self.document().clearUndoRedoStacks()
        self.document().setModified(False)
        self.blockSignals(False)
        self._loading = False

    def normalize_document(self) -> None:
        # Text follows the editor font, sizes are steps of it, links and highlights take the current palette
        link_color = self.palette().color(QPalette.ColorRole.Link)
        marker_color = highlight_color()
        cursor = QTextCursor(self.document())
        changes: list[tuple[int, int, QTextCharFormat]] = []
        block = self.document().begin()
        while block.isValid():
            iterator = block.begin()
            while iterator.atEnd() is False:
                fragment = iterator.fragment()
                if fragment.isValid():
                    char_format = fragment.charFormat()
                    changed = False
                    if char_format.hasProperty(QTextFormat.Property.FontPointSize) or char_format.hasProperty(QTextFormat.Property.FontFamilies):
                        char_format.clearProperty(QTextFormat.Property.FontPointSize)
                        char_format.clearProperty(QTextFormat.Property.FontFamilies)
                        changed = True
                    if char_format.hasProperty(QTextFormat.Property.FontSizeAdjustment) and char_format.property(QTextFormat.Property.FontSizeAdjustment) == 0:
                        char_format.clearProperty(QTextFormat.Property.FontSizeAdjustment)
                        changed = True
                    if char_format.hasProperty(QTextFormat.Property.BackgroundBrush):
                        if char_format.background().style() == Qt.BrushStyle.NoBrush:
                            char_format.clearProperty(QTextFormat.Property.BackgroundBrush)
                        else:
                            char_format.setBackground(marker_color)
                        changed = True
                    if char_format.isAnchor():
                        char_format.setForeground(link_color)
                        char_format.setFontUnderline(True)
                        changed = True
                    if changed:
                        changes.append((fragment.position(), fragment.length(), char_format))
                iterator += 1

            # Bullets are drawn by the editor, numbered lists are always decimal
            text_list = block.textList()
            if text_list is not None:
                list_format = text_list.format()
                style = list_format.style()
                if style in (QTextListFormat.Style.ListDisc, QTextListFormat.Style.ListCircle, QTextListFormat.Style.ListSquare):
                    list_format.setStyle(QTextListFormat.Style.ListStyleUndefined)
                    text_list.setFormat(list_format)
                elif style not in (QTextListFormat.Style.ListStyleUndefined, QTextListFormat.Style.ListDecimal):
                    list_format.setStyle(QTextListFormat.Style.ListDecimal)
                    text_list.setFormat(list_format)
            block = block.next()

        # Formats change after reading, so merged fragments do not disturb the reading
        for position, length, char_format in changes:
            cursor.setPosition(position)
            cursor.setPosition(position + length, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(char_format)
        self.document().setModified(False)

    # Links
    def _on_contents_change(self, position: int, removed: int, added: int) -> None:
        if self._loading or self._linkifying or self._linkify_pending:
            return
        self._linkify_pending = True
        QTimer.singleShot(0, self._linkify)

    def _link_changes(self, block) -> list[tuple[int, int, Optional[str], Optional[QTextCharFormat]]]:
        ranges = link_ranges(block.text())
        changes: list[tuple[int, int, Optional[str], Optional[QTextCharFormat]]] = []
        linked: set[tuple[int, int, str]] = set()

        # Outdated link formats are removed
        iterator = block.begin()
        while iterator.atEnd() is False:
            fragment = iterator.fragment()
            iterator += 1
            if fragment.isValid() is False or fragment.charFormat().isAnchor() is False:
                continue
            start = fragment.position() - block.position()
            end = start + fragment.length()
            href = fragment.charFormat().anchorHref()
            owner = None
            for link_range in ranges:
                if link_range[0] <= start and end <= link_range[1] and href == link_range[2]:
                    owner = link_range
            if owner is None:
                changes.append((start, end, None, without_link(fragment.charFormat())))
            else:
                linked.add(owner)

        # Missing link formats are added
        for link_range in ranges:
            if self._is_linked(block, link_range) is False:
                changes.append((link_range[0], link_range[1], link_range[2], None))
        return changes

    @staticmethod
    def _is_linked(block, link_range: tuple[int, int, str]) -> bool:
        start, end, href = link_range
        iterator = block.begin()
        while iterator.atEnd() is False:
            fragment = iterator.fragment()
            iterator += 1
            if fragment.isValid() is False:
                continue
            fragment_start = fragment.position() - block.position()
            fragment_end = fragment_start + fragment.length()
            if fragment_end <= start or fragment_start >= end:
                continue
            char_format = fragment.charFormat()
            if char_format.isAnchor() is False or char_format.anchorHref() != href:
                return False
        return True

    def _linkify(self) -> None:
        self._linkify_pending = False
        document = self.document()
        link_color = self.palette().color(QPalette.ColorRole.Link)
        cursor = QTextCursor(document)
        editing = False
        self._linkifying = True
        try:
            block = document.begin()
            while block.isValid():
                for start, end, href, cleared in self._link_changes(block):
                    if editing is False:
                        cursor.joinPreviousEditBlock()
                        editing = True
                    cursor.setPosition(block.position() + start)
                    cursor.setPosition(block.position() + end, QTextCursor.MoveMode.KeepAnchor)
                    if cleared is not None:
                        cursor.setCharFormat(cleared)
                    else:
                        cursor.mergeCharFormat(link_format(href, link_color))
                block = block.next()
        finally:
            if editing:
                cursor.endEditBlock()
            self._linkifying = False

    # Images
    def loadResource(self, resource_type: int, name: QUrl):
        if resource_type == QTextDocument.ResourceType.ImageResource.value and self._storage is not None and name.isRelative():
            image = QImage(str(self._storage.note_image_path(name.toString())))
            if image.isNull() is False:
                return image
        return super().loadResource(resource_type, name)

    def insert_image(self, image: QImage) -> bool:
        if self._images is False or self._storage is None or image.isNull():
            return False
        try:
            name = self._storage.import_note_image(image)
        except OSError:
            return False

        self.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl(name), image)
        image_format = QTextImageFormat()
        image_format.setName(name)
        image_format.setWidth(image.width())
        image_format.setMaximumWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
        # The image gets a line of its own and the cursor continues in the line below
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        line_format = cursor.blockFormat()
        if cursor.positionInBlock() > 0:
            cursor.insertBlock()
        image_line_format = QTextBlockFormat(cursor.blockFormat())
        image_line_format.setTopMargin(IMAGE_MARGIN)
        image_line_format.setBottomMargin(IMAGE_MARGIN)
        cursor.setBlockFormat(image_line_format)
        cursor.insertImage(image_format)
        cursor.insertBlock(line_format)
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        return True

    def _image_at(self, position: QPoint) -> str:
        cursor = self.cursorForPosition(position)
        for candidate in (cursor.position() + 1, cursor.position()):
            if candidate < 1 or candidate >= self.document().characterCount():
                continue
            probe = QTextCursor(self.document())
            probe.setPosition(candidate)
            char_format = probe.charFormat()
            if char_format.isImageFormat():
                return char_format.toImageFormat().name()
        return ""

    @staticmethod
    def image_files(source: QMimeData) -> list[Path]:
        return [path for path in local_files_from_mime(source) if path.suffix.lower() in IMAGE_EXTENSIONS]

    def canInsertFromMimeData(self, source: QMimeData) -> bool:
        if package_paths(source):
            return False
        if self._images and (source.hasImage() or self.image_files(source)):
            return True
        return source.hasText()

    def insertFromMimeData(self, source: QMimeData) -> None:
        if self._images:
            files = self.image_files(source)
            if files:
                for path in files:
                    self.insert_image(QImage(str(path)))
                return
            if source.hasImage() and (source.hasText() is False or not source.text().strip()):
                self.insert_image(image_from_mime(source))
                return
        if source.hasText():
            self.insertPlainText(source.text())

    # Painting
    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        metrics = QFontMetricsF(self.font())
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Placeholder while the document is empty, also hidden by an empty bullet
        document = self.document()
        if self._placeholder and document.isEmpty() and document.begin().textList() is None:
            cursor_rect = self.cursorRect(QTextCursor(document.begin()))
            painter.setFont(self.font())
            painter.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
            painter.drawText(QPointF(cursor_rect.left() + 1, cursor_rect.top() + metrics.ascent()), self._placeholder)

        # Thin frame around inline images
        if self._images:
            self._paint_image_frames(painter)

        # Bullets centered on the lower case letters of the first line: dot, ring and square per level
        radius = max(px(1.8), metrics.xHeight() * 0.2)
        text_color = self.palette().color(QPalette.ColorRole.Text)
        block = document.begin()
        while block.isValid():
            layout = block.layout()
            if is_bullet_list(block.textList()) and block.isVisible() and layout is not None and layout.lineCount() > 0:
                line = layout.lineAt(0)
                cursor_rect = self.cursorRect(QTextCursor(block))
                center = QPointF(cursor_rect.left() - px(BULLET_INDENT) / 2, cursor_rect.top() + line.ascent() - metrics.xHeight() / 2)
                level = (block.textList().format().indent() - 1) % 3
                if level == 1:
                    painter.setPen(QPen(text_color, px(1)))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(center, radius - px(0.5), radius - px(0.5))
                else:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(text_color)
                    if level == 0:
                        painter.drawEllipse(center, radius, radius)
                    else:
                        painter.drawRect(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2))
            block = block.next()
        painter.end()

    def _paint_image_frames(self, painter: QPainter) -> None:
        palette = QApplication.palette()
        painter.save()
        painter.setPen(QPen(mix_colors(palette.color(QPalette.ColorRole.Base), palette.color(QPalette.ColorRole.Text), 0.18), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        offset = QPointF(-self.horizontalScrollBar().value(), -self.verticalScrollBar().value())
        document_layout = self.document().documentLayout()
        block = self.document().begin()
        while block.isValid():
            layout = block.layout()
            iterator = block.begin()
            while layout is not None and iterator.atEnd() is False:
                fragment = iterator.fragment()
                iterator += 1
                if fragment.isValid() is False or fragment.charFormat().isImageFormat() is False:
                    continue
                block_rect = document_layout.blockBoundingRect(block)
                for position in range(fragment.position(), fragment.position() + fragment.length()):
                    relative = position - block.position()
                    line = layout.lineForTextPosition(relative)
                    if line.isValid() is False:
                        continue
                    left = line.cursorToX(relative)
                    right = line.cursorToX(relative + 1)
                    left = left[0] if isinstance(left, tuple) else left
                    right = right[0] if isinstance(right, tuple) else right
                    rect = QRectF(block_rect.left() + left, block_rect.top() + line.y(), right - left, line.ascent())
                    painter.drawRect(rect.translated(offset).adjusted(0.5, 0.5, -0.5, -0.5))
            block = block.next()
        painter.restore()

    # Formatting
    def toggle_bold(self) -> None:
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Weight.Normal if self.fontWeight() >= QFont.Weight.DemiBold.value else QFont.Weight.Bold)
        self.mergeCurrentCharFormat(char_format)

    def toggle_italic(self) -> None:
        char_format = QTextCharFormat()
        char_format.setFontItalic(self.fontItalic() is False)
        self.mergeCurrentCharFormat(char_format)

    def toggle_underline(self) -> None:
        char_format = QTextCharFormat()
        char_format.setFontUnderline(self.fontUnderline() is False)
        self.mergeCurrentCharFormat(char_format)

    def toggle_strike_out(self) -> None:
        char_format = QTextCharFormat()
        char_format.setFontStrikeOut(self.currentCharFormat().fontStrikeOut() is False)
        self.mergeCurrentCharFormat(char_format)

    def font_size_step(self) -> int:
        value = self.currentCharFormat().property(QTextFormat.Property.FontSizeAdjustment)
        return int(value) if value is not None else 0

    def set_font_size_step(self, step: int) -> None:
        # Steps relative to the editor font, so they follow the zoom
        char_format = QTextCharFormat()
        char_format.setProperty(QTextFormat.Property.FontSizeAdjustment, step)
        self.mergeCurrentCharFormat(char_format)

    def is_highlighted(self) -> bool:
        return self.currentCharFormat().background().style() != Qt.BrushStyle.NoBrush

    def toggle_highlight(self) -> None:
        char_format = QTextCharFormat()
        char_format.setBackground(QBrush() if self.is_highlighted() else QBrush(highlight_color()))
        self.mergeCurrentCharFormat(char_format)

    def _create_list(self, cursor: QTextCursor, style: QTextListFormat.Style = QTextListFormat.Style.ListStyleUndefined) -> None:
        list_format = QTextListFormat()
        list_format.setStyle(style)
        list_format.setIndent(1)
        cursor.createList(list_format)

    def toggle_bullets(self) -> None:
        self._toggle_list(QTextListFormat.Style.ListStyleUndefined)

    def toggle_numbering(self) -> None:
        self._toggle_list(QTextListFormat.Style.ListDecimal)

    def _toggle_list(self, style: QTextListFormat.Style) -> None:
        # No list creates one, the same kind removes it, the other kind changes the lists of the selected lines
        cursor = self.textCursor()
        current = cursor.currentList()
        blocks = self.selected_blocks()
        cursor.beginEditBlock()
        if current is None:
            self._create_list(cursor, style)
        elif current.format().style() == style:
            for block in blocks:
                text_list = block.textList()
                if text_list is not None:
                    text_list.remove(block)
                    block_format = block.blockFormat()
                    block_format.setIndent(0)
                    QTextCursor(block).setBlockFormat(block_format)
        else:
            for block in blocks:
                text_list = block.textList()
                if text_list is not None and text_list.format().style() != style:
                    list_format = text_list.format()
                    list_format.setStyle(style)
                    text_list.setFormat(list_format)
        cursor.endEditBlock()
        self.cursorPositionChanged.emit()

    def change_list_level(self, step: int) -> bool:
        # Selected list lines move one level in or out and join the list of that level above them
        blocks = [block for block in self.selected_blocks() if block.textList() is not None]
        if not blocks:
            return False
        cursor = self.textCursor()
        cursor.beginEditBlock()
        for block in blocks:
            text_list = block.textList()
            list_format = QTextListFormat(text_list.format())
            level = list_format.indent() + step
            if level < 1 or level > LIST_MAX_INDENT:
                continue
            text_list.remove(block)
            block_format = block.blockFormat()
            block_format.setIndent(0)
            QTextCursor(block).setBlockFormat(block_format)
            target = self._list_above(block, level)
            if target is not None:
                target.add(block)
            else:
                list_format.setIndent(level)
                QTextCursor(block).createList(list_format)
        cursor.endEditBlock()
        self.cursorPositionChanged.emit()
        return True

    @staticmethod
    def _list_above(block, level: int):
        # The nearest list of that level above, as long as no line of a lower level or outside a list comes first
        previous = block.previous()
        while previous.isValid():
            text_list = previous.textList()
            if text_list is None or text_list.format().indent() < level:
                return None
            if text_list.format().indent() == level:
                return text_list
            previous = previous.previous()
        return None

    def focusNextPrevChild(self, next_child: bool) -> bool:
        # Tab and Shift+Tab change the level of list lines, elsewhere they move the focus
        if self.hasFocus() and self.isReadOnly() is False and self.textCursor().currentList() is not None:
            self.change_list_level(1 if next_child else -1)
            return True
        return super().focusNextPrevChild(next_child)

    def selected_blocks(self) -> list:
        cursor = self.textCursor()
        document = self.document()
        start_block = document.findBlock(cursor.selectionStart())
        end_block = document.findBlock(cursor.selectionEnd())

        # A selection that ends at the start of a line does not include that line
        if cursor.hasSelection() and cursor.selectionEnd() == end_block.position() and end_block.blockNumber() > start_block.blockNumber():
            end_block = end_block.previous()

        blocks = []
        block = start_block
        while block.isValid() and block.blockNumber() <= end_block.blockNumber():
            blocks.append(block)
            block = block.next()
        return blocks

    # Keyboard and mouse
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.matches(QKeySequence.StandardKey.Bold):
            self.toggle_bold()
            return
        if event.matches(QKeySequence.StandardKey.Italic):
            self.toggle_italic()
            return
        if event.matches(QKeySequence.StandardKey.Underline):
            self.toggle_underline()
            return

        # A dash or star followed by a space at the start of a line starts a bullet list
        cursor = self.textCursor()
        if event.text() == " " and cursor.hasSelection() is False and cursor.block().textList() is None:
            if cursor.positionInBlock() == 1 and cursor.block().text()[:1] in BULLET_MARKERS:
                cursor.beginEditBlock()
                cursor.deletePreviousChar()
                self._create_list(cursor)
                cursor.endEditBlock()
                self.cursorPositionChanged.emit()
                return

        # Text typed right after a link is not part of the link
        modifiers = event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
        if event.text() and event.text().isprintable() and not modifiers and cursor.hasSelection() is False:
            current_format = self.currentCharFormat()
            if current_format.isAnchor():
                self.setCurrentCharFormat(without_link(current_format))
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        self._press_pos = event.position().toPoint() if event.button() == Qt.MouseButton.LeftButton else None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        position = event.position().toPoint()
        pressed = self._press_pos
        self._press_pos = None
        if pressed is None or event.button() != Qt.MouseButton.LeftButton or self.textCursor().hasSelection():
            return
        if (position - pressed).manhattanLength() >= QApplication.startDragDistance():
            return
        href = self.anchorAt(position)
        if href:
            open_link(href)

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        shape = Qt.CursorShape.PointingHandCursor if self.anchorAt(event.position().toPoint()) else Qt.CursorShape.IBeamCursor
        if self.viewport().cursor().shape() != shape:
            self.viewport().setCursor(shape)

    def mouseDoubleClickEvent(self, event) -> None:
        name = self._image_at(event.position().toPoint()) if self._images else ""
        if name:
            self.image_activated.emit(name)
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        # Right click outside the selection moves the cursor to the clicked line
        cursor = self.textCursor()
        clicked = self.cursorForPosition(event.pos())
        if cursor.hasSelection() is False or not cursor.selectionStart() <= clicked.position() <= cursor.selectionEnd():
            self.setTextCursor(clicked)
            cursor = clicked

        menu = create_menu(self)
        text_color = self.palette().color(QPalette.ColorRole.Text)
        href = self.anchorAt(event.pos())
        if href:
            menu.addAction(create_open_icon(text_color), tr("Link öffnen"), lambda: open_link(href))
            menu.addAction(create_copy_icon(text_color), tr("Link kopieren"), lambda: QGuiApplication.clipboard().setText(href))
            menu.addSeparator()
        if self.context_actions is not None:
            entries = self.context_actions()
            for text, icon_factory, slot, enabled in entries:
                action = menu.addAction(icon_factory(text_color), text, slot)
                action.setEnabled(enabled)
            if entries:
                menu.addSeparator()

        has_selection = cursor.hasSelection()
        standard_entries = (
            ("Rückgängig", QKeySequence.StandardKey.Undo, self.undo, self.document().isUndoAvailable()),
            ("Wiederholen", QKeySequence.StandardKey.Redo, self.redo, self.document().isRedoAvailable()),
            None,
            ("Ausschneiden", QKeySequence.StandardKey.Cut, self.cut, has_selection),
            ("Kopieren", QKeySequence.StandardKey.Copy, self.copy, has_selection),
            ("Einfügen", QKeySequence.StandardKey.Paste, self.paste, self.canPaste()),
            None,
            ("Alles auswählen", QKeySequence.StandardKey.SelectAll, self.selectAll, self.document().isEmpty() is False),
        )
        for entry in standard_entries:
            if entry is None:
                menu.addSeparator()
                continue
            text, key, slot, enabled = entry
            action = menu.addAction(shortcut_label(tr(text), QKeySequence(key)), slot)
            action.setEnabled(enabled)
        menu.exec(event.globalPos())
        menu.deleteLater()


class DescriptionEditor(QFrame):
    """Formatting toolbar and formatted text"""

    changed = Signal()

    def __init__(self, placeholder: str, images: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("descriptionFrame")

        self._edit = RichTextEdit(placeholder, images)
        self._edit.setMinimumHeight(120)
        self._edit.textChanged.connect(self.changed.emit)
        self._edit.currentCharFormatChanged.connect(self._update_buttons)
        self._edit.cursorPositionChanged.connect(self._update_buttons)
        self._separators: list[QFrame] = []

        self._bold_button = self._create_button("B", tr("Fett (Strg+B)"), self._edit.toggle_bold)
        self._italic_button = self._create_button("I", tr("Kursiv (Strg+I)"), self._edit.toggle_italic)
        self._underline_button = self._create_button("U", tr("Unterstrichen (Strg+U)"), self._edit.toggle_underline)
        self._strike_button = self._create_button("S", tr("Durchgestrichen"), self._edit.toggle_strike_out)
        self._size_button = self._create_size_button()
        self._highlight_button = self._create_button("", tr("Hervorheben"), self._edit.toggle_highlight)
        self._bullet_button = self._create_button("", tr("Aufzählung"), self._edit.toggle_bullets)
        self._numbering_button = self._create_button("", tr("Nummerierung"), self._edit.toggle_numbering)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(6, 4, 6, 4)
        toolbar.setSpacing(2)
        toolbar.addWidget(self._bold_button)
        toolbar.addWidget(self._italic_button)
        toolbar.addWidget(self._underline_button)
        toolbar.addWidget(self._strike_button)
        toolbar.addWidget(self._create_separator())
        toolbar.addWidget(self._size_button)
        toolbar.addWidget(self._highlight_button)
        toolbar.addWidget(self._create_separator())
        toolbar.addWidget(self._bullet_button)
        toolbar.addWidget(self._numbering_button)

        toolbar.addStretch()

        # The toolbar does not widen the column, in a very narrow column its last buttons are cut off
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        toolbar_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

        line = QFrame()
        line.setObjectName("toolbarLine")
        line.setFixedHeight(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(toolbar_widget)
        layout.addWidget(line)
        layout.addWidget(self._edit, 1)
        self.apply_zoom()

    def _create_button(self, text: str, tooltip: str, action) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.setCheckable(True)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.clicked.connect(lambda: self._run(action))
        return button

    def _create_separator(self) -> QFrame:
        # Thin line between the groups of the toolbar
        separator = QFrame()
        separator.setObjectName("toolbarSeparator")
        separator.setFixedWidth(1)
        self._separators.append(separator)
        return separator

    def _create_size_button(self) -> QToolButton:
        button = QToolButton()
        button.setToolTip(tr("Schriftgröße"))
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = create_menu(button)
        group = QActionGroup(menu)
        group.setExclusive(True)
        for label, step, scale in FONT_SIZE_STEPS:
            action = menu.addAction(tr(label), lambda checked=False, selected=step: self._run(lambda: self._edit.set_font_size_step(selected)))
            action.setCheckable(True)
            action.setData(step)
            group.addAction(action)
        menu.aboutToShow.connect(self._update_size_menu)
        button.setMenu(menu)
        self._size_menu = menu
        return button

    def _update_size_menu(self) -> None:
        # Every entry is shown in its size, the current size is checked
        step = self._edit.font_size_step()
        base_size = QApplication.font().pointSizeF()
        for action, (label, value, scale) in zip(self._size_menu.actions(), FONT_SIZE_STEPS):
            action.setChecked(value == step)
            font = QFont(QApplication.font())
            font.setPointSizeF(base_size * scale)
            action.setFont(font)

    def _buttons(self) -> list[QToolButton]:
        return [
            self._bold_button,
            self._italic_button,
            self._underline_button,
            self._strike_button,
            self._size_button,
            self._highlight_button,
            self._bullet_button,
            self._numbering_button,
        ]

    def _run(self, action) -> None:
        action()
        self._edit.setFocus()
        self._update_buttons()

    def _update_buttons(self, *arguments) -> None:
        current_list = self._edit.textCursor().currentList()
        self._bold_button.setChecked(self._edit.fontWeight() >= QFont.Weight.DemiBold.value)
        self._italic_button.setChecked(self._edit.fontItalic())
        self._underline_button.setChecked(self._edit.fontUnderline())
        self._strike_button.setChecked(self._edit.currentCharFormat().fontStrikeOut())
        self._highlight_button.setChecked(self._edit.is_highlighted())
        self._bullet_button.setChecked(is_bullet_list(current_list))
        self._numbering_button.setChecked(current_list is not None and is_bullet_list(current_list) is False)

    def apply_theme(self, theme: Theme) -> None:
        self._size_button.setIcon(create_text_size_icon(theme.text))
        self._highlight_button.setIcon(create_highlight_icon(theme.text, highlight_color()))
        self._bullet_button.setIcon(create_bullet_icon(theme.text))
        self._numbering_button.setIcon(create_numbering_icon(theme.text))

    def apply_zoom(self) -> None:
        self._edit.document().setIndentWidth(px(BULLET_INDENT))
        for button in self._buttons():
            button.setFixedSize(ipx(30), ipx(28))
            button.setIconSize(QSize(ipx(ICON_SIZE), ipx(ICON_SIZE)))
            font = QFont(QApplication.font())
            font.setBold(button is self._bold_button)
            font.setItalic(button is self._italic_button)
            font.setUnderline(button is self._underline_button)
            font.setStrikeOut(button is self._strike_button)
            button.setFont(font)
        for separator in self._separators:
            separator.setFixedHeight(ipx(TOOLBAR_SEPARATOR_HEIGHT))

    def set_content(self, html_text: str, plain_text: str, storage: Optional[Storage] = None) -> None:
        self._edit.set_storage(storage)
        self._edit.load_content(html_text, plain_text)
        self._update_buttons()

    def html(self) -> str:
        return self._edit.toHtml()

    def plain_text(self) -> str:
        return self._edit.toPlainText()

    def text_edit(self) -> RichTextEdit:
        return self._edit

class ScaledImage(QWidget):
    """Image scaled to the available width, never larger than its original size"""

    clicked = Signal()

    def __init__(self, pixmap: QPixmap, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._pixmap = pixmap
        self._cached_pixmap = QPixmap()
        self._cached_width = -1
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tr("Klicken zum Vergrößern"))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(50)
        self.setFixedHeight(self._height_for(400))

    def _height_for(self, width: int) -> int:
        target_width = min(width, self._pixmap.width())
        return max(1, round(target_width * self._pixmap.height() / max(1, self._pixmap.width())))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        height = self._height_for(self.width())
        if height != self.height():
            self.setFixedHeight(height)

    def paintEvent(self, event) -> None:
        target_width = min(self.width(), self._pixmap.width())
        if self._cached_width != target_width:
            self._cached_pixmap = self._pixmap.scaledToWidth(target_width, Qt.TransformationMode.SmoothTransformation)
            self._cached_width = target_width

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cached_pixmap)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ImageViewer(QDialog):
    """Large view of an image, closes on click or Escape"""

    def __init__(self, pixmap: QPixmap, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        screen = parent.screen() if parent is not None else QGuiApplication.primaryScreen()
        available = screen.availableGeometry()
        max_size = QSize(int(available.width() * 0.9), int(available.height() * 0.9))
        shown = pixmap
        if pixmap.width() > max_size.width() or pixmap.height() > max_size.height():
            shown = pixmap.scaled(max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        label = QLabel()
        label.setPixmap(shown)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        self.resize(shown.size())

    def mouseReleaseEvent(self, event) -> None:
        self.accept()


class AttachmentCard(QFrame):
    """One attachment with name, open and delete button and an inline preview"""

    delete_requested = Signal(object)

    def __init__(self, attachment: Attachment, path: Path, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._attachment = attachment
        self._path = path
        self.setObjectName("attachmentCard")

        name_label = QLabel(attachment.name)
        name_label.setToolTip(attachment.name)
        name_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        open_button = QToolButton()
        open_button.setIcon(create_open_icon(theme.text))
        open_button.setToolTip(tr("Mit dem Standardprogramm öffnen"))
        open_button.clicked.connect(self.open_file)

        delete_button = QToolButton()
        delete_button.setIcon(create_close_icon(theme.text))
        delete_button.setToolTip(tr("Anhang entfernen"))
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self._attachment))

        for button in (open_button, delete_button):
            button.setObjectName("iconButton")
            button.setFixedSize(ipx(ACTION_SIZE), ipx(ACTION_SIZE))
            button.setIconSize(QSize(ipx(ICON_SIZE), ipx(ICON_SIZE)))

        header = QHBoxLayout()
        header.setContentsMargins(10, 4, 6, 4)
        header.setSpacing(2)
        header.addWidget(name_label, 1)
        header.addSpacing(6)
        header.addWidget(open_button)
        header.addWidget(delete_button)

        line = QFrame()
        line.setObjectName("toolbarLine")
        line.setFixedHeight(1)

        preview = QVBoxLayout()
        preview.setContentsMargins(10, 10, 10, 10)
        preview.addWidget(self._create_preview())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addLayout(header)
        layout.addWidget(line)
        layout.addLayout(preview)

    def _create_preview(self) -> QWidget:
        if self._path.exists() is False:
            return self._info_label(tr("Datei nicht gefunden"))

        extension = self._path.suffix.lower()

        # Image preview
        if extension in IMAGE_EXTENSIONS:
            pixmap = QPixmap(str(self._path))
            if pixmap.isNull() is False:
                image = ScaledImage(pixmap)
                image.clicked.connect(lambda: ImageViewer(pixmap, self._attachment.name, self.window()).exec())
                return image

        # PDF preview
        if extension == ".pdf" and PDF_PREVIEW_AVAILABLE:
            document = QPdfDocument(self)
            document.load(str(self._path))
            if document.status() == QPdfDocument.Status.Ready:
                view = QPdfView(self)
                view.setDocument(document)
                view.setPageMode(QPdfView.PageMode.MultiPage)
                view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
                view.setFixedHeight(PDF_PREVIEW_HEIGHT)
                return view

        return self._info_label(tr("Keine Vorschau verfügbar"))

    def _info_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("mutedLabel")
        label.setWordWrap(True)
        return label

    def mouseDoubleClickEvent(self, event) -> None:
        self.open_file()

    def open_file(self) -> None:
        open_with_default_program(self._path)


def create_line_icon(color: QColor, path: QPainterPath, width: int = ICON_SIZE, filled: bool = False) -> QIcon:
    pixmap = QPixmap(width * 2, ICON_SIZE * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, 1.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(color if filled else Qt.BrushStyle.NoBrush)
    painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)


def create_attachment_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(10.5, 5.5)
    path.lineTo(10.5, 11.0)
    path.arcTo(QRectF(5.0, 8.25, 5.5, 5.5), 0.0, -180.0)
    path.lineTo(5.0, 4.25)
    path.arcTo(QRectF(5.0, 1.0, 4.0, 4.0), 180.0, -180.0)
    path.lineTo(9.0, 10.75)
    path.arcTo(QRectF(6.5, 9.5, 2.5, 2.5), 0.0, -180.0)
    path.lineTo(6.5, 5.5)

    # Diagonal orientation
    transform = QTransform()
    transform.translate(8.0, 8.0)
    transform.rotate(40.0)
    transform.translate(-8.0, -7.4)
    return create_line_icon(color, transform.map(path))


def create_folder_icon(color: QColor, width: int = ICON_SIZE) -> QIcon:
    path = QPainterPath()
    path.moveTo(2.25, 12.75)
    path.lineTo(2.25, 3.75)
    path.lineTo(6.25, 3.75)
    path.lineTo(7.75, 5.25)
    path.lineTo(13.75, 5.25)
    path.lineTo(13.75, 12.75)
    path.closeSubpath()
    path.moveTo(2.25, 7.25)
    path.lineTo(13.75, 7.25)
    return create_line_icon(color, path, width)


def create_delete_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(2.75, 4.25)
    path.lineTo(13.25, 4.25)
    path.moveTo(6.25, 4.25)
    path.lineTo(6.25, 2.75)
    path.lineTo(9.75, 2.75)
    path.lineTo(9.75, 4.25)
    path.moveTo(4.25, 4.25)
    path.lineTo(5.0, 13.25)
    path.lineTo(11.0, 13.25)
    path.lineTo(11.75, 4.25)
    path.moveTo(7.0, 6.75)
    path.lineTo(7.0, 10.75)
    path.moveTo(9.0, 6.75)
    path.lineTo(9.0, 10.75)
    return create_line_icon(color, path)


def create_add_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(8.0, 3.25)
    path.lineTo(8.0, 12.75)
    path.moveTo(3.25, 8.0)
    path.lineTo(12.75, 8.0)
    return create_line_icon(color, path)


def create_archive_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.addRoundedRect(QRectF(2.5, 3.0, 11.0, 3.0), 0.75, 0.75)
    path.moveTo(3.5, 6.0)
    path.lineTo(3.5, 13.0)
    path.lineTo(12.5, 13.0)
    path.lineTo(12.5, 6.0)
    path.moveTo(6.5, 8.75)
    path.lineTo(9.5, 8.75)
    return create_line_icon(color, path)


def create_restore_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(3.0, 9.5)
    path.lineTo(3.0, 13.0)
    path.lineTo(13.0, 13.0)
    path.lineTo(13.0, 9.5)
    path.moveTo(8.0, 10.5)
    path.lineTo(8.0, 2.75)
    path.moveTo(5.0, 5.75)
    path.lineTo(8.0, 2.75)
    path.lineTo(11.0, 5.75)
    return create_line_icon(color, path)


def create_flag_icon(color: QColor, filled: bool = False) -> QIcon:
    path = QPainterPath()
    path.moveTo(4.5, 13.5)
    path.lineTo(4.5, 2.75)
    path.lineTo(12.5, 2.75)
    path.lineTo(10.25, 5.75)
    path.lineTo(12.5, 8.75)
    path.lineTo(4.5, 8.75)
    return create_line_icon(color, path, ICON_SIZE, filled)


def create_moon_icon(color: QColor, width: int = ICON_SIZE) -> QIcon:
    outer = QPainterPath()
    outer.addEllipse(QRectF(2.5, 2.5, 11.0, 11.0))
    inner = QPainterPath()
    inner.addEllipse(QRectF(6.5, 0.5, 10.0, 10.0))
    return create_line_icon(color, outer.subtracted(inner), width)


def create_sun_icon(color: QColor, width: int = ICON_SIZE) -> QIcon:
    path = QPainterPath()
    path.addEllipse(QPointF(8.0, 8.0), 2.75, 2.75)
    for step in range(8):
        angle = math.radians(step * 45.0)
        path.moveTo(8.0 + math.cos(angle) * 4.75, 8.0 + math.sin(angle) * 4.75)
        path.lineTo(8.0 + math.cos(angle) * 6.5, 8.0 + math.sin(angle) * 6.5)
    return create_line_icon(color, path, width)


def create_settings_icon(color: QColor, width: int = ICON_SIZE) -> QIcon:
    path = QPainterPath()
    for tooth in range(8):
        angle = tooth * 45.0
        points = ((angle - 17.0, 5.0), (angle - 9.0, 6.75), (angle + 9.0, 6.75), (angle + 17.0, 5.0))
        for position, (degrees, radius) in enumerate(points):
            point = QPointF(8.0 + math.cos(math.radians(degrees)) * radius, 8.0 + math.sin(math.radians(degrees)) * radius)
            if tooth == 0 and position == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
    path.closeSubpath()
    path.addEllipse(QPointF(8.0, 8.0), 2.25, 2.25)
    return create_line_icon(color, path, width)


def add_badge(icon: QIcon, color: QColor, ring: QColor, width: int = ICON_SIZE) -> QIcon:
    # Filled dot at the upper right of the symbol
    pixmap = icon.pixmap(QSize(width, ICON_SIZE), 2.0)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(ring, 1.5))
    painter.setBrush(color)
    painter.drawEllipse(QPointF(13.25, 2.75), 2.75, 2.75)
    painter.end()
    return QIcon(pixmap)


def create_language_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.addEllipse(QPointF(8.0, 8.0), 5.75, 5.75)
    path.addEllipse(QRectF(5.5, 2.25, 5.0, 11.5))
    path.moveTo(2.25, 8.0)
    path.lineTo(13.75, 8.0)
    return create_line_icon(color, path)


def create_zoom_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.addEllipse(QPointF(7.0, 7.0), 4.25, 4.25)
    path.moveTo(10.25, 10.25)
    path.lineTo(13.5, 13.5)
    path.moveTo(5.0, 7.0)
    path.lineTo(9.0, 7.0)
    path.moveTo(7.0, 5.0)
    path.lineTo(7.0, 9.0)
    return create_line_icon(color, path)


def create_info_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.addEllipse(QPointF(8.0, 8.0), 5.75, 5.75)
    path.addEllipse(QPointF(8.0, 5.0), 0.35, 0.35)
    path.moveTo(8.0, 7.25)
    path.lineTo(8.0, 11.0)
    return create_line_icon(color, path)


def create_open_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(7.0, 3.5)
    path.lineTo(3.5, 3.5)
    path.lineTo(3.5, 12.5)
    path.lineTo(12.5, 12.5)
    path.lineTo(12.5, 9.0)
    path.moveTo(8.25, 7.75)
    path.lineTo(12.75, 3.25)
    path.moveTo(9.25, 3.25)
    path.lineTo(12.75, 3.25)
    path.lineTo(12.75, 6.75)
    return create_line_icon(color, path)


def create_close_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(4.25, 4.25)
    path.lineTo(11.75, 11.75)
    path.moveTo(11.75, 4.25)
    path.lineTo(4.25, 11.75)
    return create_line_icon(color, path)




def create_note_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(3.75, 2.25)
    path.lineTo(9.75, 2.25)
    path.lineTo(12.25, 4.75)
    path.lineTo(12.25, 13.75)
    path.lineTo(3.75, 13.75)
    path.closeSubpath()
    path.moveTo(9.75, 2.25)
    path.lineTo(9.75, 4.75)
    path.lineTo(12.25, 4.75)
    for y in (7.75, 9.75, 11.75):
        path.moveTo(6.0, y)
        path.lineTo(10.0, y)
    return create_line_icon(color, path)


def create_link_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.addRoundedRect(QRectF(1.5, 5.75, 7.75, 4.5), 2.25, 2.25)
    path.addRoundedRect(QRectF(6.75, 5.75, 7.75, 4.5), 2.25, 2.25)
    transform = QTransform()
    transform.translate(8.0, 8.0)
    transform.rotate(-40.0)
    transform.translate(-8.0, -8.0)
    return create_line_icon(color, transform.map(path))


def create_pdf_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(9.5, 2.25)
    path.lineTo(3.75, 2.25)
    path.lineTo(3.75, 13.75)
    path.lineTo(12.25, 13.75)
    path.lineTo(12.25, 5.0)
    path.lineTo(9.5, 2.25)
    path.lineTo(9.5, 5.0)
    path.lineTo(12.25, 5.0)
    path.moveTo(8.0, 6.75)
    path.lineTo(8.0, 11.5)
    path.moveTo(6.0, 9.5)
    path.lineTo(8.0, 11.5)
    path.lineTo(10.0, 9.5)
    return create_line_icon(color, path)


def create_task_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.addRoundedRect(QRectF(2.75, 2.75, 10.5, 10.5), 2.25, 2.25)
    path.moveTo(5.5, 8.25)
    path.lineTo(7.25, 10.0)
    path.lineTo(10.75, 6.25)
    return create_line_icon(color, path)


def create_group_add_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(2.25, 12.75)
    path.lineTo(2.25, 3.75)
    path.lineTo(6.25, 3.75)
    path.lineTo(7.75, 5.25)
    path.lineTo(13.75, 5.25)
    path.lineTo(13.75, 12.75)
    path.closeSubpath()
    path.moveTo(8.0, 7.25)
    path.lineTo(8.0, 11.25)
    path.moveTo(6.0, 9.25)
    path.lineTo(10.0, 9.25)
    return create_line_icon(color, path)


def create_collapse_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    for offset in (0.0, 4.0):
        path.moveTo(8.5 + offset, 4.5)
        path.lineTo(5.0 + offset, 8.0)
        path.lineTo(8.5 + offset, 11.5)
    return create_line_icon(color, path)


def create_expand_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    for offset in (0.0, 4.0):
        path.moveTo(3.5 + offset, 4.5)
        path.lineTo(7.0 + offset, 8.0)
        path.lineTo(3.5 + offset, 11.5)
    return create_line_icon(color, path)


def create_maximize_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(9.25, 6.75)
    path.lineTo(13.0, 3.0)
    path.moveTo(9.5, 3.0)
    path.lineTo(13.0, 3.0)
    path.lineTo(13.0, 6.5)
    path.moveTo(6.75, 9.25)
    path.lineTo(3.0, 13.0)
    path.moveTo(3.0, 9.5)
    path.lineTo(3.0, 13.0)
    path.lineTo(6.5, 13.0)
    return create_line_icon(color, path)


def create_shrink_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(13.0, 3.0)
    path.lineTo(9.25, 6.75)
    path.moveTo(9.25, 3.75)
    path.lineTo(9.25, 6.75)
    path.lineTo(12.25, 6.75)
    path.moveTo(3.0, 13.0)
    path.lineTo(6.75, 9.25)
    path.moveTo(3.75, 9.25)
    path.lineTo(6.75, 9.25)
    path.lineTo(6.75, 12.25)
    return create_line_icon(color, path)


def create_copy_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.addRoundedRect(QRectF(5.75, 5.75, 7.5, 7.5), 1.25, 1.25)
    path.moveTo(3.25, 10.25)
    path.lineTo(2.75, 10.25)
    path.lineTo(2.75, 2.75)
    path.lineTo(10.25, 2.75)
    path.lineTo(10.25, 3.25)
    return create_line_icon(color, path)


def create_tabs_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.addRoundedRect(QRectF(2.25, 2.75, 11.5, 10.5), 1.25, 1.25)
    path.moveTo(2.25, 6.25)
    path.lineTo(13.75, 6.25)
    path.moveTo(6.0, 2.75)
    path.lineTo(6.0, 6.25)
    path.moveTo(9.75, 2.75)
    path.lineTo(9.75, 6.25)
    return create_line_icon(color, path)


def create_rename_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(3.0, 13.0)
    path.lineTo(3.5, 10.25)
    path.lineTo(10.75, 3.0)
    path.lineTo(13.0, 5.25)
    path.lineTo(5.75, 12.5)
    path.closeSubpath()
    path.moveTo(9.25, 4.5)
    path.lineTo(11.5, 6.75)
    return create_line_icon(color, path)


def create_backup_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.arcMoveTo(QRectF(2.5, 2.5, 11.0, 11.0), 150.0)
    path.arcTo(QRectF(2.5, 2.5, 11.0, 11.0), 150.0, -300.0)
    path.moveTo(3.25, 3.0)
    path.lineTo(3.25, 5.75)
    path.lineTo(6.0, 5.75)
    path.moveTo(8.0, 5.0)
    path.lineTo(8.0, 8.25)
    path.lineTo(10.25, 9.5)
    return create_line_icon(color, path)


def create_export_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(5.5, 5.5)
    path.lineTo(3.0, 5.5)
    path.lineTo(3.0, 13.0)
    path.lineTo(13.0, 13.0)
    path.lineTo(13.0, 5.5)
    path.lineTo(10.5, 5.5)
    path.moveTo(8.0, 9.5)
    path.lineTo(8.0, 2.5)
    path.moveTo(5.75, 4.75)
    path.lineTo(8.0, 2.5)
    path.lineTo(10.25, 4.75)
    return create_line_icon(color, path)


def create_import_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(5.5, 5.5)
    path.lineTo(3.0, 5.5)
    path.lineTo(3.0, 13.0)
    path.lineTo(13.0, 13.0)
    path.lineTo(13.0, 5.5)
    path.lineTo(10.5, 5.5)
    path.moveTo(8.0, 2.5)
    path.lineTo(8.0, 9.5)
    path.moveTo(5.75, 7.25)
    path.lineTo(8.0, 9.5)
    path.lineTo(10.25, 7.25)
    return create_line_icon(color, path)


def create_dot_icon(color: QColor) -> QIcon:
    pixmap = QPixmap(ICON_SIZE * 2, ICON_SIZE * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawEllipse(QPointF(ICON_SIZE / 2, ICON_SIZE / 2), DOT_SIZE / 2, DOT_SIZE / 2)
    painter.end()
    return QIcon(pixmap)


def create_calendar_icon(color: QColor) -> QIcon:
    # Calendar sheet with two rings
    path = QPainterPath()
    path.addRoundedRect(QRectF(2.5, 3.5, 11.0, 10.0), 1.5, 1.5)
    path.moveTo(2.5, 6.75)
    path.lineTo(13.5, 6.75)
    path.moveTo(5.5, 2.0)
    path.lineTo(5.5, 4.75)
    path.moveTo(10.5, 2.0)
    path.lineTo(10.5, 4.75)
    return create_line_icon(color, path)


def create_chevron_down_icon(color: QColor) -> QIcon:
    path = QPainterPath()
    path.moveTo(4.5, 6.5)
    path.lineTo(8.0, 10.0)
    path.lineTo(11.5, 6.5)
    return create_line_icon(color, path)


def create_chevron_side_icon(color: QColor, forward: bool) -> QIcon:
    # Chevron to the right or to the left
    path = QPainterPath()
    tip = 10.0 if forward else 6.0
    back = 6.5 if forward else 9.5
    path.moveTo(back, 4.5)
    path.lineTo(tip, 8.0)
    path.lineTo(back, 11.5)
    return create_line_icon(color, path)


def create_text_size_icon(color: QColor) -> QIcon:
    # Large and small letter T
    path = QPainterPath()
    path.moveTo(1.5, 3.0)
    path.lineTo(9.5, 3.0)
    path.moveTo(5.5, 3.0)
    path.lineTo(5.5, 13.0)
    path.moveTo(9.0, 7.5)
    path.lineTo(14.5, 7.5)
    path.moveTo(11.75, 7.5)
    path.lineTo(11.75, 13.0)
    return create_line_icon(color, path)


def create_highlight_icon(color: QColor, marker: QColor) -> QIcon:
    # Marker pen above a bar in the highlight color
    pixmap = QPixmap(32, 32)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(marker)
    painter.drawRoundedRect(QRectF(1.5, 12.5, 13.0, 2.5), 0.8, 0.8)
    pen = QPen(color, 1.2)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    body = QPainterPath()
    body.moveTo(9.6, 1.4)
    body.lineTo(13.4, 5.2)
    body.lineTo(7.8, 10.8)
    body.lineTo(5.2, 11.0)
    body.lineTo(4.0, 9.8)
    body.lineTo(4.2, 7.2)
    body.closeSubpath()
    body.moveTo(4.2, 7.2)
    body.lineTo(7.8, 10.8)
    painter.drawPath(body)
    painter.end()
    return QIcon(pixmap)


def create_numbering_icon(color: QColor) -> QIcon:
    # Lines with the numbers 1, 2 and 3
    pixmap = QPixmap(32, 32)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    font = QFont(QApplication.font())
    font.setPixelSize(5)
    font.setWeight(QFont.Weight.DemiBold)
    painter.setFont(font)
    for row in range(3):
        y = 4.0 + row * 4.0
        painter.setPen(color)
        painter.drawText(QRectF(0.0, y - 3.0, 5.0, 6.0), Qt.AlignmentFlag.AlignCenter, str(row + 1))
        painter.setPen(QPen(color, 1.3))
        painter.drawLine(QPointF(6.5, y), QPointF(14.0, y))
    painter.end()
    return QIcon(pixmap)


def create_bullet_icon(color: QColor) -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    for row in range(3):
        y = 4.0 + row * 4.0
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(3.0, y), 1.4, 1.4)
        painter.setPen(QPen(color, 1.3))
        painter.drawLine(QPointF(6.5, y), QPointF(14.0, y))
    painter.end()
    return QIcon(pixmap)


def create_column_header(parent_layout: QVBoxLayout) -> QHBoxLayout:
    header = QFrame()
    header.setObjectName("columnHeader")
    header.setMinimumHeight(HEADER_HEIGHT)
    layout = QHBoxLayout(header)
    layout.setContentsMargins(COLUMN_PADDING, 8, COLUMN_PADDING - 4, 8)
    layout.setSpacing(8)
    parent_layout.addWidget(header)
    return layout


def create_header_label(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setFont(header_font(label.font()))
    label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
    return label


def create_icon_button(tooltip: str, slot) -> QToolButton:
    button = QToolButton()
    button.setToolTip(tooltip)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.clicked.connect(slot)
    return button


def create_field_edit(placeholder: str = "") -> QLineEdit:
    edit = QLineEdit()
    edit.setObjectName("fieldEdit")
    edit.setPlaceholderText(placeholder)
    return edit


def create_section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionLabel")
    return label


def backup_label(moment: datetime, reason: str) -> str:
    if moment.date() == date.today():
        day = tr("Heute")
    elif moment.date() == date.today() - timedelta(days=1):
        day = tr("Gestern")
    else:
        day = moment.strftime(tr("%d.%m.%Y"))
    text = day + " " + moment.strftime("%H:%M")
    if reason in BACKUP_REASON_TEXTS:
        text += " (" + tr(BACKUP_REASON_TEXTS[reason]) + ")"
    return text


def format_date(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime(tr("%d.%m.%Y"))


def iso_date(text: str) -> Optional[date]:
    try:
        return date.fromisoformat(text) if text else None
    except ValueError:
        return None


def parse_condition_date(text: str, today: Optional[date] = None) -> Optional[date]:
    # Accepts 14.11.2026, 14.11.26, 14.11. and 2026-11-14, a day without year more than half a year ago means next year
    today = today or date.today()
    value = text.strip()
    iso_match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", value)
    year_given = True
    if iso_match is not None:
        year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
    else:
        match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{2}|\d{4})?)?", value)
        if match is None:
            return None
        day, month = int(match.group(1)), int(match.group(2))
        year_text = match.group(3)
        if year_text is None:
            year = today.year
            year_given = False
        else:
            year = int(year_text) + (2000 if len(year_text) == 2 else 0)
    try:
        result = date(year, month, day)
    except ValueError:
        return None
    if year_given is False and (today - result).days > CONDITION_NEXT_YEAR_DAYS:
        try:
            result = date(year + 1, month, day)
        except ValueError:
            return None
    return result


def format_condition_date(day: date, today: Optional[date] = None) -> str:
    today = today or date.today()
    if day == today:
        return tr("heute")
    if day == today + timedelta(days=1):
        return tr("morgen")
    if day == today - timedelta(days=1):
        return tr("gestern")
    return day.strftime(tr("%d.%m.%Y"))


def todo_condition(todo: Todo, today: Optional[date] = None) -> tuple[str, str]:
    # Text under the todo title and its state: overdue, due today, started or nothing
    if not todo.condition:
        return "", ""
    today = today or date.today()
    prefix = tr(dict(CONDITION_KINDS)[todo.condition])
    day = iso_date(todo.condition_date)
    if day is None:
        value = todo.condition_text.strip()
        return (prefix + " " + value, "") if value else ("", "")

    text = prefix + " " + format_condition_date(day, today)
    if todo.done:
        return text, ""
    if todo.condition == CONDITION_UNTIL and day < today:
        return text, CONDITION_OVERDUE
    if todo.condition == CONDITION_UNTIL and day == today:
        return text, CONDITION_DUE
    if todo.condition == CONDITION_FROM and day <= today:
        return text, CONDITION_STARTED
    return text, ""


def format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime(tr("%d.%m.%Y, %H:%M"))


def count_text(item_type: str, count: int) -> str:
    singular, plural = COUNT_TEXTS[item_type]
    return tr(singular) if count == 1 else tr(plural, count=count)


def entries_text(count: int) -> str:
    return tr("1 Eintrag") if count == 1 else tr("{count} Einträge", count=count)


def format_size(size: int) -> str:
    if size < 1024 * 1024:
        return f"{max(1, round(size / 1024))} KB"
    text = f"{size / (1024 * 1024):.1f} MB"
    return text.replace(".", ",") if Language.current == LANGUAGE_GERMAN else text


class PackageError(Exception):
    """A .pdesk file that cannot be imported"""


def package_files(values: dict) -> set[str]:
    if values.get("kind") == EXPORT_PROJECT:
        return referenced_files({"projects": [values.get("project", {})]})
    item_list = ITEM_LISTS.get(str(values.get("item_type")), "")
    return referenced_files({"projects": [{item_list: values.get("items", [])}]})


def write_package(path: Path, values: dict, storage: Storage) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as package:
            package.writestr(EXPORT_CONTENT_NAME, json.dumps(values, ensure_ascii=False, indent=2))
            for relative in sorted(package_files(values)):
                source = storage.folder / relative
                if source.is_file():
                    package.write(source, EXPORT_FILES_PREFIX + relative)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class ImportPackage:
    """Content and files of a .pdesk file"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._zip: Optional[zipfile.ZipFile] = None
        try:
            self._zip = zipfile.ZipFile(path)
            values = json.loads(self._zip.read(EXPORT_CONTENT_NAME).decode("utf-8"))
        except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
            self.close()
            raise PackageError(tr("Die Datei ist keine Project-Desk-Datei oder beschädigt.")) from error

        if isinstance(values, dict) is False or values.get("format") != EXPORT_FORMAT:
            self.close()
            raise PackageError(tr("Die Datei ist keine Project-Desk-Datei oder beschädigt."))
        try:
            format_version = int(values.get("format_version", 0))
        except (TypeError, ValueError):
            format_version = 0
        if format_version > EXPORT_FORMAT_VERSION:
            self.close()
            raise PackageError(tr("Die Datei stammt aus einer neueren Version von Project Desk. Bitte Project Desk aktualisieren."))

        self.values = values
        self.kind = values.get("kind")
        self.item_type = values.get("item_type")
        valid_items = self.kind in (EXPORT_GROUP, EXPORT_ITEMS) and self.item_type in ITEM_TYPES and isinstance(values.get("items"), list)
        valid_project = self.kind == EXPORT_PROJECT and isinstance(values.get("project"), dict)
        if valid_items is False and valid_project is False:
            self.close()
            raise PackageError(tr("Die Datei ist keine Project-Desk-Datei oder beschädigt."))

    def read_file(self, relative: str) -> Optional[bytes]:
        if self._zip is None:
            return None
        try:
            return self._zip.read(EXPORT_FILES_PREFIX + relative)
        except (KeyError, OSError, zipfile.BadZipFile):
            return None

    def close(self) -> None:
        if self._zip is not None:
            self._zip.close()
            self._zip = None


def write_note_pdf(path: Path, title: str, subtitle: str, source: QTextDocument, storage: Storage) -> None:
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageMargins(QMarginsF(PDF_MARGIN_MM, PDF_MARGIN_MM, PDF_MARGIN_MM, PDF_MARGIN_MM), QPageLayout.Unit.Millimeter)
    writer.setResolution(PDF_RESOLUTION)
    writer.setTitle(title)
    writer.setCreator(APP_TITLE)

    # Page area in device pixels, the footer with the page number is kept free
    paint_rect = writer.pageLayout().paintRectPixels(PDF_RESOLUTION)
    footer_height = PDF_RESOLUTION * PDF_FOOTER_HEIGHT_INCH
    page_width = float(paint_rect.width())
    page_height = paint_rect.height() - footer_height

    document = QTextDocument()
    document.documentLayout().setPaintDevice(writer)
    font = QFont(QApplication.font())
    font.setPointSizeF(PDF_FONT_SIZE)
    document.setDefaultFont(font)
    document.setDocumentMargin(0)
    document.setIndentWidth(PDF_LIST_INDENT)
    document.setPageSize(QSizeF(page_width, page_height))

    # Space at the top and bottom of every page, so nothing of the next page shows at the page edge
    page_gap = PDF_RESOLUTION * PDF_PAGE_GAP_INCH
    root_format = document.rootFrame().frameFormat()
    root_format.setTopMargin(page_gap)
    root_format.setBottomMargin(page_gap)
    document.rootFrame().setFrameFormat(root_format)

    # Heading with title and date
    cursor = QTextCursor(document)
    title_format = QTextCharFormat()
    title_font = QFont(font)
    title_font.setPointSizeF(PDF_TITLE_SIZE)
    title_font.setWeight(QFont.Weight.DemiBold)
    title_format.setFont(title_font)
    cursor.insertText(title, title_format)

    subtitle_block = QTextBlockFormat()
    subtitle_block.setTopMargin(4)
    subtitle_block.setBottomMargin(16)
    subtitle_format = QTextCharFormat()
    subtitle_format.setForeground(QColor(PDF_MUTED_COLOR))
    cursor.insertBlock(subtitle_block, subtitle_format)
    cursor.insertText(subtitle, subtitle_format)
    cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
    cursor.insertFragment(QTextDocumentFragment(source))

    # Images are scaled by the layout from screen to printer resolution
    screen = QGuiApplication.primaryScreen()
    screen_dpi = screen.logicalDotsPerInchY() if screen is not None else 96.0
    device_scale = writer.logicalDpiY() / screen_dpi

    # Visible bullets per level, highlight in the light color, images from the storage folder, scaled to fit the page
    image_cursor = QTextCursor(document)
    marked: list[tuple[int, int]] = []
    block = document.begin()
    while block.isValid():
        text_list = block.textList()
        if is_bullet_list(text_list):
            list_format = text_list.format()
            list_format.setStyle(PDF_BULLET_STYLES[(list_format.indent() - 1) % len(PDF_BULLET_STYLES)])
            text_list.setFormat(list_format)
        elif text_list is not None:
            # Only the numbers of the list get digits of equal width, the text stays searchable
            number_format = QTextCharFormat(block.charFormat())
            number_format.setFontFeatures({QFont.Tag.fromString(TABULAR_FIGURES_FEATURE): 1})
            QTextCursor(block).setBlockCharFormat(number_format)
        iterator = block.begin()
        while iterator.atEnd() is False:
            fragment = iterator.fragment()
            iterator += 1
            if fragment.isValid() is False:
                continue
            if fragment.charFormat().background().style() != Qt.BrushStyle.NoBrush:
                marked.append((fragment.position(), fragment.length()))
            if fragment.charFormat().isImageFormat() is False:
                continue
            image_format = fragment.charFormat().toImageFormat()
            image = QImage(str(storage.note_image_path(image_format.name())))
            if image.isNull():
                continue
            document.addResource(QTextDocument.ResourceType.ImageResource.value, QUrl(image_format.name()), image)
            natural_width = image.width() * device_scale
            natural_height = image.height() * device_scale
            factor = min(1.0, page_width / natural_width, page_height * PDF_IMAGE_MAX_HEIGHT / natural_height)
            image_format.clearProperty(QTextFormat.Property.ImageMaxWidth)
            image_format.setWidth(image.width() * factor)
            image_format.setHeight(image.height() * factor)
            image_cursor.setPosition(fragment.position())
            image_cursor.setPosition(fragment.position() + fragment.length(), QTextCursor.MoveMode.KeepAnchor)
            image_cursor.setCharFormat(image_format)
        block = block.next()
    marked_format = QTextCharFormat()
    marked_format.setBackground(QColor(HIGHLIGHT_LIGHT))
    for position, length in marked:
        image_cursor.setPosition(position)
        image_cursor.setPosition(position + length, QTextCursor.MoveMode.KeepAnchor)
        image_cursor.mergeCharFormat(marked_format)

    # Pages with page number at the bottom right
    footer_font = QFont(font)
    footer_font.setPointSizeF(PDF_FOOTER_SIZE)
    page_count = document.pageCount()
    painter = QPainter(writer)
    for page in range(page_count):
        if page > 0:
            writer.newPage()
        painter.save()
        painter.translate(0, -page * page_height)
        document.drawContents(painter, QRectF(0, page * page_height, page_width, page_height))
        painter.restore()
        painter.setFont(footer_font)
        painter.setPen(QColor(PDF_MUTED_COLOR))
        footer_rect = QRectF(0, page_height, page_width, footer_height)
        painter.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, tr("Seite {page} von {count}", page=page + 1, count=page_count))
    painter.end()


class ItemPanel(QWidget):
    """Right column for one item type: header with title, content and a footer with dates"""

    content_changed = Signal()
    edit_started = Signal()
    step_started = Signal()
    maximize_toggled = Signal()

    def __init__(self, placeholder_text: str, title_placeholder: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._item = None
        self._storage: Optional[Storage] = None
        self._theme = Theme.from_palette(QApplication.palette())
        self.setObjectName("detailColumn")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header_layout = create_column_header(layout)
        self.header_frame = self._header_layout.parentWidget()
        self._title_edit = TitleEdit(title_placeholder)
        self._title_edit.title_changed.connect(self._on_title_changed)
        self._header_layout.addWidget(self._title_edit, 1, Qt.AlignmentFlag.AlignVCenter)
        self._maximized = False
        self._maximize_button = create_icon_button(tr("Maximieren"), self.maximize_toggled.emit)
        self._maximize_button.setFixedSize(ipx(32), ipx(32))
        self._header_layout.addWidget(self._maximize_button, 0, Qt.AlignmentFlag.AlignVCenter)

        # Placeholder page, also used for the number of selected entries
        self._placeholder_text = placeholder_text
        self._placeholder = QLabel(placeholder_text)
        self._placeholder.setObjectName("mutedLabel")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Editor page
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(COLUMN_PADDING, COLUMN_PADDING, COLUMN_PADDING, COLUMN_PADDING)
        self.body_layout.setSpacing(8)

        self.footer = QFrame()
        self.footer.setObjectName("columnFooter")
        self.footer.setFixedHeight(FOOTER_HEIGHT)
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(COLUMN_PADDING, 0, COLUMN_PADDING, 0)
        self._footer_label = QLabel()
        self._footer_label.setObjectName("mutedLabel")
        footer_layout.addWidget(self._footer_label)
        footer_layout.addStretch()

        editor = QWidget()
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.body, 1)
        editor_layout.addWidget(self.footer)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(editor)
        layout.addWidget(self._stack, 1)
        self._title_edit.setVisible(False)
        self._maximize_button.setVisible(False)
        self._update_maximize_button()

    @property
    def item(self):
        return self._item

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._update_maximize_button()

    def apply_zoom(self) -> None:
        self._title_edit.apply_zoom()
        self.footer.setFixedHeight(ipx(FOOTER_HEIGHT))
        self._maximize_button.setFixedSize(ipx(32), ipx(32))
        self._maximize_button.setIconSize(QSize(ipx(ICON_SIZE), ipx(ICON_SIZE)))

    def set_maximized(self, maximized: bool) -> None:
        self._maximized = maximized
        self._update_maximize_button()

    def _update_maximize_button(self) -> None:
        if self._maximized:
            self._maximize_button.setIcon(create_shrink_icon(self._theme.text))
            self._maximize_button.setToolTip(tr("Normale Größe"))
        else:
            self._maximize_button.setIcon(create_maximize_icon(self._theme.text))
            self._maximize_button.setToolTip(tr("Maximieren"))

    def set_item(self, item, storage: Optional[Storage]) -> None:
        self._item = item
        self._storage = storage
        self._title_edit.setVisible(item is not None)
        self._maximize_button.setVisible(item is not None)
        self._placeholder.setText(self._placeholder_text)

        if item is None:
            self.clear()
            self._stack.setCurrentIndex(0)
            return

        self._stack.setCurrentIndex(1)
        self._title_edit.set_title(item_title(item))
        self.load(item)
        self.set_dates(item.created, item.modified)

    def show_selection(self, text: str) -> None:
        # Several entries are selected, only their number is shown
        self.set_item(None, self._storage)
        self._placeholder.setText(text)

    def load(self, item) -> None:
        pass

    def clear(self) -> None:
        pass

    def refresh_details(self) -> None:
        if self._item is not None:
            self._title_edit.set_title(item_title(self._item))
            self.set_dates(self._item.created, self._item.modified)

    def set_dates(self, created: float, modified: float = 0.0) -> None:
        parts: list[str] = []
        if created:
            parts.append(tr("Erstellt am {date}", date=format_timestamp(created)))
        if modified and modified - created > 60:
            parts.append(tr("Geändert am {date}", date=format_timestamp(modified)))
        self._footer_label.setText("   ·   ".join(parts))

    def _on_title_changed(self, text: str) -> None:
        if self._item is None:
            return
        self.edit_started.emit()
        set_item_title(self._item, text)
        self.item_changed()

    def item_changed(self) -> None:
        if self._item is not None:
            touch(self._item)
            self.set_dates(self._item.created, self._item.modified)
        self.content_changed.emit()


class TodoPanel(ItemPanel):
    """Title, formatted description and attachments of the selected todo"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(tr("Kein ToDo ausgewählt"), tr("Titel"), parent)
        self.setAcceptDrops(True)

        self._description = DescriptionEditor(tr("Beschreibung"))
        self._description.setMaximumHeight(300)
        self._description.changed.connect(self._on_description_changed)
        self._title_edit.submitted.connect(lambda: self._description.text_edit().setFocus())

        # Condition: kind, then a date or a text, the calendar picks a date
        self._condition_button = QToolButton()
        self._condition_button.setObjectName("conditionButton")
        self._condition_button.setToolTip(tr("Art der Bedingung"))
        self._condition_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._condition_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._condition_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._condition_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        condition_menu = create_menu(self._condition_button)
        condition_menu.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        condition_group = QActionGroup(condition_menu)
        condition_group.setExclusive(True)
        for kind, label in CONDITION_KINDS:
            action = condition_menu.addAction(tr(label), lambda checked=False, selected=kind: self._set_condition_kind(selected))
            action.setCheckable(True)
            action.setData(kind)
            condition_group.addAction(action)
        condition_menu.aboutToShow.connect(self._update_condition_menu)
        self._condition_button.setMenu(condition_menu)
        self._condition_menu = condition_menu

        # Field and calendar keep their space while hidden, so the layout does not move
        self._condition_edit = create_field_edit(tr("Datum oder Text"))
        self._condition_edit.textEdited.connect(self._on_condition_edited)
        self._condition_edit.editingFinished.connect(self._show_condition)
        self._calendar_button = create_icon_button(tr("Datum auswählen"), self._show_calendar)
        for widget in (self._condition_edit, self._calendar_button):
            policy = widget.sizePolicy()
            policy.setRetainSizeWhenHidden(True)
            widget.setSizePolicy(policy)

        condition_row = QWidget()
        condition_layout = QHBoxLayout(condition_row)
        condition_layout.setContentsMargins(0, 0, 0, 0)
        condition_layout.setSpacing(6)
        condition_layout.addWidget(self._condition_button)
        condition_layout.addWidget(self._condition_edit, 1)
        condition_layout.addWidget(self._calendar_button)
        condition_layout.addStretch()

        self._drop_zone = DropZone(tr("Dateien hierher ziehen, klicken oder Strg+V"))
        self._drop_zone.clicked.connect(self._choose_files)

        attachment_container = QWidget()
        attachment_container.setObjectName("attachmentContainer")
        self._attachment_layout = QVBoxLayout(attachment_container)
        self._attachment_layout.setContentsMargins(0, 0, 10, 0)
        self._attachment_layout.setSpacing(10)
        self._attachment_layout.addStretch()

        self._attachment_scroll = QScrollArea()
        self._attachment_scroll.setObjectName("attachmentScroll")
        self._attachment_scroll.setWidgetResizable(True)
        self._attachment_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._attachment_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._attachment_scroll.setWidget(attachment_container)
        self._attachment_scroll.viewport().setAutoFillBackground(False)

        self.body_layout.addLayout(create_field_grid([(tr("Bedingung"), condition_row)]))
        self.body_layout.addSpacing(10)
        self.body_layout.addWidget(self._description)
        self.body_layout.addSpacing(10)
        self.body_layout.addWidget(create_section_label(tr("Anhänge")))
        self.body_layout.addWidget(self._drop_zone)
        self.body_layout.addWidget(self._attachment_scroll, 1)

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        self._description.apply_theme(theme)
        self._drop_zone.apply_theme(theme)
        self._condition_button.setIcon(create_chevron_down_icon(theme.muted))
        self._calendar_button.setIcon(create_calendar_icon(theme.text))
        if self._item is not None:
            self._rebuild_attachments()

    def apply_zoom(self) -> None:
        super().apply_zoom()
        self._description.apply_zoom()
        self._drop_zone.apply_theme(self._theme)
        self._condition_button.setIconSize(QSize(ipx(ICON_SIZE), ipx(ICON_SIZE)))
        self._calendar_button.setFixedSize(ipx(30), ipx(30))
        self._calendar_button.setIconSize(QSize(ipx(ICON_SIZE), ipx(ICON_SIZE)))
        if self._item is not None:
            self._rebuild_attachments()

    def load(self, todo: Todo) -> None:
        self._show_condition()
        self._description.set_content(todo.description_html, todo.description)
        self._rebuild_attachments()

    def _show_condition(self) -> None:
        # Kind on the button, a date in the date format of the language, the field only with a kind
        todo = self._item
        if todo is None:
            return
        kind = todo.condition
        self._condition_button.setText(tr(dict(CONDITION_KINDS)[kind]))
        self._condition_edit.setVisible(bool(kind))
        self._calendar_button.setVisible(bool(kind))
        day = iso_date(todo.condition_date)
        text = day.strftime(tr("%d.%m.%Y")) if day is not None else todo.condition_text
        if self._condition_edit.text() != text:
            self._condition_edit.setText(text)
            self._condition_edit.setCursorPosition(0)

    def _update_condition_menu(self) -> None:
        kind = self._item.condition if self._item is not None else ""
        for action in self._condition_menu.actions():
            action.setChecked(action.data() == kind)

    def _set_condition_kind(self, kind: str) -> None:
        if self._item is None or kind == self._item.condition:
            return
        self.step_started.emit()
        self._item.condition = kind
        if not kind:
            self._item.condition_date = ""
            self._item.condition_text = ""
        self._show_condition()
        self.item_changed()
        if kind and not self._condition_edit.text():
            self._condition_edit.setFocus()

    def _on_condition_edited(self, text: str) -> None:
        if self._item is None:
            return
        self.edit_started.emit()
        day = parse_condition_date(text)
        self._item.condition_date = day.isoformat() if day is not None else ""
        self._item.condition_text = "" if day is not None else text.strip()
        self.item_changed()

    def _set_condition_date(self, day: date) -> None:
        if self._item is None:
            return
        self.step_started.emit()
        self._item.condition_date = day.isoformat()
        self._item.condition_text = ""
        self._show_condition()
        self.item_changed()

    def _show_calendar(self) -> None:
        # Month calendar below the button, a click takes the day
        if self._item is None:
            return
        menu = create_menu(self)
        calendar = QCalendarWidget()
        calendar.setGridVisible(False)
        calendar.setLocale(QLocale(QLocale.Language.German if Language.current == LANGUAGE_GERMAN else QLocale.Language.English))
        calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)

        # Colors of the app: weekends like other days, muted day names, today bold in the accent color
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, QTextCharFormat())
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, QTextCharFormat())
        header_format = QTextCharFormat()
        header_format.setForeground(self._theme.muted)
        header_format.setBackground(self._theme.base)
        calendar.setHeaderTextFormat(header_format)
        today_format = QTextCharFormat()
        today_format.setForeground(self._theme.accent)
        today_format.setFontWeight(QFont.Weight.Bold)
        calendar.setDateTextFormat(QDate.currentDate(), today_format)
        for name, forward in (("qt_calendar_prevmonth", False), ("qt_calendar_nextmonth", True)):
            button = calendar.findChild(QToolButton, name)
            if button is not None:
                button.setIcon(create_chevron_side_icon(self._theme.text, forward))
                button.setIconSize(QSize(ipx(ICON_SIZE), ipx(ICON_SIZE)))

        current = iso_date(self._item.condition_date) or date.today()
        calendar.setSelectedDate(QDate(current.year, current.month, current.day))

        def take(selected: QDate) -> None:
            menu.close()
            self._set_condition_date(date(selected.year(), selected.month(), selected.day()))

        calendar.clicked.connect(take)
        calendar.activated.connect(take)
        action = QWidgetAction(menu)
        action.setDefaultWidget(calendar)
        menu.addAction(action)
        anchor = self._calendar_button.mapToGlobal(QPoint(self._calendar_button.width(), self._calendar_button.height()))
        menu.exec(QPoint(anchor.x() - menu.sizeHint().width(), anchor.y() + ipx(4)))
        menu.deleteLater()

    def clear(self) -> None:
        self._clear_attachments()

    def add_files(self, paths: list[Path]) -> None:
        if self._item is None or self._storage is None:
            return

        self.edit_started.emit()
        failed: list[str] = []
        for path in paths:
            try:
                self._item.attachments.append(self._storage.import_file(path))
            except OSError as error:
                failed.append(f"{path.name}: {error}")
        self._after_attachments_changed(failed)

    def add_image(self, image: QImage) -> None:
        if self._item is None or self._storage is None:
            return

        self.edit_started.emit()
        failed: list[str] = []
        try:
            self._item.attachments.append(self._storage.import_image(image))
        except OSError as error:
            failed.append(str(error))
        self._after_attachments_changed(failed)

    def _after_attachments_changed(self, failed: list[str]) -> None:
        self._rebuild_attachments()
        self.item_changed()
        if failed:
            show_message(self, tr("Folgende Anhänge konnten nicht hinzugefügt werden:") + "\n\n" + "\n".join(failed), DIALOG_WARNING)

    def _clear_attachments(self) -> None:
        while self._attachment_layout.count() > 0:
            item = self._attachment_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

    def _rebuild_attachments(self) -> None:
        self._clear_attachments()
        if self._item is not None and self._storage is not None:
            for attachment in self._item.attachments:
                card = AttachmentCard(attachment, self._storage.attachment_path(attachment), self._theme)
                card.delete_requested.connect(self._on_delete_attachment)
                self._attachment_layout.addWidget(card)
        self._attachment_layout.addStretch()

    def _choose_files(self) -> None:
        if self._item is None:
            return
        file_names, _ = QFileDialog.getOpenFileNames(self, tr("Anhänge hinzufügen"))
        if file_names:
            self.add_files([Path(name) for name in file_names])

    def _on_description_changed(self) -> None:
        if self._item is None:
            return
        self.edit_started.emit()
        self._item.description = self._description.plain_text()
        self._item.description_html = self._description.html()
        self.item_changed()

    def _on_delete_attachment(self, attachment: Attachment) -> None:
        if self._item is None or self._storage is None:
            return
        if confirm(self, tr("Anhang \"{name}\" entfernen?", name=attachment.name), tr("Entfernen")) is False:
            return

        self.edit_started.emit()
        self._item.attachments = [entry for entry in self._item.attachments if entry.id != attachment.id]
        self._rebuild_attachments()
        self.item_changed()

    def dragEnterEvent(self, event) -> None:
        files = local_files_from_mime(event.mimeData())
        if self._item is not None and files and len(package_paths(event.mimeData())) < len(files):
            self._drop_zone.set_active(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        self.dragEnterEvent(event)

    def dragLeaveEvent(self, event) -> None:
        self._drop_zone.set_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self._drop_zone.set_active(False)
        files = [path for path in local_files_from_mime(event.mimeData()) if path.suffix.lower() != EXPORT_EXTENSION]
        if self._item is None or not files:
            event.ignore()
            return
        event.acceptProposedAction()
        self.add_files(files)


class NotePanel(ItemPanel):
    """Formatted note with inline images, todo creation from lines and PDF export"""

    todos_requested = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(tr("Keine Notiz ausgewählt"), tr("Titel"), parent)
        self.todos_enabled = True

        self._editor = DescriptionEditor(tr("Notiz schreiben, Bilder mit Strg+V einfügen"), images=True)
        self._editor.changed.connect(self._on_text_changed)
        self._editor.text_edit().image_activated.connect(self._show_image)
        self._editor.text_edit().context_actions = self._context_actions
        self._title_edit.submitted.connect(lambda: self._editor.text_edit().setFocus())
        self.body_layout.addWidget(self._editor, 1)

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        self._editor.apply_theme(theme)

    def apply_zoom(self) -> None:
        super().apply_zoom()
        self._editor.apply_zoom()

    def load(self, note: Note) -> None:
        self._editor.set_content(note.html, note.text, self._storage)

    def text_edit(self) -> RichTextEdit:
        return self._editor.text_edit()

    def insert_image(self, image: QImage) -> None:
        edit = self._editor.text_edit()
        edit.setFocus()
        edit.insert_image(image)

    def _on_text_changed(self) -> None:
        if self._item is None:
            return
        self.edit_started.emit()
        self._item.text = self._editor.plain_text()
        self._item.html = self._editor.html()
        self.item_changed()

    def _todo_lines(self) -> tuple[list, list[str]]:
        blocks = []
        texts: list[str] = []
        for block in self._editor.text_edit().selected_blocks():
            text = block.text().replace(OBJECT_REPLACEMENT_CHARACTER, "").strip()
            if not text or text.startswith(TODO_MARK):
                continue
            blocks.append(block)
            texts.append(text)
        return blocks, texts

    def _context_actions(self) -> list:
        if self._item is None or self.todos_enabled is False:
            return []
        blocks, texts = self._todo_lines()
        return [(tr("Als ToDo übernehmen"), create_task_icon, self._create_todos, len(texts) > 0)]

    def _create_todos(self) -> None:
        if self._item is None:
            return
        blocks, texts = self._todo_lines()
        if not texts:
            return

        # Lines taken over as todos start with a check mark
        self.todos_requested.emit(texts)
        edit = self._editor.text_edit()
        cursor = QTextCursor(edit.document())
        cursor.beginEditBlock()
        for block in reversed(blocks):
            cursor.setPosition(block.position())
            cursor.insertText(TODO_MARK + " ")
        cursor.endEditBlock()

    def export_pdf(self) -> None:
        if self._item is None or self._storage is None:
            return

        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        folder = str(settings.value("pdfFolder", "") or QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation))
        title = self._item.title.strip() or tr("Notiz")
        suggested = str(Path(folder) / (safe_file_name(title) + ".pdf"))
        file_name, _ = QFileDialog.getSaveFileName(self, tr("Als PDF exportieren"), suggested, tr("PDF-Dateien (*.pdf)"))
        if not file_name:
            return

        path = Path(file_name)
        if path.suffix.lower() != ".pdf":
            path = path.with_suffix(".pdf")
        settings.setValue("pdfFolder", str(path.parent))
        try:
            write_note_pdf(path, title, format_timestamp(self._item.created), self._editor.text_edit().document(), self._storage)
        except OSError as error:
            show_message(self, tr("PDF konnte nicht gespeichert werden:\n{error}", error=error), DIALOG_WARNING)
            return
        open_with_default_program(path)

    def _show_image(self, name: str) -> None:
        if self._storage is None:
            return
        pixmap = QPixmap(str(self._storage.note_image_path(name)))
        if pixmap.isNull() is False:
            ImageViewer(pixmap, self._item.title if self._item is not None else APP_TITLE, self.window()).exec()


def create_field_grid(rows: list[tuple[str, QWidget]]) -> QGridLayout:
    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(8)
    grid.setColumnStretch(1, 1)
    for row, (label_text, widget) in enumerate(rows):
        label = QLabel(label_text)
        label.setObjectName("mutedLabel")
        grid.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(widget, row, 1)
    return grid


class LinkPanel(ItemPanel):
    """Title, address and note of the selected link"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(tr("Kein Link ausgewählt"), tr("Titel"), parent)

        self._url_edit = create_field_edit("https://…")
        self._url_edit.textEdited.connect(self._on_url_changed)
        self._url_edit.returnPressed.connect(self._open)
        self._note_editor = DescriptionEditor(tr("Notiz"))
        self._note_editor.changed.connect(self._on_note_changed)
        self._title_edit.submitted.connect(lambda: self._url_edit.setFocus())

        self.body_layout.addLayout(create_field_grid([(tr("Adresse"), self._url_edit)]))
        self.body_layout.addSpacing(10)
        self.body_layout.addWidget(create_section_label(tr("Notiz")))
        self.body_layout.addWidget(self._note_editor, 1)

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        self._note_editor.apply_theme(theme)

    def apply_zoom(self) -> None:
        super().apply_zoom()
        self._note_editor.apply_zoom()

    def load(self, link: Link) -> None:
        self._url_edit.setText(link.url)
        self._url_edit.setCursorPosition(0)
        self._note_editor.set_content(link.note_html, link.note)

    def focus_url(self) -> None:
        self._url_edit.setFocus()

    def _on_url_changed(self, text: str) -> None:
        if self._item is None:
            return
        self.edit_started.emit()
        self._item.url = text.strip()
        self.item_changed()

    def _on_note_changed(self) -> None:
        if self._item is None:
            return
        self.edit_started.emit()
        self._item.note = self._note_editor.plain_text()
        self._item.note_html = self._note_editor.html()
        self.item_changed()

    def _open(self) -> None:
        if self._item is not None:
            open_link(self._item.url)


class TabBar(QFrame):
    """Tabs for todos, notes and links"""

    tab_changed = Signal(str)

    def __init__(self, tabs: list[tuple[str, str]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("tabRow")
        self._buttons: dict[str, QToolButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(COLUMN_PADDING, 0, COLUMN_PADDING, 0)
        layout.setSpacing(ipx(TAB_SPACING))
        for key, text in tabs:
            button = QToolButton()
            button.setObjectName("tabButton")
            button.setText(text)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.clicked.connect(lambda checked=False, selected=key: self.tab_changed.emit(selected))
            layout.addWidget(button)
            self._buttons[key] = button
        layout.addStretch()

    def set_current(self, key: str) -> None:
        button = self._buttons.get(key)
        if button is not None:
            button.setChecked(True)

    def set_tabs(self, keys: list[str]) -> None:
        for key, button in self._buttons.items():
            button.setVisible(key in keys)

    def apply_zoom(self) -> None:
        self.layout().setSpacing(ipx(TAB_SPACING))
        bold = QFont(QApplication.font())
        bold.setWeight(QFont.Weight.DemiBold)
        metrics = QFontMetrics(bold)
        for button in self._buttons.values():
            button.setFixedWidth(metrics.horizontalAdvance(button.text()) + ipx(4))
            button.setFixedHeight(metrics.height() + ipx(18))


class InputFilter(QObject):
    """Turns Ctrl+V with images or files into attachments or note images and Ctrl+mouse wheel into zoom"""

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if isinstance(watched, QWidget) and watched.window() is self._window:
                delta = event.angleDelta().y()
                if delta != 0:
                    self._window.zoom_step(1 if delta > 0 else -1)
                return True
            return False

        if event.type() != QEvent.Type.KeyPress or isinstance(event, QKeyEvent) is False:
            return False
        if event.matches(QKeySequence.StandardKey.Paste) is False:
            return False
        if self._window.isActiveWindow() is False:
            return False
        return self._window.handle_paste()

# Main window
class MainWindow(QMainWindow):
    current: Optional[MainWindow] = None

    def __init__(self, storage: Storage, data: AppData, settings: QSettings) -> None:
        super().__init__()
        self._rebuilding = False
        self._storage = storage
        self._data = data
        self._settings = settings
        self._selected: dict[str, Optional[str]] = {item_type: None for item_type in ITEM_TYPES}
        self._selection: list[str] = []
        self._detail_maximized = False
        self._normal_sizes: list[int] = []
        self._quick_add_id: Optional[str] = None
        self._quick_add_undo_size = -1
        self._fresh_name_id: Optional[str] = None
        self._editing_key: Optional[tuple[str, str]] = None
        self._undo_stack: list[tuple[dict, dict]] = []
        self._redo_stack: list[tuple[dict, dict]] = []
        self._last_backup_day: Optional[str] = None
        self._import_queue: list[Path] = []
        self._import_busy = False
        self._save_error_shown = False
        self._archive_expanded = bool(settings.value("archiveExpanded", False, type=bool))
        self._theme = Theme.from_palette(QApplication.palette())
        self._icon_buttons: list[tuple[QToolButton, object]] = []

        self._enabled_tabs = self._load_enabled_tabs()
        self._tab = str(settings.value("activeTab", ITEM_TODO))
        if self._tab not in self._enabled_tabs:
            self._tab = self._enabled_tabs[0]

        # New users with only the general project start with a collapsed project column
        if settings.contains("sidebarCollapsed"):
            self._sidebar_collapsed = bool(settings.value("sidebarCollapsed", False, type=bool))
        else:
            self._sidebar_collapsed = len(data.projects) <= 1
        self._sidebar_width = int(settings.value("sidebarWidth", SIDEBAR_WIDTH))

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(SAVE_DELAY_MS)
        self._save_timer.timeout.connect(self._save_now)

        self._today = date.today()
        self._day_timer = QTimer(self)
        self._day_timer.setInterval(DAY_CHECK_MS)
        self._day_timer.timeout.connect(self._check_day)
        self._day_timer.start()

        # Once per start a look on GitHub for a newer version
        self._update_checker = UpdateChecker(self)
        self._update_checker.found.connect(self._on_update_found)
        QTimer.singleShot(UPDATE_CHECK_DELAY_MS, self._start_update_check)

        self.setWindowTitle(APP_TITLE)
        self.setAcceptDrops(True)
        self.resize(1300, 800)
        self._build_ui()
        self._apply_theme()
        self._apply_zoom()
        self._restore_window_state()
        self._apply_sidebar_state()
        self._render_all()

        QGuiApplication.styleHints().colorSchemeChanged.connect(lambda scheme: QTimer.singleShot(0, self._on_system_color_scheme_changed))

    # UI setup
    def _icon_button(self, icon_factory, tooltip: str, slot) -> QToolButton:
        button = create_icon_button(tooltip, slot)
        self._icon_buttons.append((button, icon_factory))
        return button

    def _build_ui(self) -> None:
        self._header_frames: list[QWidget] = []
        self._footers: list[QFrame] = []

        # Settings menu shared by the project column and the collapsed rail
        self._settings_menu = create_menu(self)
        self._settings_menu.aboutToShow.connect(self._fill_settings_menu)

        # Project column
        project_column = QWidget()
        project_column.setObjectName("projectColumn")
        project_column.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        project_layout = QVBoxLayout(project_column)
        project_layout.setContentsMargins(0, 0, 0, 0)
        project_layout.setSpacing(0)

        project_header = create_column_header(project_layout)
        self._header_frames.append(project_header.parentWidget())
        self._projects_label = create_header_label(tr("Projekte"))
        project_header.addWidget(self._projects_label, 1)
        project_header.addWidget(self._icon_button(create_add_icon, tr("Neues Projekt"), self._add_project))
        project_header.addWidget(self._icon_button(create_collapse_icon, tr("Projektspalte einklappen"), lambda: self._set_sidebar_collapsed(True)))

        self._project_list = ProjectListWidget()
        self._project_delegate = ProjectDelegate(self._project_list, self._theme)
        self._project_list.setItemDelegate(self._project_delegate)
        self._project_list.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        self._project_list.project_drop_validator = self._can_drop_project
        self._project_list.item_drop_validator = self._can_drop_item_on_project
        self._project_list.currentItemChanged.connect(self._on_project_selected)
        self._project_list.itemChanged.connect(self._on_project_renamed)
        self._project_list.context_requested.connect(self._show_project_menu)
        self._project_list.archive_toggle_requested.connect(self._toggle_archive)
        self._project_list.project_dropped.connect(self._on_project_dropped)
        self._project_list.item_dropped.connect(self._on_item_dropped_on_project)
        project_layout.addWidget(self._project_list, 1)

        project_delete_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self._project_list)
        project_delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        project_delete_shortcut.activated.connect(self._delete_current_project)

        self._settings_button = QToolButton()
        self._settings_button.setText(tr("Einstellungen"))
        self._settings_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._settings_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._settings_button.setMenu(self._settings_menu)

        project_footer = QFrame()
        project_footer.setObjectName("columnFooter")
        project_footer_layout = QHBoxLayout(project_footer)
        project_footer_layout.setContentsMargins(COLUMN_PADDING - 6, 0, COLUMN_PADDING - 6, 0)
        project_footer_layout.addWidget(self._settings_button)
        project_footer_layout.addStretch()
        project_layout.addWidget(project_footer)
        self._footers.append(project_footer)

        # Collapsed project column
        rail = QWidget()
        rail.setObjectName("projectColumn")
        rail.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(0, 0, 0, 0)
        rail_layout.setSpacing(0)

        rail_header = QFrame()
        rail_header.setObjectName("columnHeader")
        rail_header_layout = QHBoxLayout(rail_header)
        rail_header_layout.setContentsMargins(0, 8, 0, 8)
        rail_header_layout.addWidget(self._icon_button(create_expand_icon, tr("Projektspalte ausklappen"), lambda: self._set_sidebar_collapsed(False)), 0, Qt.AlignmentFlag.AlignCenter)
        self._header_frames.append(rail_header)
        rail_layout.addWidget(rail_header)
        rail_layout.addStretch(1)

        self._rail_settings_button = QToolButton()
        self._rail_settings_button.setToolTip(tr("Einstellungen"))
        self._rail_settings_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._rail_settings_button.setMenu(self._settings_menu)
        rail_footer = QFrame()
        rail_footer.setObjectName("columnFooter")
        rail_footer_layout = QHBoxLayout(rail_footer)
        rail_footer_layout.setContentsMargins(0, 0, 0, 0)
        rail_footer_layout.addWidget(self._rail_settings_button, 0, Qt.AlignmentFlag.AlignCenter)
        rail_layout.addWidget(rail_footer)
        self._footers.append(rail_footer)

        self._sidebar = QStackedWidget()
        self._sidebar.addWidget(project_column)
        self._sidebar.addWidget(rail)

        # Zoom shortcuts
        zoom_in_action = QAction(self)
        zoom_in_action.setShortcuts([QKeySequence(QKeySequence.StandardKey.ZoomIn), QKeySequence("Ctrl+=")])
        zoom_in_action.triggered.connect(lambda: self.zoom_step(1))
        zoom_out_action = QAction(self)
        zoom_out_action.setShortcuts([QKeySequence(QKeySequence.StandardKey.ZoomOut)])
        zoom_out_action.triggered.connect(lambda: self.zoom_step(-1))
        zoom_reset_action = QAction(self)
        zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_action.triggered.connect(lambda: self.set_zoom(1.0))
        self.addActions([zoom_in_action, zoom_out_action, zoom_reset_action])

        # Undo and redo, text fields keep their own undo while they have the focus
        undo_action = QAction(self)
        undo_action.setShortcuts([QKeySequence(QKeySequence.StandardKey.Undo)])
        undo_action.triggered.connect(self.undo)
        redo_action = QAction(self)
        redo_action.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        redo_action.triggered.connect(self.redo)
        self.addActions([undo_action, redo_action])

        # Item column
        item_column = QWidget()
        self._item_column = item_column
        item_column.setObjectName("itemColumn")
        item_column.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        item_layout = QVBoxLayout(item_column)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(0)

        item_header = create_column_header(item_layout)
        self._header_frames.append(item_header.parentWidget())
        self._header_label = create_header_label()
        self._header_count_label = QLabel()
        self._header_count_label.setObjectName("countLabel")
        item_header.addWidget(self._header_label, 1)
        item_header.addWidget(self._header_count_label)

        self._tab_bar = TabBar([(item_type, tr(TAB_TITLES[item_type])) for item_type in ITEM_TYPES])
        self._tab_bar.tab_changed.connect(self._on_tab_changed)
        self._tab_bar.set_tabs(self._enabled_tabs)
        self._tab_bar.setVisible(len(self._enabled_tabs) > 1)
        item_layout.addWidget(self._tab_bar)

        self._new_item_edit = QLineEdit()
        self._new_item_edit.setObjectName("newItemEdit")
        self._new_item_edit.setClearButtonEnabled(True)
        self._new_item_edit.returnPressed.connect(self._add_item)

        self._item_list = ItemListWidget()
        self._item_delegate = ItemDelegate(self._item_list, self._theme)
        self._item_list.setItemDelegate(self._item_delegate)
        self._item_list.itemSelectionChanged.connect(self._on_item_selection_changed)
        self._item_list.itemChanged.connect(self._on_item_row_changed)
        self._item_list.action_requested.connect(self._on_item_action)
        self._item_list.context_requested.connect(self._show_item_menu)
        self._item_list.section_add_requested.connect(self._quick_add_in_group)
        self._item_delegate.closeEditor.connect(self._on_item_editor_closed)
        self._item_list.section_toggle_requested.connect(self._toggle_section)
        self._item_list.section_rename_requested.connect(self._rename_section)
        self._item_list.done_toggle_requested.connect(self._toggle_done)
        self._item_list.item_dropped.connect(self._on_item_dropped)
        self._item_list.section_dropped.connect(self._on_section_dropped)

        item_delete_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self._item_list)
        item_delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        item_delete_shortcut.activated.connect(self._delete_selection)

        item_body = QVBoxLayout()
        item_body.setContentsMargins(12, 12, 12, 0)
        item_body.setSpacing(8)
        item_body.addWidget(self._new_item_edit)
        item_body.addWidget(self._item_list, 1)
        item_layout.addLayout(item_body, 1)

        # Detail column
        self._todo_panel = TodoPanel()
        self._note_panel = NotePanel()
        self._link_panel = LinkPanel()
        self._panels: dict[str, ItemPanel] = {
            ITEM_TODO: self._todo_panel,
            ITEM_NOTE: self._note_panel,
            ITEM_LINK: self._link_panel,
        }
        self._detail_stack = QStackedWidget()
        for item_type in ITEM_TYPES:
            panel = self._panels[item_type]
            panel.content_changed.connect(self._on_detail_changed)
            panel.edit_started.connect(self._on_edit_started)
            panel.step_started.connect(self._on_step_started)
            panel.maximize_toggled.connect(lambda: self._set_detail_maximized(self._detail_maximized is False))
            self._header_frames.append(panel.header_frame)
            self._footers.append(panel.footer)
            self._detail_stack.addWidget(panel)
        self._note_panel.todos_requested.connect(self._create_todos_from_note)
        self._note_panel.todos_enabled = ITEM_TODO in self._enabled_tabs

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.addWidget(self._sidebar)
        self._splitter.addWidget(item_column)
        self._splitter.addWidget(self._detail_stack)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 1)
        self._splitter.setSizes([SIDEBAR_WIDTH, 500, 560])
        self.setCentralWidget(self._splitter)
        self._status_banner = StatusBanner(self._splitter, self)

    def _restore_window_state(self) -> None:
        geometry = self._settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        splitter_state = self._settings.value("splitter")
        if splitter_state is not None:
            self._splitter.restoreState(splitter_state)

    # Project column collapsing
    def _apply_sidebar_state(self) -> None:
        if self._sidebar_collapsed:
            rail_width = ipx(SIDEBAR_RAIL_WIDTH)
            self._sidebar.setCurrentIndex(1)
            self._sidebar.setFixedWidth(rail_width)
            sizes = self._splitter.sizes()
            if sizes[0] != rail_width:
                sizes[1] += sizes[0] - rail_width
                sizes[0] = rail_width
                self._splitter.setSizes(sizes)
            return

        self._sidebar.setCurrentIndex(0)
        self._sidebar.setMinimumWidth(ipx(SIDEBAR_MIN_WIDTH))
        self._sidebar.setMaximumWidth(QWIDGETSIZE_MAX)
        sizes = self._splitter.sizes()
        width = max(ipx(SIDEBAR_MIN_WIDTH), self._sidebar_width)
        if sizes[0] < width:
            sizes[1] = max(ipx(200), sizes[1] - (width - sizes[0]))
            sizes[0] = width
            self._splitter.setSizes(sizes)

    def _set_sidebar_collapsed(self, collapsed: bool) -> None:
        if collapsed and self._sidebar_collapsed is False:
            self._sidebar_width = self._splitter.sizes()[0]
            self._settings.setValue("sidebarWidth", self._sidebar_width)
        self._sidebar_collapsed = collapsed
        self._settings.setValue("sidebarCollapsed", collapsed)
        self._apply_sidebar_state()

    # Color mode, zoom and language
    def _set_color_mode(self, mode: str) -> None:
        self._settings.setValue("colorMode", mode)
        apply_color_mode(mode)
        self._apply_theme()

    def zoom_step(self, direction: int) -> None:
        current = min(range(len(ZOOM_STEPS)), key=lambda position: abs(ZOOM_STEPS[position] - UiScale.factor))
        target = max(0, min(len(ZOOM_STEPS) - 1, current + direction))
        self.set_zoom(ZOOM_STEPS[target])

    def set_zoom(self, factor: float) -> None:
        if abs(factor - UiScale.factor) < 0.001:
            return
        self._settings.setValue("zoom", factor)
        apply_zoom_factor(factor)
        self._apply_zoom()

    def _apply_zoom(self) -> None:
        # Reapplying the style sheet makes every widget take over the new application font
        QApplication.instance().setStyleSheet(self._theme.style_sheet())
        for frame in self._header_frames:
            frame.setMinimumHeight(ipx(HEADER_HEIGHT))
        for label in (self._projects_label, self._header_label):
            label.setFont(header_font(QApplication.font()))
        for footer in self._footers:
            footer.setFixedHeight(ipx(FOOTER_HEIGHT))
        for button, icon_factory in self._icon_buttons:
            button.setFixedSize(ipx(32), ipx(32))
            button.setIconSize(QSize(ipx(ICON_SIZE), ipx(ICON_SIZE)))
        self._rail_settings_button.setFixedSize(ipx(32), ipx(32))
        self._rail_settings_button.setIconSize(QSize(ipx(ICON_SIZE), ipx(ICON_SIZE)))
        self._settings_button.setIconSize(QSize(ipx(ICON_SIZE + FOLDER_ICON_GAP), ipx(ICON_SIZE)))
        self._tab_bar.apply_zoom()
        for panel in self._panels.values():
            panel.apply_zoom()
        if self._sidebar_collapsed:
            self._apply_sidebar_state()
        self._project_list.scheduleDelayedItemsLayout()
        self._item_list.verticalScrollBar().setSingleStep(ipx(LIST_SCROLL_STEP))
        self._item_list.relayout()
        self._project_list.viewport().update()
        self._item_list.viewport().update()

    def _update_settings_icons(self) -> None:
        # A new version adds a dot to the settings icon
        wide = create_settings_icon(self._theme.text, ICON_SIZE + FOLDER_ICON_GAP)
        narrow = create_settings_icon(self._theme.text)
        if UpdateState.version:
            wide = add_badge(wide, self._theme.accent, self._theme.window, ICON_SIZE + FOLDER_ICON_GAP)
            narrow = add_badge(narrow, self._theme.accent, self._theme.window)
        self._settings_button.setIcon(wide)
        self._rail_settings_button.setIcon(narrow)

    def _start_update_check(self) -> None:
        self._update_checker.start()

    def _on_update_found(self, version: str, url: str) -> None:
        UpdateState.version = version
        UpdateState.url = url
        self._update_settings_icons()
        self._show_status(tr("Update verfügbar, siehe Einstellungen"))

    def _fill_settings_menu(self) -> None:
        menu = self._settings_menu
        menu.clear()
        for submenu in menu.findChildren(QMenu, options=Qt.FindChildOption.FindDirectChildrenOnly):
            submenu.deleteLater()
        text_color = self._theme.text

        mode = str(self._settings.value("colorMode", COLOR_MODE_SYSTEM))
        mode_menu = create_menu(menu, tr("Modus"))
        mode_menu.setIcon(create_sun_icon(text_color) if self._theme.is_dark is False else create_moon_icon(text_color))
        for label, value in (("Wie Windows", COLOR_MODE_SYSTEM), ("Hell", COLOR_MODE_LIGHT), ("Dunkel", COLOR_MODE_DARK)):
            action = mode_menu.addAction(tr(label), lambda checked=False, selected=value: self._set_color_mode(selected))
            action.setCheckable(True)
            action.setChecked(mode == value)
        menu.addMenu(mode_menu)

        language_menu = create_menu(menu, tr("Sprache"))
        language_menu.setIcon(create_language_icon(text_color))
        for label, value in (("Deutsch", LANGUAGE_GERMAN), ("English", LANGUAGE_ENGLISH)):
            action = language_menu.addAction(label, lambda checked=False, selected=value: self._set_language(selected))
            action.setCheckable(True)
            action.setChecked(Language.current == value)
        menu.addMenu(language_menu)

        zoom_menu = create_menu(menu, tr("Zoom ({percent} %)", percent=round(UiScale.factor * 100)))
        zoom_menu.setIcon(create_zoom_icon(text_color))
        # Shortcut texts only, the shortcuts themselves belong to the window
        zoom_menu.addAction(shortcut_label(tr("Vergrößern"), QKeySequence(QKeySequence.StandardKey.ZoomIn)), lambda: self.zoom_step(1))
        zoom_menu.addAction(shortcut_label(tr("Verkleinern"), QKeySequence(QKeySequence.StandardKey.ZoomOut)), lambda: self.zoom_step(-1))
        zoom_menu.addAction(shortcut_label(tr("Zurücksetzen (100 %)"), QKeySequence("Ctrl+0")), lambda: self.set_zoom(1.0))
        menu.addMenu(zoom_menu)

        tabs_menu = create_menu(menu, tr("Reiter"))
        tabs_menu.setIcon(create_tabs_icon(text_color))
        for item_type in ITEM_TYPES:
            enabled = item_type in self._enabled_tabs
            action = tabs_menu.addAction(tr(TAB_TITLES[item_type]), lambda checked=False, selected=item_type: self._set_tab_enabled(selected, selected not in self._enabled_tabs))
            action.setCheckable(True)
            action.setChecked(enabled)
            # The last switched on tab stays
            action.setEnabled(enabled is False or len(self._enabled_tabs) > 1)
        menu.addMenu(tabs_menu)

        menu.addSeparator()
        folder_menu = create_menu(menu, tr("Speicherort"))
        folder_menu.setIcon(create_folder_icon(text_color))
        path_action = folder_menu.addAction(str(self._storage.folder))
        path_action.setEnabled(False)
        folder_menu.addSeparator()
        folder_menu.addAction(tr("Im Explorer öffnen"), lambda: open_with_default_program(self._storage.folder))
        folder_menu.addAction(tr("Daten verschieben …"), self._move_data)
        folder_menu.addAction(tr("Anderen Speicherort öffnen …"), self._change_folder)
        menu.addMenu(folder_menu)

        backup_menu = create_menu(menu, tr("Backups"))
        backup_menu.setIcon(create_backup_icon(text_color))
        self._fill_backup_menu(backup_menu, text_color)
        menu.addMenu(backup_menu)

        # The version line offers a newer version with the dot of the settings icon, a click opens the download page
        menu.addSeparator()
        if UpdateState.version:
            info_icon = add_badge(create_info_icon(text_color), self._theme.accent, self._theme.base)
            menu.addAction(info_icon, tr("Version {version} (Update verfügbar)", version=APP_VERSION), lambda: open_link(UpdateState.url))
        else:
            version_action = menu.addAction(create_info_icon(text_color), tr("Version {version}", version=APP_VERSION))
            version_action.setEnabled(False)

    def _set_language(self, language: str) -> None:
        if language == Language.current:
            return
        self._set_detail_maximized(False)
        self._settings.setValue("language", language)
        self._settings.setValue("activeTab", self._tab)
        if self._sidebar_collapsed is False:
            self._settings.setValue("sidebarWidth", self._splitter.sizes()[0])
        Language.current = language
        self._save_now()

        # The window is rebuilt so every text uses the new language
        replacement = MainWindow(self._storage, self._data, self._settings)
        replacement._selected = dict(self._selected)
        replacement._render_all()
        replacement._splitter.setSizes(self._splitter.sizes())
        replacement.setGeometry(self.geometry())
        if self.isMaximized():
            replacement.showMaximized()
        else:
            replacement.show()
        QApplication.instance().installEventFilter(InputFilter(replacement))
        MainWindow.current = replacement
        self._rebuilding = True
        self.close()
        self.deleteLater()

    def _on_system_color_scheme_changed(self) -> None:
        apply_color_mode(str(self._settings.value("colorMode", COLOR_MODE_SYSTEM)))
        self._apply_theme()

    def _apply_theme(self) -> None:
        self._theme = Theme.from_palette(QApplication.palette())
        palette = QApplication.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, self._theme.muted)
        QApplication.setPalette(palette)
        QApplication.instance().setStyleSheet(self._theme.style_sheet())
        self._project_delegate.theme = self._theme
        self._item_delegate.theme = self._theme
        for panel in self._panels.values():
            panel.apply_theme(self._theme)
        for button, icon_factory in self._icon_buttons:
            button.setIcon(icon_factory(self._theme.text))
        self._update_settings_icons()
        self._project_list.viewport().update()
        self._item_list.viewport().update()

        # Links take the color of the new palette
        self._render_detail()

    # Accessors
    def _project(self) -> Project:
        return self._data.active_project()

    def _current_item(self):
        return self._project().find_item(self._tab, self._selected[self._tab])

    def _clear_selection(self) -> None:
        self._selected = {item_type: None for item_type in ITEM_TYPES}
        self._selection = []

    def _selected_items(self) -> list:
        # Entries of the multi selection in the order of the list
        project = self._project()
        items = []
        for item_id in self._selection:
            item = project.find_item(self._tab, item_id)
            if item is not None:
                items.append(item)
        return items

    # Rendering
    def _render_all(self) -> None:
        self._render_projects()
        self._render_header()
        self._render_input()
        self._render_items()
        self._render_detail()

    def _render_projects(self) -> None:
        self._project_list.blockSignals(True)
        self._project_list.clear()
        for project in self._data.open_projects():
            self._add_project_row(project)

        archived_projects = self._data.archived_projects()
        if archived_projects:
            header = QListWidgetItem(tr("Archiv"))
            header.setData(KIND_ROLE, KIND_ARCHIVE_HEADER)
            header.setData(COUNT_ROLE, len(archived_projects))
            header.setData(EXPANDED_ROLE, self._archive_expanded)
            header.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._project_list.addItem(header)

            if self._archive_expanded:
                for project in archived_projects:
                    self._add_project_row(project)
        self._project_list.blockSignals(False)

    def _add_project_row(self, project: Project) -> None:
        row = QListWidgetItem(project.display_name())
        row.setData(ID_ROLE, project.id)
        row.setData(KIND_ROLE, KIND_PROJECT)
        row.setData(GENERAL_ROLE, project.general)
        row.setData(ARCHIVED_ROLE, project.archived)
        row.setData(COLOR_ROLE, project.color)
        todos_shown = ITEM_TODO in self._enabled_tabs
        row.setData(COUNT_ROLE, len(project.open_todos()) if todos_shown else 0)
        row.setData(FLAGGED_ROLE, project.has_flagged_todo() and todos_shown)

        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if project.general is False:
            flags |= Qt.ItemFlag.ItemIsEditable
        row.setFlags(flags)
        self._project_list.addItem(row)
        if project.id == self._data.active_project_id:
            self._project_list.setCurrentItem(row)

    def _update_project_counts(self) -> None:
        self._project_list.blockSignals(True)
        for row in range(self._project_list.count()):
            item = self._project_list.item(row)
            project = self._data.find_project(item.data(ID_ROLE))
            if project is None:
                continue
            todos_shown = ITEM_TODO in self._enabled_tabs
            item.setData(COUNT_ROLE, len(project.open_todos()) if todos_shown else 0)
            item.setData(FLAGGED_ROLE, project.has_flagged_todo() and todos_shown)
        self._project_list.blockSignals(False)
        self._project_list.viewport().update()
        self._render_header()

    def _render_header(self) -> None:
        project = self._project()
        self._header_label.setText(project.display_name())
        self._header_label.setToolTip(project.display_name())

        details: list[str] = []
        if self._tab == ITEM_TODO:
            count = len(project.open_todos())
            if count:
                details.append(tr("{count} offen", count=count))
        else:
            count = len(project.items(self._tab))
            if count:
                details.append(count_text(self._tab, count))
        if project.archived:
            details.append(tr("archiviert"))
        self._header_count_label.setText(" · ".join(details))

    def _render_input(self) -> None:
        self._tab_bar.set_current(self._tab)
        self._new_item_edit.setPlaceholderText(tr(INPUT_PLACEHOLDERS[self._tab]))

    def _render_items(self) -> None:
        project = self._project()
        item_type = self._tab
        self._item_list.item_type = item_type
        self._item_list.empty_text = tr(EMPTY_TEXTS[item_type])

        self._item_list.blockSignals(True)
        self._item_list.clear()
        selected_row: Optional[QListWidgetItem] = None
        kept_ids = set(self._selection) if self._selected[item_type] in self._selection else set()
        kept_rows: list[QListWidgetItem] = []

        groups = project.groups_of(item_type)
        items = project.items(item_type)
        if item_type == ITEM_TODO:
            items = [todo for todo in items if todo.done is False]

        # Items without group first, then every group with its items
        sections: list[tuple[Optional[ItemGroup], list]] = [(None, [entry for entry in items if entry.group_id is None])]
        for group in groups:
            sections.append((group, [entry for entry in items if entry.group_id == group.id]))

        for group, members in sections:
            if group is not None:
                self._item_list.addItem(self._create_section_row(group, len(members)))
                if group.collapsed:
                    continue
            for entry in members:
                row = self._create_item_row(item_type, entry, group.id if group is not None else "")
                self._item_list.addItem(row)
                if entry.id == self._selected[item_type]:
                    selected_row = row
                if entry.id in kept_ids:
                    kept_rows.append(row)

        # Done todos in their own collapsible section
        if item_type == ITEM_TODO:
            done_todos = project.done_todos()
            if done_todos:
                header = QListWidgetItem(tr("Erledigt"))
                header.setData(KIND_ROLE, KIND_DONE)
                header.setData(COUNT_ROLE, len(done_todos))
                header.setData(EXPANDED_ROLE, project.done_collapsed is False)
                header.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self._item_list.addItem(header)
                if project.done_collapsed is False:
                    for todo in done_todos:
                        row = self._create_item_row(item_type, todo, "")
                        self._item_list.addItem(row)
                        if todo.id == self._selected[item_type]:
                            selected_row = row
                        if todo.id in kept_ids:
                            kept_rows.append(row)

        # Free space at the end for the right click menu and drops
        spacer = QListWidgetItem()
        spacer.setData(KIND_ROLE, KIND_SPACER)
        spacer.setFlags(Qt.ItemFlag.NoItemFlags)
        self._item_list.addItem(spacer)

        if selected_row is not None:
            self._item_list.setCurrentItem(selected_row, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        for row in kept_rows:
            row.setSelected(True)
        self._selection = self._item_list.selected_ids()
        self._item_list.blockSignals(False)
        self._item_list.relayout()

    def _create_section_row(self, group: ItemGroup, count: int) -> QListWidgetItem:
        row = QListWidgetItem(group.name)
        row.setData(ID_ROLE, group.id)
        row.setData(KIND_ROLE, KIND_SECTION)
        row.setData(TITLE_ROLE, group.name)
        row.setData(COUNT_ROLE, count)
        row.setData(EXPANDED_ROLE, group.collapsed is False)
        row.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
        return row

    def _create_item_row(self, item_type: str, item, section_id: str) -> QListWidgetItem:
        row = QListWidgetItem()
        row.setData(ID_ROLE, item.id)
        row.setData(KIND_ROLE, KIND_ITEM)
        row.setData(TYPE_ROLE, item_type)
        row.setData(SECTION_ROLE, section_id)
        self._apply_item_row(row, item_type, item)
        return row

    def _apply_item_row(self, row: QListWidgetItem, item_type: str, item) -> None:
        title = item_title(item)
        row.setText(title if title.strip() else "(" + tr("ohne Titel") + ")")
        row.setData(TITLE_ROLE, title)

        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        subtitle = ""
        tooltip = ""
        target = False
        if item_type == ITEM_TODO:
            row.setCheckState(Qt.CheckState.Checked if item.done else Qt.CheckState.Unchecked)
            row.setData(DONE_ROLE, item.done)
            row.setData(COUNT_ROLE, len(item.attachments))
            row.setData(FLAGGED_ROLE, item.flagged)
            condition, state = todo_condition(item)
            row.setData(CONDITION_ROLE, condition)
            row.setData(STATE_ROLE, state)
            flags |= Qt.ItemFlag.ItemIsUserCheckable
            if item.done is False:
                flags |= Qt.ItemFlag.ItemIsDragEnabled
        else:
            flags |= Qt.ItemFlag.ItemIsDragEnabled

        if item_type == ITEM_NOTE:
            subtitle = format_date(item.created) if item.created else ""
            preview = note_preview(item)
            if preview:
                subtitle = subtitle + "   " + preview if subtitle else preview
        elif item_type == ITEM_LINK:
            subtitle = item.url
            tooltip = item.url
            target = bool(item.url.strip())

        row.setData(SUBTITLE_ROLE, subtitle)
        row.setData(TOOLTIP_ROLE, tooltip)
        row.setData(TARGET_ROLE, target)
        row.setFlags(flags)

    def _update_item_row(self, item_type: str, item) -> None:
        row = self._item_list.find_row(KIND_ITEM, item.id)
        if row is None:
            return
        self._item_list.blockSignals(True)
        self._apply_item_row(row, item_type, item)
        self._item_list.blockSignals(False)
        self._item_list.relayout()

    def _render_detail(self) -> None:
        self._detail_stack.setCurrentIndex(ITEM_TYPES.index(self._tab))
        panel = self._panels[self._tab]
        if len(self._selection) > 1:
            panel.show_selection(tr("{entries} ausgewählt", entries=count_text(self._tab, len(self._selection))))
        else:
            panel.set_item(self._current_item(), self._storage)

        # Without an entry the maximized right column returns to normal
        if self._detail_maximized and panel.item is None:
            self._set_detail_maximized(False)

    def _set_detail_maximized(self, maximized: bool) -> None:
        if maximized == self._detail_maximized:
            return
        if maximized:
            self._normal_sizes = self._splitter.sizes()
        self._detail_maximized = maximized
        self._sidebar.setVisible(maximized is False)
        self._item_column.setVisible(maximized is False)
        if maximized is False and self._normal_sizes:
            self._splitter.setSizes(self._normal_sizes)
        for panel in self._panels.values():
            panel.set_maximized(maximized)

    def _edit_row(self, row: Optional[QListWidgetItem]) -> None:
        if row is None:
            return
        self._item_list.scrollToItem(row)
        self._item_list.editItem(row)

    # Tabs
    def _load_enabled_tabs(self) -> list[str]:
        stored = self._settings.value("enabledTabs")
        if stored is None:
            return list(ITEM_TYPES)
        names = stored if isinstance(stored, list) else str(stored).split()
        tabs = [item_type for item_type in ITEM_TYPES if item_type in names]
        return tabs or list(ITEM_TYPES)

    def _set_tab_enabled(self, item_type: str, enabled: bool) -> None:
        tabs = [entry for entry in ITEM_TYPES if (entry in self._enabled_tabs or entry == item_type) and (entry != item_type or enabled)]
        if not tabs:
            return
        self._enabled_tabs = tabs
        self._settings.setValue("enabledTabs", " ".join(tabs))
        self._apply_enabled_tabs()
        self._render_all()

    def _apply_enabled_tabs(self) -> None:
        # Hidden tabs keep their data, with only one tab the tab row disappears
        self._tab_bar.set_tabs(self._enabled_tabs)
        self._tab_bar.setVisible(len(self._enabled_tabs) > 1)
        self._note_panel.todos_enabled = ITEM_TODO in self._enabled_tabs
        if self._tab not in self._enabled_tabs:
            self._tab = self._enabled_tabs[0]
            self._selection = []
            self._settings.setValue("activeTab", self._tab)

    def _on_tab_changed(self, item_type: str) -> None:
        if item_type == self._tab:
            return
        self._tab = item_type
        self._selection = []
        self._settings.setValue("activeTab", item_type)
        self._render_header()
        self._render_input()
        self._render_items()
        self._render_detail()

    # Projects
    def _on_project_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        if current is None or current.data(KIND_ROLE) != KIND_PROJECT:
            return
        project_id = current.data(ID_ROLE)
        if project_id == self._data.active_project_id:
            return

        self._data.active_project_id = project_id
        self._clear_selection()
        self._render_header()
        self._render_items()
        self._render_detail()
        self._schedule_save()

    def _show_project_menu(self, project_id: str, position: QPoint) -> None:
        text_color = self._theme.text
        menu = create_menu(self)
        project = self._data.find_project(project_id)

        # Free space below the projects
        if project is None:
            menu.addAction(create_add_icon(text_color), tr("Neues Projekt"), self._add_project)
            menu.addAction(create_import_icon(text_color), tr("Importieren …"), self._choose_import_file)
            menu.exec(position)
            menu.deleteLater()
            return

        if project.general is False:
            menu.addAction(create_rename_icon(text_color), tr("Umbenennen"), lambda: self._project_list.editItem(self._project_list.find_row(project.id)))

        color_menu = create_menu(menu, tr("Farbe"))
        color_menu.setIcon(create_dot_icon(QColor(project.color or GENERAL_COLOR)))
        for name, value in PROJECT_COLORS:
            action = color_menu.addAction(create_dot_icon(QColor(value)), tr(name), lambda selected=value: self._set_project_color(project, selected))
            if project.color == value:
                font = QFont(action.font())
                font.setWeight(QFont.Weight.DemiBold)
                action.setFont(font)
        menu.addMenu(color_menu)

        if project.general is False:
            if project.archived:
                menu.addAction(create_restore_icon(text_color), tr("Wiederherstellen"), lambda: self._set_project_archived(project, False))
            else:
                menu.addAction(create_archive_icon(text_color), tr("Archivieren"), lambda: self._set_project_archived(project, True))
        menu.addAction(create_export_icon(text_color), tr("Exportieren …"), lambda: self._export_project(project))
        if project.general is False:
            menu.addSeparator()
            menu.addAction(create_delete_icon(text_color), tr("Löschen"), lambda: self._delete_project(project))
        menu.exec(position)
        menu.deleteLater()

    def _set_project_color(self, project: Project, color: str) -> None:
        if project.color == color:
            return
        self._checkpoint()
        project.color = color
        self._render_projects()
        self._schedule_save()

    def _toggle_archive(self) -> None:
        self._archive_expanded = self._archive_expanded is False
        self._settings.setValue("archiveExpanded", self._archive_expanded)
        self._render_projects()

    def _add_project(self) -> None:
        self._checkpoint()
        project = Project.create(tr("Neues Projekt"))
        self._fresh_name_id = project.id
        project.color = self._data.next_color()
        self._data.projects.insert(len(self._data.open_projects()), project)
        self._data.active_project_id = project.id
        self._clear_selection()
        self._render_all()
        self._schedule_save()

        row = self._project_list.currentItem()
        if row is not None:
            self._project_list.editItem(row)

    def _on_project_renamed(self, row: QListWidgetItem) -> None:
        project = self._data.find_project(row.data(ID_ROLE))
        if project is None or project.general:
            return

        name = row.text().strip()
        if not name:
            name = project.name
        if row.text() != name:
            self._project_list.blockSignals(True)
            row.setText(name)
            self._project_list.blockSignals(False)
        if name == project.name:
            self._fresh_name_id = None
            return

        # Naming a new project belongs to creating it
        if project.id != self._fresh_name_id:
            self._checkpoint()
        self._fresh_name_id = None
        project.name = name
        self._render_header()
        self._schedule_save()

    def _delete_current_project(self) -> None:
        row = self._project_list.currentItem()
        if row is None:
            return
        project = self._data.find_project(row.data(ID_ROLE))
        if project is not None:
            self._delete_project(project)

    def _delete_project(self, project: Project) -> None:
        if project.general:
            return
        if project.item_count():
            message = tr("Projekt \"{name}\" mit allen ToDos, Notizen und Links löschen?", name=project.name)
        else:
            message = tr("Projekt \"{name}\" löschen?", name=project.name)
        if confirm(self, message, tr("Löschen")) is False:
            return

        self._checkpoint()
        self._data.projects.remove(project)
        if self._data.active_project_id == project.id:
            self._data.active_project_id = self._data.general_project().id
            self._clear_selection()
        self._render_all()
        self._schedule_save()

    def _set_project_archived(self, project: Project, archived: bool) -> None:
        if project.general:
            return

        # Archived projects move to the end, restored ones to the end of the open projects
        self._checkpoint()
        self._data.projects.remove(project)
        project.archived = archived
        if archived:
            self._data.projects.append(project)
        else:
            self._data.projects.insert(len(self._data.open_projects()), project)

        if archived and self._data.active_project_id == project.id:
            self._data.active_project_id = self._data.general_project().id
            self._clear_selection()
        self._render_all()
        self._schedule_save()

    def _can_drop_project(self, dragged_id: str, target_id: str, zone: str) -> bool:
        dragged = self._data.find_project(dragged_id)
        if dragged is None or dragged.general:
            return False
        if target_id == ARCHIVE_TARGET:
            return dragged.archived is False if zone == DROP_ONTO else True

        target = self._data.find_project(target_id)
        if target is None or target is dragged:
            return False
        return not (target.general and zone == DROP_BEFORE)

    def _on_project_dropped(self, dragged_id: str, target_id: str, zone: str) -> None:
        if self._can_drop_project(dragged_id, target_id, zone) is False:
            return
        self._checkpoint()
        dragged = self._data.find_project(dragged_id)
        self._data.projects.remove(dragged)

        if target_id == ARCHIVE_TARGET:
            dragged.archived = zone == DROP_ONTO
            if dragged.archived:
                self._data.projects.append(dragged)
            else:
                self._data.projects.insert(len(self._data.open_projects()), dragged)
        else:
            target = self._data.find_project(target_id)
            dragged.archived = target.archived
            position = self._data.projects.index(target)
            if zone == DROP_AFTER:
                position += 1
            self._data.projects.insert(position, dragged)

        if dragged.archived and self._data.active_project_id == dragged.id:
            self._data.active_project_id = self._data.general_project().id
            self._clear_selection()
        self._render_all()
        self._schedule_save()

    def _can_drop_item_on_project(self, item_type: str, item_ids: list, project_id: str) -> bool:
        target = self._data.find_project(project_id)
        if target is None:
            return False
        for item_id in item_ids:
            found = self._data.find_item(item_type, item_id)
            if found is not None and found[0] is not target:
                return True
        return False

    def _on_item_dropped_on_project(self, item_type: str, item_ids: list, project_id: str) -> None:
        if self._can_drop_item_on_project(item_type, item_ids, project_id) is False:
            return
        self._checkpoint()
        target = self._data.find_project(project_id)
        for item_id in item_ids:
            found = self._data.find_item(item_type, item_id)
            if found is None or found[0] is target:
                continue
            source, item = found
            source.items(item_type).remove(item)
            item.group_id = None
            target.items(item_type).append(item)
            if self._selected[item_type] == item.id:
                self._selected[item_type] = None
        self._selection = []
        self._render_items()
        self._render_detail()
        self._update_project_counts()
        self._schedule_save()

    # Items
    def _add_item(self) -> None:
        text = self._new_item_edit.text().strip()
        if not text and self._tab != ITEM_NOTE:
            return

        item = self._create_item(self._tab, text, None)
        self._new_item_edit.clear()

        # Notes continue in the editor, links without address in the address field
        if self._tab == ITEM_NOTE:
            self._note_panel.text_edit().setFocus()
        elif self._tab == ITEM_LINK and not item.url:
            self._link_panel.focus_url()

    def _create_item(self, item_type: str, text: str, group_id: Optional[str], named_later: bool = False):
        self._checkpoint()
        project = self._project()
        if item_type == ITEM_TODO:
            item = Todo.create(text, group_id)
            project.todos.append(item)
        elif item_type == ITEM_NOTE:
            # Notes without text are named with the date, unless the name is typed right afterwards
            item = Note.create(text or ("" if named_later else format_date(time.time())), group_id)
            project.notes.insert(0, item)
        else:
            title, url = parse_link_input(text)
            item = Link.create(title, url, group_id)
            project.links.append(item)

        self._selected[item_type] = item.id
        self._render_items()
        self._render_detail()
        self._update_project_counts()
        self._schedule_save()

        row = self._item_list.currentItem()
        if row is not None:
            self._item_list.scrollToItem(row)
        return item

    def _on_item_selection_changed(self) -> None:
        previous = self._selected.get(self._tab)
        ids = self._item_list.selected_ids()
        current = self._item_list.currentItem()
        current_id = current.data(ID_ROLE) if current is not None and current.data(KIND_ROLE) == KIND_ITEM else None
        self._selection = ids
        if len(ids) == 1:
            self._selected[self._tab] = ids[0]
        elif not ids:
            self._selected[self._tab] = None
        elif current_id in ids:
            self._selected[self._tab] = current_id
        elif self._selected[self._tab] not in ids:
            self._selected[self._tab] = ids[-1]
        if self._selected[self._tab] != previous:
            self._editing_key = None
        self._render_detail()

    def _on_item_row_changed(self, row: QListWidgetItem) -> None:
        project = self._project()
        kind = row.data(KIND_ROLE)
        if kind == KIND_SECTION:
            self._on_section_renamed(row)
            return
        if kind != KIND_ITEM:
            return
        item = project.find_item(self._tab, row.data(ID_ROLE))
        if item is None:
            return

        if self._tab == ITEM_TODO:
            checked = row.checkState() == Qt.CheckState.Checked
            if checked != item.done:
                QTimer.singleShot(0, lambda: self._set_todo_done(item, checked))
                return

        # New entry from the add icon of a group
        if item.id == self._quick_add_id:
            self._finish_quick_add(item, row.text().strip())
            return

        # Inline renaming
        title = item_title(item)
        shown = title if title.strip() else "(" + tr("ohne Titel") + ")"
        if row.text() == shown:
            return
        new_title = row.text().strip()
        if new_title and new_title != title:
            self._checkpoint()
            set_item_title(item, new_title)
            touch(item)
        self._update_item_row(self._tab, item)
        if self._panels[self._tab].item is item:
            self._panels[self._tab].refresh_details()
        self._schedule_save()

    def _quick_add_in_group(self, group_id: str) -> None:
        group = self._project().find_group(self._tab, group_id)
        if group is None:
            return
        group.collapsed = False
        item = self._create_item(self._tab, "", group.id, True)
        self._quick_add_id = item.id
        self._quick_add_undo_size = len(self._undo_stack)
        self._edit_row(self._item_list.find_row(KIND_ITEM, item.id))

    def _finish_quick_add(self, item, text: str) -> None:
        # Without text the closing editor removes the entry again
        if not text:
            return
        self._quick_add_id = None
        if self._tab == ITEM_LINK:
            item.title, item.url = parse_link_input(text)
        else:
            set_item_title(item, text)
        self._update_item_row(self._tab, item)
        if self._panels[self._tab].item is item:
            self._panels[self._tab].set_item(item, self._storage)
        self._schedule_save()

        # Notes continue in the note text, other entries with the next entry of the same group
        if self._tab == ITEM_NOTE:
            QTimer.singleShot(0, lambda: self._note_panel.text_edit().setFocus())
            return
        group_id = item.group_id
        QTimer.singleShot(0, lambda: self._quick_add_in_group(group_id))

    def _on_item_editor_closed(self, editor: QWidget, hint) -> None:
        # A new entry from the add icon that stayed without name is removed again
        item_id = self._quick_add_id
        project = self._project()
        item = project.find_item(self._tab, item_id) if item_id else None
        self._quick_add_id = None
        if item is None or item_title(item).strip():
            return

        def remove() -> None:
            items = project.items(self._tab)
            if item in items and not item_title(item).strip():
                items.remove(item)
                if self._undo_stack and len(self._undo_stack) == self._quick_add_undo_size:
                    self._undo_stack.pop()
                if self._selected[self._tab] == item.id:
                    self._selected[self._tab] = None
                self._render_items()
                self._render_detail()
                self._update_project_counts()
                self._schedule_save()
        QTimer.singleShot(0, remove)

    def _set_todo_done(self, todo: Todo, done: bool) -> None:
        project = self._project()
        if todo not in project.todos:
            return

        self._checkpoint()
        todo.done = done
        touch(todo)
        if done:
            todo.done_at = time.time()
            todo.flagged = False
        else:
            todo.done_at = None
            project.todos.remove(todo)
            project.todos.append(todo)

        self._render_items()
        self._update_project_counts()
        if self._panels[ITEM_TODO].item is todo:
            self._panels[ITEM_TODO].refresh_details()
        self._schedule_save()

    def _on_item_action(self, action: str, item_id: str) -> None:
        item = self._project().find_item(self._tab, item_id)
        if item is None:
            return

        if action == "check":
            self._set_todo_done(item, item.done is False)
        elif action == "flag":
            self._checkpoint()
            item.flagged = item.flagged is False
            touch(item)
            self._update_item_row(self._tab, item)
            if self._panels[self._tab].item is item:
                self._panels[self._tab].refresh_details()
            self._update_project_counts()
            self._schedule_save()
        elif action == "open":
            open_link(item.url)

    def _delete_item(self, item_type: str, item) -> None:
        project = self._project()
        if item is None or item not in project.items(item_type):
            return

        title = item_title(item) if item_title(item).strip() else tr("ohne Titel")
        if item_type == ITEM_TODO and item.attachments:
            message = tr("ToDo \"{title}\" mit {count} Anhängen löschen?", title=title, count=len(item.attachments))
        else:
            message = tr(DELETE_MESSAGES[item_type], title=title)
        if confirm(self, message, tr("Löschen")) is False:
            return

        self._checkpoint()
        project.items(item_type).remove(item)
        if self._selected[item_type] == item.id:
            self._selected[item_type] = None

        self._render_items()
        self._render_detail()
        self._update_project_counts()
        self._schedule_save()

    def _delete_selection(self) -> None:
        items = self._selected_items()
        if not items and self._current_item() is not None:
            items = [self._current_item()]
        if len(items) == 1:
            self._delete_item(self._tab, items[0])
        elif items:
            self._delete_items(self._tab, items)

    def _delete_items(self, item_type: str, items: list) -> None:
        project = self._project()
        items = [item for item in items if item in project.items(item_type)]
        if not items:
            return

        attachments = sum(len(item.attachments) for item in items) if item_type == ITEM_TODO else 0
        if attachments:
            message = tr("{entries} mit {count} Anhängen löschen?", entries=count_text(item_type, len(items)), count=attachments)
        else:
            message = tr("{entries} löschen?", entries=count_text(item_type, len(items)))
        if confirm(self, message, tr("Löschen")) is False:
            return

        self._checkpoint()
        for item in items:
            project.items(item_type).remove(item)
        self._selected[item_type] = None
        self._selection = []

        self._render_items()
        self._render_detail()
        self._update_project_counts()
        self._schedule_save()

    def _on_item_dropped(self, item_ids: list, group_id: str, anchor_id: str, after: bool) -> None:
        project = self._project()
        items = project.items(self._tab)
        moved = [entry for entry in items if entry.id in item_ids]
        if not moved or (group_id and project.find_group(self._tab, group_id) is None):
            return

        self._checkpoint()
        moved_ids = {entry.id for entry in moved}
        remaining = [entry for entry in items if entry.id not in moved_ids]
        for entry in moved:
            entry.group_id = group_id or None
        anchor = project.find_item(self._tab, anchor_id) if anchor_id else None
        if anchor is not None and anchor.id not in moved_ids:
            position = remaining.index(anchor) + (1 if after else 0)
        elif anchor is not None:
            # Dropped onto one of the moved entries, they stay where that entry was
            position = len([entry for entry in items[:items.index(anchor)] if entry.id not in moved_ids])
        else:
            # End of the group
            position = len(remaining)
            for index, entry in enumerate(remaining):
                if entry.group_id == (group_id or None):
                    position = index + 1
        items[:] = remaining[:position] + moved + remaining[position:]

        self._render_items()
        self._schedule_save()

    def _on_detail_changed(self) -> None:
        item = self._panels[self._tab].item
        if item is not None:
            self._update_item_row(self._tab, item)
        self._schedule_save()

    def _on_edit_started(self) -> None:
        # Typing in the right column is one undo step per entry until something else happens
        item = self._panels[self._tab].item
        key = (self._tab, item.id if item is not None else "")
        if key == self._editing_key:
            return
        self._checkpoint()
        self._editing_key = key

    def _check_day(self) -> None:
        # On a new day the conditions of the todos show the new state, also after sleep
        if date.today() == self._today:
            return
        self._today = date.today()
        if self._tab != ITEM_TODO:
            return
        for todo in self._project().todos:
            self._update_item_row(ITEM_TODO, todo)

    def _on_step_started(self) -> None:
        # A choice in the right column is an undo step of its own, typing afterwards starts the next one
        self._checkpoint()
        self._editing_key = None

    def _create_todos_from_note(self, texts: list[str]) -> None:
        project = self._project()
        note = self._note_panel.item
        self._checkpoint()
        if note is not None:
            self._editing_key = (ITEM_NOTE, note.id)
        for text in texts:
            todo = Todo.create(text)
            if note is not None:
                todo.description = tr("Aus Notiz \"{title}\"", title=note.title)
            project.todos.append(todo)
        self._update_project_counts()
        self._schedule_save()
        self._show_status(tr("1 ToDo erstellt") if len(texts) == 1 else tr("{count} ToDos erstellt", count=len(texts)))

    # Groups inside a tab
    def _add_section(self) -> None:
        self._checkpoint()
        project = self._project()
        group = ItemGroup.create(tr("Neue Gruppe"))
        self._fresh_name_id = group.id
        project.groups_of(self._tab).append(group)
        self._render_items()
        self._schedule_save()
        self._edit_row(self._item_list.find_row(KIND_SECTION, group.id))

    def _show_item_menu(self, kind: str, target_id: str, position: QPoint) -> None:
        project = self._project()
        text_color = self._theme.text
        menu = create_menu(self)

        if kind == "section":
            group = project.find_group(self._tab, target_id)
            if group is None:
                return
            menu.addAction(create_rename_icon(text_color), tr("Umbenennen"), lambda: self._edit_row(self._item_list.find_row(KIND_SECTION, group.id)))
            menu.addAction(create_export_icon(text_color), tr("Exportieren …"), lambda: self._export_section(group))
            menu.addSeparator()
            menu.addAction(create_delete_icon(text_color), tr("Löschen"), lambda: self._delete_section(group))
        elif kind == "item":
            item = project.find_item(self._tab, target_id)
            if item is None:
                return

            # Several selected entries share one menu
            selection = self._selected_items()
            if len(selection) > 1 and item in selection:
                menu.addAction(create_export_icon(text_color), tr("Exportieren …"), lambda: self._export_items(selection))
                menu.addSeparator()
                menu.addAction(create_delete_icon(text_color), tr("Löschen"), lambda: self._delete_items(self._tab, selection))
                menu.exec(position)
                menu.deleteLater()
                return

            if self._tab == ITEM_TODO:
                if item.done is False:
                    flag_text = tr("Markierung entfernen") if item.flagged else tr("Markieren")
                    menu.addAction(create_flag_icon(text_color), flag_text, lambda: self._on_item_action("flag", item.id))
            elif self._tab == ITEM_NOTE:
                menu.addAction(create_pdf_icon(text_color), tr("Als PDF exportieren"), lambda: self._export_note_pdf(item))
            else:
                open_action = menu.addAction(create_open_icon(text_color), tr("Öffnen"), lambda: open_link(item.url))
                copy_action = menu.addAction(create_copy_icon(text_color), tr("Adresse kopieren"), lambda: QGuiApplication.clipboard().setText(item.url))
                open_action.setEnabled(bool(item.url.strip()))
                copy_action.setEnabled(bool(item.url.strip()))
            menu.addAction(create_export_icon(text_color), tr("Exportieren …"), lambda: self._export_item(item))
            menu.addSeparator()
            menu.addAction(create_delete_icon(text_color), tr("Löschen"), lambda: self._delete_item(self._tab, item))
        else:
            menu.addAction(create_group_add_icon(text_color), tr("Neue Gruppe"), self._add_section)
            menu.addAction(create_import_icon(text_color), tr("Importieren …"), self._choose_import_file)

        menu.exec(position)
        menu.deleteLater()

    def _export_note_pdf(self, note: Note) -> None:
        if self._note_panel.item is not note:
            self._selected[ITEM_NOTE] = note.id
            self._render_detail()
        self._note_panel.export_pdf()

    def _delete_section(self, group: ItemGroup) -> None:
        project = self._project()
        members = [entry for entry in project.items(self._tab) if entry.group_id == group.id]
        if members:
            message = tr("Gruppe \"{name}\" löschen? Die {count} Einträge bleiben ohne Gruppe erhalten.", name=group.name, count=len(members))
        else:
            message = tr("Gruppe \"{name}\" löschen?", name=group.name)
        if confirm(self, message, tr("Löschen")) is False:
            return

        self._checkpoint()
        for entry in members:
            entry.group_id = None
        project.groups_of(self._tab).remove(group)
        self._render_items()
        self._schedule_save()

    def _toggle_section(self, group_id: str) -> None:
        group = self._project().find_group(self._tab, group_id)
        if group is None:
            return
        group.collapsed = group.collapsed is False
        self._render_items()
        self._schedule_save()

    def _rename_section(self, group_id: str, undo_toggle: bool) -> None:
        group = self._project().find_group(self._tab, group_id)
        if group is None:
            return

        # The first click of the double click toggled the group, this restores it
        if undo_toggle:
            group.collapsed = group.collapsed is False
            self._render_items()
            self._schedule_save()
        self._edit_row(self._item_list.find_row(KIND_SECTION, group_id))

    def _on_section_renamed(self, row: QListWidgetItem) -> None:
        group = self._project().find_group(self._tab, row.data(ID_ROLE))
        if group is None:
            return
        name = row.text().strip()
        if name and name != group.name:
            # Naming a new group belongs to creating it
            if group.id != self._fresh_name_id:
                self._checkpoint()
            group.name = name
            self._schedule_save()
        self._fresh_name_id = None
        self._item_list.blockSignals(True)
        row.setText(group.name)
        row.setData(TITLE_ROLE, group.name)
        self._item_list.blockSignals(False)

    def _toggle_done(self) -> None:
        project = self._project()
        project.done_collapsed = project.done_collapsed is False
        self._render_items()
        self._schedule_save()

    def _on_section_dropped(self, group_id: str, anchor_group_id: str, after: bool) -> None:
        groups = self._project().groups_of(self._tab)
        group = self._project().find_group(self._tab, group_id)
        anchor = self._project().find_group(self._tab, anchor_group_id)
        if group is None or anchor is None or group is anchor:
            return
        self._checkpoint()
        groups.remove(group)
        groups.insert(groups.index(anchor) + (1 if after else 0), group)
        self._render_items()
        self._schedule_save()

    # Export
    def _export_values(self, kind: str, name: str, item_type: Optional[str] = None) -> dict:
        return {
            "format": EXPORT_FORMAT,
            "format_version": EXPORT_FORMAT_VERSION,
            "app_version": APP_VERSION,
            "kind": kind,
            "item_type": item_type,
            "name": name,
            "created": time.time(),
        }

    def _export_item(self, item) -> None:
        self._export_items([item])

    def _export_items(self, items: list) -> None:
        project = self._project()
        if len(items) == 1:
            name = item_title(items[0]) or tr(SINGULAR_TITLES[self._tab])
        else:
            name = project.display_name() + " " + count_text(self._tab, len(items))
        values = self._export_values(EXPORT_ITEMS, name, self._tab)
        groups: list[dict] = []
        for item in items:
            group = project.find_group(self._tab, item.group_id)
            if group is not None and asdict(group) not in groups:
                groups.append(asdict(group))
        values["groups"] = groups
        values["items"] = [asdict(item) for item in items]
        self._write_export(name, values)

    def _export_section(self, group: ItemGroup) -> None:
        project = self._project()
        values = self._export_values(EXPORT_GROUP, group.name, self._tab)
        values["groups"] = [asdict(group)]
        values["items"] = [asdict(entry) for entry in project.items(self._tab) if entry.group_id == group.id]
        self._write_export(group.name, values)

    def _export_project(self, project: Project) -> None:
        values = self._export_values(EXPORT_PROJECT, project.display_name())
        project_values = asdict(project)
        project_values["name"] = project.display_name()
        project_values["general"] = False
        values["project"] = project_values
        self._write_export(project.display_name(), values)

    def _exchange_folder(self) -> str:
        return str(self._settings.value("exchangeFolder", "") or QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation))

    def _write_export(self, name: str, values: dict) -> None:
        suggested = str(Path(self._exchange_folder()) / (safe_file_name(name) + EXPORT_EXTENSION))
        file_name, _ = QFileDialog.getSaveFileName(self, tr("Exportieren"), suggested, tr("Project-Desk-Dateien (*.pdesk)"))
        if not file_name:
            return
        path = Path(file_name)
        if path.suffix.lower() != EXPORT_EXTENSION:
            path = path.with_name(path.name + EXPORT_EXTENSION)
        self._settings.setValue("exchangeFolder", str(path.parent))

        self._save_now()
        try:
            write_package(path, values, self._storage)
        except OSError as error:
            show_message(self, tr("Export fehlgeschlagen:\n{error}", error=error), DIALOG_WARNING)
            return
        show_message(self, tr("Exportiert nach\n{path}\n\nGröße: {size}", path=path, size=format_size(path.stat().st_size)))

    # Import
    def bring_to_front(self) -> None:
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def _choose_import_file(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, tr("Importieren"), self._exchange_folder(), tr("Project-Desk-Dateien (*.pdesk)"))
        if file_name:
            self._settings.setValue("exchangeFolder", str(Path(file_name).parent))
            self.import_file(Path(file_name))

    def import_file(self, path: Path) -> None:
        # Files arriving while a dialog is open wait for their turn
        self._import_queue.append(path)
        if self._import_busy:
            return
        self._import_busy = True
        try:
            while self._import_queue:
                self._import_one(self._import_queue.pop(0))
        finally:
            self._import_busy = False

    def _import_one(self, path: Path) -> None:
        self.bring_to_front()
        try:
            package = ImportPackage(path)
        except PackageError as error:
            show_message(self, tr("\"{name}\" kann nicht importiert werden:\n{error}", name=path.name, error=error), DIALOG_WARNING)
            return
        try:
            self._run_import(package)
        finally:
            package.close()

    def _plan_import(self, package: ImportPackage) -> dict:
        values = package.values
        if package.kind == EXPORT_PROJECT:
            project_values = values["project"]
            groups = project_values.get("groups", {}) if isinstance(project_values.get("groups"), dict) else {}
            sections = [(item_type, list(project_values.get(ITEM_LISTS[item_type], [])), list(groups.get(item_type, []))) for item_type in ITEM_TYPES]
            target = self._data.find_project(str(project_values.get("id", "")))
            name = str(project_values.get("name", "")) or tr("Projekt")
            counts = [count_text(item_type, len(entries)) for item_type, entries, group_values in sections if entries]
            summary = tr("Projekt \"{name}\"", name=name) + (": " + ", ".join(counts) if counts else "")
            if target is None:
                target_text = tr("Ziel: neues Projekt")
            else:
                target_text = tr("Ziel: vorhandenes Projekt \"{name}\", fehlende Einträge werden ergänzt", name=target.display_name())
        else:
            item_type = package.item_type
            entries = list(values.get("items", []))
            sections = [(item_type, entries, list(values.get("groups", [])))]
            target = self._project()
            if package.kind == EXPORT_GROUP:
                summary = tr("Gruppe \"{name}\": {count}", name=values.get("name", ""), count=count_text(item_type, len(entries)))
            elif len(entries) == 1:
                summary = tr(SINGULAR_TITLES[item_type]) + " \"" + str(values.get("name", "")) + "\""
            else:
                summary = count_text(item_type, len(entries))
            target_text = tr("Ziel: Projekt \"{project}\", Reiter {tab}", project=target.display_name(), tab=tr(TAB_TITLES[item_type]))

        # Every entry must be readable before anything changes
        duplicates = 0
        for item_type, entries, group_values in sections:
            for group in group_values:
                ItemGroup.from_dict(group)
            for entry in entries:
                ITEM_FACTORIES[item_type](entry)
                if target is not None and self._find_duplicate(target, item_type, entry) is not None:
                    duplicates += 1
        return {"sections": sections, "target": target, "summary": summary, "target_text": target_text, "duplicates": duplicates}

    def _find_duplicate(self, project: Project, item_type: str, values: dict):
        item_id = str(values.get("id", ""))
        for item in project.items(item_type):
            if item.id == item_id:
                return item
        if item_type == ITEM_LINK:
            url = str(values.get("url", "")).strip().rstrip("/").casefold()
            for link in project.links:
                if url and link.url.strip().rstrip("/").casefold() == url:
                    return link
        return None

    def _run_import(self, package: ImportPackage) -> None:
        try:
            plan = self._plan_import(package)
        except LOAD_ERRORS:
            show_message(self, tr("\"{name}\" kann nicht importiert werden:\n{error}", name=package.path.name, error=tr("Die Datei ist keine Project-Desk-Datei oder beschädigt.")), DIALOG_WARNING)
            return

        text = tr("Inhalt: {summary}", summary=plan["summary"]) + "\n" + plan["target_text"]
        if plan["duplicates"]:
            if plan["duplicates"] == 1:
                text += "\n\n" + tr("1 Eintrag gibt es schon.")
            else:
                text += "\n\n" + tr("{count} Einträge gibt es schon.", count=plan["duplicates"])
            mode = ask(self, text, [(tr("Überspringen"), IMPORT_SKIP), (tr("Ersetzen"), IMPORT_REPLACE)])
        else:
            mode = IMPORT_ADD if confirm(self, text, tr("Importieren"), DIALOG_INFO) else None
        if mode is None or self._backup(BACKUP_IMPORT) is False:
            return

        self._checkpoint()
        before = self._undo_stack[-1][0]
        report = {"imported": 0, "replaced": 0, "skipped": 0, "missing": []}
        written: list[Path] = []
        first: Optional[tuple[str, str]] = None
        try:
            project = plan["target"]
            if project is None:
                project = self._create_imported_project(package.values["project"])
            for item_type, entries, group_values in plan["sections"]:
                imported = self._import_entries(project, item_type, entries, group_values, package, mode, report, written)
                if imported and first is None:
                    first = (item_type, imported[0])
        except (OSError, *LOAD_ERRORS) as error:
            for path in written:
                path.unlink(missing_ok=True)
            self._undo_stack.pop()
            self._restore_state(before, self._view_state())
            show_message(self, tr("Import fehlgeschlagen:\n{error}\n\nEs wurde nichts verändert.", error=error), DIALOG_ERROR)
            return

        # Tabs of imported entries are switched on again
        hidden = [item_type for item_type, entries, group_values in plan["sections"] if entries and item_type not in self._enabled_tabs]
        if hidden:
            self._enabled_tabs = [item_type for item_type in ITEM_TYPES if item_type in self._enabled_tabs or item_type in hidden]
            self._settings.setValue("enabledTabs", " ".join(self._enabled_tabs))
            self._apply_enabled_tabs()

        # Show the result in its project and tab
        self._data.active_project_id = project.id
        self._clear_selection()
        if first is not None:
            self._tab = first[0]
            self._selected[first[0]] = first[1]
        elif package.kind != EXPORT_PROJECT:
            self._tab = package.item_type
        self._settings.setValue("activeTab", self._tab)
        self._render_all()
        row = self._item_list.currentItem()
        if row is not None:
            self._item_list.scrollToItem(row)
        self._save_now()

        # Result with the kind of entries, a project counts all its entries together
        if package.kind == EXPORT_PROJECT:
            def amount(count: int) -> str:
                return entries_text(count)
        else:
            def amount(count: int) -> str:
                return count_text(package.item_type, count)
        lines: list[str] = []
        if report["imported"] or not (report["replaced"] or report["skipped"]):
            lines.append(tr("{entries} importiert", entries=amount(report["imported"])))
        if report["replaced"]:
            lines.append(tr("{entries} ersetzt", entries=amount(report["replaced"])))
        if report["skipped"]:
            lines.append(tr("{entries} übersprungen, weil schon vorhanden", entries=amount(report["skipped"])))
        message = "\n".join(lines)
        if package.kind == EXPORT_PROJECT:
            message = tr("Projekt \"{name}\"", name=project.display_name()) + "\n\n" + message
        if report["missing"]:
            message += "\n\n" + tr("Diese Dateien fehlen in der Importdatei:") + "\n" + "\n".join(report["missing"][:IMPORT_MISSING_LIMIT])
        show_message(self, message)
        if hidden:
            self._show_status(tr("Reiter eingeblendet: {tabs}", tabs=", ".join(tr(TAB_TITLES[item_type]) for item_type in hidden)))

    def _create_imported_project(self, values: dict) -> Project:
        names = {project.display_name().casefold() for project in self._data.projects}
        base_name = str(values.get("name", "")).strip() or tr("Projekt")
        name = base_name
        counter = 2
        while name.casefold() in names:
            name = f"{base_name} ({counter})"
            counter += 1
        project = Project(id=str(values.get("id") or new_id()), name=name, color=str(values.get("color", "")) or self._data.next_color())
        self._data.projects.insert(len(self._data.open_projects()), project)
        return project

    def _import_group(self, project: Project, item_type: str, values: dict) -> ItemGroup:
        name = str(values.get("name", "")).strip() or tr("Gruppe")
        groups = project.groups_of(item_type)
        for group in groups:
            if group.name.strip().casefold() == name.casefold():
                return group
        group_id = str(values.get("id") or new_id())
        if project.find_group(item_type, group_id) is not None:
            group_id = new_id()
        group = ItemGroup(id=group_id, name=name)
        groups.append(group)
        return group

    def _import_entries(self, project: Project, item_type: str, entries: list, group_values: list, package: ImportPackage, mode: str, report: dict, written: list[Path]) -> list[str]:
        known_ids = {item.id for entry_project in self._data.projects for item in entry_project.items(item_type)}
        group_targets: dict[str, ItemGroup] = {}
        for values in group_values:
            group_targets[str(values.get("id"))] = self._import_group(project, item_type, values)

        imported: list[str] = []
        for source_values in entries:
            values = copy.deepcopy(source_values)
            duplicate = self._find_duplicate(project, item_type, values)
            if duplicate is not None and mode == IMPORT_SKIP:
                report["skipped"] += 1
                continue

            self._import_entry_files(item_type, values, package, report, written)
            target_group = group_targets.get(str(values.get("group_id")))
            values["group_id"] = target_group.id if target_group is not None else None
            items = project.items(item_type)
            if duplicate is not None:
                values["id"] = duplicate.id
                item = ITEM_FACTORIES[item_type](values)
                items[items.index(duplicate)] = item
                report["replaced"] += 1
            else:
                if not values.get("id") or str(values.get("id")) in known_ids:
                    values["id"] = new_id()
                item = ITEM_FACTORIES[item_type](values)
                items.append(item)
                report["imported"] += 1
            known_ids.add(item.id)
            imported.append(item.id)
        return imported

    def _import_entry_files(self, item_type: str, values: dict, package: ImportPackage, report: dict, written: list[Path]) -> None:
        if item_type == ITEM_TODO:
            attachments = []
            for attachment in values.get("attachments", []):
                file_name = str(attachment.get("file", ""))
                name = str(attachment.get("name", file_name))
                content = package.read_file(ATTACHMENT_FOLDER_NAME + "/" + file_name)
                if content is None:
                    report["missing"].append(name)
                    continue
                attachment_id = new_id()
                new_file = attachment_id[:12] + "_" + safe_file_name(name)
                self._storage.attachment_folder.mkdir(parents=True, exist_ok=True)
                target = self._storage.attachment_folder / new_file
                target.write_bytes(content)
                written.append(target)
                attachments.append({"id": attachment_id, "name": name, "file": new_file, "added": attachment.get("added", time.time())})
            values["attachments"] = attachments
        elif item_type == ITEM_NOTE:
            note_html = str(values.get("html", ""))
            for name in sorted(set(NOTE_IMAGE_PATTERN.findall(note_html))):
                content = package.read_file(name)
                if content is None:
                    report["missing"].append(name)
                    continue
                new_name = IMAGE_FOLDER_NAME + "/" + new_id()[:16] + ".png"
                self._storage.image_folder.mkdir(parents=True, exist_ok=True)
                target = self._storage.note_image_path(new_name)
                target.write_bytes(content)
                written.append(target)
                note_html = note_html.replace(name, new_name)
            values["html"] = note_html

    def dragEnterEvent(self, event) -> None:
        if package_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        self.dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        paths = package_paths(event.mimeData())
        if not paths:
            event.ignore()
            return
        event.acceptProposedAction()
        for path in paths:
            QTimer.singleShot(0, lambda selected=path: self.import_file(selected))

    # Undo and redo
    def _view_state(self) -> dict:
        return {"tab": self._tab, "selected": dict(self._selected)}

    def _checkpoint(self) -> None:
        # The state before a change, for Ctrl+Z
        self._undo_stack.append((self._data.to_dict(), self._view_state()))
        if len(self._undo_stack) > UNDO_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._editing_key = None

    def _clear_undo(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._editing_key = None

    def undo(self) -> None:
        if not self._undo_stack:
            return
        values, view = self._undo_stack.pop()
        self._redo_stack.append((self._data.to_dict(), self._view_state()))
        self._restore_state(values, view)

    def redo(self) -> None:
        if not self._redo_stack:
            return
        values, view = self._redo_stack.pop()
        self._undo_stack.append((self._data.to_dict(), self._view_state()))
        self._restore_state(values, view)

    def _restore_state(self, values: dict, view: dict) -> None:
        self._data = AppData.from_dict(values)
        self._tab = view.get("tab", self._tab)
        if self._tab not in self._enabled_tabs:
            self._tab = self._enabled_tabs[0]
        self._selected = dict(view.get("selected", self._selected))
        self._selection = []
        self._quick_add_id = None
        self._editing_key = None
        try:
            self._storage.restore_files(self._data)
        except OSError:
            pass
        self._render_all()
        self._schedule_save()

    def _show_status(self, text: str) -> None:
        self._status_banner.show_message(text)

    # Paste
    def handle_paste(self) -> bool:
        clipboard = QGuiApplication.clipboard()
        mime = clipboard.mimeData()
        if mime is None:
            return False
        focus = QApplication.focusWidget()
        is_text_input = isinstance(focus, (QLineEdit, QTextEdit, QPlainTextEdit))

        if self._tab == ITEM_TODO and self._todo_panel.item is not None:
            files = local_files_from_mime(mime)
            if files:
                self._todo_panel.add_files(files)
                return True
            if mime.hasText() and is_text_input:
                return False
            if mime.hasImage():
                image = image_from_mime(mime)
                if image.isNull() is False:
                    self._todo_panel.add_image(image)
                    return True
            return False

        # Notes take images inline, the editor handles its own paste
        if self._tab == ITEM_NOTE and self._note_panel.item is not None:
            if focus is self._note_panel.text_edit() or (mime.hasText() and is_text_input):
                return False
            if mime.hasImage():
                image = image_from_mime(mime)
                if image.isNull() is False:
                    self._note_panel.insert_image(image)
                    return True
        return False

    # Storage folder
    def _change_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr("Speicherort wählen"), str(self._storage.folder))
        if not folder:
            return

        self._save_now()
        storage = Storage(Path(folder))
        try:
            data = storage.load()
        except LOAD_ERRORS as error:
            show_message(self, tr("Die Daten in\n{folder}\nkonnten nicht geladen werden:\n{error}", folder=folder, error=error), DIALOG_ERROR)
            return

        self._storage = storage
        self._data = data
        self._clear_selection()
        self._clear_undo()
        self._last_backup_day = None
        self._settings.setValue("dataFolder", folder)
        self._render_all()

    def _move_data(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr("Neuen Speicherort wählen"), str(self._storage.folder))
        if not folder:
            return

        source = self._storage.folder.resolve()
        target = Path(folder).resolve()
        if target == source:
            return
        if source in target.parents:
            show_message(self, tr("Der neue Speicherort darf nicht im bisherigen Ordner liegen."), DIALOG_WARNING)
            return
        if (target / DATA_FILE_NAME).exists():
            show_message(self, tr("Im gewählten Ordner liegen bereits Daten. Bitte einen leeren Ordner wählen oder ihn über \"Anderen Speicherort öffnen …\" öffnen."), DIALOG_WARNING)
            return
        if confirm(self, tr("Alle Daten nach\n{folder}\nverschieben?", folder=target), tr("Verschieben"), DIALOG_INFO) is False:
            return
        if self._save_now() is False:
            return
        self._backup(BACKUP_MOVE)

        # Copy, check the copy, then remove the old files
        moved = Storage(target)
        try:
            self._storage.copy_to(target)
            moved_data = moved.load()
            if len(moved_data.projects) != len(self._data.projects):
                raise OSError(tr("Die kopierten Daten sind unvollständig."))
        except LOAD_ERRORS as error:
            moved.remove_entries()
            show_message(self, tr("Die Daten konnten nicht verschoben werden:\n{error}\n\nEs wurde nichts verändert.", error=error), DIALOG_ERROR)
            return

        failed = self._storage.remove_entries()
        self._storage = moved
        self._settings.setValue("dataFolder", str(target))
        self._render_detail()
        if failed:
            show_message(self, tr("Die Daten liegen jetzt in\n{folder}\n\nFolgende alte Dateien konnten nicht gelöscht werden:\n{files}", folder=target, files="\n".join(failed)), DIALOG_WARNING)
        else:
            show_message(self, tr("Die Daten liegen jetzt in\n{folder}", folder=target))

    # Backups
    def _backup(self, reason: str) -> bool:
        if self._save_now() is False:
            return False
        try:
            self._storage.backup_data_file(reason)
        except OSError as error:
            show_message(self, tr("Backup fehlgeschlagen:\n{error}", error=error), DIALOG_WARNING)
            return False
        return True

    def _backup_now(self) -> None:
        if self._backup(BACKUP_MANUAL):
            self._show_status(tr("Backup erstellt"))

    def _set_auto_backup(self, enabled: bool) -> None:
        self._settings.setValue("autoBackup", enabled)
        self._last_backup_day = None

    def _restore_backup(self, path: Path, label: str) -> None:
        if confirm(self, tr("Stand vom {date} wiederherstellen?\n\nDer aktuelle Stand wird vorher gesichert.", date=label), tr("Wiederherstellen")) is False:
            return
        try:
            data = self._storage.load_backup(path)
        except LOAD_ERRORS as error:
            show_message(self, tr("Das Backup konnte nicht geladen werden:\n{error}", error=error), DIALOG_ERROR)
            return
        if self._backup(BACKUP_RESTORE) is False:
            return

        self._checkpoint()
        self._restore_state(data.to_dict(), {"tab": self._tab, "selected": {item_type: None for item_type in ITEM_TYPES}})
        self._save_now()
        self._show_status(tr("Stand vom {date} wiederhergestellt", date=label))

    def _fill_backup_menu(self, menu: QMenu, text_color: QColor) -> None:
        auto_action = menu.addAction(tr("Automatisch sichern"), lambda: self._set_auto_backup(self._auto_backup_enabled() is False))
        auto_action.setCheckable(True)
        auto_action.setChecked(self._auto_backup_enabled())
        menu.addAction(tr("Jetzt sichern"), self._backup_now)

        restore_menu = create_menu(menu, tr("Wiederherstellen"))
        restore_menu.setIcon(create_restore_icon(text_color))
        backups = self._storage.list_backups()
        for path, moment, reason in backups:
            label = backup_label(moment, reason)
            restore_menu.addAction(label, lambda checked=False, selected=path, text=label: self._restore_backup(selected, text))
        if not backups:
            empty_action = restore_menu.addAction(tr("Keine Backups vorhanden"))
            empty_action.setEnabled(False)
        menu.addMenu(restore_menu)

        menu.addSeparator()
        menu.addAction(create_folder_icon(text_color), tr("Ordner öffnen"), self._open_backup_folder)

    def _open_backup_folder(self) -> None:
        self._storage.backup_folder.mkdir(parents=True, exist_ok=True)
        open_with_default_program(self._storage.backup_folder)

    # Saving
    def _schedule_save(self) -> None:
        self._save_timer.start()

    def _auto_backup_enabled(self) -> bool:
        return bool(self._settings.value("autoBackup", True, type=bool))

    def _save_now(self) -> bool:
        self._save_timer.stop()

        # Once a day the last saved state is kept as a backup before it is overwritten
        today = date.today().isoformat()
        if self._auto_backup_enabled() and self._last_backup_day != today:
            try:
                latest = self._storage.latest_backup_time()
                if latest is None or latest.date().isoformat() != today:
                    self._storage.backup_data_file(BACKUP_AUTOMATIC)
                self._last_backup_day = today
            except OSError:
                pass

        try:
            self._storage.save(self._data)
        except OSError as error:
            if self._save_error_shown is False:
                self._save_error_shown = True
                show_message(self, tr("Speichern fehlgeschlagen:\n{error}", error=error), DIALOG_WARNING)
            return False
        self._save_error_shown = False
        return True

    def closeEvent(self, event) -> None:
        self._set_detail_maximized(False)
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("splitter", self._splitter.saveState())
        self._settings.setValue("activeTab", self._tab)
        if self._sidebar_collapsed is False:
            self._settings.setValue("sidebarWidth", self._splitter.sizes()[0])

        if self._save_now() is False:
            if confirm(self, tr("Die letzten Änderungen konnten nicht gespeichert werden. Trotzdem schließen?"), tr("Trotzdem schließen")) is False:
                event.ignore()
                return
        elif self._rebuilding is False:
            try:
                self._storage.collect_garbage(self._data)
            except OSError:
                pass
        event.accept()


# Startup
def choose_folder(start_folder: str) -> Optional[Path]:
    folder = QFileDialog.getExistingDirectory(None, tr("Speicherort wählen"), start_folder)
    return Path(folder) if folder else None


def open_initial_storage(settings: QSettings) -> Optional[tuple[Storage, AppData]]:
    stored_folder = str(settings.value("dataFolder", "") or "")
    folder: Optional[Path] = Path(stored_folder) if stored_folder else None

    if folder is not None and folder.is_dir() is False:
        show_message(None, tr("Der Speicherort\n{folder}\nwurde nicht gefunden. Bitte einen Ordner wählen.", folder=folder), DIALOG_WARNING)
        folder = choose_folder(str(Path.home()))
    elif folder is None:
        show_message(None, tr("Bitte einen Ordner wählen, in dem alle Daten gespeichert werden.\n\nEin Ordner in OneDrive wird automatisch gesichert."))
        folder = choose_folder(str(Path.home() / "Documents"))

    while folder is not None:
        storage = Storage(folder)
        try:
            data = storage.load()
        except LOAD_ERRORS as error:
            show_message(None, tr("Die Daten in\n{folder}\nkonnten nicht geladen werden:\n{error}\n\nBitte einen anderen Ordner wählen.", folder=folder, error=error), DIALOG_ERROR)
            folder = choose_folder(str(folder))
            continue

        settings.setValue("dataFolder", str(folder))
        return storage, data
    return None


def instance_server_name() -> str:
    try:
        user = getpass.getuser()
    except (OSError, KeyError):
        user = "user"
    return INSTANCE_SERVER_PREFIX + safe_file_name(user)


def send_to_running_instance(file_path: str) -> bool:
    # A running ProjectDesk takes over the file and comes to the front
    socket = QLocalSocket()
    socket.connectToServer(instance_server_name())
    if socket.waitForConnected(INSTANCE_TIMEOUT_MS) is False:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.AllowSetForegroundWindow(-1)
        except (AttributeError, OSError):
            pass
    socket.write(file_path.encode("utf-8"))
    socket.flush()
    socket.waitForBytesWritten(INSTANCE_TIMEOUT_MS)
    socket.disconnectFromServer()
    return True


class InstanceServer(QObject):
    """Receives files from ProjectDesk instances started later, for example by a double click on a .pdesk file"""

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        name = instance_server_name()
        QLocalServer.removeServer(name)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        self._server.listen(name)

    def _on_connection(self) -> None:
        socket = self._server.nextPendingConnection()
        if socket is None:
            return
        socket.readyRead.connect(lambda: self._on_message(socket))
        socket.disconnected.connect(socket.deleteLater)

    def _on_message(self, socket: QLocalSocket) -> None:
        file_path = bytes(socket.readAll()).decode("utf-8").strip()
        window = MainWindow.current
        if window is None:
            return
        window.bring_to_front()
        if file_path:
            QTimer.singleShot(0, lambda: MainWindow.current.import_file(Path(file_path)))


def main() -> int:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except (AttributeError, OSError):
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")

    # Only one ProjectDesk per user, a second start hands over its file
    file_arguments = [argument for argument in sys.argv[1:] if argument.lower().endswith(EXPORT_EXTENSION)]
    if send_to_running_instance(file_arguments[0] if file_arguments else ""):
        return 0
    InstanceServer(app)

    icon_path = resource_path(ICON_FILE_NAME)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    apply_color_mode(str(settings.value("colorMode", COLOR_MODE_SYSTEM)))
    apply_zoom_factor(float(settings.value("zoom", 1.0)))
    Language.current = str(settings.value("language", LANGUAGE_GERMAN))

    # Dialogs before the main window already use the colors of the window
    app.setStyleSheet(Theme.from_palette(QApplication.palette()).style_sheet())
    opened = open_initial_storage(settings)
    if opened is None:
        return 0
    storage, data = opened

    window = MainWindow(storage, data, settings)
    app.installEventFilter(InputFilter(window))
    MainWindow.current = window
    window.show()
    if file_arguments:
        QTimer.singleShot(0, lambda: MainWindow.current.import_file(Path(file_arguments[0])))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
