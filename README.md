CMSC 124 - Final Project
Section: S2L

# LOLCODE IDE – "Ang Pogi ni Sir JC LOLETPRETER"

Welcome to the LOLCODE IDE, a full-featured environment to write, run, and debug LOLCODE programs with ease. It includes syntax highlighting, a live console, variable tracking, and input handling.

---

## Features

- **Code Editor** with syntax highlighting for all LOLCODE keywords.
- **Lexeme Table** shows tokens and their classification.
- **Symbol Table** displays variables and their current values in real-time.
- **Console** for program output.
- **Input Support** for `GIMMEH` statements.
- **File Handling**: drag-and-drop, dropdown selection, or manual file path input.
- **Threaded Execution**: runs programs without freezing the IDE.

---

## Requirements

- Python 3.11 or later
- PyQt6

---

## Installation ##

1. **Clone the repository** (or download the ZIP):

git clone https://github.com/Jacarlos776/CMSC124-Project.git
cd CMSC124-Project


2. **Install dependencies:**

pip install pyqt6


3. **Ensure your lexer.py, parser.py, and interpreter.py are in the same folder as main.py.**

Running the IDE
Open a terminal/command prompt.
Navigate to the project folder.
Run the IDE:
    python main.py


4. **The IDE window will open:**

Use the editor to type or load your LOLCODE file.

Click Execute to run your program.

Use the console input bar for GIMMEH input during execution.

The lexeme and symbol tables update automatically.

## File Support ##

.lol and .txt files

Drag-and-drop directly into the IDE

Load using the dropdown or by typing the path


### Have Fun ###
