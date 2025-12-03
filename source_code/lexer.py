import re

class LexicalAnalyzer:
    # Global line counter for tokens
    lin_num = 1

    def tokenize(self, code):
        # ======================
        # TOKEN DEFINITIONS
        # ======================
        # Each tuple = (TOKEN_NAME, REGEX_PATTERN)
        # The ordering matters: earlier rules have higher priority.
        rules = [
            # =======================
            #   COMMENTS (Highest Priority)
            #   These must be matched BEFORE other tokens.
            # =======================

            # Multi-line comment: matches OBTW ... TLDR including all newlines.
            # Uses lazy quantifier to match smallest block.
            ('MULTI_CMT_SKIP',  r'\bOBTW\b[\s\S]*?\bTLDR\b[ \t]*\n'),

            # Single-line comment: BTW until newline.
            ('SINGLE_CMT_SKIP', r'\bBTW\b[^\n]*\n'),

            # =======================
            #   MULTI-WORD KEYWORDS
            #   (Important to match BEFORE ID)
            # =======================

            ('I_HAS_A',        r'\bI\s+HAS\s+A\b'),
            ('SUM_OF',         r'\bSUM\s+OF\b'),
            ('DIFF_OF',        r'\bDIFF\s+OF\b'),
            ('PRODUKT_OF',     r'\bPRODUKT\s+OF\b'),
            ('QUOSHUNT_OF',    r'\bQUOSHUNT\s+OF\b'),
            ('MOD_OF',         r'\bMOD\s+OF\b'),

            ('BIGGR_OF',       r'\bBIGGR\s+OF\b'),
            ('SMALLR_OF',      r'\bSMALLR\s+OF\b'),

            ('BOTH_OF',        r'\bBOTH\s+OF\b'),
            ('EITHER_OF',      r'\bEITHER\s+OF\b'),
            ('WON_OF',         r'\bWON\s+OF\b'),
            ('ANY_OF',         r'\bANY\s+OF\b'),
            ('ALL_OF',         r'\bALL\s+OF\b'),

            ('BOTH_SAEM',      r'\bBOTH\s+SAEM\b'),
            ('DIFFRINT',       r'\bDIFFRINT\b'),
            ('IS_NOW_A',       r'\bIS\s+NOW\s+A\b'),

            ('O_RLY',          r'\bO\s+RLY\?'),
            ('NO_WAI',         r'\bNO\s+WAI\b'),
            ('YA_RLY',         r'\bYA\s+RLY\b'),

            ('IM_IN_YR',       r'\bIM\s+IN\s+YR\b'),
            ('IM_OUTTA_YR',    r'\bIM\s+OUTTA\s+YR\b'),

            ('HOW_IZ_I',       r'\bHOW\s+IZ\s+I\b'),
            ('IF_U_SAY_SO',    r'\bIF\s+U\s+SAY\s+SO\b'),

            ('FOUND_YR',       r'\bFOUND\s+YR\b'),
            ('I_IZ',           r'\bI\s+IZ\b'),
            ('MAEK_A', r'\bMAEK A\b'), # Variation seen in test cases.

            # =======================
            #   SINGLE-WORD KEYWORDS
            # =======================

            ('HAI',        r'\bHAI\b'),
            ('KTHXBYE',    r'\bKTHXBYE\b'),
            ('WAZZUP',     r'\bWAZZUP\b'),
            ('BUHBYE',     r'\bBUHBYE\b'),

            ('ITZ',        r'\bITZ\b'),
            ('R',          r'\bR\b'),
            ('VISIBLE',    r'\bVISIBLE\b'),
            ('GIMMEH',     r'\bGIMMEH\b'),

            ('SMOOSH',     r'\bSMOOSH\b'),
            ('MAEK',       r'\bMAEK\b'),

            ('NOT',        r'\bNOT\b'),
            ('MEBBE',      r'\bMEBBE\b'),
            ('OIC',        r'\bOIC\b'),

            ('WTF',        r'\bWTF\?'),
            ('OMG',        r'\bOMG\b'),
            ('OMGWTF',     r'\bOMGWTF\b'),

            ('UPPIN',      r'\bUPPIN\b'),
            ('NERFIN',     r'\bNERFIN\b'),

            ('YR',         r'\bYR\b'),
            ('TIL',        r'\bTIL\b'),
            ('WILE',       r'\bWILE\b'),
            ('GTFO',       r'\bGTFO\b'),
            ('MKAY',       r'\bMKAY\b'),

            # Missing but required words
            ('AN',         r'\bAN\b'),
            ('A',          r'\bA\b'),

            # Plus operator for string concatenation
            ('PLUS',       r'\+'),

            # =======================
            #   LITERALS (Strings, Numbers, Booleans, Types)
            # =======================

            ('YARN_LIT',   r'"[^"]*"'),     # Basic string literal
            ('NUMBAR_LIT', r'-?\d+\.\d+'),  # Decimal number
            ('NUMBR_LIT',  r'-?\d+'),       # Integer
            ('TROOF_LIT',  r'\b(WIN|FAIL)\b'),
            ('TYPE_LIT',   r'\b(NUMBR|NUMBAR|YARN|TROOF|BUKKIT|NOOB)\b'),

            # =======================
            #   IDENTIFIER & WHITESPACE
            # =======================

            ('ID',         r'[a-zA-Z][a-zA-Z0-9_]*'),  # Variable / function identifiers

            # NEWLINE increases line count
            ('NEWLINE',    r'\n+'),

            ('SKIP',       r'[ \t]+'),  # spaces + tabs only

            # Catch-all for illegal characters
            ('MISMATCH',   r'.'),
        ]

        # Compile all token rules into a single regex
        token_patterns = []
        regex_flags = 0  # default: no special flags

        for name, pattern in rules:
            if name == 'MULTI_CMT_SKIP':
                # MULTI_CMT_SKIP needs DOTALL so that `.` matches newlines
                regex_flags = re.DOTALL
                token_patterns.append(f'(?P<{name}>{pattern})')

            elif len(pattern) == 3 and pattern[2] == re.DOTALL:
                # Unused branch but preserved by author
                token_patterns.append(f'(?P<{name}>{pattern[0]})')
                regex_flags = re.DOTALL

            else:
                # Standard case
                token_patterns.append(f'(?P<{name}>{pattern})')

        # Combine all patterns into one master regex with named groups
        tokens_join = '|'.join(token_patterns)
        TOKEN_RE = re.compile(tokens_join, regex_flags)

        # Track start of lines for column calculation
        lin_start = 0
        self.lin_num = 1  # reset line counter

        # Output lists
        token = []
        lexeme = []
        row = []
        column = []

        # =======================
        #   LEXING LOOP
        #   Iterate through matches sequentially
        # =======================
        for m in re.finditer(TOKEN_RE, code):
            token_type = m.lastgroup        # matched token name
            token_lexeme = m.group(token_type)  # actual text

            # Handle NEWLINE → update line & column tracking
            if token_type == 'NEWLINE':
                lin_start = m.end()
                self.lin_num += 1

            # Skip whitespace and comments
            elif token_type in ['SKIP', 'SINGLE_CMT_SKIP', 'MULTI_CMT_SKIP']:

                # MULTI_CMT_SKIP may contain multiple newlines → update counter
                if token_type == 'MULTI_CMT_SKIP':
                    self.lin_num += token_lexeme.count('\n')

                continue  # do not record token

            # Invalid token → throw error
            elif token_type == 'MISMATCH':
                raise RuntimeError(
                    "'%s' unexpected on line %d, column %d"
                    % (token_lexeme, self.lin_num, m.start() - lin_start)
                )

            else:
                # Valid token → compute column index
                col = m.start() - lin_start
                column.append(col)
                token.append(token_type)
                lexeme.append(token_lexeme)
                row.append(self.lin_num)

                # Debug print hook (commented out)
                # print(f"Token={token_type}, Lexeme='{token_lexeme}', Row={self.lin_num}, Column={col}")

        # Return four aligned lists containing token information
        return token, lexeme, row, column
