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
                print(f"{current_token}")
                self.parse_variable()
            # print
            elif current_token == "VISIBLE":
                self.parse_print()
            
            # assignment
            elif current_token == "ID":
                self.parse_assignment()

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

    # Parses through Variable Declarations
    def parse_variable(self):
        current_token = self.get_current_token()
        self.consume('I_HAS_A')
        self.consume('ID')

        if current_token == 'NUMBR_LIT':
            self.consume('NUMBR_LIT')
        elif current_token == 'NUMBAR_LIT':
            self.consume('NUMBAR_LIT')
        elif current_token == 'YARN_LIT':
            self.consume('YARN_LIT')
        elif current_token == '':
            print("BOO! lean!")
            #boolean
        else:
            row = self.rows[-1] if self.rows else 0 
            col = self.columns[-1] if self.columns else 0
            raise SyntaxError(
                f"Syntax error at line {row}, column {col}. "
                f"Expected a variable, but found '{current_token}'"
            )
        # store initial value somewhere
    def parse_print(self):
        current_token = self.get_current_token

        self.consume('VISIBLE')

        if current_token == 'ID':
            self.consume('ID')
        elif current_token == 'YARN_LIT':
            self.consume('YARN_LIT')

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