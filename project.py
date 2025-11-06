import re

token_patterns = [
    ('KEYWORD',    r'\b(HAI|KTHXBYE|WAZZUP|BUHBYE|VISIBLE|GIMMEH|I HAS A|ITZ|R|AN|OF|BOTH|EITHER|WON|NOT|SUM|DIFF|PRODUKT|QUOSHUNT|MOD|BIGGR|SMALLR|MAEK|A|IS NOW A|SMOOSH|MKAY|O RLY\?|YA RLY|NO WAI|OIC)\b'),
    ('LITERAL',    r'"[^"]*"'),             
    ('NUMBER',     r'\b\d+(\.\d+)?\b'),    
    ('VARIDENT',   r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('COMMENT',    r'BTW[^\n]*'),           
    ('NEWLINE',    r'\n'),                  
    ('SKIP',       r'[ \t]+'),              
    ('MISMATCH',   r'.'),                   
]

regex = '|'.join(f'(?P<{name}>{pattern})')

def lex(code):
    tokens = []
    line = 1

    for mo in re.finditer(regex, code):
        



