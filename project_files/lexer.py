import re

class LexicalAnalyzer:
    # Token row
    lin_num = 1 # Static variable to track the current line number during tokenization.

    def tokenize(self, code):
        """
        Main method to perform lexical analysis on the input source code.

        It relies on a combined regular expression (TOKEN_RE) to find the longest 
        possible match at the current position (Maximal Munch rule).

        Args:
            code (str): The raw LOLCODE source code string.

        Returns:
            tuple: Four lists representing the token stream: 
                   (token_types, token_lexemes, line_numbers, column_numbers).
        """
        rules = [
            # =======================
            #   COMMENTS (Highest Priority)
            # =======================
            # Comments must be matched first to ensure they are skipped and not tokenized as code.
        
            # Multi-line comment: OBTW ... TLDR + newline
            # r'\bOBTW\b[\s\S]*?\bTLDR\b[ \t]*\n' uses:
            # - [\s\S]*? : Non-greedy match for any character (including newlines, required for multi-line).
            # - \b...\b : Ensures word boundaries.
            ('MULTI_CMT_SKIP',  r'\bOBTW\b[\s\S]*?\bTLDR\b[ \t]*\n'),
        
            # Single-line comment: BTW ... (until newline)
            # [^\n]* matches any character except a newline. The final \n consumes the mandatory newline.
            ('SINGLE_CMT_SKIP', r'\bBTW\b[^\n]*\n'),
        
            # =======================
            #   MULTI-WORD KEYWORDS
            # =======================
            # Must be placed before single words like 'I', 'OF', 'A' to ensure the entire phrase
            # is matched as a single, unique token. \s+ allows one or more spaces between words.
        
            ('I_HAS_A',          r'\bI\s+HAS\s+A\b'),
            ('SUM_OF',           r'\bSUM\s+OF\b'),
            # ... (other multi-word keywords follow the same pattern) ...
        
            # =======================
            #   SINGLE-WORD KEYWORDS
            # =======================
            # All remaining reserved words in the language.
        
            ('HAI',         r'\bHAI\b'),
            ('KTHXBYE',     r'\bKTHXBYE\b'),
            # ... (other single-word keywords) ...
        
            # --- Newly added (missing) ---
            ('AN',          r'\bAN\b'),
            ('A',           r'\bA\b'),
            # The PLUS token is recognized as a literal '+' character for print concatenation.
            ('PLUS',        r'\+'), 
            
            # =======================
            #   LITERALS
            # =======================
            
            # YARN_LIT (String Literal) - Matches characters inside double quotes.
            ('YARN_LIT',    r'"[^"]*"'),
            # NUMBAR_LIT (Float Literal) - Must precede NUMBR_LIT to correctly match decimals.
            ('NUMBAR_LIT', r'-?\d+\.\d+'),
            # NUMBR_LIT (Integer Literal)
            ('NUMBR_LIT',   r'-?\d+'),
            # TROOF_LIT (Boolean Literal)
            ('TROOF_LIT',   r'\b(WIN|FAIL)\b'),
            # TYPE_LIT (Built-in Type Names)
            ('TYPE_LIT',    r'\b(NUMBR|NUMBAR|YARN|TROOF|BUKKIT|NOOB)\b'),
        
            # =======================
            #   IDENTIFIER & WHITESPACE
            # =======================
            
            # ID (Variable and Function Names)
            # This is the catch-all for user-defined names. It must be placed after ALL keywords 
            # and literals to prevent names (like "HAIX") from being misinterpreted as keywords.
            ('ID',          r'[a-zA-Z][a-zA-Z0-9_]*'),
        
            # NEWLINE - Critical for LOLCODE, which uses line breaks as statement terminators.
            ('NEWLINE',     r'\n+'),
        
            # SKIP - Horizontal whitespace to be ignored.
            ('SKIP',        r'[ \t]+'),
        
            # Catch-all
            # Matches any single character not matched by a previous rule, signaling a lexical error.
            ('MISMATCH',    r'.'),
        ]


        # --- Regex Compilation Setup ---
        token_patterns = []
        regex_flags = 0
        
        # Build the final massive regular expression by joining all named patterns.
        for name, pattern in rules:
            if name == 'MULTI_CMT_SKIP':
                # Set re.DOTALL flag to allow the '.' metacharacter to match newlines 
                # (essential for multi-line comment matching).
                regex_flags = re.DOTALL
                # (?P<name>...) creates a named capture group for easy type retrieval.
                token_patterns.append(f'(?P<{name}>{pattern})')
            elif len(pattern) == 3 and pattern[2] == re.DOTALL:
                # This seems to be a custom check, possibly related to how the rules were structured elsewhere.
                token_patterns.append(f'(?P<{name}>{pattern[0]})')
                regex_flags = re.DOTALL
            else:
                token_patterns.append(f'(?P<{name}>{pattern})')
        
        # Combine all patterns into a single regex using the OR operator '|'.
        tokens_join = '|'.join(token_patterns)
        # Compile the final pattern for efficiency.
        TOKEN_RE = re.compile(tokens_join, regex_flags)
        
        # --- Tokenization Execution ---
        lin_start = 0     # Character index of the start of the current line. Used for column calculation.
        self.lin_num = 1 # Reset line number for each call

        token = []    # List to store the token types (e.g., 'ID', 'SUM_OF').
        lexeme = []   # List to store the matched text (e.g., 'myVar', 'SUM OF').
        row = []      # List to store the line number.
        column = []   # List to store the column number.

        # It analyzes the code to find the lexemes and their respective Tokens
        # Iterate over all non-overlapping matches found by the compiled regex.
        for m in re.finditer(TOKEN_RE, code):
            token_type = m.lastgroup     # Name of the matching capture group (the token type).
            token_lexeme = m.group(token_type) # The text matched by the pattern.

            if token_type == 'NEWLINE':
                # Update tracking variables when a newline is matched.
                lin_start = m.end() # New line starts after the newline character(s).
                self.lin_num += 1
            elif token_type in ['SKIP', 'SINGLE_CMT_SKIP', 'MULTI_CMT_SKIP']:
                # Skip whitespace and all comments
                if token_type == 'MULTI_CMT_SKIP':
                    # Manually update lin_num for multi-line comments by counting newlines inside.
                    self.lin_num += token_lexeme.count('\n')
                continue # Do not add these to the output token stream.
            elif token_type == 'MISMATCH':
                # The RuntimeError should probably be defined as a custom LexerError
                # Unmatched character found. Report error with location data.
                col = m.start() - lin_start
                raise RuntimeError("'%s' unexpected on line %d, column %d" % (token_lexeme, self.lin_num, col))
            else:
                # Valid token found. Calculate location and record.
                col = m.start() - lin_start # Column is the match start index relative to the line start index.
                column.append(col)
                token.append(token_type)
                lexeme.append(token_lexeme)
                row.append(self.lin_num)
                # To print information about a Token
                # print('Token = {0}, Lexeme = \'{1}\', Row = {2}, Column = {3}'.format(token_type, token_lexeme, self.lin_num, col))

        return token, lexeme, row, column