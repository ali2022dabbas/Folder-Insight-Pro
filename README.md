# Folder Insight Pro

Folder Insight Pro lets you explore, filter, preview, measure and export the source files in a folder. Use it for code reviews, documentation and archiving, or to paste a whole project into an AI assistant in one go.

## Table of contents
- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Contributing](#contributing)

## Features

- **Built-in help (ⓘ)**: click the round *i* button in the top bar (or press `F1`) to open a guide to every part of the app. Small *i* buttons next to each panel open the matching section, and every control has a tooltip.
- **Folder tree view**: files are shown in a collapsible tree with line counts and sizes. Folders show the totals of everything inside them. You can sort by name, lines or size.
- **Pick the files you want**: tick or untick files and whole folders, then copy or export only those.
- **Search and filter**: filter by file name, or turn on **Search inside files** to match text in file contents. Matches are highlighted in the preview, and you can step through them with `F3`. A type filter shows one extension at a time.
- **Code preview**: line numbers, syntax highlighting, word-wrap toggle and zoom. You can also open a file in your default app or show it in your file manager.
- **Copy in three formats**: **Markdown** (code blocks), **Plain text** (the original *Filename / File Data* layout) or **XML tags** (`<file path="…">`, a good fit for AI prompts).
- **Token estimate**: see roughly how many LLM tokens your selection uses before you paste it.
- **Folder structure diagram**: a `├──`/`└──` tree of the folder, copied to your clipboard. You can also add it to the top of every copy or export.
- **Export** to `.md`, `.txt` or `.json` (JSON includes size, line count and modified date for each file).
- **Statistics tab**: totals, a breakdown by file type with share-of-lines bars, and a list of the largest files.
- **Configurable scanning**: choose your own extensions (with presets, or `*` for all text files), folders to skip (`node_modules`, `.git`, `venv`… are skipped by default), a maximum file size and whether to include hidden files. Binary files are skipped automatically.
- **Fast and responsive**: scanning runs in the background and can be cancelled.
- **Nice to have**: drag and drop a folder onto the window, a list of your 10 most recent folders, a dark/light theme, and settings that are remembered between sessions.

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ali2022dabbas/Folder-Insight-Pro.git
   cd Folder-Insight-Pro
   ```
2. **Install the dependency** (Python 3.7+)
   ```bash
   pip install PyQt5
   ```
3. **Run the app**
   ```bash
   python FIP.py
   # or open a folder straight away:
   python FIP.py path/to/project
   ```

## Usage

1. **Choose a folder**: click **Browse…**, paste a path, pick a recent folder, or drag a folder onto the window.
2. **Scan**: press **Scan** (`F5`). The scan uses the extensions and skip list from **⚙ Settings**.
3. **Explore**: click a file to preview it, or double-click to open it in your default app. Right-click for more options (copy path, copy one folder, select only this…).
4. **Filter**: type in the search box. Tick *Search inside files* to search file contents as well.
5. **Copy or export**: tick the files you want, choose a **Format**, then click **Copy selected** or **Export…**. Only files that are ticked *and* visible under the current filter are included.
6. **Tree**: click **Tree** to copy and view a diagram of the folder structure.
7. **Statistics**: open the **Statistics** tab for totals and per-type breakdowns.

If you're unsure what something does, click the **ⓘ** button.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+O` | Browse for a folder |
| `F5` / `Ctrl+R` | Scan / rescan |
| `Esc` | Cancel scan / clear search |
| `Ctrl+F` | Focus search |
| `F3` / `Shift+F3` | Next / previous match |
| `Ctrl+Shift+C` | Copy selected files |
| `Ctrl+T` | Copy and show folder tree |
| `Ctrl+E` | Export selected files |
| `Ctrl +` / `Ctrl -` / `Ctrl+0` | Zoom preview |
| `Ctrl+Shift+L` | Toggle theme |
| `Ctrl+,` | Settings |
| `F1` | Help |

## Contributing

Contributions are welcome. If you find a bug, have an idea for a new feature or want to improve the code, open an issue or submit a pull request.

This project is licensed under the MIT License.
