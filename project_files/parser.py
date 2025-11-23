# The parser class implements a Recursive Descent Parser (RDP). It works by taking the stream of tokens from the lexer then checking if the sequence conforms to the grammar we set.
# 
from dataclasses import dataclass, field
from typing import Any, List, Optional

# === || AST node classes || ===
@dataclass
class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    declarations: List[ASTNode]
    statements: List[ASTNode]
@dataclass
class VarDecl(ASTNode):
    name: str
    init: Optional[ASTNode] # None means NOOB

@dataclass
class Assignment(ASTNode):
    target: str
    value: ASTNode

@dataclass
class TypeCastAssignment(ASTNode):
    target: str
    source: str
    target_type: str

@dataclass
class TypeOnlyAssignment(ASTNode):
    target: str
    new_type: str

@dataclass
class Gimmeh(ASTNode):
    target: str

@dataclass
class Print(ASTNode):
    operands: List[ASTNode]

@dataclass
class IfStmt(ASTNode):
    condition: Optional[ASTNode] # condition before O_RLY?, optional
    ya_block: List[ASTNode]
    mebbe_blocks: List[tuple]
    nowai_block: Optional[List[ASTNode]]

@dataclass
class Loop(ASTNode):
    name: str
    mode: str # added this for UPPIN and NERFIN
    iterator: str
    condition: Optional[ASTNode] # conditional loops
    body: List[ASTNode]

@dataclass
class SwitchCase(ASTNode):
    cases: List[tuple]
    default: Optional[List[ASTNode]]

@dataclass
class Expression(ASTNode):
    op: Optional[str] # e.g. 'SUM_OF', 'NOT', None for plain literal/var
    operands: List[Any] = field(default_factory=list)

@dataclass
class Literal(ASTNode):
    value: Any

@dataclass
class VarRef(ASTNode):
    name: str

# Added for 10_functions.lol testcase
@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]
    return_expr: Optional[ASTNode]

@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]

@dataclass
class ReturnStmt(ASTNode):
    value: ASTNode

@dataclass
class BreakStmt(ASTNode):
    pass
# === || Parser || ===
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
    
    # Helper function to look at next token    
    def lookahead(self, k=1):
        i = self.current_token_index + k
        if i < len(self.tokens):
            return self.tokens[i]
        return 'EOF'
    
    # Matches and consumes expected token, else returns an error
    def consume(self, expected_token_type):
        current_token = self.get_current_token()

        if expected_token_type is None or current_token == expected_token_type:
            value = self.lexemes[self.current_token_index]
            self.current_token_index += 1
            # print(f"Parsed: {current_token} -> {value}")
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

    # --||-- Recursive Descent Functions --||--
    
    # Parses through Program -> HAI <Statements> KTHXBYE
    def parse_program(self):
        self.consume('HAI')
        
        # Variable declaration block
        if self.get_current_token() == 'WAZZUP':
            declarations = self.parse_declaration_block()
        
        # Functions
        functions = []
        while self.get_current_token() == 'HOW_IZ_I':
            functions.append(self.parse_function_def())
        
        # Actual main code
        statements = self.parse_statements()
        
        self.consume('KTHXBYE')
        
        if self.get_current_token() != 'EOF':
            raise SyntaxError("Syntax Error: Extra tokens found after KTHXBYE.")
        
        return Program(declarations=declarations, statements=statements)
    
    # Parses through the declaration block
    def parse_declaration_block(self):
        self.consume("WAZZUP")
        decls = []
        while self.get_current_token() == 'I_HAS_A':
            decls.append(self.parse_variable_declaration())
        if self.get_current_token() == 'BUHBYE':
            self.consume("BUHBYE")
        else:
            raise SyntaxError("Syntax Error: Did not end declaration block with BUHBYE or added a non-declaring keyword inside of declaration block")
        return decls
        
    # Parses through Statements -> <statement> <linebreak> <statements> <comment> | ε
    def parse_statements(self, stop_tokens: Optional[List[str]] = None):
        if stop_tokens is None:
            stop_tokens = []

        nodes = []
        while True:
            tok = self.get_current_token()
            if tok in ('KTHXBYE', 'EOF') or tok in stop_tokens:
                break
            nodes.append(self.parse_statement())
        return nodes
    
    def parse_statement(self):
        tok = self.get_current_token()

        if tok == "I_HAS_A":
            return self.parse_variable_declaration()
        elif tok == "HOW_IZ_I":
            return self.parse_function_def()
        elif tok == "FOUND_YR":
            self.consume("FOUND_YR")
            return ReturnStmt(value=self.parse_value_or_expression())
        elif tok == "GTFO":
            self.consume("GTFO")
            return BreakStmt()
        elif tok == "I_IZ":
            return self.parse_function_call()
        elif tok == "VISIBLE":
            return self.parse_print()
        elif tok == "GIMMEH":
            return self.parse_gimmeh()
        elif tok == "ID":
            if self.lookahead() in ("R", "IS_NOW_A"):
                return self.parse_assignment()
            else:
                expr = self.parse_expression()
                return expr
        if tok in (
            'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF', 'BIGGR_OF', 'SMALLR_OF',
            'SMOOSH', 'BOTH_OF', 'EITHER_OF', 'WON_OF', 'ANY_OF', 'ALL_OF', 'NOT', 'BOTH_SAEM', 'DIFFRINT'
        ):
            expr = self.parse_expression()
            return expr
        
        elif tok == "O_RLY":
            return self.parse_o_rly()
        elif tok == "WTF":
            return self.parse_wtf()
        elif tok == "IM_IN_YR":
            return self.parse_loop()
        else:
            raise SyntaxError(f"Unexpected token {tok}")
        
    # Parses through Variable Declarations
    def parse_variable_declaration(self):
        self.consume('I_HAS_A')
        id_lexeme = self.lexemes[self.current_token_index] # Just to check for uniitalized vairables
        name = self.consume('ID') # might need to store variable name in the future
        
        init_node = None        
        # If the variable is initialized
        if self.get_current_token() == "ITZ":
            self.consume("ITZ")
            init_node = self.parse_value_or_expression()
            
        return VarDecl(name=name, init=init_node)
    
    def parse_value_or_expression(self):
        tok = self.get_current_token()
        if tok in ('NUMBR_LIT', 'NUMBAR_LIT', 'YARN_LIT', 'TROOF_LIT'):
            val = self.consume(tok)
            return Literal(value=val)
        if tok == 'ID':
            name = self.consume('ID')
            return VarRef(name=name)
        if tok == 'SMOOSH':
            return self.parse_smoosh()
        if tok in ('SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF',
            'BIGGR_OF', 'SMALLR_OF', 'BOTH_OF', 'EITHER_OF', 'WON_OF',
            'ANY_OF', 'ALL_OF', 'NOT', 'BOTH_SAEM', 'DIFFRINT'):
            return self.parse_expression()
        # unexpected token
        row = self.rows[self.current_token_index] if self.current_token_index < len(self.rows) else 0
        col = self.columns[self.current_token_index] if self.current_token_index < len(self.columns) else 0
        raise SyntaxError(f"Unexpected token '{tok}' in expression at line {row}, col {col}")
    
    def parse_expression(self):
        op_tok = self.get_current_token()
        
        # If the expression begins with an operator
        if op_tok in ('NOT', 'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF',
                    'BIGGR_OF', 'SMALLR_OF', 'SMOOSH', 'BOTH_OF', 'EITHER_OF', 'WON_OF',
                    'ANY_OF', 'ALL_OF', 'BOTH_SAEM', 'DIFFRINT'):
            op = self.consume(op_tok) # SUM_OF, DIFF_OF, etc.
            # Handles NOT
            if op == 'NOT':
                operand = self.parse_value_or_expression()
                return Expression(op=op, operands=[operand])
                
            operands = [self.parse_value_or_expression()]
            while self.get_current_token() == "AN":
                self.consume("AN")
                operands.append(self.parse_value_or_expression())
            
            # Added optional MKAY based on 05_bool.lol testcase
            if self.get_current_token() == "MKAY":
                self.consume("MKAY")
            return Expression(op=op, operands=operands)
        
        # Else expression can also be a value (literal or var)
        return self.parse_value_or_expression()
    
    def parse_print(self):
        self.consume('VISIBLE')
        operands = [self.parse_value_or_expression()]
        
        while self.get_current_token() in ['PLUS', 'AN']:
            self.consume(self.get_current_token())
            operands.append(self.parse_value_or_expression())
        return Print(operands=operands)
    
    def parse_smoosh(self):
        self.consume("SMOOSH")
        operands = [self.parse_value_or_expression()] # first operand
        
        while self.get_current_token() == "AN":
            self.consume("AN")
            operands.append(self.parse_value_or_expression())
        if self.get_current_token() == 'MKAY':
            self.consume('MKAY')
            
        return Expression(op='SMOOSH', operands=operands)
    def parse_assignment(self):
        # print("we in here!")
        target = self.consume('ID')
        tok = self.get_current_token()
        if tok == 'R':
            self.consume('R')
            if self.get_current_token() in ('MAEK', 'MAEK_A'):
                self.consume(self.get_current_token())
                source = self.consume('ID')
                target_type = self.consume(self.get_current_token())
                return TypeCastAssignment(target=target, source=source, target_type=target_type)
            else:
                value = self.parse_value_or_expression()
                return Assignment(target=target, value=value)
        elif tok == 'IS_NOW_A':
            self.consume('IS_NOW_A')
            new_type = self.consume(self.get_current_token())
            return TypeOnlyAssignment(target=target, new_type=new_type)
        else:
            row = self.rows[self.current_token_index] if self.current_token_index < len(self.rows) else 0
            col = self.columns[self.current_token_index] if self.current_token_index < len(self.columns) else 0
            raise SyntaxError(f"Unexpected token '{tok}' after variable '{target}' at line {row}, col {col}")
        
    def parse_gimmeh(self): #User Input
        self.consume("GIMMEH")
        
        if self.get_current_token() == 'ID':
            target =  self.consume("ID")
            # print(f"GIMMEH input into variable: {var_name}")
            # print(self.get_current_token())
            return Gimmeh(target=target)
        else:
            row = self.rows[self.current_token_index] if self.rows else 0
            col = self.columns[self.current_token_index] if self.columns else 0
            raise SyntaxError(
                f"Expected variable name after GIMMEH at line {row}, column {col}, "
                f"found '{self.get_current_token()}'"
            )

    def parse_o_rly(self, condition_expr: Optional[ASTNode] = None): # Optional conditional expression in o rly
        # print(self.get_current_token())
        self.consume('O_RLY')
        
        # parse YA RLY
        if self.get_current_token() == 'YA_RLY':
            self.consume('YA_RLY')
            ya_block = self.parse_statements(stop_tokens=['MEBBE', 'NO_WAI', 'OIC'])
        
        # optional multiple MEBBE blocks
        mebbe_blocks = []
        while self.get_current_token() == 'MEBBE':
            self.consume('MEBBE')
            mebbe_cond = self.parse_value_or_expression()
            mebbe_body = self.parse_statements(stop_tokens=['MEBBE', 'NO_WAI', 'OIC'])
            mebbe_blocks.append((mebbe_cond, mebbe_body))
        
        # optional else block
        nowai_block = None
        if self.get_current_token() == 'NO_WAI':
            self.consume('NO_WAI')
            nowai_block = self.parse_statements(stop_tokens=['OIC'])

        self.consume('OIC')
        return IfStmt(condition=condition_expr, ya_block=ya_block, mebbe_blocks=mebbe_blocks, nowai_block=nowai_block)
    
    # parse statement wtf
    def parse_wtf(self):
        if self.get_current_token() in ['WTF']:
            self.consume(self.get_current_token())
        
        cases = []
        default = None
        while self.get_current_token() == 'OMG':
            self.consume('OMG')
            lit = self.parse_value_or_expression()
            body = self.parse_statements(stop_tokens=['OMG', 'OMGWTF', 'OIC'])
            cases.append((lit, body))
            if self.get_current_token() == 'GTFO':
                self.consume('GTFO')
        if self.get_current_token() == 'OMGWTF':
            self.consume('OMGWTF')
            default = self.parse_statements(stop_tokens=['OIC'])

        self.consume('OIC')
        return SwitchCase(cases=cases, default=default)

    # parses through loop
    def parse_loop(self):
        self.consume('IM_IN_YR')
        loop_name = self.consume("ID")

        mode = None
        iterator = None
        condition = None
        
        # Optional UPPIN / NERFIN
        if self.get_current_token() in ("UPPIN", "NERFIN"):
            mode = self.consume(self.get_current_token())  # UPPIN or NERFIN
            self.consume("YR")
            iterator = self.consume("ID")
            
        # Optional WILE or TIL + condition expression
        if self.get_current_token() == "WILE":
            self.consume("WILE")
            condition = self.parse_value_or_expression()
        elif self.get_current_token() == "TIL":
            self.consume("TIL")
            condition = self.parse_value_or_expression()
            
        # loop through body
        body = self.parse_statements(stop_tokens=["IM_OUTTA_YR"])
        
        # end of loop
        self.consume("IM_OUTTA_YR")
        end_name = self.consume("ID")
        
        # check if loop names match
        if end_name != loop_name:
            raise SyntaxError(f"Loop name mismatch: started {loop_name}, ended {end_name}")
        
        return Loop(
            name=loop_name,
            mode=mode,
            iterator=iterator,
            condition=condition,
            body=body
        )
        
    def parse_function_def(self):
        self.consume("HOW_IZ_I")
        
        name = self.consume("ID")
        
        params = []
        if self.get_current_token() == "YR":
            params.append(self.parse_param())
            
            while self.get_current_token() == "AN":
                self.consume("AN")
                params.append(self.parse_param())
        
        body = []
        return_expr = None
        
        while self.get_current_token() not in ("FOUND", "IF_U_SAY_SO"):
            body.append(self.parse_statement())
            
        if self.get_current_token() == "FOUND_YR":
            self.consume("FOUND_YR")
            return_expr = self.parse_value_or_expression()
            
        self.consume("IF_U_SAY_SO")
        
        return FunctionDef(name=name, params=params, body=body, return_expr=return_expr)
    
    # Function functions (lol)
    def parse_function_call(self):
        self.consume("I_IZ")
        name = self.consume("ID")

        args = []
        if self.get_current_token() == "YR":
            args.append(self.parse_call_arg())
            while self.get_current_token() == "AN":
                self.consume("AN")
                args.append(self.parse_call_arg())

        return FunctionCall(name=name, args=args)
    
    def parse_call_arg(self):
        self.consume("YR")
        return self.parse_value_or_expression()
    
    def parse_param(self):
        self.consume("YR")
        return self.consume("ID")