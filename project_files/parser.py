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
        print(self.lexemes[self.current_token_index])
        tok = self.get_current_token()
        if tok in ['NUMBR_LIT', 'NUMBAR_LIT', 'YARN_LIT', 'TROOF_LIT']:
            return {'type': 'literal', 'value': self.consume(tok)}
        elif tok == 'ID':
            return {'type': 'var', 'name': self.consume('ID')}
        elif tok in [
            'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF',
            'MOD_OF', 'BIGGR_OF', 'SMALLR_OF', 'SMOOSH',
            'BOTH_OF', 'EITHER_OF', 'WON_OF', 'ANY_OF', 'ALL_OF', 
            'NOT', 'BOTH_SAEM', 'DIFFRINT'
        ]:
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
            self.parse_variable_declaration()
        if self.get_current_token() == 'BUHBYE':
            self.consume("BUHBYE")
        else:
            raise SyntaxError("Syntax Error: Did not end declaration block with BUHBYE or added a non-declaring keyword inside of declaration block")
        
    # Parses through Statements -> <statement> <linebreak> <statements> <comment> | ε
    def parse_statements(self, stop_tokens=None):
        if stop_tokens is None:
            stop_tokens = []

        nodes = []

        while self.get_current_token() not in stop_tokens:
            if self.get_current_token() in ('KTHXBYE', 'EOF'):
                break
            nodes.append(self.parse_statement())

        return nodes
    
    def parse_statement(self):
        tok = self.get_current_token()

        if tok == "I_HAS_A":
            return self.parse_variable_declaration()
        elif tok == "VISIBLE":
            return self.parse_print()
        elif tok == "GIMMEH":
            return self.parse_gimmeh()
        elif tok == "ID":
            if self.lookahead() in ("R", "IS_NOW_A"):
                return self.parse_assignment()
            else:
                return self.parse_value_or_expression()
        elif tok == "O_RLY?":
            return self.parse_o_rly()
        elif tok == "WTF?":
            return self.parse_switch()
        elif tok == "IM_IN_YR":
            return self.parse_loop()
        else:
            raise SyntaxError(f"Unexpected token {tok}")
        
    # Parses through Variable Declarations
    def parse_variable_declaration(self):
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
        print(self.get_current_token())
        # Handles NOT
        if op == 'NOT':
            operand = self.parse_value_or_expression()
            return {
                'op': op,
                'operands': [operand]
        }
            
        operands.append(self.parse_value_or_expression())
        
        while self.get_current_token() == "AN":
            self.consume("AN")
            operands.append(self.parse_value_or_expression())
        
        # Added optional MKAY based on 05_bool.lol testcase
        if self.get_current_token() == "MKAY":
            self.consume("MKAY")
        return {'op': op, 'operands': operands}
    
    def parse_print(self):
        self.consume('VISIBLE')
        operands = [self.parse_value_or_expression()]
        
        while self.get_current_token() in ['PLUS', 'AN']:
            self.consume(self.get_current_token())
            operands.append(self.parse_value_or_expression())
        print(f"VISIBLE concatenation: {operands}")
    
    def parse_smoosh(self):
        self.consume("SMOOSH")
        operands = [self.parse_value_or_expression()] # first operand
        
        while self.get_current_token() == "AN":
            self.consume("AN")
            operands.append(self.parse_value_or_expression())
        
        return {
            "op": "SMOOSH",
            "operands": operands
        }
    def parse_assignment(self):
        # print("we in here!")
        var_name = self.consume('ID')
        tok = self.get_current_token()
        if tok == 'R':
            self.consume('R')
            # Check if its a MAEK typecast
            if self.get_current_token() in ["MAEK", "MAEK_A"]:
                self.consume(self.get_current_token())
                source_var = self.consume('ID')
                target_type = self.consume(self.get_current_token())
                value = {
                'type': 'typecast_assignment',
                'source': source_var,
                'target_type': target_type
                }
            else: # Else just normal assignment
                value = self.parse_value_or_expression()
        elif tok == 'IS_NOW_A':
            self.consume("IS_NOW_A")
            new_type = self.consume(self.get_current_token())
            #TODO: should store values in a symbol table
            '''
            example:
            self.symbol_table[var_name] = {
                'type': 'type_only_assignment',
                'new_type': new_type
            }
            '''
        else:
            # Unexpected token after variable
            row = self.rows[self.current_token_index] if self.rows else 0
            col = self.columns[self.current_token_index] if self.columns else 0
            raise SyntaxError(
                f"Unexpected token '{tok}' after variable '{var_name}' "
                f"at line {row}, column {col}"
        )
        
        
        #TODO: should store values in a symbol table
        
    def parse_gimmeh(self): #User Input
        self.consume("GIMMEH")
        
        if self.get_current_token() == 'ID':
            var_name =  self.consume("ID")
            print(f"GIMMEH input into variable: {var_name}")
            print(self.get_current_token())
        else:
            row = self.rows[self.current_token_index] if self.rows else 0
            col = self.columns[self.current_token_index] if self.columns else 0
            raise SyntaxError(
                f"Expected variable name after GIMMEH at line {row}, column {col}, "
                f"found '{self.get_current_token()}'"
            )

    def parse_o_rly(self, condition_expr=None): # Optional conditional expression in o rly
        print(self.get_current_token())
        self.consume('O_RLY')
        
        # parse YA RLY
        if self.get_current_token() == 'YA_RLY':
            self.consume('YA_RLY')
            self.parse_statement()
        
        # optional multiple MEBBE blocks
        while self.get_current_token() == 'MEBBE':
            self.consume('MEBBE')
            expr = self.parse_value_or_expression()
            self.parse_statement()
        
        # optional else block
        if self.get_current_token() == 'NO_WAI':
            self.consume('NO_WAI')
            self.parse_statement()

        self.consume('OIC')
    
    # parse statement wtf
    def parse_wtf(self):
        if self.get_current_token() in ['WTF?']:
            self.consume(self.get_current_token())

        while self.get_current_token() == 'OMG':
            self.consume('OMG')
            self.parse_literal()
            self.parse_statement()
            if self.get_current_token() == 'GTFO':
                self.consume('GTFO')

        if self.get_current_token() == 'OMGWTF':
            self.consume('OMGWTF')
            self.parse_statement()

        self.consume('OIC')

    # parses through loop
    def parse_loop(self):
        self.consume('IM_IN_YR')
        self.consume('ID')
        self.parse_statement()
        self.consume('IM_OUTTA_YR')
        self.consume('ID')

    # parses through literal values
    def parse_literal(self):
        current = self.get_current_token()
        if current in ['NUMBR_LIT', 'NUMBAR_LIT', 'YARN_LIT']:
            self.consume(current)
        else:
            raise SyntaxError('Syntax Error found.')