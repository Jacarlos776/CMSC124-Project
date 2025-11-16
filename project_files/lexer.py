import re

class LexicalAnalyzer:
    # Token row
    lin_num = 1

    def tokenize(self, code):
        rules = [
            # =======================
            #   COMMENTS (Highest Priority)
            # =======================
        
            # Multi-line comment: OBTW ... TLDR + newline
            ('MULTI_CMT_SKIP',  r'\bOBTW\b[\s\S]*?\bTLDR\b[ \t]*\n'),
        
            # Single-line comment: BTW ... (until newline)
            ('SINGLE_CMT_SKIP', r'\bBTW\b[^\n]*\n'),
        
            # =======================
            #   MULTI-WORD KEYWORDS
            # =======================
        
            ('I_HAS_A',        r'\bI\s+HAS\s+A\b'),
            ('SUM_OF',         r'\bSUM\s+OF\b'),
            ('DIFF_OF',        r'\bDIFF\s+OF\b'),
            ('PRODUKT_OF',     r'\bPRODUKT\s+OF\b'),
            ('QUOSHUNT_OF',    r'\bQUOSHUNT\s+OF\b'),
            ('MOD_OF',         r'\bMOD\s+OF\b'), # removed ITS from ITS MOD OF, moved it down to single word keywords UPDATE: ITS is probably a type of ITZ, removed for now. 
        
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
        
            # =======================
            #   SINGLE-WORD KEYWORDS
            # =======================
        
            ('HAI',        r'\bHAI\b'),
            ('KTHXBYE',    r'\bKTHXBYE\b'),
            ('WAZZUP',     r'\bWAZZUP\b'),
            ('BUHBYE',     r'\bBUHBYE\b'),
        
            ('ITZ',        r'\bITZ\b'),
            #UPDATE: ITS is probably a typo of ITZ, removed for now: ('ITS',        r'\bITS\b'), # removed ITS from ITS MOD OF regex then placed it here
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
        
            # --- Newly added (missing) ---
            ('AN',         r'\bAN\b'),
            ('A',          r'\bA\b'),
            ('IT',         r'\bIT\b'), # implicit variable in LOLCode
            ('PLUS',       r'\+'), # for concatenation in VISIBLE
            # =======================
            #   LITERALS
            # =======================
        
            ('YARN_LIT',   r'"[^"]*"'),
            ('NUMBAR_LIT', r'-?\d+\.\d+'),
            ('NUMBR_LIT',  r'-?\d+'),
            ('TROOF_LIT',  r'\b(WIN|FAIL)\b'),
            ('TYPE_LIT',   r'\b(NUMBR|NUMBAR|YARN|TROOF|BUKKIT|NOOB)\b'),
        
            # =======================
            #   IDENTIFIER & WHITESPACE
            # =======================
        
            # varident and funcident
            ('ID',         r'[a-zA-Z][a-zA-Z0-9_]*'),
        
            # NEWLINE maps to <linebreak>
            ('NEWLINE',    r'\n+'),
        
            ('SKIP',       r'[ \t]+'),
        
            # Catch-all
            ('MISMATCH',   r'.'),
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
