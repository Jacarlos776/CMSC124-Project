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
        
        self.parse_statements(self)
        
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

# Personal Task 
            elif current_token == 'GIMMEH':
                self.parse_gimmeh(self)

# Personal Task
            # if/else
            elif current_token == 'O_RLY?':
                self.parse_o_rly(self)
            
            # switch
            elif current_token == 'WTF?':
                self.parse_wtf(self)
            elif current_token == "IM_IN_YR":
                self.parse_loop(self)
            # error
            
            current_token = self.get_current_token()
    
    # Parses through Variable Declarations
    def parse_variable(self):
        self.consume('I_HAS_A')

        # store varident somewhere?

        # store initial value somewhere
    
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