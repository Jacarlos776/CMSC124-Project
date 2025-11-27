import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QListWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QTextEdit, QPushButton, QMessageBox, QFrame, QInputDialog,
    QLineEdit
)
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtCore import Qt, QProcess

# function that will highlight LOL Code syntax
class highlight(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        keywords = [
            "HAI", "KTHXBYE", "I HAS A", "VISIBLE", "GIMMEH",
            "ITZ", "R", "SUM OF", "DIFF OF", "PRODUKT OF",
            "QUOSHUNT OF", "MOD OF", "BIGGR OF", "SMALLR OF",
            "O RLY?", "YA RLY", "NO WAI", "OIC", "BTW", "OBTW", "TLDR"
            "BOTH OF", "EITHER OF", "WON OF", "ANY OF", "ALL OF", "BOTH SAEM", 
            "DIFFRINT", "IS NOW A", "O RLY", "NO WAI", "YA RLY", "IM IN YR", 
            "IM OUTTA YR", "HOW IZ I", "IF U SAY SO", "FOUND YR", "I IZ", "MAEK A",
            "WAZZUP", "BUHBYE", "ITZ", "R", "VISIBLE", "GIMMEH", "SMOOSH", "MAEK", 
            "NOT", "MEBBE", "OIC", "WTF", "OMG", "OMGWTF", "UPPIN", "NERFIN", "YR", 
            "TIL", "WILE", "GTFO", "MKAY"
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
        self.run_all_button = QPushButton("Run All")
        self.run_all_button.clicked.connect(self.run_all_tests)

        top_buttons.addWidget(self.save_button)
        top_buttons.addWidget(self.delete_button)
        top_buttons.addWidget(self.run_button)
        top_buttons.addWidget(self.run_all_button)
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

        # input line for programs that request stdin (GIMMEH)
        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Type input here and press Enter to send to running program")
        self.input_line.returnPressed.connect(self.send_input_to_process)
        input_layout.addWidget(self.input_line)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_input_to_process)
        input_layout.addWidget(self.send_button)
        right_panel.addLayout(input_layout)

        # process state
        self.proc = None
        self.run_queue = []

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
    def run_file(self):
        # save current file first
        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No File Selected", "Please select a file to run.")
            return

        filename = item.text()
        filepath = self.file_paths[filename]

        # write current editor contents to disk
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file: {e}")
            return

        self.terminal.append(f"Running {filename}...")

        # run the project's main runner (main.py) using the same Python interpreter
        main_path = os.path.join(os.path.dirname(__file__), "main.py")
        if not os.path.exists(main_path):
            self.terminal.append("Error: main.py not found in project_files.")
            return

        # if a process is already running, ask to terminate it first
        if self.proc is not None and self.proc.state() == QProcess.ProcessState.Running:
            resp = QMessageBox.question(self, "Process Running", "A program is already running. Stop it and start a new run?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp != QMessageBox.StandardButton.Yes:
                return
            self.proc.kill()

        # start the process using QProcess for live IO
        try:
            # ensure file saved already
            code_text = self.editor.toPlainText()

            self.terminal.append(f"----- Running {filename} -----")

            main_path = os.path.join(os.path.dirname(__file__), "main.py")

            # configure QProcess
            self.proc = QProcess(self)
            self.proc.setProgram(sys.executable)
            self.proc.setArguments([main_path, filepath])
            self.proc.setWorkingDirectory(os.path.dirname(main_path))
            self.proc.setProcessEnvironment(self.proc.processEnvironment())
            self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

            self.proc.readyReadStandardOutput.connect(self._on_proc_output)
            self.proc.readyReadStandardError.connect(self._on_proc_error)
            self.proc.finished.connect(self._on_proc_finished)

            # start
            self.proc.start()
            if not self.proc.waitForStarted(3000):
                self.terminal.append("Failed to start process.")
                self.proc = None
                return

            # if code expects a simple single GIMMEH, prompt immediately
            if "GIMMEH" in code_text.upper():
                self.terminal.append("Program requested input (GIMMEH). Type into the input box and press Enter to send.")

        except Exception as e:
            self.terminal.append(f"Error starting process: {e}")

    # function for delete button
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

    # QProcess output handlers and input forwarding
    def _on_proc_output(self):
        if not self.proc:
            return
        data = self.proc.readAllStandardOutput().data().decode()
        if data:
            self.terminal.append(data)

    def _on_proc_error(self):
        if not self.proc:
            return
        data = self.proc.readAllStandardError().data().decode()
        if data:
            self.terminal.append(data)

    def _on_proc_finished(self, exitCode, exitStatus):
        self.terminal.append(f"Process finished with exit code {exitCode}")
        self.proc = None

    def send_input_to_process(self):
        text = self.input_line.text()
        if not self.proc or self.proc.state() != QProcess.ProcessState.Running:
            self.terminal.append("No running program to send input to.")
            return
        # write text + newline to stdin
        try:
            self.proc.write((text + "\n").encode())
            self.proc.waitForBytesWritten(1000)
            self.input_line.clear()
        except Exception as e:
            self.terminal.append(f"Failed to send input: {e}")

    # run all test
    def run_all_tests(self):
        # build queue of test cases 01..07 from test_cases folder
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        test_dir = os.path.join(project_root, "test_cases")
        if not os.path.exists(test_dir):
            QMessageBox.critical(self, "Error", f"test_cases folder not found at {test_dir}")
            return

        self.run_queue = []
        for i in range(1, 8):
            pattern = os.path.join(test_dir, f"{i:02d}_*.lol")
            # glob manually
            import glob
            matches = glob.glob(pattern)
            if matches:
                # take first match
                self.run_queue.append(matches[0])
            else:
                self.terminal.append(f"Test case for {i:02d} not found.")

        if not self.run_queue:
            QMessageBox.information(self, "Run All", "No test cases found to run.")
            return

        # disable run buttons while running
        self.run_button.setEnabled(False)
        self.run_all_button.setEnabled(False)

        # start first
        self._start_next_in_queue()

    def _start_next_in_queue(self):
        if not self.run_queue:
            self.terminal.append("All queued tests finished.")
            self.run_button.setEnabled(True)
            self.run_all_button.setEnabled(True)
            return

        next_path = self.run_queue.pop(0)
        filename = os.path.basename(next_path)
        # load file into editor and save to ensure current contents run
        with open(next_path, "r", encoding="utf-8") as f:
            self.editor.setPlainText(f.read())

        # save file back to disk (it already is) but ensure file_list contains it
        if filename not in self.file_paths:
            self.file_paths[filename] = next_path
            self.file_list.addItem(filename)

        # start process for this test case
        # reuse run_file's process starting logic but without asking
        # If a process is already running, wait for it to finish (shouldn't happen here)
        if self.proc is not None and self.proc.state() == QProcess.ProcessState.Running:
            self.terminal.append("Waiting for previous process to finish...")
            return

        # start process
        main_path = os.path.join(os.path.dirname(__file__), "main.py")
        self.terminal.append(f"----- Running {filename} -----")
        self.proc = QProcess(self)
        self.proc.setProgram(sys.executable)
        self.proc.setArguments([main_path, next_path])
        self.proc.setWorkingDirectory(os.path.dirname(main_path))
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._on_proc_output)
        self.proc.readyReadStandardError.connect(self._on_proc_error)
        # when finished, start next
        def finished_and_continue(code, status):
            self.terminal.append(f"Finished {filename} with code {code}")
            self.proc = None
            # small delay could be added; directly start next
            self._start_next_in_queue()

        self.proc.finished.connect(finished_and_continue)
        self.proc.start()
        if not self.proc.waitForStarted(3000):
            self.terminal.append("Failed to start process for " + filename)
            self.proc = None
            self._start_next_in_queue()

# main
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ide()
    window.show()
    sys.exit(app.exec())
