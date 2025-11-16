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
            value = self.lexemes[self.current_token_index]
            self.current_token_index += 1
            print(f"Parsed: {current_token} -> {value}")
            return value
        else:
            # Get line and column info
            if self.current_token_index < len(self.tokens):
                row = self.rows[self.current_token_index]
                col = self.columns[self.current_token_index]
            else:
                row = self.rows[-1] if self.rows else 0 
                col = self.columns[-1] if self.columns else 0
            raise SyntaxError(
                f"Syntax error at line {row}, column {col}. "
                f"Expected '{expected_token_type}', but found '{current_token}'"
            )
    
    # Helper function for parsing values and expressions
    def parse_value_or_expression(self):
        tok = self.get_current_token()
        if tok in ['NUMBR_LIT', 'NUMBAR_LIT', 'YARN_LIT', 'TROOF_LIT']:
            return {'type': 'literal', 'value': self.consume(tok)}
        elif tok == 'ID':
            return {'type': 'var', 'name': self.consume('ID')}
        elif tok in ['SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF', 'BIGGR_OF', 'SMALLR_OF']:
            return self.parse_expression()  # recurse
        else:
            row = self.rows[self.current_token_index] if self.rows else 0
            col = self.columns[self.current_token_index] if self.columns else 0
            raise SyntaxError(
                f"Syntax error at line {row}, column {col}: unexpected token '{tok}' in expression"
            )
    # --||-- Recursive Descent Functions --||--
    
    # Parses through Program -> HAI <Statements> KTHXBYE
    def parse_program(self):
        self.consume('HAI')
        
        # Variable declaration block
        if self.get_current_token() == 'WAZZUP':
            self.parse_declaration_block()

        self.parse_statements()
        
        self.consume('KTHXBYE')
        
        if self.get_current_token() != 'EOF':
            raise SyntaxError("Syntax Error: Extra tokens found after KTHXBYE.")
        
        return True
    
    # Parses through the declaration block
    def parse_declaration_block(self):
        self.consume("WAZZUP")
        while self.get_current_token() == 'I_HAS_A':
            self.parse_variable()
        if self.get_current_token() == 'BUHBYE':
            self.consume("BUHBYE")
        else:
            raise SyntaxError("Syntax Error: Did not end declaration block with BUHBYE or added a non-declaring keyword inside of declaration block")
        
    # Parses through Statements -> <statement> <linebreak> <statements> <comment> | ε
    def parse_statements(self):
        while self.get_current_token() != 'KTHXBYE' and self.get_current_token() != 'EOF':
            # variable declaration
            if self.get_current_token() == "I_HAS_A":
                print(f"{self.get_current_token()}")
                self.parse_variable()
            # print
            elif self.get_current_token() == "VISIBLE":
                self.parse_print()
            
            # assignment
            elif self.get_current_token() == "ID":
                self.parse_assignment()

            # input
            elif self.get_current_token() == 'GIMMEH':
                self.parse_gimmeh(self)

            # if/else
            elif self.get_current_token() == 'O_RLY?':
                self.parse_o_rly(self)
                # we can add maybe block to if else parser
                # we can also add no wai block to if else
            
            # switch
            elif self.get_current_token() == 'WTF?':
                self.parse_wtf(self)
            elif self.get_current_token() == "IM_IN_YR":
                self.parse_loop(self)
            # error

    # Parses through Variable Declarations
    def parse_variable(self):
        self.consume('I_HAS_A')
        id_lexeme = self.lexemes[self.current_token_index] # Just to check for uniitalized vairables
        self.consume('ID') # might need to store variable name in the future
        
        init_value = {'kind': 'NOOB', 'value': None} # Store variable as unitialized first.
        
        # If the variable is initialized
        if self.get_current_token() == "ITZ":
            self.consume("ITZ")
            self.parse_value_or_expression()

    def parse_expression(self):
        op = self.consume(self.get_current_token()) # SUM_OF, DIFF_OF, etc.
        operands = []
        
        operands.append(self.parse_value_or_expression())
        
        while self.get_current_token() == "AN":
            self.consume("AN")
            operands.append(self.parse_value_or_expression())
        
        return {'op': op, 'operands': operands}
    
    def parse_print(self):
        self.consume('VISIBLE')
        # print(f"Stuck here? {self.get_current_token()}")
        if self.get_current_token() == 'ID':
            print(f"{self.lexemes[self.current_token_index]}")
            # print("Or here?")
            self.consume('ID')
        elif self.get_current_token() == 'YARN_LIT':
            # print("Maybe here??")
            self.consume('YARN_LIT')
        elif self.get_current_token() in ["SUM_OF", "DIFF_OF", "PRODUKT_OF", "QUOSHUNT_OF", "BIGGR_OF", "SMALLR_OF", "MOD_OF"]:
            # print("Who knows man??")
            expr = self.parse_expression()
            print(expr)
        

    def parse_assignment(self):
        current_token = self.get_current_token
        
        self.consume('ID')

        self.consume('ID') # should be storing R token, add it to lexemes
    def parse_gimmeh(self): #User Input
        #add type checker -- YARN
        self.consume('GIMMEH')
        #symbol table for input

        
    def parse_o_rly(self): #\
        current_token = self.get_current_token()
        self.consume('O_RLY')



        while current_token == 'YA_RLY':
            self.parse_ya_rly(self)
        
        while current_token == 'MEBBE':
            self.parse_mebbe(self)

        while current_token == 'NO_WAI':
            self.parse_no_wai(self)

        self.parse_oic('OIC')

    def parse_ya_rly(self):
        self.consume('ID')

    def parse_mebbe(self):
        self.consume('ID')

    def parse_no_wai(self):
        self.consume('ID')

    def parse_oic(self):
        self.consume('ID')
    
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