import re

class LexicalAnalyzer:
    # Token row
    lin_num = 1

    def tokenize(self, code):
        rules = [
            # OBTW ... TLDR (Multi-line)
            # The pattern is non-greedy (`.*?`) to stop at the first TLDR
            ('MULTI_CMT_SKIP', r'\bOBTW\b.*?\bTLDR\b'), 
            # BTW ... (Single-line)
            ('SINGLE_CMT_SKIP', r'\bBTW\b.*'),
            
            # --- LOLCODE Multi-Word Keywords (High Priority) ---
            ('BOTH_SAEM', r'\bBOTH\s+SAEM\b'),        # ==
            ('DIFFRINT',  r'\bDIFFRINT\b'),          # !=
            ('O_RLY',     r'\bO\s+RLY\b'),         # if
            ('YA_RLY',    r'\bYA\s+RLY\b'),          # then
            ('NO_WAI',    r'\bNO\s+WAI\b'),          # else
            ('O_RLY_END', r'\bO\s+RLY\s+END\b'),     # End of conditional
            ('I_HAS_A',   r'\bI\s+HAS\s+A\b'),       # Variable declaration
            ('IM_IN_YR',  r'\bIM\s+IN\s+YR\b'),      # Start of loop
            ('IM_OUTTA_YR', r'\bIM\s+OUTTA\s+YR\b'), # End of loop
            ('SUM_OF',    r'\bSUM\s+OF\b'),          # +
            ('DIFF_OF',   r'\bDIFF\s+OF\b'),         # -
            ('PRODUKT_OF', r'\bPRODUKT\s+OF\b'),     # *
            ('QUOSHUNT_OF', r'\bQUOSHUNT\s+OF\b'),   # /
            ('MOD_OF',    r'\bMOD\s+OF\b'),          # %
            ('UPPIN_YR'), r'\bUPPIN\s+YR\b',
            # --- LOLCODE Single-Word Keywords ---
            ('HAI',       r'\bHAI\b'),               # Start of program
            ('KTHXBYE',   r'\bKTHXBYE\b'),           # End of program
            ('VISIBLE',   r'\bVISIBLE\b'),           # Print
            ('GIMMEH',    r'\bGIMMEH\b'),            # Read/Input
            ('ITZ',       r'\bITZ\b'),               # Initialization
            ('GTFO',      r'\bGTFO\b'),              # Break / Return
            ('NOT',       r'\bNOT\b'),               # Logical NOT
            
            # --- Data/Literal Types ---
            ('YARN_LIT',  r'"[^"]*"'),               # "string value"
            ('NUMBAR_LIT', r'-?\d+\.\d+'),           # Float
            ('NUMBR_LIT', r'-?\d+'),                 # Integer
            
            # --- Identifiers and Catch-All (Lowest Priority) ---
            ('ID',        r'[a-zA-Z]\w*'),           # Variable/Function names
            ('NEWLINE',   r'\n'),                    # NEW LINE
            ('SKIP',      r'[ \t]+'),                # SPACE and TABS
            ('MISMATCH',  r'.'),                     # ANOTHER CHARACTER
        ]

        token_patterns = []
        regex_flags = 0
        # print(rules)
        for name, pattern in rules:
            if name == 'MULTI_CMT_SKIP':
                # The re.DOTALL flag allows '.' to match newlines
                regex_flags = re.DOTALL
                token_patterns.append(f'(?P<{name}>{pattern})')
            elif len(pattern) == 3 and pattern[2] == re.DOTALL:
                token_patterns.append(f'(?P<{name}>{pattern[0]})')
                regex_flags = re.DOTALL
            else:
                token_patterns.append(f'(?P<{name}>{pattern})')
        
        tokens_join = '|'.join(token_patterns)
        TOKEN_RE = re.compile(tokens_join, regex_flags)
        
        lin_start = 0
        self.lin_num = 1 # Reset line number for each call

        token = []
        lexeme = []
        row = []
        column = []

        # It analyzes the code to find the lexemes and their respective Tokens
        for m in re.finditer(TOKEN_RE, code):
            token_type = m.lastgroup
            token_lexeme = m.group(token_type)

            if token_type == 'NEWLINE':
                lin_start = m.end()
                self.lin_num += 1
            elif token_type in ['SKIP', 'SINGLE_CMT_SKIP', 'MULTI_CMT_SKIP']:
                # Skip whitespace and all comments
                if token_type == 'MULTI_CMT_SKIP':
                    # Manually update lin_num for multi-line comments
                    self.lin_num += token_lexeme.count('\n')
                continue
            elif token_type == 'MISMATCH':
                # The RuntimeError should probably be defined as a custom LexerError
                raise RuntimeError("'%s' unexpected on line %d, column %d" % (token_lexeme, self.lin_num, m.start() - lin_start))
            else:
                col = m.start() - lin_start
                column.append(col)
                token.append(token_type)
                lexeme.append(token_lexeme)
                row.append(self.lin_num)
                # To print information about a Token
                print('Token = {0}, Lexeme = \'{1}\', Row = {2}, Column = {3}'.format(token_type, token_lexeme, self.lin_num, col))

        return token, lexeme, row, column