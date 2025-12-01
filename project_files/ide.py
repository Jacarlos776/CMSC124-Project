import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog
)
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtCore import Qt, QProcess, QEvent


class highlight(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        keywords = ["HAI", "KTHXBYE", "I HAS A", "ITZ", "VISIBLE", "R"]
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


class ide(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ang Ganda ni Maam Kat LOLETPRETER")
        self.resize(1400, 900)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # TOP BAR - FILE COMBO AND TITLE ----------------
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(5, 5, 5, 5)
        top_bar.setSpacing(5)
        
        # (1) FILE COMBO
        self.file_combo = QComboBox()
        self.file_combo.setEditable(True)
        # Start with a placeholder entry when no file is loaded
        self.file_combo.addItem("(None)")
        self.file_combo.setCurrentIndex(0)
        # Use an event filter to detect clicks on the combo's arrow and open file dialog
        self.file_combo.installEventFilter(self)
        top_bar.addWidget(self.file_combo, 1)

        # Connect Enter key to load file
        self.file_combo.lineEdit().returnPressed.connect(self.load_file_from_input)
        
        # TITLE
        title_label = QLabel("LOL CODE INTERPRETER")
        title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_label, 1)
        
        layout.addLayout(top_bar)

        # MIDDLE SECTION ----------------
        middle = QHBoxLayout()
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setSpacing(5)
        layout.addLayout(middle, 1)

        # LEFT COLUMN - EDITOR ----------------
        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(5)
        middle.addLayout(left_column, 1)

        # (2) EDITOR ----------------
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.highlighter = highlight(self.editor.document())
        left_column.addWidget(self.editor, 1)

        # RIGHT SECTION = LEXEMES AND SYMBOL TABLE (SIDE BY SIDE) ----------------
        right_section = QHBoxLayout()
        right_section.setContentsMargins(0, 0, 0, 0)
        right_section.setSpacing(5)
        middle.addLayout(right_section, 1)

        # LEXEMES TABLE ----------------
        lex_container = QVBoxLayout()
        lex_container.setContentsMargins(0, 0, 0, 0)
        lex_container.setSpacing(0)
        
        lex_label = QLabel("Lexemes")
        lex_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lex_label.setStyleSheet("padding: 5px; text-align: center;")
        lex_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lex_container.addWidget(lex_label)

        self.lex_table = QTableWidget(0, 2)
        self.lex_table.setHorizontalHeaderLabels(["Lexeme", "Classification"])
        self.lex_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lex_table.setFont(QFont("Consolas", 9))
        lex_container.addWidget(self.lex_table, 1)
        
        right_section.addLayout(lex_container, 1)

        # SYMBOL TABLE ----------------
        sym_container = QVBoxLayout()
        sym_container.setContentsMargins(0, 0, 0, 0)
        sym_container.setSpacing(0)
        
        sym_label = QLabel("SYMBOL TABLE")
        sym_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        sym_label.setStyleSheet("padding: 5px; text-align: center;")
        sym_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sym_container.addWidget(sym_label)

        self.symbol_table = QTableWidget(0, 2)
        self.symbol_table.setHorizontalHeaderLabels(["Identifier", "Value"])
        self.symbol_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.symbol_table.setFont(QFont("Consolas", 9))
        sym_container.addWidget(self.symbol_table, 1)
        
        right_section.addLayout(sym_container, 1)

        # (5) EXECUTE BUTTON ----------------
        self.exec_btn = QPushButton("EXECUTE")
        self.exec_btn.setFixedHeight(45)
        self.exec_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(self.exec_btn)

        # (6) CONSOLE ----------------
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 11))
        layout.addWidget(self.console, 1)

        # Process runner
        self.proc = None
        self.exec_btn.clicked.connect(self.run_program)
        self.file_combo.currentIndexChanged.connect(self.load_file)
        self.file_paths = {}

    # -------- FILE DROPS ----------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            name = os.path.basename(path)
            if path.endswith(".txt") or path.endswith(".lol"):
                # remove placeholder if present
                idx_none = self.file_combo.findText("(None)")
                if idx_none != -1:
                    self.file_combo.removeItem(idx_none)
                self.file_paths[name] = path
                self.file_combo.addItem(name)
                with open(path, "r") as f:
                    self.editor.setText(f.read())

    def load_file(self):
        name = self.file_combo.currentText()
        if name == "(None)":
            return
        if name in self.file_paths:
            with open(self.file_paths[name], "r") as f:
                self.editor.setText(f.read())

    def eventFilter(self, watched, event):
        # Intercept mouse presses on the file combo to open file dialog when arrow clicked
        if watched is self.file_combo and event.type() == QEvent.Type.MouseButtonPress:
            # Determine if click is on the dropdown arrow area (right side)
            click_x = event.position().x() if hasattr(event, 'position') else event.x()
            if click_x >= self.file_combo.width() - 24:
                self.open_file_dialog()
                return True
        return super().eventFilter(watched, event)
    
    def open_file_dialog(self):
        file_dialog = QFileDialog()
        paths, _ = file_dialog.getOpenFileNames(
            self,
            "Open LOL File",
            "",
            "LOL Files (*.lol);;Text Files (*.txt);;All Files (*.*)"
        )
        for path in paths:
            name = os.path.basename(path)
            # remove placeholder if present
            idx_none = self.file_combo.findText("(None)")
            if idx_none != -1:
                self.file_combo.removeItem(idx_none)
            if name not in self.file_paths:
                self.file_paths[name] = path
                self.file_combo.addItem(name)
            self.file_combo.setCurrentText(name)
    
    def load_file_from_input(self):
        # Load file when user types path and presses Enter
        text = self.file_combo.currentText()
        if os.path.exists(text):
            name = os.path.basename(text)
            # remove placeholder if present
            idx_none = self.file_combo.findText("(None)")
            if idx_none != -1:
                self.file_combo.removeItem(idx_none)
            self.file_paths[name] = text
            if self.file_combo.findText(name) == -1:
                self.file_combo.addItem(name)
            self.file_combo.setCurrentText(name)

    # -------- EXECUTE BUTTON ACTION ----------
    def run_program(self):
        if self.file_combo.currentText() not in self.file_paths:
            self.console.append("No file selected!")
            return

        path = self.file_paths[self.file_combo.currentText()]
        self.console.clear()
        self.lex_table.setRowCount(0)
        self.symbol_table.setRowCount(0)

        self.proc = QProcess()
        self.proc.readyReadStandardOutput.connect(self.read_output)
        self.proc.start("python", ["main.py", path])

        self.section = None

    def read_output(self):
        txt = self.proc.readAllStandardOutput().data().decode()

        if "TOKENS_BEGIN" in txt:
            self.section = "tokens"
            return
        if "TOKENS_END" in txt:
            self.section = None
            return
        if "SYMBOL_BEGIN" in txt:
            self.section = "symbols"
            return
        if "SYMBOL_END" in txt:
            self.section = None
            return

        if self.section == "tokens":
            parts = txt.strip().split("|")
            if len(parts) == 2:
                row = self.lex_table.rowCount()
                self.lex_table.insertRow(row)
                self.lex_table.setItem(row, 0, QTableWidgetItem(parts[1]))
                self.lex_table.setItem(row, 1, QTableWidgetItem(parts[0]))
            return

        if self.section == "symbols":
            parts = txt.strip().split("|")
            if len(parts) == 2:
                row = self.symbol_table.rowCount()
                self.symbol_table.insertRow(row)
                self.symbol_table.setItem(row, 0, QTableWidgetItem(parts[0]))
                self.symbol_table.setItem(row, 1, QTableWidgetItem(parts[1]))
            return

        self.console.append(txt)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ide()
    win.show()
    sys.exit(app.exec())