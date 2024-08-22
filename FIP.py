import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox, QTextEdit, QTreeView, QSplitter, QGroupBox
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QStandardPaths
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor


class FolderSelectionApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up window
        self.setWindowTitle("Advanced Folder Selection App")
        self.setGeometry(100, 100, 1200, 600)
        self.setMinimumSize(1000, 400)

        # Set up initial styles
        self.dark_theme = True
        self.set_dark_theme()

        # Create widgets
        self.folder_label = QLabel("Select the folder to process:", self)
        self.folder_entry = QLineEdit()
        self.select_folder_btn = QPushButton("Select Folder", self)
        self.start_btn = QPushButton("Start Processing", self)
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search files...")
        self.search_bar.textChanged.connect(self.filter_files)

        self.file_preview = QTextEdit(self)
        self.file_preview.setReadOnly(True)

        self.theme_toggle_btn = QPushButton("Toggle Theme", self)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)

        self.export_btn = QPushButton("Export File List", self)
        self.export_btn.clicked.connect(self.export_file_list)

        # Set up layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.folder_entry)
        top_layout.addWidget(self.select_folder_btn)
        top_layout.addWidget(self.start_btn)

        # Collapsible sections
        self.files_group = QGroupBox("Files")
        self.files_group.setCheckable(True)
        self.files_group.setChecked(True)
        self.files_layout = QHBoxLayout()
        self.files_group.setLayout(self.files_layout)

        self.tree_group = QGroupBox("File Tree")
        self.tree_group.setCheckable(True)
        self.tree_group.setChecked(True)
        self.tree_layout = QVBoxLayout()
        self.tree_group.setLayout(self.tree_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.folder_label)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.search_bar)
        main_layout.addWidget(self.files_group)
        main_layout.addWidget(self.tree_group)
        main_layout.addWidget(self.file_preview)
        main_layout.addWidget(self.theme_toggle_btn)
        main_layout.addWidget(self.export_btn)

        # Create main widget and set layout
        main_widget = QWidget(self)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Connect buttons
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.start_btn.clicked.connect(self.start_processing)

    def set_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E3440;
            }
            QLabel, QLineEdit, QPushButton, QGroupBox, QTextEdit {
                color: #D8DEE9;
                background-color: #4C566A;
                border: 1px solid #D8DEE9;
                border-radius: 4px;
                padding: 8px;
                font-size: 16px;
            }
            QPushButton {
                background-color: #5E81AC;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QLineEdit {
                padding: 6px;
            }
            QGroupBox::title {
                color: #D8DEE9;
                background-color: transparent;
            }
            QGroupBox {
                border: 1px solid #5E81AC;
                margin-top: 10px;
                padding-top: 20px;
            }
        """)

    def set_light_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECEFF4;
            }
            QLabel, QLineEdit, QPushButton, QGroupBox, QTextEdit {
                color: #2E3440;
                background-color: #D8DEE9;
                border: 1px solid #2E3440;
                border-radius: 4px;
                padding: 8px;
                font-size: 16px;
            }
            QPushButton {
                background-color: #A3BE8C;
            }
            QPushButton:hover {
                background-color: #8FBC8B;
            }
            QLineEdit {
                padding: 6px;
            }
            QGroupBox::title {
                color: #2E3440;
                background-color: transparent;
            }
            QGroupBox {
                border: 1px solid #A3BE8C;
                margin-top: 10px;
                padding-top: 20px;
            }
        """)

    def toggle_theme(self):
        if self.dark_theme:
            self.set_light_theme()
        else:
            self.set_dark_theme()
        self.dark_theme = not self.dark_theme

    def select_folder(self):
        # Open folder selection dialog
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")

        # Update folder path in entry widget
        self.folder_entry.setText(folder_path)

    def scan_files(self, work_dir, file_extensions):
        file_list = []
        for dirpath, dirnames, filenames in os.walk(work_dir):
            for filename in filenames:
                if filename.endswith(tuple(file_extensions)):
                    filepath = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(filepath, work_dir)
                    try:
                        with open(filepath, 'r') as file:
                            content = file.read()
                            file_list.append([relative_path, content])
                    except Exception as e:
                        file_list.append((relative_path, "error"))

        return file_list

    def generate_file_tree(self, work_dir):
        file_tree = ""
        for dirpath, dirnames, filenames in os.walk(work_dir):
            depth = dirpath.replace(work_dir, "").count(os.sep)
            indent = " " * 4 * depth
            file_tree += f"{indent}{os.path.basename(dirpath)}/\n"
            sub_indent = " " * 4 * (depth + 1)
            for filename in filenames:
                file_tree += f"{sub_indent}{filename}\n"
        return file_tree

    def start_processing(self):
        # Get folder path from entry widget
        folder_path = self.folder_entry.text()
        self.file_data_list = self.scan_files(folder_path, ["py", "html", "css", "js", "svelte"])

        if not self.file_data_list:
            QMessageBox.warning(self, "No Files Found", "No files with the specified extensions were found in the selected directory.")
            return

        # Clear previous file buttons
        for i in reversed(range(self.files_layout.count())):
            self.files_layout.itemAt(i).widget().setParent(None)

        # Add "Copy All" button to layout
        all_files_text = "\n\n".join([f"Filename:\n{fd[0]}\n\nFile Data:\n{fd[1]}" for fd in self.file_data_list])
        copy_all_button = QPushButton("Copy All", self)
        copy_all_button.setObjectName("copyAllButton")
        copy_all_button.clicked.connect(lambda checked, text=all_files_text: QApplication.clipboard().setText(text))
        self.files_layout.addWidget(copy_all_button)

        # Add "Tree" button to layout
        tree_button = QPushButton("Tree", self)
        tree_button.setObjectName("treeButton")
        tree_button.clicked.connect(lambda: QApplication.clipboard().setText(self.generate_file_tree(folder_path)))
        self.files_layout.addWidget(tree_button)

        # Create and add buttons for each file
        self.file_buttons = []
        for index, file_data in enumerate(self.file_data_list):
            button = QPushButton(file_data[0], self)
            button.clicked.connect(lambda checked, text=file_data[1]: self.file_preview.setText(text))
            self.file_buttons.append(button)
            self.files_layout.addWidget(button)

    def filter_files(self):
        filter_text = self.search_bar.text().lower()
        for button in self.file_buttons:
            if filter_text in button.text().lower():
                button.show()
            else:
                button.hide()

    def export_file_list(self):
        save_path = QFileDialog.getSaveFileName(self, "Save File List", QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation), "Text Files (*.txt)")[0]
        if save_path:
            with open(save_path, 'w') as file:
                for file_data in self.file_data_list:
                    file.write(f"Filename: {file_data[0]}\n")
                    file.write(f"File Data:\n{file_data[1]}\n\n")
            QMessageBox.information(self, "Export Complete", f"File list exported to {save_path}")


# Create Qt application
app = QApplication([])

# Create instance of FolderSelectionApp
window = FolderSelectionApp()
window.show()

# Start Qt event loop
app.exec_()
