# Import modules
from lexer import LexicalAnalyzer  # Lexical analyzer (tokenizer)
from parser import Parser           # Recursive Descent Parser
from interpreter import Interpreter  # Interpreter to execute AST
import sys                          # System module for command-line args

# main.py
import sys
from PyQt6.QtWidgets import QApplication
import ide  # replace 'ide_file' with the filename where IDE class is defined

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ide.ide()
    window.show()
    sys.exit(app.exec())



# -- MAIN --

# Check if the user provided a file path as command-line argument
if len(sys.argv) < 2:
    print("Usage: python project.py 'file path'")  # Show usage instructions
    sys.exit(1)                                   # Exit program if no file path

file_path = sys.argv[1]  # Get the file path from arguments

# Initialize the lexical analyzer
Analyzer = LexicalAnalyzer()

# Prepare empty lists to store results of tokenization
token = []   # List of token types returned by lexer
lexeme = []  # List of actual lexemes (strings from code)
row = []     # List of row numbers for each token (for error reporting)
column = []  # List of column numbers for each token

# Tokenize and parse the source code
try:
    # Open the source file and read all its content
    with open(f"{file_path}", "r") as file:
        code = file.read()  # Read entire file as a single string

    # Tokenize the code: returns token types, lexemes, rows, and columns
    token, lexeme, row, column = Analyzer.tokenize(code)

    # Uncomment to debug the lexer output
    # print("\nRecognized Tokens \n", token)
    # print("\nRecognized lexemes \n", lexeme)
    
    # Initialize the parser with tokenized input
    parser = Parser(token, lexeme, row, column)
    try:
        # Parse the program and build the AST
        ast = parser.parse_program()
        print("\nParsing successful! Program is valid.\n")
        print("\n=== AST OUTPUT ===")
        print(ast)  # Print the AST (Abstract Syntax Tree)
    except SyntaxError as e:
        # Catch syntax errors from parser
        print("Parsing failed...")
        print(e)
    
    # Initialize the interpreter with the AST and run it
    interpreter = Interpreter(ast)
    interpreter.run()

# Handle errors
except RuntimeError as e:
    # RuntimeError usually from lexer
    print(f"Lexical Error: {e}")
    sys.exit(1)
except SyntaxError as e:
    # Syntax errors from parser
    print(f"Parsing failed: {e}")
    sys.exit(1)
except FileNotFoundError:
    # If file path is invalid
    print(f"Error: File not found at {file_path}")
    sys.exit(1)
