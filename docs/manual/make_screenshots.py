"""Screenshots with neutral example data for the user manual and the README

Runs on Linux without a display, for example in a Claude chat:
    python3 docs/manual/make_screenshots.py
The images are written to docs/manual/build, the README screenshot to docs/screenshot.png.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "2")

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))

from PySide6.QtCore import QPoint, QRect, QRectF, QSettings, Qt, QTimer
from PySide6.QtGui import QColor, QContextMenuEvent, QImage, QPainter, QPen, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QMenu, QWidget

import project_desk as app_module

BUILD = REPOSITORY / "docs" / "manual" / "build"
README_SCREENSHOT = REPOSITORY / "docs" / "screenshot.png"
WINDOW_SIZE = (1200, 720)
README_SIZE = (1200, 680)
MENU_DELAY_MS = 150
SUBMENU_DELAY_MS = 400


def wireframe_image(width: int, height: int) -> QImage:
    # Gray boxes like a page draft
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor("#f4f6f8"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#0f6cbd"))
    painter.drawRect(0, 0, width, height // 9)
    painter.setBrush(QColor("#cfd8e3"))
    painter.drawRoundedRect(QRectF(width * 0.06, height * 0.18, width * 0.88, height * 0.34), 10, 10)
    for column in range(3):
        left = width * (0.06 + column * 0.3)
        painter.drawRoundedRect(QRectF(left, height * 0.58, width * 0.27, height * 0.3), 10, 10)
    painter.end()
    return image


def chart_image(width: int, height: int) -> QImage:
    # Simple bar chart
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor("#ffffff"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#d0d0d0"), 1))
    for step in range(5):
        y = height * 0.1 + step * height * 0.18
        painter.drawLine(int(width * 0.06), int(y), int(width * 0.96), int(y))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#0f6cbd"))
    values = [0.35, 0.42, 0.4, 0.55, 0.62, 0.58, 0.7, 0.78]
    bar_width = width * 0.8 / len(values)
    for index, value in enumerate(values):
        left = width * 0.08 + index * bar_width
        bar_height = height * 0.72 * value / max(values)
        painter.drawRoundedRect(QRectF(left + bar_width * 0.15, height * 0.82 - bar_height, bar_width * 0.7, bar_height), 4, 4)
    painter.end()
    return image


class Shooter:
    """Example data, main window and helpers for the screenshots"""

    def __init__(self, data_folder: Path) -> None:
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setStyle("Fusion")
        app_module.apply_color_mode("light")
        app_module.apply_zoom_factor(1.0)
        app_module.Language.current = app_module.LANGUAGE_ENGLISH
        app_module.UpdateState.checked = True
        app_module.confirm = lambda *args, **kwargs: True
        app_module.show_message = lambda *args, **kwargs: None

        if data_folder.exists():
            shutil.rmtree(data_folder)
        data_folder.mkdir(parents=True)
        self.settings = QSettings(str(data_folder / "settings.ini"), QSettings.Format.IniFormat)
        self.settings.setValue("sidebarCollapsed", False)
        self.storage = app_module.Storage(data_folder)
        self.data = self.storage.load()
        self._create_data(data_folder)

        self.window = app_module.MainWindow(self.storage, self.data, self.settings)
        self.window.resize(*WINDOW_SIZE)
        self.window.show()
        self.items = self.window._item_list
        self.viewport = self.items.viewport()
        self.settle()

    def _create_data(self, data_folder: Path) -> None:
        tr = app_module.tr
        now = time.time()
        general = self.data.general_project()
        for title in ("Submit travel expenses", "Book a first aid course"):
            general.todos.append(app_module.Todo.create(title))

        website = app_module.Project.create("Website Relaunch")
        website.color = "#0f6cbd"
        office = app_module.Project.create("Office Move")
        office.color = "#107c10"
        event = app_module.Project.create("Summer Event")
        event.color = "#ca5010"
        fair = app_module.Project.create("Trade Fair 2025")
        fair.color = "#8764b8"
        fair.archived = True
        self.data.projects.extend([website, office, event, fair])
        self.website = website

        # Todos
        self.design = app_module.ItemGroup.create("Design")
        self.content = app_module.ItemGroup.create("Content")
        website.groups_of(app_module.ITEM_TODO).extend([self.design, self.content])
        website.todos.append(app_module.Todo.create("Align schedule with marketing"))
        self.review = app_module.Todo.create("Review homepage draft", self.design.id)
        self.review.flagged = True
        self.review.description = "Check the navigation and the mobile view first.\nFeedback round: https://wiki.example.com/relaunch/feedback"
        draft = data_folder / "homepage_draft.png"
        wireframe_image(960, 600).save(str(draft))
        self.review.attachments.append(self.storage.import_file(draft))
        self.review.created = now - 3 * 86400
        self.review.modified = now - 3600
        self.review.condition = app_module.CONDITION_UNTIL
        self.review.condition_date = (date.today() + timedelta(days=3)).isoformat()
        for title, done in (("Check the navigation", True), ("Test the mobile view", False), ("Proofread the texts", False)):
            step = app_module.Step.create(title)
            step.done = done
            self.review.steps.append(step)
        about = app_module.Todo.create("Write the about us page", self.content.id)
        about.condition = app_module.CONDITION_FROM
        about.condition_text = "design approval"
        quotes = app_module.Todo.create("Collect customer quotes", self.content.id)
        quotes.condition = app_module.CONDITION_UNTIL
        quotes.condition_date = (date.today() - timedelta(days=1)).isoformat()
        website.todos.extend([
            self.review,
            app_module.Todo.create("Choose image style", self.design.id),
            app_module.Todo.create("Check colors for accessibility", self.design.id),
            about,
            quotes,
        ])
        done = app_module.Todo.create("Hold kickoff meeting")
        done.done = True
        done.done_at = now
        website.todos.append(done)
        office.todos.append(app_module.Todo.create("Order moving boxes"))
        event.todos.extend([app_module.Todo.create("Book the location"), app_module.Todo.create("Send invitations")])

        # Notes
        meetings = app_module.ItemGroup.create("Meetings")
        howtos = app_module.ItemGroup.create("How-tos")
        website.groups_of(app_module.ITEM_NOTE).extend([meetings, howtos])
        self.weekly = app_module.Note.create("Weekly meeting", meetings.id)
        self.weekly.created = now - 86400
        image_name = self.storage.import_note_image(chart_image(560, 300))
        self.weekly.html = (
            "<html><body>"
            "<p>Participants: marketing, design, content</p>"
            "<ul><li>Draft of the homepage is ready</li><li>Texts are due on <span style=\"background-color:#ffe97a;\">Friday</span></li><li>Ask the agency about the launch date</li></ul>"
            "<p>Details: https://wiki.example.com/relaunch/status</p>"
            f"<p style=\"margin-top:6px; margin-bottom:6px;\"><img src=\"{image_name}\" width=\"560\" style=\"max-width:100%;\" /></p>"
            "<p>Visitors per week on the old website.</p>"
            "</body></html>"
        )
        self.weekly.text = "Participants: marketing, design, content"
        ideas = app_module.Note.create("Ideas for later")
        ideas.text = "Newsletter signup on every page"
        howto = app_module.Note.create("How to publish a page", howtos.id)
        howto.html = "<html><body><ol><li>Open the page in the editor</li><li>Change the text</li><li>Click <b>Publish</b></li></ol></body></html>"
        howto.text = "Open the page in the editor\nChange the text\nClick Publish"
        website.notes.extend([ideas, self.weekly, howto])

        # Links
        shared = app_module.ItemGroup.create("Shared")
        tools = app_module.ItemGroup.create("Tools")
        website.groups_of(app_module.ITEM_LINK).extend([shared, tools])
        self.wiki = app_module.Link.create("Project wiki", "https://wiki.example.com/relaunch", shared.id)
        self.wiki.note = "Schedule and decisions"
        website.links.extend([
            app_module.Link.create("Brand guidelines", "https://www.example.com/brand.pdf", None),
            app_module.Link.create("Project folder", r"\\fileserver\projects\Website", shared.id),
            self.wiki,
            app_module.Link.create("Design tool", "https://design.example.com", tools.id),
        ])
        self.data.active_project_id = website.id
        self.data.normalize()
        self.tr = tr

    # Helpers
    def settle(self) -> None:
        for _ in range(6):
            self.app.processEvents()
            QTest.qWait(10)

    def show(self, item_type: str, item=None) -> None:
        window = self.window
        window._set_detail_maximized(False)
        window._on_tab_changed(item_type)
        window._selected[item_type] = item.id if item is not None else None
        window._selection = []
        window._render_all()
        self.settle()

    def save(self, name: str) -> None:
        self.settle()
        self.window.grab().save(str(BUILD / f"{name}.png"))

    def compose(self, widgets: list[tuple[QWidget, QPoint]], name: str, dim: bool = False) -> QRect:
        # Popups are separate windows, they are painted onto the window image, the result is the area they cover
        self.settle()
        image = self.window.grab()
        painter = QPainter(image)
        if dim:
            painter.fillRect(image.rect(), QColor(0, 0, 0, 40))
        covered = QRect()
        for widget, position in widgets:
            painter.drawPixmap(position, widget.grab())
            covered = covered.united(QRect(position, widget.size()))
        painter.end()
        image.save(str(BUILD / f"{name}.png"))
        return covered

    def popup_widgets(self, popup: QMenu, path: list[str], origin: QPoint | None = None) -> list[tuple[QWidget, QPoint]]:
        # Opens the submenus along the path, each one is placed to the right of its parent like on a large screen
        if origin is None:
            origin = self.window.mapFromGlobal(popup.mapToGlobal(QPoint(0, 0)))
        else:
            # The offscreen screen is small and moves menus, so they are placed at the click point inside the window
            origin = QPoint(min(origin.x(), self.window.width() - popup.width() - 4), min(origin.y(), self.window.height() - popup.height() - 4))
        widgets: list[tuple[QWidget, QPoint]] = [(popup, origin)]
        current = popup
        for text in path:
            action = [entry for entry in current.actions() if entry.text() == text][0]
            current.setActiveAction(action)
            QTest.qWait(SUBMENU_DELAY_MS)
            submenu = action.menu()
            parent_position = widgets[-1][1]
            top = parent_position.y() + current.actionGeometry(action).top() - 4
            top = min(top, self.window.height() - submenu.height() - 4)
            widgets.append((submenu, QPoint(parent_position.x() + current.width() + 2, top)))
            current = submenu
        return widgets

    def context_menu(self, widget: QWidget, point: QPoint, name: str, path: list[str] | None = None) -> QRect:
        covered: list[QRect] = []

        def grab() -> None:
            popup = QApplication.activePopupWidget()
            covered.append(self.compose(self.popup_widgets(popup, path or [], widget.mapTo(self.window, point)), name))
            popup.close()
        QTimer.singleShot(MENU_DELAY_MS, grab)
        QApplication.sendEvent(widget, QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point, widget.mapToGlobal(point)))
        QTest.qWait(SUBMENU_DELAY_MS + 400)
        return covered[0]

    def settings_menu(self, name: str, path: list[str]) -> QRect:
        covered: list[QRect] = []

        def grab() -> None:
            # The menu opens directly above the settings button, as on Windows
            popup = QApplication.activePopupWidget()
            button = self.window._settings_button
            origin = button.mapTo(self.window, QPoint(0, -popup.height() - 2))
            covered.append(self.compose(self.popup_widgets(popup, path, origin), name))
            popup.close()
        QTimer.singleShot(MENU_DELAY_MS, grab)
        self.window._settings_button.showMenu()
        QTest.qWait(SUBMENU_DELAY_MS * 2 + 400)
        return covered[0]

    def window_rect(self, widget: QWidget, rect: QRect | None = None) -> QRect:
        area = rect if rect is not None else widget.rect()
        return QRect(widget.mapTo(self.window, area.topLeft()), area.size())

    def item_center(self, item) -> QPoint:
        return self.items.visualItemRect(self.items.find_row(app_module.KIND_ITEM, item.id)).center() + QPoint(80, 0)


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    shooter = Shooter(BUILD / "data")
    window = shooter.window
    tr = shooter.tr
    items = shooter.items
    viewport = shooter.viewport

    # README screenshot
    shooter.show(app_module.ITEM_TODO, shooter.review)
    window.resize(*README_SIZE)
    shooter.settle()
    window.grab().save(str(README_SCREENSHOT))
    window.resize(*WINDOW_SIZE)

    # Condition of a todo with the calendar
    shooter.show(app_module.ITEM_TODO, shooter.review)
    panel = window._todo_panel
    calendar_covered: list[QRect] = []

    def grab_calendar() -> None:
        popup = QApplication.activePopupWidget()
        button = panel._calendar_button
        anchor = button.mapTo(window, QPoint(button.width(), button.height() + 4))
        calendar_covered.append(shooter.compose([(popup, QPoint(anchor.x() - popup.width(), anchor.y()))], "condition"))
        popup.close()

    QTimer.singleShot(MENU_DELAY_MS, grab_calendar)
    panel._show_calendar()
    detail = shooter.window_rect(window._detail_stack)
    condition_crop = QRect(detail.left(), detail.top() + 50, detail.width(), calendar_covered[0].bottom() - detail.top() - 42)

    # Main window with the positions of the callouts
    shooter.show(app_module.ITEM_TODO, shooter.review)
    shooter.save("overview")
    section_rect = items.visualItemRect(items.find_row(app_module.KIND_SECTION, shooter.design.id))
    add_point = window._item_delegate.section_add_rect(section_rect, items.font()).center().toPoint()
    callouts = {
        "1": window._project_list.mapTo(window, QPoint(window._project_list.width() // 2, 330)),
        "2": window._tab_bar.mapTo(window, QPoint(window._tab_bar.width() // 2 + 120, window._tab_bar.height() // 2)),
        "3": window._new_item_edit.mapTo(window, QPoint(window._new_item_edit.width() - 40, window._new_item_edit.height() // 2)),
        "4": viewport.mapTo(window, QPoint(add_point.x() - 48, add_point.y())),
        "5": window._todo_panel.mapTo(window, QPoint(window._todo_panel.width() - 50, 260)),
        "6": window._settings_button.mapTo(window, QPoint(window._settings_button.width() + 24, window._settings_button.height() // 2)),
    }
    positions = {key: [point.x(), point.y()] for key, point in callouts.items()}
    positions["size"] = list(WINDOW_SIZE)
    (BUILD / "callouts.json").write_text(json.dumps(positions), encoding="utf-8")

    # Areas of the screenshots shown as a detail in the manual, in window coordinates
    crops: dict[str, QRect] = {"todo_details": shooter.window_rect(window._detail_stack), "condition": condition_crop}
    design_rect = shooter.window_rect(viewport, items.visualItemRect(items.find_row(app_module.KIND_SECTION, shooter.design.id)))
    quotes_rect = shooter.window_rect(viewport, items.visualItemRect(items.find_row(app_module.KIND_ITEM, shooter.website.todos[-2].id)))
    crops["todo_cards"] = QRect(design_rect.left(), design_rect.top(), design_rect.width(), quotes_rect.bottom() - design_rect.top() + 8)
    steps_rect = shooter.window_rect(window._todo_panel._steps)
    detail = shooter.window_rect(window._detail_stack)
    crops["steps"] = QRect(detail.left(), steps_rect.top() - 40, detail.width(), steps_rect.height() + 56)

    # Project menu with the colors
    project_rect = window._project_list.visualItemRect(window._project_list.find_row(shooter.website.id))
    covered = shooter.context_menu(window._project_list.viewport(), project_rect.center() + QPoint(-20, 0), "project_menu", [tr("Farbe")])
    crops["project_menu"] = QRect(0, 0, covered.right() + 60, covered.bottom() + 40)

    # New todo directly in a group
    shooter.show(app_module.ITEM_TODO)
    window._quick_add_in_group(shooter.content.id)
    QTest.qWait(50)
    editor = next(entry for entry in items.findChildren(QLineEdit, "inlineEdit") if entry.isVisible())
    editor.setText("Proofread all texts")
    shooter.save("quick_add")
    content_rect = shooter.window_rect(viewport, items.visualItemRect(items.find_row(app_module.KIND_SECTION, shooter.content.id)))
    last_rect = shooter.window_rect(viewport, items.visualItemRect(items.item(items.content_count() - 1)))
    column = shooter.window_rect(window._item_column)
    crops["quick_add"] = QRect(column.left(), content_rect.top() - 70, column.width(), last_rect.bottom() - content_rect.top() + 90)
    QTest.keyClick(editor, Qt.Key.Key_Escape)
    shooter.settle()

    # Several selected todos with their menu
    shooter.show(app_module.ITEM_TODO)
    chosen = [shooter.website.todos[2], shooter.website.todos[3], shooter.website.todos[4]]
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, shooter.item_center(chosen[0]))
    for todo in chosen[1:]:
        QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, shooter.item_center(todo))
    shooter.context_menu(viewport, shooter.item_center(chosen[1]), "multi_select")

    # Notes and the right-click menu of the note text
    shooter.show(app_module.ITEM_NOTE, shooter.weekly)
    shooter.save("notes")
    shooter.save("toolbar")
    editor = window._note_panel.findChildren(app_module.DescriptionEditor)[0]
    first_button = shooter.window_rect(editor._bold_button)
    last_button = shooter.window_rect(editor._numbering_button)
    crops["toolbar"] = first_button.united(last_button).adjusted(-8, -6, 8, 6)
    edit = window._note_panel.text_edit()
    first = edit.document().findBlockByNumber(2)
    second = edit.document().findBlockByNumber(3)
    selection = QTextCursor(first)
    selection.setPosition(second.position() + second.length() - 1, QTextCursor.MoveMode.KeepAnchor)
    edit.setTextCursor(selection)
    edit.setFocus()
    # Clicked at the lower edge of the last selected line, so the menu opens below the selection
    line = edit.cursorRect(QTextCursor(second))
    covered = shooter.context_menu(edit.viewport(), QPoint(line.left() + 30, line.bottom() - 1), "note_menu")
    detail = shooter.window_rect(window._detail_stack)
    crops["note_menu"] = QRect(detail.left(), detail.top() + 50, detail.width(), covered.bottom() - detail.top() - 10)

    # Maximized right column
    shooter.show(app_module.ITEM_NOTE, shooter.weekly)
    window._set_detail_maximized(True)
    window.setFocus()
    shooter.save("maximized")
    window._set_detail_maximized(False)

    # Links
    shooter.show(app_module.ITEM_LINK, shooter.wiki)
    shooter.save("links")

    # Import question for entries that already exist
    dialog, buttons = app_module.create_message_dialog(
        window,
        app_module.DIALOG_INFO,
        tr("Inhalt: {summary}", summary=tr("Gruppe \"{name}\": {count}", name="Shared", count=app_module.count_text(app_module.ITEM_LINK, 3)))
        + "\n" + tr("Ziel: Projekt \"{project}\", Reiter {tab}", project="Website Relaunch", tab=tr("Links"))
        + "\n\n" + tr("{count} Einträge gibt es schon.", count=2),
    )
    for position, (label, default) in enumerate(((tr("Überspringen"), False), (tr("Ersetzen"), False), (tr("Abbrechen"), True))):
        app_module.add_dialog_button(dialog, buttons, label, position, default)
    dialog.show()
    QTest.qWait(80)
    dialog.adjustSize()
    covered = shooter.compose([(dialog, QPoint((window.width() - dialog.width()) // 2, (window.height() - dialog.height()) // 3))], "import_dialog", True)
    column = shooter.window_rect(window._item_column)
    crops["import_dialog"] = QRect(column.left(), 0, window.width() - column.left(), covered.bottom() + 120)
    dialog.close()

    # Settings with tabs and backups
    shooter.show(app_module.ITEM_TODO)
    window._save_now()
    shooter.storage.backup_data_file(app_module.BACKUP_IMPORT)
    shooter.storage.backup_data_file(app_module.BACKUP_MANUAL)
    for name, path in (("settings_tabs", [tr("Reiter")]), ("settings_backups", [tr("Backups"), tr("Wiederherstellen")])):
        covered = shooter.settings_menu(name, path)
        crops[name] = QRect(0, covered.top() - 40, covered.right() + 40, window.height() - covered.top() + 40)

    # A newer version in the settings, the version number is an example
    numbers = app_module.version_numbers(app_module.APP_VERSION)
    app_module.UpdateState.version = f"{numbers[0]}.{numbers[1] + 1}.0"
    app_module.UpdateState.url = app_module.RELEASES_URL
    window._update_settings_icons()
    covered = shooter.settings_menu("settings_update", [])
    crops["settings_update"] = QRect(0, covered.bottom() - 128, covered.right() + 40, window.height() - covered.bottom() + 128)
    app_module.UpdateState.version = ""
    window._update_settings_icons()
    (BUILD / "crops.json").write_text(json.dumps({name: [rect.x(), rect.y(), rect.width(), rect.height()] for name, rect in crops.items()}), encoding="utf-8")

    # Blue message bar
    window._show_status(tr("Backup erstellt"))
    QTest.qWait(400)
    image = window.grab()
    scale = image.devicePixelRatio()
    image.copy(QRect(0, int((window.height() - 120) * scale), int(window.width() * scale), int(120 * scale))).save(str(BUILD / "banner.png"))
    QTest.qWait(3000)

    window.close()
    print("Screenshots in", BUILD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
