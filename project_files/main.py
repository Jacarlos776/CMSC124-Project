from lexer import LexicalAnalyzer
from parser import Parser
from interpreter import Interpreter
import sys

# -- MAIN --

# checks if number of arguments is correct
# The script expects the file path as the first command-line argument (sys.argv[1]).
if len(sys.argv) < 2:
    print("Usage: python project.py 'file path'")
    sys.exit(1) # Exit if the file path is missing.

file_path = sys.argv[1] # Retrieve the path to the LOLCODE source file.

# Initialize the Lexical Analyzer (Lexer).
Analyzer = LexicalAnalyzer()

# Lists for every list returned list from the function tokenize
# These lists will store the output of the Lexical Analyzer.
token = []    # List of token types (e.g., 'ID', 'HAI').
lexeme = []   # List of matched text (e.g., 'x', 'HAI').
row = []      # List of line numbers.
column = []   # List of column numbers.

# Tokenize and reload of the buffer
try:
    ## 1. File Loading and Lexical Analysis Phase (Source Code -> Tokens)
    
    with open(f"{file_path}", "r") as file:
        # Read the entire file content into a single string for the lexer.
        code = file.read() 
    
    # Call tokenize: Converts the raw code string into a stream of tokens.
    token, lexeme, row, column = Analyzer.tokenize(code)

    # print("\nRecognized Tokens \n", token)
    # print("\nRecognized lexemes \n", lexeme)
    
    ## 2. Parsing Phase (Tokens -> AST)

    # Initialize the Parser with the token stream provided by the Lexer.
    parser = Parser(token, lexeme, row, column)
    try:
        # Call parse_program: This function builds the Abstract Syntax Tree (AST).
        ast = parser.parse_program()
        print("\nParsing successful! Program is valid.\n")
        
        # Optional: Print the resulting AST structure (useful for debugging the parser).
        print("\n=== AST OUTPUT ===")
        print(ast)
    except SyntaxError as e:
        # Catches syntax errors (grammatical errors) found during parsing.
        print("Parsing failed...")
        print(e)
        # We allow execution to proceed only if parsing was successful, otherwise, an error would occur in the next step.
        sys.exit(1) # Exit the program if the parsing failed.
    
    ## 3. Interpretation Phase (AST Execution)

    # Initialize the Interpreter with the generated AST.
    interpreter = Interpreter(ast)
    # Call run: Begins the execution of the program statements defined in the AST.
    interpreter.run()

# --- Error Handling ---

except RuntimeError as e:
    # Catches errors raised by the Lexer (e.g., unexpected characters/MISMATCH).
    print(f"Lexical Error: {e}")
    sys.exit(1)
except SyntaxError as e:
    # Catches general parsing errors if not caught by the inner try-except (e.g., if re-raising).
    print(f"Parsing failed: {e}")
    sys.exit(1)
except FileNotFoundError:
    # Handles the case where the input file path is invalid.
    print(f"Error: File not found at {file_path}")
    sys.exit(1)