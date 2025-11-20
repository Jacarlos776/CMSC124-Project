import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QListWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QTextEdit, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtCore import Qt

# function that will highlight LOL Code syntax
class highlight(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        keywords = [
            "HAI", "KTHXBYE", "I HAS A", "VISIBLE", "GIMMEH",
            "ITZ", "R", "SUM OF", "DIFF OF", "PRODUKT OF",
            "QUOSHUNT OF", "MOD OF", "BIGGR OF", "SMALLR OF",
            "O RLY?", "YA RLY", "NO WAI", "OIC", "BTW", "OBTW", "TLDR"
        ]

        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#00eaff"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        self.rules = [(kw, self.keyword_format) for kw in keywords]

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            index = text.find(pattern)
            while index != -1:
                self.setFormat(index, len(pattern), fmt)
                index = text.find(pattern, index + len(pattern))

# left panel: widget that accepts file drops
class left_panel(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setAcceptDrops(True)

        self.setStyleSheet("background-color: transparent;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.parent_window.process_dropped_files(event)

# main window
class ide(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LOL Code Interpreter")
        self.resize(1200, 750)

        self.file_paths = {}

        # main layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # left panel: file drop area + file list
        self.drop_area = left_panel(self)
        left_panel_layout = QVBoxLayout(self.drop_area)

        files_label = QLabel("FILES")
        files_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        files_label.setStyleSheet("color: white;")
        left_panel_layout.addWidget(files_label)

        self.file_list = QListWidget()
        self.file_list.setStyleSheet("background-color: #3a3a3a; color: white;")
        self.file_list.clicked.connect(self.load_selected_file)

        left_panel_layout.addWidget(self.file_list)

        main_layout.addWidget(self.drop_area, 1)

        # right panel: buttons + editor + terminal
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 3)

        # top buttons: save, run, delete
        top_buttons = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_file)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_file)
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_file)

        top_buttons.addWidget(self.save_button)
        top_buttons.addWidget(self.delete_button)
        top_buttons.addWidget(self.run_button)
        top_buttons.addStretch()
        right_panel.addLayout(top_buttons)

        # editor
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.highlighter = highlight(self.editor.document())
        right_panel.addWidget(self.editor)

        # terminal
        terminal_label = QLabel("Terminal")
        terminal_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        right_panel.addWidget(terminal_label)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFixedHeight(180)
        self.terminal.setStyleSheet("background-color: #3a3a3a; color: white;")
        right_panel.addWidget(self.terminal)

    # process dropped files
    def process_dropped_files(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()

            if file_path.endswith(".txt") or file_path.endswith(".lol"):
                file_name = os.path.basename(file_path)
                self.file_paths[file_name] = file_path

                if not self.file_in_list(file_name):
                    self.file_list.addItem(file_name)
            else:
                QMessageBox.warning(self, "Invalid File", "Only .txt or .lol allowed.")

    def file_in_list(self, name):
        for i in range(self.file_list.count()):
            if self.file_list.item(i).text() == name:
                return True
        return False

    # load selected file into editor
    def load_selected_file(self):
        item = self.file_list.currentItem()
        if not item:
            return

        filename = item.text()
        filepath = self.file_paths[filename]

        with open(filepath, "r", encoding="utf-8") as f:
            self.editor.setPlainText(f.read())

    # function to save file
    def save_file(self):
        item = self.file_list.currentItem()
        if not item:
            return

        filename = item.text()
        filepath = self.file_paths[filename]

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.editor.toPlainText())

        self.terminal.append("File saved.")

    # function to handle run button press
    # checker for now
    def run_file(self):
        self.terminal.append("Run button pressed!")

    # function to handle delete button press
    def delete_file(self):
        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No File Selected", "Please select a file to delete.")
            return

        filename = item.text()

        confirm = QMessageBox.question(
            self,
            "Delete File",
            f"Remove '{filename}' from the IDE?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        # remove from internal dict
        if filename in self.file_paths:
            del self.file_paths[filename]

        # remove from list widget
        row = self.file_list.row(item)
        self.file_list.takeItem(row)
        
        # if deleted file was being edited, clear editor
        self.editor.clear()
        self.terminal.append(f"Removed '{filename}' from the IDE.")

# main
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ide()
    window.show()
    sys.exit(app.exec())
