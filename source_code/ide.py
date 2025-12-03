from lexer import LexicalAnalyzer
from parser import Parser
from interpreter import Interpreter

import re
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog
)

from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QIcon
from PyQt6.QtCore import Qt, QProcess, QEvent, QObject, pyqtSignal
import threading
import queue

# Function for syntax highlighting
class highlight(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        keywords = [
            # Program Structure
            ["HAI", "KTHXBYE", "OBTW", "TLDR", "BTW"],  # Light Blue
            
            # Variable Declaration & Assignment
            ["I HAS A", "ITZ", "R", "IS NOW A", "MAEK", "MAEK A"],  # Green
            
            # Input/Output
            ["VISIBLE", "GIMMEH", "SMOOSH"],  # Yellow
            
            # Arithmetic Operators
            ["SUM OF", "DIFF OF", "PRODUKT OF", "QUOSHUNT OF", "MOD OF", "BIGGR OF", "SMALLR OF"],  # Purple
            
            # Boolean/Logic Operators
            ["BOTH OF", "EITHER OF", "WON OF", "ANY OF", "ALL OF", "BOTH SAEM", "DIFFRINT", "NOT"],  # Teal
            
            # Conditionals
            ["O RLY?", "O RLY", "YA RLY", "NO WAI", "MEBBE", "OIC", "WTF?", "OMG", "OMGWTF"],  # Orange
            
            # Loops
            ["IM IN YR", "IM OUTTA YR", "UPPIN", "NERFIN", "YR", "TIL", "WILE"],  # Pink
            
            # Functions/Procedures
            ["HOW IZ I", "IF U SAY SO", "FOUND YR", "I IZ"],  # Cyan
            
            # Flow Control
            ["GTFO"],  # Red
            
            # Miscellaneous / Others
            ["WAZZUP", "BUHBYE", "MKAY", "FAIL", "WIN", "AN"],  # Grey
        ]

        
        colors = ["#00bfff", "#32cd32", "#ffff00", "#991072", "#0004ff", "#ffa500", "#ff69b4", "#ff1493", "#ff0000", "#0CE4BD"]
        
        self.rules = []
        for keyword_list, color in zip(keywords, colors):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            fmt.setFontWeight(QFont.Weight.Bold)
            for kw in keyword_list:
                regex = re.compile(r'\b' + re.escape(kw) + r'\b')
                self.rules.append((regex, fmt))

    def highlightBlock(self, text):
        for regex, fmt in self.rules:
            for match in regex.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)

class ide(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(":icons/lolenterpreter_icon.png"))
        self.setWindowTitle("Ang Pogi ni Sir JC LOLETPRETER")
        self.resize(1400, 900)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # TOP SECTION ----------------
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(5, 5, 5, 5)
        top_bar.setSpacing(5)
        
        # (1) FILE EXPLORER
        self.file_combo = QComboBox()
        self.file_combo.setEditable(True)
        # placeholder when no file is loaded
        self.file_combo.addItem("(None)")
        self.file_combo.setCurrentIndex(0)
        # detects if drop down arrow is clicked
        self.file_combo.installEventFilter(self)
        top_bar.addWidget(self.file_combo, 1)

        # connect enter press in line edit to load file
        self.file_combo.lineEdit().returnPressed.connect(self.load_file_from_input)
        
        # title label
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

        # LEFT COLUMN - EDITOR
        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(5)
        middle.addLayout(left_column, 1)

        # (2) EDITOR
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.highlighter = highlight(self.editor.document())

        # classification mapping for lexeme table
        self.token_class = {
            'HAI': 'Code Delimiter',
            'KTHXBYE': 'Code Delimiter',
            'I_HAS_A': 'Variable Declaration',
            'ITZ': 'Variable Assignment',
            'R': 'Assignment Keyword',
            'VISIBLE': 'Output Keyword',
            'GIMMEH': 'Input Keyword',
            'YARN_LIT': 'String Literal (delimited by ")',
            'NUMBR_LIT': 'Literal',
            'NUMBAR_LIT': 'Literal',
            'TROOF_LIT': 'Literal',
            'ID': 'Variable Identifier',
            'SMOOSH': 'String Concatenation',
            'SUM_OF': 'Operator',
            'DIFF_OF': 'Operator',
            'PRODUKT_OF': 'Operator',
            'QUOSHUNT_OF': 'Operator',
            'MOD_OF': 'Operator',
            'WAZZUP': 'Declaration Block',
            'BUHBYE': 'End Declaration Block',
            'O_RLY': 'Conditional Start',
            'YA_RLY': 'Conditional Branch',
            'NO_WAI': 'Conditional Branch',
            'OIC': 'Conditional End',
            'IM_IN_YR': 'Loop Start',
            'IM_OUTTA_YR': 'Loop End',
            'BOTH_OF': 'Operator',
            'EITHER_OF': 'Operator',
            'WON_OF': 'Operator',
            'ALL_OF': 'Operator',
            'ANY_OF': 'Operator',
            'AN': 'Connector',
            'MKAY': 'Terminator',
            'NOT': 'Operator',
            'BOTH_SAEM': 'Operator',
            'DIFFRINT': 'Operator',
            'BIGGR_OF': 'Operator',
            'SMALLR_OF': 'Operator',

            # Added Tokens
            'OBTW': 'Comment Block Start',
            'TLDR': 'Comment Block End',
            'BTW': 'Comment',

            'IS_NOW_A': 'Type Casting',
            'MAEK': 'Type Casting / Construct',
            'MAEK_A': 'Type Casting / Construct',

            'O_RLY?': 'Conditional Start',
            'MEBBE': 'Conditional Branch',

            'WTF': 'Switch Start',
            'OMG': 'Switch Case',
            'OMGWTF': 'Default Case',

            'UPPIN': 'Increment Keyword',
            'NERFIN': 'Decrement Keyword',
            'YR': 'Loop Variable',
            'TIL': 'Loop Condition (until)',
            'WILE': 'Loop Condition (while)',

            'HOW_IZ_I': 'Function Declaration',
            'IF_U_SAY_SO': 'Function End',
            'FOUND_YR': 'Function Return',
            'I_IZ': 'Function Call',

            'GTFO': 'Flow Control (Break/Return)',

            'FAIL': 'Literal',
            'WIN': 'Literal'
        }

        left_column.addWidget(self.editor, 1)

        # RIGHT COLUMN = LIST OF TOKENS AND SYMBOL TABLE
        right_section = QHBoxLayout()
        right_section.setContentsMargins(0, 0, 0, 0)
        right_section.setSpacing(5)
        middle.addLayout(right_section, 1)

        # (3) LIST OF TOKENS
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

        # (4) SYMBOL TABLE
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

        # BOTTOM SECTION ----------------
        # (5) EXECUTE BUTTON
        self.exec_btn = QPushButton("EXECUTE")
        self.exec_btn.setFixedHeight(45)
        self.exec_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(self.exec_btn)

        # (6) CONSOLE
        console_widget = QWidget()
        console_layout = QVBoxLayout()
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(0)
        console_widget.setLayout(console_layout)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 11))
        console_layout.addWidget(self.console, 1)

        # input bar for user input during GIMMEH
        input_bar = QWidget()
        input_bar_layout = QHBoxLayout()
        input_bar_layout.setContentsMargins(6, 4, 6, 4)
        input_bar_layout.setSpacing(6)
        input_bar.setLayout(input_bar_layout)

        self.input_line = QLineEdit()
        self.input_line.setFont(QFont("Consolas", 11))
        self.input_line.setPlaceholderText("Type input for GIMMEH and press enter or send")
        try:
            self.input_line.setFrame(False)
        except Exception:
            pass

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)
        input_bar_layout.addWidget(self.input_line, 1)
        input_bar_layout.addWidget(self.send_btn)

        console_layout.addWidget(input_bar)
        layout.addWidget(console_widget, 1)

        # connect buttons and events to their corresponding handlers
        # (execute → run_program, send → send_input, file selection → load_file)
        self.proc = None
        self.exec_btn.clicked.connect(self.run_program)
        self.send_btn.clicked.connect(self.send_input)
        self.input_line.returnPressed.connect(self.send_input)
        self.file_combo.currentIndexChanged.connect(self.load_file)
        self.file_paths = {}

        # queue for input lines from user to interpreter
        self.input_queue = queue.Queue()

        # define and initialize custom Qt signals to update UI from
        # the interpreter thread:
        # output(str) → append printed text to console
        # symbol(name, value) → update the symbol table display
        # enable_input(bool) → enable or disable the input field when needed
        class WorkerSignals(QObject):
            output = pyqtSignal(str)
            symbol = pyqtSignal(str, object)
            enable_input = pyqtSignal(bool)

        self.signals = WorkerSignals()
        self.signals.output.connect(self.append_output)
        self.signals.symbol.connect(self.update_symbol_table_from_signal)
        self.signals.enable_input.connect(self.set_input_enabled)

        # input bar is disabled by default
        self.set_input_enabled(False)

    # FILE DROP HANDLING
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
        # intercept mouse presses on the file combo to open file dialog when arrow clicked
        if watched is self.file_combo and event.type() == QEvent.Type.MouseButtonPress:
            # determine if click is on the dropdown arrow area (right side)
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
        # load file when user types path and presses Enter
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

    # EXECUTION HANDLING    
    def run_program(self):
        # === || Added to completely reset inputs || ===
        self.current_interpreter = None
        # Reset input buffer
        self.input_queue = queue.Queue()
        # Disable input bar
        self.set_input_enabled(False)

        # run code from the editor (not the selected file)
        code = self.editor.toPlainText()
        self.console.clear()
        self.lex_table.setRowCount(0)
        self.symbol_table.setRowCount(0)

        # tokenize
        try:
            analyzer = LexicalAnalyzer()
            tokens, lexemes, rows, cols = analyzer.tokenize(code)
        except Exception as e:
            self.console.append(f"Lexical error: {e}")
            return

        # Populate lexeme table (one-time) using human-friendly classifications
        for tok, lex in zip(tokens, lexemes):
            row = self.lex_table.rowCount()
            self.lex_table.insertRow(row)
            self.lex_table.setItem(row, 0, QTableWidgetItem(lex))
            cls = self.token_class.get(tok)
            if cls is None:
                # Fallback: prettify token name
                cls = tok.replace('_', ' ').title()
            self.lex_table.setItem(row, 1, QTableWidgetItem(cls))

        # parse
        try:
            parser = Parser(tokens, lexemes, rows, cols)
            ast = parser.parse_program()
        except Exception as e:
            self.console.append(f"Parsing error: {e}")
            return

        # create interpreter with callbacks
        def on_output(s):
            # ensure string
            self.signals.output.emit(str(s))

        def on_symbol(name, val):
            # val is a dict like {"type": ..., "value": ...}
            self.signals.symbol.emit(name, val)

        def on_input():
            # notify UI to enable input
            self.signals.output.emit(">> Waiting for input...")
            self.signals.enable_input.emit(True)
            # block until input available
            try:
                val = self.input_queue.get()
            finally:
                # disable input after receiving
                self.signals.enable_input.emit(False)
            return val

        interp = Interpreter(ast, on_output=on_output, on_input=on_input, on_symbol_update=on_symbol)

        # run interpreter in separate thread
        t = threading.Thread(target=self._run_interpreter_thread, args=(interp,), daemon=True)
        t.start()

    # function for reading output from interpreter thread
    def read_output(self):
        pass

    def _run_interpreter_thread(self, interp: Interpreter):
        try:
            interp.run()
        except Exception as e:
            self.signals.output.emit(f"Runtime error: {e}")

    # slot for appending output from interpreter thread
    def append_output(self, txt):
        self.console.append(str(txt))

    def set_input_enabled(self, enabled: bool):
        self.input_line.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        if enabled:
            self.input_line.setFocus()

    def send_input(self):
        # called when user clicks Send
        text = self.input_line.text()
        # clear input field
        self.input_line.clear()
        # put into queue for interpreter
        self.input_queue.put(text)
        # echo to console
        self.console.append(f"> {text}")

    def update_symbol_table_from_signal(self, name, val):
        # update or insert symbol table row for name
        # val is dict {"type":..., "value":...}
        value_str = '' if val is None else str(val.get('value', val))
        # find existing row
        for r in range(self.symbol_table.rowCount()):
            item = self.symbol_table.item(r, 0)
            if item and item.text() == name:
                self.symbol_table.setItem(r, 1, QTableWidgetItem(value_str))
                return
        # not found -> insert
        row = self.symbol_table.rowCount()
        self.symbol_table.insertRow(row)
        self.symbol_table.setItem(row, 0, QTableWidgetItem(name))
        self.symbol_table.setItem(row, 1, QTableWidgetItem(value_str))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ide()
    win.show()
    sys.exit(app.exec())