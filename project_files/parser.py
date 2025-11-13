# The parser class implements a Recursive Descent Parser (RDP). It works by taking the stream of tokens from the lexer then checking if the sequence conforms to the grammar we set.
# 

class Parser:
    def __init__(self, tokens, lexemes, rows, columns):
        self.tokens = tokens
        self.lexemes = lexemes
        self.rows = rows
        self.columns = columns

        # Pointer to current token 
        self.current_token_index = 0
        
    def get_current_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return 'EOF'
    
    # Matches and consumes expected token, else returns an error
    def consume(self, expected_token_type):
        current_token = self.get_current_token()
        
        if current_token == expected_token_type:
            self.current_token_index += 1
        else:
            if self.current_token_index < len(self.tokens):
                rows = self.rows[self.current_token_index]
                col = self.columns[self.current_token_index]
            else:
                row = self.rows[-1] if self.rows else 0 
                col = self.columns[-1] if self.columns else 0
            raise SyntaxError(
                f"Syntax error at line {row}, column {col}. "
                f"Expected '{expected_token_type}', but found '{current_token}'"
            )
    
    # --||-- Recursive Descent Functions --||--
    
    # Parses through Program -> HAI <Statements> KTHXBYE
    def parse_program(self):
        self.consume('HAI')
        
        self.parse_statements()
        
        self.consume('KTHXBYE')
        
        if self.get_current_token() != 'EOF':
            raise SyntaxError("Syntax Error: Extra tokens found after KTHXBYE.")
        
        return True
    
    # Parses through Statements -> <statement> <linebreak> <statements> <comment> | ε
    def parse_statements(self):
        current_token = self.get_current_token()

        while current_token != 'KTHXBYE' and current_token != 'EOF':
            # variable declaration
            if current_token == "I_HAS_A":
                self.parse_variable(self)
            # print
            elif current_token == "WAZZUP":
                self.parse_print(self)
            
            # assignment
            #elif current_token ==

            # input
            elif current_token == 'GIMMEH':
                self.parse_gimmeh(self)

            # if/else
            elif current_token == 'O_RLY?':
                self.parse_o_rly(self)
                # we can add maybe block to if else parser
                # we can also add no wai block to if else
            
            # switch
            elif current_token == 'WTF?':
                self.parse_wtf(self)
            elif current_token == "IM_IN_YR":
                self.parse_loop(self)
            # error
            
            current_token = self.get_current_token()

    # parse statement wtf
    def parse_wtf(self):
        if self.get_current_token() in ['WTF?']:
            self.consume(self.get_current_token())

        while self.get_current_token() == 'OMG':
            self.consume('OMG')
            self.parse_literal()
            self.parse_statements()
            if self.get_current_token() == 'GTFO':
                self.consume('GTFO')

        if self.get_current_token() == 'OMGWTF':
            self.consume('OMGWTF')
            self.parse_statements()

        self.consume('OIC')

    # parses through loop
    def parse_loop(self):
        self.consume('IM_IN_YR')
        self.consume('ID')
        self.parse_statements()
        self.consume('IM_OUTTA_YR')
        self.consume('ID')

    # parses through literal values
    def parse_literal(self):
        current = self.get_current_token()
        if current in ['NUMBR_LIT', 'NUMBAR_LIT', 'YARN_LIT']:
            self.consume(current)
        else:
            raise SyntaxError('Syntax Error found.')