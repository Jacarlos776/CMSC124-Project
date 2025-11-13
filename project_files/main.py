from lexer import LexicalAnalyzer
from parser import Parser
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
        # Read the entire file content into a single string
        code = file.read() 
    
    # Call tokenize
    token, lexeme, row, column = Analyzer.tokenize(code)

    print("\nRecognized Tokens \n", token)
    print("\nRecognized lexemes \n", lexeme)
    
    # parser = Parser(token, lexeme, row, column)
    # if (parser.parse_program()):
    #     print("Parsing successful! Program is valid.")

except RuntimeError as e:
    print(f"Lexical Error: {e}")
    sys.exit(1)
except SyntaxError as e:
    print(f"Parsing failed: {e}")
    sys.exit(1)
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    sys.exit(1)