from lexer import LexicalAnalyzer
import sys

# -- MAIN --

# checks if number of arguments is correct
if len(sys.argv) < 2:
    print("Usage: python project.py 'file path'")
    sys.exit(1)

file_path = sys.argv[1]

Analyzer = LexicalAnalyzer()

# Lists for every list returned list from the function tokenize
token = []
lexeme = []
row = []
column = []

# Tokenize and reload of the buffer

try:
    with open(f"{file_path}", "r") as file:
        # 1. Read the entire file content into a single string
        code = file.read() 
    
    # 2. Call tokenize only once with the full code string
    token, lexeme, row, column = Analyzer.tokenize(code)

    print("\nRecognized Tokens \n", token)
    print("\nRecognized lexemes \n", lexeme)

except RuntimeError as e:
    # Handle the mismatch error gracefully
    print(f"Lexical Error: {e}")
    sys.exit(1)
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    sys.exit(1)