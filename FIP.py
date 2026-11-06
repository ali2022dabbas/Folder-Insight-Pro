"""
Folder Insight Pro
==================

Explore, filter, preview, measure and export the source files inside a folder.
Great for code reviews, documentation, archiving, or pasting a project into an
AI assistant.

Run:  python FIP.py
Requires: PyQt5  (pip install PyQt5)
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional

from PyQt5.QtCore import (
    QRect, QRegularExpression, QSettings, QSize, QStandardPaths, Qt, QThread,
    QTimer, QUrl, pyqtSignal,
)
from PyQt5.QtGui import (
    QColor, QDesktopServices, QFont, QFontDatabase, QKeySequence, QPainter,
    QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat,
)
from PyQt5.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog,
    QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMenu,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QShortcut,
    QSizePolicy, QSpinBox, QSplitter, QStackedWidget, QStyle, QTableWidget,
    QTableWidgetItem, QTabWidget, QTextBrowser, QTextEdit, QToolButton,
    QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QVBoxLayout,
    QWidget,
)

APP_NAME = "Folder Insight Pro"
APP_VERSION = "2.0"

DEFAULT_EXTENSIONS = ".py, .html, .css, .js, .ts, .jsx, .tsx, .svelte, .vue, .json, .md"
DEFAULT_IGNORES = (".git, node_modules, __pycache__, venv, .venv, env, dist, build, "
                   ".idea, .vscode, .next, .svelte-kit, target, .mypy_cache, .pytest_cache")
DEFAULT_MAX_KB = 1024

EXTENSION_PRESETS = {
    "Web": ".html, .css, .scss, .js, .ts, .jsx, .tsx, .svelte, .vue, .json",
    "Python": ".py, .pyi, .ipynb, .toml, .cfg, .ini, .txt, .md",
    "Original": ".py, .html, .css, .js, .svelte",
    "All text": "*",
}

# Language names used for Markdown code fences.
LANG_BY_EXT = {
    ".py": "python", ".pyi": "python", ".js": "javascript", ".jsx": "jsx",
    ".ts": "typescript", ".tsx": "tsx", ".html": "html", ".htm": "html",
    ".css": "css", ".scss": "scss", ".json": "json", ".md": "markdown",
    ".svelte": "svelte", ".vue": "vue", ".java": "java", ".c": "c",
    ".h": "c", ".cpp": "cpp", ".cs": "csharp", ".go": "go", ".rs": "rust",
    ".rb": "ruby", ".php": "php", ".sh": "bash", ".yml": "yaml",
    ".yaml": "yaml", ".toml": "toml", ".sql": "sql", ".xml": "xml",
    ".kt": "kotlin", ".swift": "swift",
}

OUTPUT_FORMATS = ["Markdown", "Plain text", "XML tags"]


# --------------------------------------------------------------------------- #
#  Themes
# --------------------------------------------------------------------------- #

THEMES = {
    "dark": {
        "bg": "#1f232b", "surface": "#2a2f3a", "surface2": "#343a47",
        "border": "#3d4452", "text": "#e5e9f0", "muted": "#9aa3b2",
        "accent": "#5e81ac", "accent_hover": "#81a1c1", "accent_text": "#ffffff",
        "danger": "#bf616a", "success": "#a3be8c", "warning": "#ebcb8b",
        "selection": "#44506a", "line_hl": "#262b35", "match": "#8a6d1f",
        "kw": "#81a1c1", "string": "#a3be8c", "comment": "#6c7689",
        "number": "#b48ead", "func": "#88c0d0", "tag": "#d08770",
    },
    "light": {
        "bg": "#f3f5f9", "surface": "#ffffff", "surface2": "#e9edf3",
        "border": "#d5dbe5", "text": "#2e3440", "muted": "#68717f",
        "accent": "#3b6db3", "accent_hover": "#5584c7", "accent_text": "#ffffff",
        "danger": "#c0392b", "success": "#2e7d32", "warning": "#b7791f",
        "selection": "#cfe0f7", "line_hl": "#f1f4f9", "match": "#ffe08a",
        "kw": "#1f5fbf", "string": "#2e7d32", "comment": "#8a94a3",
        "number": "#8e44ad", "func": "#00838f", "tag": "#c0592b",
    },
}


def build_stylesheet(t):
    return f"""
    * {{ font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif; font-size: 14px; }}
    QMainWindow, QDialog {{ background: {t['bg']}; }}
    QWidget {{ color: {t['text']}; }}
    QFrame#header {{ background: {t['surface']}; border-bottom: 1px solid {t['border']}; }}
    QFrame#panel {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 10px; }}
    QFrame#card {{ background: {t['surface2']}; border-radius: 10px; }}
    QLabel {{ background: transparent; }}
    QLabel#appTitle {{ font-size: 19px; font-weight: 700; }}
    QLabel#appSubtitle, QLabel#muted {{ color: {t['muted']}; }}
    QLabel#sectionTitle {{ font-size: 15px; font-weight: 600; }}
    QLabel#cardValue {{ font-size: 22px; font-weight: 700; }}
    QLabel#cardLabel {{ color: {t['muted']}; font-size: 12px; }}
    QLabel#filePath {{ font-size: 15px; font-weight: 600; }}
    QLabel#emptyTitle {{ font-size: 22px; font-weight: 700; }}
    QLabel#toast {{ background: {t['text']}; color: {t['bg']}; border-radius: 8px; padding: 9px 16px; font-weight: 600; }}
    QLineEdit, QComboBox, QSpinBox {{
        background: {t['surface2']}; border: 1px solid {t['border']}; border-radius: 7px;
        padding: 6px 9px; selection-background-color: {t['accent']};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {t['accent']}; }}
    QComboBox QAbstractItemView {{ background: {t['surface']}; border: 1px solid {t['border']};
        selection-background-color: {t['selection']}; selection-color: {t['text']}; }}
    QPushButton {{
        background: {t['surface2']}; border: 1px solid {t['border']}; border-radius: 7px;
        padding: 7px 14px;
    }}
    QPushButton:hover {{ border-color: {t['accent']}; }}
    QPushButton:pressed {{ background: {t['selection']}; }}
    QPushButton:disabled {{ color: {t['muted']}; }}
    QPushButton#primary {{ background: {t['accent']}; color: {t['accent_text']}; border: none; font-weight: 600; }}
    QPushButton#primary:hover {{ background: {t['accent_hover']}; }}
    QPushButton#primary:disabled {{ background: {t['border']}; }}
    QPushButton#danger {{ background: {t['danger']}; color: #fff; border: none; }}
    QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 7px; padding: 5px; }}
    QToolButton:hover {{ background: {t['surface2']}; border-color: {t['border']}; }}
    QToolButton:checked {{ background: {t['selection']}; }}
    QToolButton#info {{ border: 1.5px solid {t['accent']}; color: {t['accent']}; border-radius: 13px;
        font-weight: 700; font-family: Georgia, serif; font-style: italic; min-width: 22px; min-height: 22px;
        max-width: 22px; max-height: 22px; padding: 0; }}
    QToolButton#info:hover {{ background: {t['accent']}; color: {t['accent_text']}; }}
    QToolButton#infoSmall {{ color: {t['muted']}; font-weight: 700; font-family: Georgia, serif;
        font-style: italic; border: 1px solid {t['border']}; border-radius: 9px; padding: 0;
        min-width: 16px; min-height: 16px; max-width: 16px; max-height: 16px; font-size: 11px; }}
    QToolButton#infoSmall:hover {{ color: {t['accent_text']}; background: {t['accent']}; border-color: {t['accent']}; }}
    QCheckBox {{ spacing: 7px; }}
    QTreeWidget, QTableWidget, QPlainTextEdit, QTextBrowser, QTextEdit {{
        background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 8px;
        selection-background-color: {t['selection']}; selection-color: {t['text']};
        alternate-background-color: {t['line_hl']};
    }}
    QTreeWidget::item, QTableWidget::item {{ padding: 3px 2px; }}
    QTreeWidget::item:hover {{ background: {t['line_hl']}; }}
    QHeaderView::section {{ background: {t['surface2']}; color: {t['muted']}; border: none;
        border-bottom: 1px solid {t['border']}; padding: 6px; font-weight: 600; }}
    QTabWidget::pane {{ border: none; border-top: 1px solid {t['border']}; top: -1px; }}
    QTabWidget::tab-bar {{ left: 0px; }}
    QToolButton#iconBtn {{ font-size: 18px; min-width: 30px; min-height: 30px; }}
    QTabBar::tab {{ background: transparent; color: {t['muted']}; padding: 8px 16px; border: none;
        border-bottom: 2px solid transparent; font-weight: 600; }}
    QTabBar::tab:selected {{ color: {t['text']}; border-bottom: 2px solid {t['accent']}; }}
    QTabBar::tab:hover {{ color: {t['text']}; }}
    QSplitter::handle {{ background: transparent; width: 8px; }}
    QStatusBar {{ background: {t['surface']}; border-top: 1px solid {t['border']}; color: {t['muted']}; }}
    QProgressBar {{ background: {t['surface2']}; border: none; border-radius: 4px; height: 8px;
        text-align: center; color: transparent; }}
    QProgressBar::chunk {{ background: {t['accent']}; border-radius: 4px; }}
    QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
    QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
    QScrollBar::handle {{ background: {t['border']}; border-radius: 4px; min-height: 24px; min-width: 24px; }}
    QScrollBar::handle:hover {{ background: {t['muted']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    QMenu {{ background: {t['surface']}; border: 1px solid {t['border']}; padding: 4px; }}
    QMenu::item {{ padding: 6px 22px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {t['selection']}; }}
    QToolTip {{ background: {t['surface']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 6px; }}
    """


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def human_size(num):
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} GB"


def human_count(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1000:.1f}k"
    return f"{n:,}"


def estimate_tokens(text_len):
    """Rough LLM token estimate (~4 characters per token)."""
    return max(0, round(text_len / 4))


def parse_list(text):
    return [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]


def normalize_extensions(text):
    exts = parse_list(text)
    if not exts or "*" in exts:
        return None  # None == any text file
    return {e.lower() if e.startswith(".") else "." + e.lower() for e in exts}


@dataclass
class FileEntry:
    rel_path: str
    abs_path: str
    ext: str
    size: int
    mtime: float
    content: str = ""
    lines: int = 0
    error: Optional[str] = None
    _lower: Optional[str] = field(default=None, repr=False)

    @property
    def name(self):
        return os.path.basename(self.rel_path)

    @property
    def lower(self):
        if self._lower is None:
            self._lower = self.content.lower()
        return self._lower


# --------------------------------------------------------------------------- #
#  Background scanner
# --------------------------------------------------------------------------- #

class ScanWorker(QThread):
    progress = pyqtSignal(int, str)
    finished_scan = pyqtSignal(object, object)  # entries, info dict

    def __init__(self, root, extensions, ignores, max_kb, include_hidden):
        super().__init__()
        self.root = root
        self.extensions = extensions
        self.ignores = {i.lower() for i in ignores}
        self.max_bytes = max_kb * 1024
        self.include_hidden = include_hidden
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        entries: List[FileEntry] = []
        info = {"skipped_large": 0, "skipped_binary": 0, "errors": 0,
                "folders": 0, "cancelled": False, "elapsed": 0.0}
        start = time.time()
        last_emit = 0.0
        for dirpath, dirnames, filenames in os.walk(self.root):
            if self._cancel:
                info["cancelled"] = True
                break
            dirnames[:] = sorted(
                d for d in dirnames
                if d.lower() not in self.ignores and (self.include_hidden or not d.startswith("."))
            )
            info["folders"] += 1
            for filename in sorted(filenames):
                if not self.include_hidden and filename.startswith("."):
                    continue
                ext = os.path.splitext(filename)[1].lower()
                if self.extensions is not None and ext not in self.extensions:
                    continue
                path = os.path.join(dirpath, filename)
                try:
                    st = os.stat(path)
                except OSError:
                    info["errors"] += 1
                    continue
                if st.st_size > self.max_bytes:
                    info["skipped_large"] += 1
                    continue
                entry = FileEntry(os.path.relpath(path, self.root), path, ext, st.st_size, st.st_mtime)
                try:
                    with open(path, "rb") as fh:
                        raw = fh.read()
                    if b"\0" in raw[:8192]:
                        info["skipped_binary"] += 1
                        continue
                    try:
                        entry.content = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        entry.content = raw.decode("latin-1")
                    entry.lines = entry.content.count("\n") + (1 if entry.content and not entry.content.endswith("\n") else 0)
                except Exception as exc:  # noqa: BLE001
                    entry.error = str(exc)
                    entry.content = f"<< Error reading file: {exc} >>"
                    info["errors"] += 1
                entries.append(entry)
                now = time.time()
                if now - last_emit > 0.05:
                    last_emit = now
                    self.progress.emit(len(entries), entry.rel_path)
        info["elapsed"] = time.time() - start
        self.finished_scan.emit(entries, info)


# --------------------------------------------------------------------------- #
#  Syntax highlighting + code viewer
# --------------------------------------------------------------------------- #

KEYWORDS = (
    "and as assert async await break case catch class const continue def default del "
    "delete do elif else enum except export extends False finally for from function "
    "global if implements import in instanceof interface is lambda let new None "
    "nonlocal not null of or pass private protected public raise return self static "
    "super switch this throw True try type typeof undefined var void while with yield "
    "true false"
).split()

HASH_COMMENT_EXTS = {".py", ".pyi", ".sh", ".rb", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".r", ".pl"}
HTML_LIKE_EXTS = {".html", ".htm", ".svelte", ".vue", ".xml", ".md"}


def _fmt(color, bold=False, italic=False, bg=None):
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Bold)
    if italic:
        f.setFontItalic(True)
    if bg:
        f.setBackground(QColor(bg))
    return f


class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme):
        super().__init__(document)
        self.ext = ""
        self.set_theme(theme, rehighlight=False)

    def set_theme(self, t, rehighlight=True):
        self.f_kw = _fmt(t["kw"], bold=True)
        self.f_str = _fmt(t["string"])
        self.f_com = _fmt(t["comment"], italic=True)
        self.f_num = _fmt(t["number"])
        self.f_func = _fmt(t["func"])
        self.f_tag = _fmt(t["tag"])
        self._build()
        if rehighlight:
            self.rehighlight()

    def set_extension(self, ext):
        self.ext = ext
        self._build()

    def _build(self):
        self.rules = []
        if self.ext in HTML_LIKE_EXTS:
            self.rules.append((QRegularExpression(r"</?[A-Za-z][\w:-]*|/?>"), self.f_tag))
            self.rules.append((QRegularExpression(r"\b[\w:-]+(?==)"), self.f_func))
        self.rules.append((QRegularExpression(r"\b(" + "|".join(KEYWORDS) + r")\b"), self.f_kw))
        self.rules.append((QRegularExpression(r"\b[A-Za-z_]\w*(?=\s*\()"), self.f_func))
        self.rules.append((QRegularExpression(r"\b(0x[0-9A-Fa-f]+|\d+(\.\d+)?)\b"), self.f_num))

        line_comment = "#.*$" if self.ext in HASH_COMMENT_EXTS else r"//.*$"
        if self.ext in {".css", ".scss", ".json", ".md", ".html", ".htm"}:
            line_comment = r"(?!x)x"  # never matches
        self.str_com = QRegularExpression(
            r'(?<str>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`)|(?<com>' + line_comment + ")"
        )
        self.multi = []
        if self.ext in {".py", ".pyi"}:
            self.multi.append((QRegularExpression('"""'), QRegularExpression('"""'), self.f_str))
            self.multi.append((QRegularExpression("'''"), QRegularExpression("'''"), self.f_str))
        elif self.ext not in HASH_COMMENT_EXTS:
            self.multi.append((QRegularExpression(r"/\*"), QRegularExpression(r"\*/"), self.f_com))
        if self.ext in HTML_LIKE_EXTS:
            self.multi.append((QRegularExpression("<!--"), QRegularExpression("-->"), self.f_com))

    def highlightBlock(self, text):
        for regex, fmt in self.rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
        it = self.str_com.globalMatch(text)
        while it.hasNext():
            m = it.next()
            fmt = self.f_com if m.capturedLength("com") > 0 else self.f_str
            self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

        big = 10 ** 6
        state = self.previousBlockState()
        pos = 0
        while True:
            if state > 0 and state <= len(self.multi):
                _, end_re, fmt = self.multi[state - 1]
                m = end_re.match(text, pos)
                if m.hasMatch():
                    end = m.capturedEnd()
                    self.setFormat(pos, end - pos, fmt)
                    pos = end
                    state = 0
                else:
                    self.setFormat(pos, big, fmt)
                    self.setCurrentBlockState(state)
                    return
            else:
                best = None
                for i, (start_re, _, _) in enumerate(self.multi):
                    m = start_re.match(text, pos)
                    if m.hasMatch() and (best is None or m.capturedStart() < best[1]):
                        best = (i, m.capturedStart(), m.capturedEnd())
                if best is None:
                    self.setCurrentBlockState(0)
                    return
                state = best[0] + 1
                self.setFormat(best[1], best[2] - best[1], self.multi[best[0]][2])
                pos = best[2]


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeView(QPlainTextEdit):
    """Read-only code viewer with line numbers, highlighting and search marks."""

    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(11)
        self.setFont(font)
        self.number_area = LineNumberArea(self)
        self.highlighter = CodeHighlighter(self.document(), theme)
        self.search_term = ""
        self.blockCountChanged.connect(self._update_margin)
        self.updateRequest.connect(self._update_area)
        self.cursorPositionChanged.connect(self._refresh_selections)
        self._update_margin()

    # -- appearance --
    def set_theme(self, theme):
        self.theme = theme
        self.highlighter.set_theme(theme)
        self._refresh_selections()
        self.number_area.update()

    def zoom(self, delta):
        font = self.font()
        font.setPointSize(max(7, min(32, font.pointSize() + delta)))
        self.setFont(font)
        self._update_margin()

    def set_font_size(self, size):
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        self._update_margin()

    # -- content --
    def show_file(self, text, ext, search_term=""):
        self.highlighter.set_extension(ext)
        self.setPlainText(text)
        self.search_term = search_term
        self._refresh_selections()
        if search_term:
            self.goto_match(forward=True, from_start=True)

    def set_search(self, term):
        self.search_term = term
        self._refresh_selections()

    def goto_match(self, forward=True, from_start=False):
        if not self.search_term:
            return False
        doc = self.document()
        cursor = QTextCursor(doc) if from_start else self.textCursor()
        flags = doc.FindFlags() if forward else doc.FindBackward
        found = doc.find(self.search_term, cursor, flags)
        if found.isNull():  # wrap around
            cursor = QTextCursor(doc)
            if not forward:
                cursor.movePosition(QTextCursor.End)
            found = doc.find(self.search_term, cursor, flags)
        if not found.isNull():
            self.setTextCursor(found)
            self.centerCursor()
            return True
        return False

    def count_matches(self):
        if not self.search_term:
            return 0
        return self.toPlainText().lower().count(self.search_term.lower())

    def _refresh_selections(self):
        sels = []
        line = QTextEdit.ExtraSelection()
        line.format.setBackground(QColor(self.theme["line_hl"]))
        line.format.setProperty(QTextFormat.FullWidthSelection, True)
        line.cursor = self.textCursor()
        line.cursor.clearSelection()
        sels.append(line)
        if self.search_term and len(self.search_term) >= 1:
            doc = self.document()
            cursor = QTextCursor(doc)
            limit = 2000
            while limit:
                cursor = doc.find(self.search_term, cursor)
                if cursor.isNull():
                    break
                sel = QTextEdit.ExtraSelection()
                sel.format.setBackground(QColor(self.theme["match"]))
                sel.cursor = cursor
                sels.append(sel)
                limit -= 1
        self.setExtraSelections(sels)

    # -- line numbers --
    def line_number_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 18 + self.fontMetrics().horizontalAdvance("9") * max(3, digits)

    def _update_margin(self, *_):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def _update_area(self, rect, dy):
        if dy:
            self.number_area.scroll(0, dy)
        else:
            self.number_area.update(0, rect.y(), self.number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_margin()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()))

    def paint_line_numbers(self, event):
        painter = QPainter(self.number_area)
        painter.fillRect(event.rect(), QColor(self.theme["surface"]))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()
        h = self.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = self.theme["text"] if number == current else self.theme["muted"]
                painter.setPen(QColor(color))
                painter.drawText(0, top, self.number_area.width() - 10, h, Qt.AlignRight, str(number + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1


# --------------------------------------------------------------------------- #
#  Help content (the ⓘ button)
# --------------------------------------------------------------------------- #

HELP_SECTIONS = [
    ("quickstart", "Quick start", """
<ol>
<li><b>Choose a folder</b> &ndash; click <b>Browse…</b>, paste a path into the folder box,
pick one from the recent-folders list, or simply <b>drag &amp; drop a folder</b> onto the window.</li>
<li><b>Scan</b> &ndash; press <b>Scan</b> (or <kbd>F5</kbd>). Files matching your extension list are
read in the background; you can keep working or press <b>Cancel</b>.</li>
<li><b>Explore</b> &ndash; click any file in the left panel to preview it with syntax highlighting.</li>
<li><b>Pick &amp; share</b> &ndash; tick the files you want, then <b>Copy selected</b> or <b>Export…</b>.</li>
</ol>
<p>Tip: hover over any button or field to see a short tooltip. The small <i>i</i> buttons next to
each panel title jump straight to the matching section of this guide.</p>
"""),
    ("header", "Top bar", """
<table cellpadding="5">
<tr><td><b>Folder box</b></td><td>The folder that will be scanned. Type or paste a path, or open the drop-down to
reuse one of your last 10 folders.</td></tr>
<tr><td><b>Browse…</b></td><td>Opens a folder picker (<kbd>Ctrl+O</kbd>). Picking a folder starts a scan automatically.</td></tr>
<tr><td><b>Scan</b></td><td>Reads the folder again using the current settings (<kbd>F5</kbd>). Use it after files change on disk.</td></tr>
<tr><td><b>⚙ Settings</b></td><td>Choose which file types to include, which folders to skip, size limits and more (<kbd>Ctrl+,</kbd>).</td></tr>
<tr><td><b>☾ / ☀ Theme</b></td><td>Switch between dark and light mode (<kbd>Ctrl+Shift+L</kbd>). Your choice is remembered.</td></tr>
<tr><td><b><i>i</i> Help</b></td><td>Opens this guide (<kbd>F1</kbd>).</td></tr>
</table>
"""),
    ("files", "Files panel (left)", """
<p>Shows every scanned file as a folder tree with its <b>line count</b> and <b>size</b>.
Folders show the totals of everything inside them.</p>
<ul>
<li><b>Click</b> a file to preview it. <b>Double-click</b> opens it in your default app.</li>
<li><b>Right-click</b> for more: open, show in folder, copy path, copy contents, select only this.</li>
<li><b>Checkboxes</b> decide which files are included when you copy or export.
Ticking a folder ticks everything inside it. Use <b>All</b> / <b>None</b> to change everything at once,
or <b>Expand</b> / <b>Collapse</b> to open or close every folder.</li>
<li>The line under the tree tells you how many files are selected, their total size, and an
<b>estimated token count</b> (≈ characters ÷ 4) &ndash; handy when pasting into an AI chat with a context limit.</li>
</ul>
"""),
    ("search", "Searching &amp; filtering", """
<ul>
<li><b>Search box</b> (<kbd>Ctrl+F</kbd>) filters the tree by file name or path as you type.</li>
<li>Tick <b>Search inside files</b> to also match text <i>inside</i> files. Matches are highlighted in the
preview; press <kbd>Enter</kbd> / <kbd>F3</kbd> for the next match and <kbd>Shift+F3</kbd> for the previous one.</li>
<li>The <b>type filter</b> drop-down shows only one file type (e.g. only <code>.py</code>). Each entry shows how many files it has.</li>
<li>Filtering never unticks anything, but <b>copy and export only include ticked files that are currently visible</b>.
That makes &ldquo;search for something, then copy&rdquo; a quick way to grab exactly the files you need.</li>
</ul>
"""),
    ("copy", "Copying, the tree &amp; exporting", """
<table cellpadding="5">
<tr><td><b>Format</b></td><td>How copied/exported text is laid out:
<br>&bull; <b>Markdown</b> &ndash; each file under a heading inside a fenced code block (great for chats, GitHub, docs).
<br>&bull; <b>Plain text</b> &ndash; the classic <i>Filename / File Data</i> layout.
<br>&bull; <b>XML tags</b> &ndash; each file wrapped in <code>&lt;file path="…"&gt;</code> tags; ideal for AI prompts.</td></tr>
<tr><td><b>Copy selected</b></td><td>Copies every ticked, visible file to the clipboard in the chosen format (<kbd>Ctrl+Shift+C</kbd>).</td></tr>
<tr><td><b>Tree</b></td><td>Builds a text diagram of the folder structure (respecting your skip list), copies it,
and shows it in a window (<kbd>Ctrl+T</kbd>).</td></tr>
<tr><td><b>Export…</b></td><td>Saves the selected files to <b>.md</b>, <b>.txt</b> or <b>.json</b> (JSON includes size, lines and dates) (<kbd>Ctrl+E</kbd>).</td></tr>
</table>
<p>Enable <b>Include folder tree</b> in Settings to put the tree at the top of every copy/export.</p>
"""),
    ("preview", "Preview tab", """
<ul>
<li>Shows the selected file with <b>line numbers</b> and <b>syntax highlighting</b>.</li>
<li>The header shows the path, line count, size, estimated tokens and last-modified date.</li>
<li><b>Copy</b> copies just this file; <b>Open</b> opens it in your default app; <b>Folder</b> shows it in your file manager.</li>
<li><b>Wrap</b> toggles word wrap for long lines. <kbd>Ctrl +</kbd> / <kbd>Ctrl -</kbd> zoom the text; <kbd>Ctrl+0</kbd> resets it.</li>
</ul>
"""),
    ("stats", "Statistics tab", """
<ul>
<li>Summary cards: number of files, folders, total lines, total size and estimated tokens.</li>
<li><b>By file type</b>: files, lines and size per extension with a bar showing each type&rsquo;s share of lines.</li>
<li><b>Largest files</b>: the 15 biggest files &ndash; click one to open it in the preview.</li>
<li>The footer reports files skipped because they were too large, binary or unreadable.</li>
</ul>
"""),
    ("settings", "Settings", """
<table cellpadding="5">
<tr><td><b>File extensions</b></td><td>Comma-separated list such as <code>.py, .js, .css</code>. Use <code>*</code> for every text file.
The preset buttons fill in common lists.</td></tr>
<tr><td><b>Skip folders</b></td><td>Folder names that are never scanned (e.g. <code>node_modules, .git, venv</code>). Speeds up big projects a lot.</td></tr>
<tr><td><b>Max file size</b></td><td>Files larger than this are skipped, so huge logs or bundles don&rsquo;t slow things down.</td></tr>
<tr><td><b>Include hidden</b></td><td>Also scan files and folders starting with a dot.</td></tr>
<tr><td><b>Include folder tree</b></td><td>Prepend the tree diagram to copies and exports.</td></tr>
<tr><td><b>Preview font size</b></td><td>Default text size in the preview.</td></tr>
</table>
<p>All settings, the theme, recent folders and the window layout are saved automatically.</p>
"""),
    ("shortcuts", "Keyboard shortcuts", """
<table cellpadding="4">
<tr><td><kbd>Ctrl+O</kbd></td><td>Browse for a folder</td></tr>
<tr><td><kbd>F5</kbd> / <kbd>Ctrl+R</kbd></td><td>Scan / rescan</td></tr>
<tr><td><kbd>Esc</kbd></td><td>Cancel a scan, or clear the search</td></tr>
<tr><td><kbd>Ctrl+F</kbd></td><td>Focus the search box</td></tr>
<tr><td><kbd>F3</kbd> / <kbd>Shift+F3</kbd></td><td>Next / previous match in preview</td></tr>
<tr><td><kbd>Ctrl+Shift+C</kbd></td><td>Copy selected files</td></tr>
<tr><td><kbd>Ctrl+T</kbd></td><td>Copy &amp; show folder tree</td></tr>
<tr><td><kbd>Ctrl+E</kbd></td><td>Export selected files</td></tr>
<tr><td><kbd>Ctrl +</kbd> / <kbd>Ctrl -</kbd> / <kbd>Ctrl+0</kbd></td><td>Zoom preview in / out / reset</td></tr>
<tr><td><kbd>Ctrl+Shift+L</kbd></td><td>Toggle dark / light theme</td></tr>
<tr><td><kbd>Ctrl+,</kbd></td><td>Settings</td></tr>
<tr><td><kbd>F1</kbd></td><td>This help</td></tr>
</table>
"""),
]


class HelpDialog(QDialog):
    def __init__(self, parent, theme, anchor=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} – Help")
        self.resize(780, 640)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel(f"How to use {APP_NAME}")
        title.setObjectName("appTitle")
        layout.addWidget(title)
        sub = QLabel("Everything each part of the app does, and how to use it.")
        sub.setObjectName("muted")
        layout.addWidget(sub)

        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)
        self.browser.anchorClicked.connect(lambda url: self.browser.scrollToAnchor(url.fragment()))
        self.browser.setHtml(self._html(theme))
        layout.addWidget(self.browser, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if anchor:
            QTimer.singleShot(0, lambda: self.browser.scrollToAnchor(anchor))

    @staticmethod
    def _html(t):
        toc = " &middot; ".join(f'<a href="#{key}">{title}</a>' for key, title, _ in HELP_SECTIONS)
        body = "".join(
            f'<a name="{key}"></a><h2>{title}</h2>{html}' for key, title, html in HELP_SECTIONS
        )
        return f"""
        <html><head><style>
        body {{ color: {t['text']}; font-size: 14px; line-height: 150%; }}
        h2 {{ color: {t['accent_hover'] if t is THEMES['dark'] else t['accent']}; font-size: 17px; margin-top: 18px; }}
        a {{ color: {t['accent_hover'] if t is THEMES['dark'] else t['accent']}; text-decoration: none; }}
        code, kbd {{ background: {t['surface2']}; font-family: monospace; }}
        td {{ vertical-align: top; }}
        </style></head><body>
        <p style="color:{t['muted']}">Jump to: {toc}</p>
        {body}
        <p style="color:{t['muted']}; margin-top: 24px">{APP_NAME} v{APP_VERSION}</p>
        </body></html>"""


# --------------------------------------------------------------------------- #
#  Other dialogs
# --------------------------------------------------------------------------- #

class TreeDialog(QDialog):
    def __init__(self, parent, tree_text):
        super().__init__(parent)
        self.setWindowTitle("Folder tree")
        self.resize(560, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        note = QLabel("The tree below has been copied to your clipboard.")
        note.setObjectName("muted")
        layout.addWidget(note)
        view = QPlainTextEdit(tree_text)
        view.setReadOnly(True)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(11)
        view.setFont(font)
        view.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(view, 1)
        row = QHBoxLayout()
        row.addStretch()
        copy_btn = QPushButton("Copy again")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(tree_text))
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.accept)
        row.addWidget(copy_btn)
        row.addWidget(close_btn)
        layout.addLayout(row)


class SettingsDialog(QDialog):
    def __init__(self, parent, values):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel("Scan & output settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.ext_edit = QLineEdit(values["extensions"])
        self.ext_edit.setToolTip("Comma-separated list, e.g. .py, .js, .css — use * to include every text file.")
        presets = QHBoxLayout()
        presets.setSpacing(6)
        for name, exts in EXTENSION_PRESETS.items():
            b = QPushButton(name)
            b.setToolTip(exts)
            b.clicked.connect(lambda _=False, e=exts: self.ext_edit.setText(e))
            presets.addWidget(b)
        presets.addStretch()
        ext_box = QVBoxLayout()
        ext_box.addWidget(self.ext_edit)
        ext_box.addLayout(presets)
        form.addRow("File extensions:", ext_box)

        self.ignore_edit = QLineEdit(values["ignores"])
        self.ignore_edit.setToolTip("Folder names that are never scanned.")
        form.addRow("Skip folders:", self.ignore_edit)

        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 1024 * 100)
        self.max_spin.setSuffix(" KB")
        self.max_spin.setValue(values["max_kb"])
        self.max_spin.setToolTip("Files bigger than this are skipped.")
        form.addRow("Max file size:", self.max_spin)

        self.hidden_check = QCheckBox("Include hidden files and folders (starting with “.”)")
        self.hidden_check.setChecked(values["include_hidden"])
        form.addRow("", self.hidden_check)

        self.tree_check = QCheckBox("Include folder tree at the top of copies and exports")
        self.tree_check.setChecked(values["include_tree"])
        form.addRow("", self.tree_check)

        self.font_spin = QSpinBox()
        self.font_spin.setRange(7, 32)
        self.font_spin.setSuffix(" pt")
        self.font_spin.setValue(values["font_size"])
        form.addRow("Preview font size:", self.font_spin)

        layout.addLayout(form)
        layout.addSpacing(8)

        row = QHBoxLayout()
        reset = QPushButton("Restore defaults")
        reset.clicked.connect(self._reset)
        row.addWidget(reset)
        row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Save")
        ok.setObjectName("primary")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(ok)
        layout.addLayout(row)

    def _reset(self):
        self.ext_edit.setText(DEFAULT_EXTENSIONS)
        self.ignore_edit.setText(DEFAULT_IGNORES)
        self.max_spin.setValue(DEFAULT_MAX_KB)
        self.hidden_check.setChecked(False)
        self.tree_check.setChecked(False)
        self.font_spin.setValue(11)

    def values(self):
        return {
            "extensions": self.ext_edit.text().strip() or DEFAULT_EXTENSIONS,
            "ignores": self.ignore_edit.text().strip(),
            "max_kb": self.max_spin.value(),
            "include_hidden": self.hidden_check.isChecked(),
            "include_tree": self.tree_check.isChecked(),
            "font_size": self.font_spin.value(),
        }


# --------------------------------------------------------------------------- #
#  Small UI building blocks
# --------------------------------------------------------------------------- #

class StatCard(QFrame):
    def __init__(self, label):
        super().__init__()
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)
        self.value = QLabel("–")
        self.value.setObjectName("cardValue")
        cap = QLabel(label)
        cap.setObjectName("cardLabel")
        lay.addWidget(self.value)
        lay.addWidget(cap)

    def set(self, text):
        self.value.setText(text)


class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.hide()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

    def show_message(self, text, ms=2200):
        self.setText(text)
        self.adjustSize()
        p = self.parentWidget()
        self.move((p.width() - self.width()) // 2, p.height() - self.height() - 28)
        self.raise_()
        self.show()
        self.timer.start(ms)


class NumericItem(QTreeWidgetItem):
    """Tree item that sorts folders first and numeric columns numerically."""

    def __lt__(self, other):
        col = self.treeWidget().sortColumn() if self.treeWidget() else 0
        a_dir = self.data(0, Qt.UserRole) is None
        b_dir = other.data(0, Qt.UserRole) is None
        if a_dir != b_dir:
            order = self.treeWidget().header().sortIndicatorOrder()
            return a_dir if order == Qt.AscendingOrder else b_dir
        if col in (1, 2):
            return (self.data(col, Qt.UserRole + 1) or 0) < (other.data(col, Qt.UserRole + 1) or 0)
        return self.text(0).lower() < other.text(0).lower()


# --------------------------------------------------------------------------- #
#  Main window
# --------------------------------------------------------------------------- #

class FolderInsightPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("FolderInsightPro", "FolderInsightPro")
        self.theme_name = self.settings.value("theme", "dark")
        if self.theme_name not in THEMES:
            self.theme_name = "dark"
        self.opts = {
            "extensions": self.settings.value("extensions", DEFAULT_EXTENSIONS),
            "ignores": self.settings.value("ignores", DEFAULT_IGNORES),
            "max_kb": int(self.settings.value("max_kb", DEFAULT_MAX_KB)),
            "include_hidden": self.settings.value("include_hidden", False, type=bool),
            "include_tree": self.settings.value("include_tree", False, type=bool),
            "font_size": int(self.settings.value("font_size", 11)),
        }
        self.entries: List[FileEntry] = []
        self.scan_info = {}
        self.scanned_root = ""
        self.worker: Optional[ScanWorker] = None
        self.current_entry: Optional[FileEntry] = None
        self.file_items = []

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(980, 600)
        self.setAcceptDrops(True)

        self._build_ui()
        self._build_shortcuts()
        self.apply_theme()

        geo = self.settings.value("geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        else:
            self.resize(1320, 820)
        split = self.settings.value("splitter")
        if split is not None:
            self.splitter.restoreState(split)

        self.selection_timer = QTimer(self)
        self.selection_timer.setSingleShot(True)
        self.selection_timer.setInterval(60)
        self.selection_timer.timeout.connect(self.update_selection_info)
        self.update_actions()

    # ------------------------------------------------------------------ UI --
    def info_button(self, anchor, tip, small=True):
        b = QToolButton()
        b.setText("i")
        b.setObjectName("infoSmall" if small else "info")
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda: self.show_help(anchor))
        return b

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header ---------------------------------------------------------
        header = QFrame()
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(18, 12, 18, 12)
        h.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel(APP_NAME)
        title.setObjectName("appTitle")
        subtitle = QLabel("Explore · filter · preview · export")
        subtitle.setObjectName("appSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h.addLayout(title_box)
        h.addSpacing(18)

        self.folder_combo = QComboBox()
        self.folder_combo.setEditable(True)
        self.folder_combo.setInsertPolicy(QComboBox.NoInsert)
        self.folder_combo.lineEdit().setPlaceholderText("Choose, paste or drop a folder…")
        self.folder_combo.setToolTip("Folder to scan. Open the drop-down for recent folders, "
                                     "or drag a folder onto the window.")
        self.folder_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.folder_combo.setMinimumWidth(320)
        for f in self._recent_folders():
            self.folder_combo.addItem(f)
        self.folder_combo.setCurrentIndex(-1)
        self.folder_combo.lineEdit().returnPressed.connect(self.start_scan)
        self.folder_combo.activated.connect(lambda _: self.start_scan())
        h.addWidget(self.folder_combo, 1)

        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.setToolTip("Pick a folder (Ctrl+O)")
        self.browse_btn.clicked.connect(self.browse_folder)
        h.addWidget(self.browse_btn)

        self.scan_btn = QPushButton("Scan")
        self.scan_btn.setObjectName("primary")
        self.scan_btn.setToolTip("Scan the folder with the current settings (F5)")
        self.scan_btn.clicked.connect(self.start_scan)
        h.addWidget(self.scan_btn)

        h.addSpacing(8)
        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙")
        self.settings_btn.setObjectName("iconBtn")
        self.settings_btn.setToolTip("Settings – file types, skipped folders, size limit… (Ctrl+,)")
        self.settings_btn.clicked.connect(self.open_settings)
        h.addWidget(self.settings_btn)

        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("iconBtn")
        self.theme_btn.setToolTip("Toggle dark / light theme (Ctrl+Shift+L)")
        self.theme_btn.clicked.connect(self.toggle_theme)
        h.addWidget(self.theme_btn)

        self.help_btn = self.info_button(None, "Help – what everything does and how to use it (F1)", small=False)
        h.addWidget(self.help_btn)
        root.addWidget(header)

        # Body -------------------------------------------------------------
        body = QWidget()
        b = QHBoxLayout(body)
        b.setContentsMargins(14, 14, 14, 10)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        b.addWidget(self.splitter)
        root.addWidget(body, 1)

        self.splitter.addWidget(self._build_files_panel())
        self.splitter.addWidget(self._build_right_panel())
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([420, 880])

        # Status bar -------------------------------------------------------
        sb = self.statusBar()
        sb.setSizeGripEnabled(False)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(160)
        self.progress.hide()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.clicked.connect(self.cancel_scan)
        self.cancel_btn.hide()
        sb.addPermanentWidget(self.progress)
        sb.addPermanentWidget(self.cancel_btn)
        sb.showMessage("Ready – choose a folder to begin. Press F1 for help.")

        self.toast = Toast(central)

    def _panel_header(self, text, anchor, tip):
        row = QHBoxLayout()
        row.setSpacing(6)
        lbl = QLabel(text)
        lbl.setObjectName("sectionTitle")
        row.addWidget(lbl)
        row.addWidget(self.info_button(anchor, tip))
        row.addStretch()
        return row, lbl

    def _build_files_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(330)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        head, self.files_title = self._panel_header("Files", "files", "How the Files panel works")
        self.expand_btn = QToolButton()
        self.expand_btn.setText("Expand")
        self.expand_btn.setToolTip("Expand all folders")
        self.expand_btn.clicked.connect(lambda: self.tree.expandAll())
        self.collapse_btn = QToolButton()
        self.collapse_btn.setText("Collapse")
        self.collapse_btn.setToolTip("Collapse all folders")
        self.collapse_btn.clicked.connect(lambda: self.tree.collapseAll())
        head.addWidget(self.expand_btn)
        head.addWidget(self.collapse_btn)
        lay.addLayout(head)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search files…  (Ctrl+F)")
        self.search.setClearButtonEnabled(True)
        self.search.setToolTip("Filter by file name or path. Tick “Search inside files” to search file contents too.")
        self.search.textChanged.connect(self._schedule_filter)
        self.search.returnPressed.connect(lambda: self.preview.goto_match(True))
        search_row.addWidget(self.search, 1)
        search_row.addWidget(self.info_button("search", "How searching and filtering work"))
        lay.addLayout(search_row)

        opts = QHBoxLayout()
        self.content_check = QCheckBox("Search inside files")
        self.content_check.setToolTip("Also match text inside files; matches are highlighted in the preview.")
        self.content_check.toggled.connect(self._schedule_filter)
        opts.addWidget(self.content_check)
        opts.addStretch()
        self.type_combo = QComboBox()
        self.type_combo.setToolTip("Show only one file type")
        self.type_combo.addItem("All types", None)
        self.type_combo.currentIndexChanged.connect(self._schedule_filter)
        opts.addWidget(self.type_combo)
        lay.addLayout(opts)

        self.filter_timer = QTimer(self)
        self.filter_timer.setSingleShot(True)
        self.filter_timer.setInterval(120)
        self.filter_timer.timeout.connect(self.apply_filter)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Lines", "Size"])
        self.tree.setAlternatingRowColors(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.tree_menu)
        self.tree.currentItemChanged.connect(self.on_tree_current)
        self.tree.itemDoubleClicked.connect(self.on_tree_double)
        self.tree.itemChanged.connect(lambda *_: self.selection_timer.start())
        hdr = self.tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.AscendingOrder)
        lay.addWidget(self.tree, 1)

        sel_row = QHBoxLayout()
        self.selection_label = QLabel("No files yet")
        self.selection_label.setObjectName("muted")
        self.selection_label.setWordWrap(True)
        sel_row.addWidget(self.selection_label, 1)
        self.all_btn = QToolButton()
        self.all_btn.setText("All")
        self.all_btn.setToolTip("Tick every file")
        self.all_btn.clicked.connect(lambda: self.set_all_checked(True))
        self.none_btn = QToolButton()
        self.none_btn.setText("None")
        self.none_btn.setToolTip("Untick every file")
        self.none_btn.clicked.connect(lambda: self.set_all_checked(False))
        sel_row.addWidget(self.all_btn)
        sel_row.addWidget(self.none_btn)
        lay.addLayout(sel_row)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: rgba(128,128,128,60);")
        lay.addWidget(line)

        fmt_row = QHBoxLayout()
        fmt_lbl = QLabel("Format")
        fmt_lbl.setObjectName("muted")
        fmt_row.addWidget(fmt_lbl)
        self.format_combo = QComboBox()
        self.format_combo.addItems(OUTPUT_FORMATS)
        self.format_combo.setCurrentText(self.settings.value("format", "Markdown"))
        self.format_combo.setToolTip("Layout used when copying or exporting:\n"
                                     "Markdown – headings + code blocks\n"
                                     "Plain text – Filename / File Data\n"
                                     "XML tags – <file path=…> blocks, great for AI prompts")
        self.format_combo.currentTextChanged.connect(lambda v: self.settings.setValue("format", v))
        fmt_row.addWidget(self.format_combo, 1)
        fmt_row.addWidget(self.info_button("copy", "About copying, the tree and exporting"))
        lay.addLayout(fmt_row)

        actions = QGridLayout()
        actions.setSpacing(6)
        self.copy_btn = QPushButton("Copy selected")
        self.copy_btn.setObjectName("primary")
        self.copy_btn.setToolTip("Copy all ticked, visible files to the clipboard (Ctrl+Shift+C)")
        self.copy_btn.clicked.connect(self.copy_selected)
        self.tree_btn = QPushButton("Tree")
        self.tree_btn.setToolTip("Copy and show a text diagram of the folder structure (Ctrl+T)")
        self.tree_btn.clicked.connect(self.show_tree)
        self.export_btn = QPushButton("Export…")
        self.export_btn.setToolTip("Save ticked files as Markdown, text or JSON (Ctrl+E)")
        self.export_btn.clicked.connect(self.export_files)
        actions.addWidget(self.copy_btn, 0, 0, 1, 2)
        actions.addWidget(self.tree_btn, 1, 0)
        actions.addWidget(self.export_btn, 1, 1)
        lay.addLayout(actions)
        return panel

    def _build_right_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 6, 12, 12)

        self.tabs = QTabWidget()
        corner = QWidget()
        cl = QHBoxLayout(corner)
        cl.setContentsMargins(0, 4, 4, 4)
        self.tab_info = self.info_button("preview", "About the Preview and Statistics tabs")
        cl.addWidget(self.tab_info)
        self.tabs.setCornerWidget(corner, Qt.TopRightCorner)
        self.tabs.currentChanged.connect(self._update_tab_info)
        lay.addWidget(self.tabs)

        # --- Preview tab ---
        self.preview_stack = QStackedWidget()
        self.preview_stack.addWidget(self._build_empty_state())

        prev = QWidget()
        pl = QVBoxLayout(prev)
        pl.setContentsMargins(0, 10, 0, 0)
        pl.setSpacing(8)
        top = QHBoxLayout()
        meta_box = QVBoxLayout()
        meta_box.setSpacing(2)
        self.file_path_label = QLabel()
        self.file_path_label.setObjectName("filePath")
        self.file_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.file_meta_label = QLabel()
        self.file_meta_label.setObjectName("muted")
        meta_box.addWidget(self.file_path_label)
        meta_box.addWidget(self.file_meta_label)
        top.addLayout(meta_box, 1)

        self.match_label = QLabel()
        self.match_label.setObjectName("muted")
        top.addWidget(self.match_label)
        self.prev_match_btn = QToolButton()
        self.prev_match_btn.setText("▲")
        self.prev_match_btn.setToolTip("Previous match (Shift+F3)")
        self.prev_match_btn.clicked.connect(lambda: self.preview.goto_match(False))
        self.next_match_btn = QToolButton()
        self.next_match_btn.setText("▼")
        self.next_match_btn.setToolTip("Next match (F3)")
        self.next_match_btn.clicked.connect(lambda: self.preview.goto_match(True))
        top.addWidget(self.prev_match_btn)
        top.addWidget(self.next_match_btn)

        self.wrap_btn = QToolButton()
        self.wrap_btn.setText("Wrap")
        self.wrap_btn.setCheckable(True)
        self.wrap_btn.setToolTip("Toggle word wrap")
        self.wrap_btn.toggled.connect(lambda on: self.preview.setLineWrapMode(
            QPlainTextEdit.WidgetWidth if on else QPlainTextEdit.NoWrap))
        self.copy_file_btn = QPushButton("Copy")
        self.copy_file_btn.setToolTip("Copy this file's contents")
        self.copy_file_btn.clicked.connect(self.copy_current_file)
        self.open_file_btn = QPushButton("Open")
        self.open_file_btn.setToolTip("Open in your default application")
        self.open_file_btn.clicked.connect(lambda: self.open_external(self.current_entry))
        self.reveal_btn = QPushButton("Folder")
        self.reveal_btn.setToolTip("Show the containing folder in your file manager")
        self.reveal_btn.clicked.connect(lambda: self.reveal(self.current_entry))
        for w in (self.wrap_btn, self.copy_file_btn, self.open_file_btn, self.reveal_btn):
            top.addWidget(w)
        pl.addLayout(top)

        self.preview = CodeView(THEMES[self.theme_name])
        self.preview.set_font_size(self.opts["font_size"])
        pl.addWidget(self.preview, 1)
        self.preview_stack.addWidget(prev)
        self.tabs.addTab(self.preview_stack, "Preview")

        # --- Stats tab ---
        self.tabs.addTab(self._build_stats(), "Statistics")
        return panel

    def _build_empty_state(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addStretch(2)
        icon = QLabel("📂")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 56px;")
        lay.addWidget(icon)
        title = QLabel("Drop a folder here to get started")
        title.setObjectName("emptyTitle")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        self.empty_text = QLabel(
            "…or click <b>Browse…</b> in the top bar.<br><br>"
            "1&nbsp;&nbsp;Choose a folder&nbsp;&nbsp;·&nbsp;&nbsp;2&nbsp;&nbsp;Scan&nbsp;&nbsp;·&nbsp;&nbsp;"
            "3&nbsp;&nbsp;Click a file to preview&nbsp;&nbsp;·&nbsp;&nbsp;4&nbsp;&nbsp;Tick files and copy or export")
        self.empty_text.setObjectName("muted")
        self.empty_text.setAlignment(Qt.AlignCenter)
        self.empty_text.setWordWrap(True)
        lay.addWidget(self.empty_text)
        lay.addSpacing(14)
        row = QHBoxLayout()
        row.addStretch()
        b1 = QPushButton("Browse for a folder")
        b1.setObjectName("primary")
        b1.clicked.connect(self.browse_folder)
        b2 = QPushButton("How does it work?")
        b2.clicked.connect(lambda: self.show_help("quickstart"))
        row.addWidget(b1)
        row.addWidget(b2)
        row.addStretch()
        lay.addLayout(row)
        lay.addStretch(3)
        return w

    def _build_stats(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(12)
        cards = QHBoxLayout()
        self.card_files = StatCard("Files")
        self.card_folders = StatCard("Folders scanned")
        self.card_lines = StatCard("Lines")
        self.card_size = StatCard("Total size")
        self.card_tokens = StatCard("Est. tokens")
        for c in (self.card_files, self.card_folders, self.card_lines, self.card_size, self.card_tokens):
            cards.addWidget(c)
        lay.addLayout(cards)

        tables = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(self._section_label("By file type"))
        self.type_table = QTableWidget(0, 6)
        self.type_table.setHorizontalHeaderLabels(["Type", "Files", "Lines", "Size", "Share of lines", ""])
        self._style_table(self.type_table)
        self.type_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        left.addWidget(self.type_table)
        right = QVBoxLayout()
        right.addWidget(self._section_label("Largest files  (click to preview)"))
        self.big_table = QTableWidget(0, 3)
        self.big_table.setHorizontalHeaderLabels(["File", "Lines", "Size"])
        self._style_table(self.big_table)
        self.big_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.big_table.cellClicked.connect(self._open_big_file)
        right.addWidget(self.big_table)
        tables.addLayout(left, 1)
        tables.addLayout(right, 1)
        lay.addLayout(tables, 1)

        self.stats_footer = QLabel()
        self.stats_footer.setObjectName("muted")
        lay.addWidget(self.stats_footer)
        return w

    @staticmethod
    def _section_label(text):
        l = QLabel(text)
        l.setObjectName("sectionTitle")
        return l

    @staticmethod
    def _style_table(t):
        t.verticalHeader().hide()
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setShowGrid(False)
        t.setFocusPolicy(Qt.NoFocus)
        t.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def _update_tab_info(self, index):
        anchor = "stats" if index == 1 else "preview"
        try:
            self.tab_info.clicked.disconnect()
        except TypeError:
            pass
        self.tab_info.clicked.connect(lambda: self.show_help(anchor))

    def _build_shortcuts(self):
        pairs = [
            ("Ctrl+O", self.browse_folder), ("F5", self.start_scan), ("Ctrl+R", self.start_scan),
            ("Ctrl+F", self.focus_search), ("F3", lambda: self.preview.goto_match(True)),
            ("Shift+F3", lambda: self.preview.goto_match(False)),
            ("Ctrl+Shift+C", self.copy_selected), ("Ctrl+T", self.show_tree),
            ("Ctrl+E", self.export_files), ("Ctrl+Shift+L", self.toggle_theme),
            ("Ctrl+,", self.open_settings), ("F1", lambda: self.show_help(None)),
            ("Ctrl+=", lambda: self.preview.zoom(1)), ("Ctrl++", lambda: self.preview.zoom(1)),
            ("Ctrl+-", lambda: self.preview.zoom(-1)),
            ("Ctrl+0", lambda: self.preview.set_font_size(self.opts["font_size"])),
            ("Esc", self.on_escape),
        ]
        for seq, fn in pairs:
            QShortcut(QKeySequence(seq), self, activated=fn)

    # --------------------------------------------------------------- theme --
    @property
    def theme(self):
        return THEMES[self.theme_name]

    def apply_theme(self):
        QApplication.instance().setStyleSheet(build_stylesheet(self.theme))
        self.theme_btn.setText("☀" if self.theme_name == "dark" else "☾")
        self.preview.set_theme(self.theme)
        if self.entries:
            self.populate_stats()

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.settings.setValue("theme", self.theme_name)
        self.apply_theme()

    # ------------------------------------------------------------- folders --
    def _recent_folders(self):
        value = self.settings.value("recent", [])
        if isinstance(value, str):
            value = [value]
        return [v for v in (value or []) if v]

    def _remember_folder(self, path):
        recent = [p for p in self._recent_folders() if os.path.normcase(p) != os.path.normcase(path)]
        recent.insert(0, path)
        recent = recent[:10]
        self.settings.setValue("recent", recent)
        self.folder_combo.blockSignals(True)
        self.folder_combo.clear()
        self.folder_combo.addItems(recent)
        self.folder_combo.setCurrentIndex(0)
        self.folder_combo.blockSignals(False)

    def browse_folder(self):
        start = self.folder_combo.currentText() or QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        path = QFileDialog.getExistingDirectory(self, "Select folder", start)
        if path:
            self.folder_combo.setEditText(path)
            self.start_scan()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                path = os.path.dirname(path)
            if os.path.isdir(path):
                self.folder_combo.setEditText(path)
                self.start_scan()
                return

    # ---------------------------------------------------------------- scan --
    def start_scan(self):
        if self.worker and self.worker.isRunning():
            return
        path = os.path.expanduser(self.folder_combo.currentText().strip().strip('"'))
        if not path:
            self.toast.show_message("Choose a folder first")
            self.browse_folder()
            return
        if not os.path.isdir(path):
            QMessageBox.warning(self, "Folder not found", f"This folder does not exist:\n\n{path}")
            return
        path = os.path.abspath(path)
        self._remember_folder(path)
        self.worker = ScanWorker(path, normalize_extensions(self.opts["extensions"]),
                                 parse_list(self.opts["ignores"]), self.opts["max_kb"],
                                 self.opts["include_hidden"])
        self.worker.progress.connect(self.on_scan_progress)
        self.worker.finished_scan.connect(self.on_scan_done)
        self.progress.show()
        self.cancel_btn.show()
        self.scan_btn.setEnabled(False)
        self.statusBar().showMessage(f"Scanning {path} …")
        self.worker.start()

    def cancel_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()

    def on_scan_progress(self, count, current):
        self.statusBar().showMessage(f"Scanning… {count} files  ·  {current}")

    def on_scan_done(self, entries, info):
        root = self.worker.root
        self.worker = None
        self.progress.hide()
        self.cancel_btn.hide()
        self.scan_btn.setEnabled(True)
        self.entries = entries
        self.scan_info = info
        self.scanned_root = root

        self.populate_tree()
        self.populate_type_filter()
        self.populate_stats()
        self.apply_filter()
        self.update_actions()

        total_lines = sum(e.lines for e in entries)
        msg = (f"{'Cancelled – ' if info['cancelled'] else ''}{len(entries)} files · "
               f"{human_count(total_lines)} lines · {info['elapsed']:.2f}s")
        skipped = info["skipped_large"] + info["skipped_binary"]
        if skipped:
            msg += f" · {skipped} skipped"
        self.statusBar().showMessage(msg)
        self.setWindowTitle(f"{os.path.basename(root) or root} – {APP_NAME}")

        if not entries:
            self.preview_stack.setCurrentIndex(0)
            QMessageBox.information(
                self, "No files found",
                "No files matched your settings in this folder.\n\n"
                f"Extensions: {self.opts['extensions']}\n\n"
                "Open Settings (⚙) to change the file types or skipped folders.")
        else:
            self.toast.show_message(f"Found {len(entries)} files")

    # ---------------------------------------------------------------- tree --
    def populate_tree(self):
        self.tree.blockSignals(True)
        self.tree.setSortingEnabled(False)
        self.tree.clear()
        self.file_items = []
        style = self.style()
        dir_icon = style.standardIcon(QStyle.SP_DirIcon)
        file_icon = style.standardIcon(QStyle.SP_FileIcon)
        folders = {}

        def folder_item(rel):
            if rel in folders:
                return folders[rel]
            parent_rel = os.path.dirname(rel)
            parent = folder_item(parent_rel) if parent_rel else self.tree.invisibleRootItem()
            item = NumericItem(parent, [os.path.basename(rel)])
            item.setIcon(0, dir_icon)
            item.setData(0, Qt.UserRole, None)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            item.setCheckState(0, Qt.Checked)
            item.setData(1, Qt.UserRole + 1, 0)
            item.setData(2, Qt.UserRole + 1, 0)
            folders[rel] = item
            return item

        for idx, e in enumerate(self.entries):
            parent_rel = os.path.dirname(e.rel_path)
            parent = folder_item(parent_rel) if parent_rel else self.tree.invisibleRootItem()
            item = NumericItem(parent, [e.name, f"{e.lines:,}", human_size(e.size)])
            item.setIcon(0, file_icon)
            item.setData(0, Qt.UserRole, idx)
            item.setData(1, Qt.UserRole + 1, e.lines)
            item.setData(2, Qt.UserRole + 1, e.size)
            item.setToolTip(0, e.rel_path + (f"\n⚠ {e.error}" if e.error else ""))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
            item.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
            if e.error:
                item.setForeground(0, QColor(self.theme["danger"]))
            self.file_items.append(item)
            # roll totals up to every parent folder
            p = item.parent()
            while p is not None:
                p.setData(1, Qt.UserRole + 1, p.data(1, Qt.UserRole + 1) + e.lines)
                p.setData(2, Qt.UserRole + 1, p.data(2, Qt.UserRole + 1) + e.size)
                p = p.parent()

        for item in folders.values():
            item.setText(1, f"{item.data(1, Qt.UserRole + 1):,}")
            item.setText(2, human_size(item.data(2, Qt.UserRole + 1)))
            item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
            item.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
            for col in (1, 2):
                item.setForeground(col, QColor(self.theme["muted"]))

        self.tree.setSortingEnabled(True)
        if len(self.entries) <= 300:
            self.tree.expandAll()
        else:
            for i in range(self.tree.topLevelItemCount()):
                self.tree.topLevelItem(i).setExpanded(True)
        self.tree.blockSignals(False)
        self.files_title.setText(f"Files  ({len(self.entries)})")
        self.update_selection_info()

    def populate_type_filter(self):
        counts = {}
        for e in self.entries:
            counts[e.ext or "(none)"] = counts.get(e.ext or "(none)", 0) + 1
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        self.type_combo.addItem(f"All types ({len(self.entries)})", None)
        for ext, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            self.type_combo.addItem(f"{ext}  ({n})", ext)
        self.type_combo.blockSignals(False)

    def _schedule_filter(self, *_):
        self.filter_timer.start()

    def apply_filter(self):
        text = self.search.text().strip().lower()
        ext = self.type_combo.currentData()
        in_content = self.content_check.isChecked()
        visible = 0

        def visit(item):
            nonlocal visible
            idx = item.data(0, Qt.UserRole)
            if idx is None:
                any_visible = False
                for i in range(item.childCount()):
                    any_visible = visit(item.child(i)) or any_visible
                item.setHidden(not any_visible)
                if text and any_visible:
                    item.setExpanded(True)
                return any_visible
            e = self.entries[idx]
            ok = ext is None or (e.ext or "(none)") == ext
            if ok and text:
                ok = text in e.rel_path.lower() or (in_content and text in e.lower)
            item.setHidden(not ok)
            visible += ok
            return ok

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            visit(root.child(i))

        term = self.search.text().strip() if in_content else ""
        self.preview.set_search(term)
        self._update_match_label()
        if self.entries:
            if text or ext:
                self.files_title.setText(f"Files  ({visible} of {len(self.entries)})")
            else:
                self.files_title.setText(f"Files  ({len(self.entries)})")
        self.update_selection_info()

    def selected_entries(self):
        result = []
        it = QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            idx = item.data(0, Qt.UserRole)
            if idx is not None and item.checkState(0) == Qt.Checked and not self._is_hidden(item):
                result.append(self.entries[idx])
            it += 1
        return result

    @staticmethod
    def _is_hidden(item):
        while item is not None:
            if item.isHidden():
                return True
            item = item.parent()
        return False

    def set_all_checked(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        self.tree.blockSignals(True)
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            root.child(i).setCheckState(0, state)
        self.tree.blockSignals(False)
        self.update_selection_info()

    def update_selection_info(self):
        if not self.entries:
            self.selection_label.setText("No files yet – choose a folder and press Scan.")
            self.update_actions()
            return
        sel = self.selected_entries()
        chars = sum(len(e.content) for e in sel)
        size = sum(e.size for e in sel)
        self.selection_label.setText(
            f"<b>{len(sel)}</b> selected · {human_size(size)} · ~{human_count(estimate_tokens(chars))} tokens")
        self.selection_label.setToolTip("Files that are ticked and visible with the current filter. "
                                        "Tokens are estimated as characters ÷ 4.")
        self.update_actions()

    def update_actions(self):
        has = bool(self.entries)
        for w in (self.copy_btn, self.export_btn, self.tree_btn, self.all_btn, self.none_btn,
                  self.expand_btn, self.collapse_btn):
            w.setEnabled(has)

    def on_tree_current(self, current, _previous):
        if current is None:
            return
        idx = current.data(0, Qt.UserRole)
        if idx is not None:
            self.show_entry(self.entries[idx])

    def on_tree_double(self, item, _col):
        idx = item.data(0, Qt.UserRole)
        if idx is not None:
            self.open_external(self.entries[idx])

    def tree_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is None:
            return
        idx = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        if idx is not None:
            e = self.entries[idx]
            menu.addAction("Preview", lambda: self.show_entry(e))
            menu.addAction("Open in default app", lambda: self.open_external(e))
            menu.addAction("Show in folder", lambda: self.reveal(e))
            menu.addSeparator()
            menu.addAction("Copy contents", lambda: self._copy(self.format_entries([e]), "File copied"))
            menu.addAction("Copy relative path", lambda: self._copy(e.rel_path.replace(os.sep, "/"), "Path copied"))
            menu.addAction("Copy full path", lambda: self._copy(e.abs_path, "Path copied"))
        else:
            menu.addAction("Expand all inside", lambda: self._expand_recursive(item, True))
            menu.addAction("Collapse all inside", lambda: self._expand_recursive(item, False))
            menu.addSeparator()
            menu.addAction("Copy files in this folder", lambda: self._copy_folder(item))
        menu.addSeparator()
        menu.addAction("Select only this", lambda: self._select_only(item))
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def _expand_recursive(self, item, expand):
        item.setExpanded(expand)
        for i in range(item.childCount()):
            self._expand_recursive(item.child(i), expand)

    def _collect(self, item):
        idx = item.data(0, Qt.UserRole)
        if idx is not None:
            return [] if self._is_hidden(item) else [self.entries[idx]]
        out = []
        for i in range(item.childCount()):
            out.extend(self._collect(item.child(i)))
        return out

    def _copy_folder(self, item):
        files = self._collect(item)
        self._copy(self.format_entries(files), f"{len(files)} files copied")

    def _select_only(self, item):
        self.tree.blockSignals(True)
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            root.child(i).setCheckState(0, Qt.Unchecked)
        item.setCheckState(0, Qt.Checked)
        self.tree.blockSignals(False)
        self.update_selection_info()

    # ------------------------------------------------------------- preview --
    def show_entry(self, e: FileEntry):
        self.current_entry = e
        self.preview_stack.setCurrentIndex(1)
        self.tabs.setCurrentIndex(0)
        self.file_path_label.setText(e.rel_path.replace(os.sep, " / "))
        modified = time.strftime("%Y-%m-%d %H:%M", time.localtime(e.mtime))
        self.file_meta_label.setText(
            f"{e.lines:,} lines  ·  {human_size(e.size)}  ·  ~{human_count(estimate_tokens(len(e.content)))} tokens"
            f"  ·  modified {modified}")
        term = self.search.text().strip() if self.content_check.isChecked() else ""
        self.preview.show_file(e.content, e.ext, term)
        self._update_match_label()

    def _update_match_label(self):
        n = self.preview.count_matches() if self.current_entry else 0
        has = bool(self.preview.search_term)
        self.match_label.setText(f"{n} match{'es' if n != 1 else ''}" if has else "")
        self.prev_match_btn.setVisible(has)
        self.next_match_btn.setVisible(has)

    def copy_current_file(self):
        if self.current_entry:
            self._copy(self.current_entry.content, f"Copied {self.current_entry.name}")

    def open_external(self, e):
        if e:
            QDesktopServices.openUrl(QUrl.fromLocalFile(e.abs_path))

    def reveal(self, e):
        if e:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(e.abs_path)))

    # --------------------------------------------------------------- stats --
    def populate_stats(self):
        t = self.theme
        entries = self.entries
        total_lines = sum(e.lines for e in entries)
        total_size = sum(e.size for e in entries)
        total_chars = sum(len(e.content) for e in entries)
        self.card_files.set(f"{len(entries):,}")
        self.card_folders.set(f"{self.scan_info.get('folders', 0):,}")
        self.card_lines.set(human_count(total_lines))
        self.card_size.set(human_size(total_size))
        self.card_tokens.set(human_count(estimate_tokens(total_chars)))

        by_type = {}
        for e in entries:
            d = by_type.setdefault(e.ext or "(none)", [0, 0, 0])
            d[0] += 1
            d[1] += e.lines
            d[2] += e.size
        rows = sorted(by_type.items(), key=lambda kv: -kv[1][1])
        self.type_table.setRowCount(len(rows))
        for r, (ext, (n, lines, size)) in enumerate(rows):
            self.type_table.setItem(r, 0, QTableWidgetItem(ext))
            for c, val in ((1, f"{n:,}"), (2, f"{lines:,}"), (3, human_size(size))):
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.type_table.setItem(r, c, it)
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setValue(int(1000 * lines / total_lines) if total_lines else 0)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar {{ background: {t['surface2']}; "
                              f"border-radius: 4px; margin: 10px 4px; max-height: 10px; }}"
                              f"QProgressBar::chunk {{ background: {t['accent']}; border-radius: 4px; }}")
            self.type_table.setCellWidget(r, 4, bar)
            pct = QTableWidgetItem(f"{100 * lines / total_lines:.1f}%" if total_lines else "0%")
            pct.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.type_table.setItem(r, 5, pct)

        biggest = sorted(range(len(entries)), key=lambda i: -entries[i].size)[:15]
        self.big_table.setRowCount(len(biggest))
        for r, i in enumerate(biggest):
            e = entries[i]
            name = QTableWidgetItem(e.rel_path)
            name.setData(Qt.UserRole, i)
            name.setToolTip(e.rel_path)
            self.big_table.setItem(r, 0, name)
            for c, val in ((1, f"{e.lines:,}"), (2, human_size(e.size))):
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.big_table.setItem(r, c, it)

        info = self.scan_info
        parts = [f"Scanned in {info.get('elapsed', 0):.2f}s"]
        if info.get("skipped_large"):
            parts.append(f"{info['skipped_large']} skipped (larger than {self.opts['max_kb']} KB)")
        if info.get("skipped_binary"):
            parts.append(f"{info['skipped_binary']} binary skipped")
        if info.get("errors"):
            parts.append(f"{info['errors']} unreadable")
        if info.get("cancelled"):
            parts.append("scan was cancelled – results are partial")
        self.stats_footer.setText("  ·  ".join(parts))

    def _open_big_file(self, row, _col):
        item = self.big_table.item(row, 0)
        if item is not None:
            idx = item.data(Qt.UserRole)
            self.show_entry(self.entries[idx])
            self.tree.setCurrentItem(self.file_items[idx])

    # ------------------------------------------------------ copy / export --
    def generate_tree(self):
        root = self.scanned_root or self.folder_combo.currentText().strip()
        if not root or not os.path.isdir(root):
            return ""
        ignores = {i.lower() for i in parse_list(self.opts["ignores"])}
        hidden = self.opts["include_hidden"]
        lines = [os.path.basename(os.path.normpath(root)) + "/"]
        count = 0

        def walk(path, prefix):
            nonlocal count
            try:
                names = sorted(os.listdir(path), key=lambda n: (not os.path.isdir(os.path.join(path, n)), n.lower()))
            except OSError:
                return
            names = [n for n in names if (hidden or not n.startswith("."))
                     and not (os.path.isdir(os.path.join(path, n)) and n.lower() in ignores)]
            for i, name in enumerate(names):
                count += 1
                if count > 5000:
                    if count == 5001:
                        lines.append(prefix + "… (truncated)")
                    return
                last = i == len(names) - 1
                full = os.path.join(path, name)
                is_dir = os.path.isdir(full)
                lines.append(prefix + ("└── " if last else "├── ") + name + ("/" if is_dir else ""))
                if is_dir:
                    walk(full, prefix + ("    " if last else "│   "))

        walk(root, "")
        return "\n".join(lines)

    def format_entries(self, entries, fmt=None):
        fmt = fmt or self.format_combo.currentText()
        parts = []
        tree = self.generate_tree() if self.opts["include_tree"] else ""
        for e in entries:
            path = e.rel_path.replace(os.sep, "/")
            if fmt == "Markdown":
                lang = LANG_BY_EXT.get(e.ext, "")
                fence = "````" if "```" in e.content else "```"
                parts.append(f"### {path}\n\n{fence}{lang}\n{e.content.rstrip()}\n{fence}")
            elif fmt == "XML tags":
                parts.append(f'<file path="{path}">\n{e.content.rstrip()}\n</file>')
            else:
                parts.append(f"Filename:\n{path}\n\nFile Data:\n{e.content}")
        body = "\n\n".join(parts)
        if tree:
            if fmt == "Markdown":
                body = f"## Folder structure\n\n```\n{tree}\n```\n\n## Files\n\n{body}"
            elif fmt == "XML tags":
                body = f"<folder_structure>\n{tree}\n</folder_structure>\n\n{body}"
            else:
                body = f"Folder structure:\n{tree}\n\n{'=' * 40}\n\n{body}"
        return body

    def _copy(self, text, message):
        QApplication.clipboard().setText(text)
        self.toast.show_message(message)
        self.statusBar().showMessage(message, 4000)

    def copy_selected(self):
        if not self.entries:
            return
        sel = self.selected_entries()
        if not sel:
            self.toast.show_message("No files selected – tick some files first")
            return
        text = self.format_entries(sel)
        self._copy(text, f"Copied {len(sel)} files · ~{human_count(estimate_tokens(len(text)))} tokens")

    def show_tree(self):
        if not self.entries and not self.scanned_root:
            return
        text = self.generate_tree()
        QApplication.clipboard().setText(text)
        self.toast.show_message("Folder tree copied")
        TreeDialog(self, text).exec_()

    def export_files(self):
        if not self.entries:
            return
        sel = self.selected_entries()
        if not sel:
            self.toast.show_message("No files selected – tick some files first")
            return
        base = os.path.basename(os.path.normpath(self.scanned_root)) or "files"
        docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        fmt = self.format_combo.currentText()
        filters = "Markdown (*.md);;Text (*.txt);;JSON (*.json)"
        default_filter = {"Markdown": "Markdown (*.md)", "XML tags": "Text (*.txt)"}.get(fmt, "Text (*.txt)")
        ext = ".md" if default_filter.startswith("Markdown") else ".txt"
        path, chosen = QFileDialog.getSaveFileName(
            self, "Export selected files", os.path.join(docs, base + ext), filters, default_filter)
        if not path:
            return
        try:
            if path.lower().endswith(".json") or chosen.startswith("JSON"):
                if not path.lower().endswith(".json"):
                    path += ".json"
                data = {
                    "root": self.scanned_root,
                    "exported": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "file_count": len(sel),
                    "files": [{
                        "path": e.rel_path.replace(os.sep, "/"), "extension": e.ext,
                        "size": e.size, "lines": e.lines,
                        "modified": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(e.mtime)),
                        "content": e.content,
                    } for e in sel],
                }
                if self.opts["include_tree"]:
                    data["tree"] = self.generate_tree()
                text = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                use_fmt = "Markdown" if path.lower().endswith(".md") else fmt
                if use_fmt == "Markdown" and not path.lower().endswith(".md"):
                    use_fmt = "Plain text"
                text = self.format_entries(sel, use_fmt)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.toast.show_message(f"Exported {len(sel)} files")
        self.statusBar().showMessage(f"Exported {len(sel)} files to {path}", 6000)

    # ------------------------------------------------------------ misc UI --
    def focus_search(self):
        self.search.setFocus()
        self.search.selectAll()

    def on_escape(self):
        if self.worker and self.worker.isRunning():
            self.cancel_scan()
        elif self.search.text():
            self.search.clear()

    def open_settings(self):
        dlg = SettingsDialog(self, self.opts)
        if dlg.exec_() != QDialog.Accepted:
            return
        old = dict(self.opts)
        self.opts = dlg.values()
        for k, v in self.opts.items():
            self.settings.setValue(k, v)
        self.preview.set_font_size(self.opts["font_size"])
        scan_keys = ("extensions", "ignores", "max_kb", "include_hidden")
        if self.scanned_root and any(old[k] != self.opts[k] for k in scan_keys):
            self.start_scan()
        else:
            self.toast.show_message("Settings saved")

    def show_help(self, anchor=None):
        HelpDialog(self, self.theme, anchor).exec_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast.isVisible():
            p = self.toast.parentWidget()
            self.toast.move((p.width() - self.toast.width()) // 2, p.height() - self.toast.height() - 28)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(2000)
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter", self.splitter.saveState())
        super().closeEvent(event)


def main():
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = FolderInsightPro()
    window.show()
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        window.folder_combo.setEditText(sys.argv[1])
        QTimer.singleShot(0, window.start_scan)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
