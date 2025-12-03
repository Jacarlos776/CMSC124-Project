# The parser class implements a Recursive Descent Parser (RDP) for the LOLCODE-like language.
# It consumes a stream of tokens from the lexer and tries to build an Abstract Syntax Tree (AST)
# according to the grammar rules.

from dataclasses import dataclass, field
from typing import Any, List, Optional

# === || AST node classes || ===
# ASTNode is the base class for all nodes in the abstract syntax tree.
@dataclass
class ASTNode:
    pass # Abstract base class; no fields needed.

# Represents the whole program
@dataclass
class Program(ASTNode):
    declarations: List[ASTNode]  # Variable declarations
    statements: List[ASTNode]    # Main code statements
    functions: List[ASTNode]     # Functions defined in the program

# Represents a variable declaration, e.g., I HAS A x ITZ 5
@dataclass
class VarDecl(ASTNode):
    name: str                    # Variable name
    init: Optional[ASTNode]      # Initial value; None if uninitialized

# Represents a standard assignment, e.g., x R 10
@dataclass
class Assignment(ASTNode):
    target: str                  # Variable name
    value: ASTNode               # Value or expression assigned

# Assignment with type casting, e.g., x R MAEK y A NUMBR
@dataclass
class TypeCastAssignment(ASTNode):
    target: str                  # Variable being assigned
    source: str                  # Source variable
    target_type: str             # Type to cast to

# Change variable type without assignment, e.g., x IS NOW A NUMBAR
@dataclass
class TypeOnlyAssignment(ASTNode):
    target: str
    new_type: str

# Represents input from the user, e.g., GIMMEH x
@dataclass
class Gimmeh(ASTNode):
    target: str

# Represents printing/output, e.g., VISIBLE x
@dataclass
class Print(ASTNode):
    operands: List[ASTNode]      # Values/expressions to print

# Represents an if-elif-else construct
@dataclass
class IfStmt(ASTNode):
    condition: Optional[ASTNode] # Optional condition before O_RLY
    ya_block: List[ASTNode]      # Statements under YA_RLY
    mebbe_blocks: List[tuple]    # List of (condition, statements) tuples for MEBBE
    nowai_block: Optional[List[ASTNode]] # Statements under NO_WAI

# Represents loops: IM IN YR <loop_name> ... IM OUTTA YR <loop_name>
@dataclass
class Loop(ASTNode):
    name: str
    mode: str                     # Optional: UPPIN or NERFIN
    iterator: str                 # Optional iterator variable
    condition: Optional[ASTNode] # Optional loop condition (WILE/TIL)
    body: List[ASTNode]           # Statements inside the loop

# Represents switch/case-like structure (WTF/OMG/OMGWTF)
@dataclass
class SwitchCase(ASTNode):
    cases: List[tuple]            # List of (case_literal, statements)
    default: Optional[List[ASTNode]] # Default case

# Represents expressions with operators, e.g., SUM OF x AN y
@dataclass
class Expression(ASTNode):
    op: Optional[str]             # Operator (SUM_OF, NOT, etc.)
    operands: List[Any] = field(default_factory=list) # List of operand AST nodes

# Represents literal values like numbers, strings, booleans
@dataclass
class Literal(ASTNode):
    value: Any

# Represents a reference to a variable
@dataclass
class VarRef(ASTNode):
    name: str

# Represents function definition
@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List[str]            # List of parameter names
    body: List[ASTNode]          # Statements inside function
    return_expr: Optional[ASTNode] # Optional return expression

# Represents a function call
@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]          # Arguments passed to the function

# Represents a return statement
@dataclass
class ReturnStmt(ASTNode):
    value: ASTNode               # Expression returned

# Represents a break statement in loops
@dataclass
class BreakStmt(ASTNode):
    pass

# Represents the implicit "IT" variable
@dataclass
class ImplicitIT(ASTNode):
    pass

# === || Parser Class || ===
class Parser:
    def __init__(self, tokens, lexemes, rows, columns):
        self.tokens = tokens      # List of token types from lexer
        self.lexemes = lexemes    # Corresponding lexeme strings
        self.rows = rows          # Line numbers for each token (for errors)
        self.columns = columns    # Column numbers for each token (for errors)

        # Index of current token being parsed
        self.current_token_index = 0
        
    # Returns the current token type
    def get_current_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return 'EOF'
    
    # Look ahead k tokens without consuming them
    def lookahead(self, k=1):
        i = self.current_token_index + k
        if i < len(self.tokens):
            return self.tokens[i]
        return 'EOF'
    
    # Consume the current token if it matches expected_token_type
    def consume(self, expected_token_type):
        current_token = self.get_current_token()

        if expected_token_type is None or current_token == expected_token_type:
            value = self.lexemes[self.current_token_index]
            self.current_token_index += 1
            return value
        else:
            # Raise error with line/column info
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

    # -- Recursive Descent Parsing Functions --

    # Top-level program parser: HAI ... KTHXBYE
    def parse_program(self):
        self.consume('HAI')
        
        # Parse variable declarations if present
        if self.get_current_token() == 'WAZZUP':
            declarations = self.parse_declaration_block()
        
        # Parse functions
        functions = []
        while self.get_current_token() == 'HOW_IZ_I':
            functions.append(self.parse_function_def())
        
        # Parse main statements
        statements = self.parse_statements()
        
        self.consume('KTHXBYE')
        
        # Ensure no extra tokens after program end
        if self.get_current_token() != 'EOF':
            raise SyntaxError("Syntax Error: Extra tokens found after KTHXBYE.")
        
        return Program(declarations=declarations, statements=statements, functions=functions)
    
    # Parses WAZZUP ... BUHBYE block for variable declarations
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
        
    # Parse multiple statements until one of stop_tokens is encountered
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

    # Parse a single statement based on its starting token
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
                return self.parse_expression()
        # Check if the token is an expression operator
        if tok in (
            'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF', 'BIGGR_OF', 'SMALLR_OF',
            'SMOOSH', 'BOTH_OF', 'EITHER_OF', 'WON_OF', 'ANY_OF', 'ALL_OF', 'NOT', 'BOTH_SAEM', 'DIFFRINT'
        ):
            return self.parse_expression()
        elif tok == "O_RLY":
            return self.parse_o_rly()
        elif tok == "WTF":
            return self.parse_wtf()
        elif tok == "IM_IN_YR":
            return self.parse_loop()
        else:
            raise SyntaxError(f"Unexpected token {tok}")
        
    # Parses a variable declaration: I HAS A <ID> [ITZ <value>]
    def parse_variable_declaration(self):
        self.consume('I_HAS_A')                  # Consume "I_HAS_A" token
        id_lexeme = self.lexemes[self.current_token_index]  # Current lexeme (for checking)
        name = self.consume('ID')                # Consume variable name token
        
        init_node = None                          # Default: uninitialized variable
        # If variable is initialized: ITZ <expression>
        if self.get_current_token() == "ITZ":
            self.consume("ITZ")
            init_node = self.parse_value_or_expression()  # Parse initial value expression
        
        return VarDecl(name=name, init=init_node) # Return AST node for declaration

    # Parses a value or expression (literal, variable, or expression starting with operator)
    def parse_value_or_expression(self):
        tok = self.get_current_token()
        if tok in ('NUMBR_LIT', 'NUMBAR_LIT', 'YARN_LIT', 'TROOF_LIT'):
            val = self.consume(tok)               # Consume literal token
            return Literal(value=val)
        if tok == 'ID':                           # Variable reference
            name = self.consume('ID')
            if name == "IT":                      # Special implicit IT variable
                return ImplicitIT()
            return VarRef(name=name)
        if tok == 'SMOOSH':                       # String concatenation operator
            return self.parse_smoosh()
        # Expression operators like SUM_OF, DIFF_OF, etc.
        if tok in ('SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF',
                'BIGGR_OF', 'SMALLR_OF', 'BOTH_OF', 'EITHER_OF', 'WON_OF',
                'ANY_OF', 'ALL_OF', 'NOT', 'BOTH_SAEM', 'DIFFRINT'):
            return self.parse_expression()
        # If token is unexpected, raise syntax error
        row = self.rows[self.current_token_index] if self.current_token_index < len(self.rows) else 0
        col = self.columns[self.current_token_index] if self.current_token_index < len(self.columns) else 0
        raise SyntaxError(f"Unexpected token '{tok}' in expression at line {row}, col {col}")

    # Parses expressions starting with an operator
    def parse_expression(self):
        op_tok = self.get_current_token()

        # Operators recognized by the language
        if op_tok in (
            'NOT', 'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF',
            'BIGGR_OF', 'SMALLR_OF', 'SMOOSH', 'BOTH_OF', 'EITHER_OF', 'WON_OF',
            'ANY_OF', 'ALL_OF', 'BOTH_SAEM', 'DIFFRINT'
        ):
            op = op_tok
            self.consume(op_tok)                     # Consume operator

            # Unary operator NOT
            if op == 'NOT':
                operand = self.parse_value_or_expression()
                return Expression(op=op, operands=[operand])

            # Parse first operand for binary/infinite-arity operators
            first_operand = self.parse_value_or_expression()

            # Define sets of binary operators (2 operands) vs infinite-arity operators
            binary_ops = {
                'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF',
                'BIGGR_OF', 'SMALLR_OF', 'BOTH_OF', 'EITHER_OF', 'WON_OF',
                'BOTH_SAEM', 'DIFFRINT'
            }

            infinite_ops = {'SMOOSH', 'ALL_OF', 'ANY_OF'}

            # Binary operator: must have exactly 2 operands
            if op in binary_ops:
                if self.get_current_token() != "AN":  # Must have AN between operands
                    row = self.rows[self.current_token_index]
                    col = self.columns[self.current_token_index]
                    raise SyntaxError(
                        f"Operator '{op.replace('_',' ')}' requires 'AN <operand>' "
                        f"(line {row}, col {col})"
                    )
                self.consume("AN")
                second_operand = self.parse_value_or_expression()
                return Expression(op=op, operands=[first_operand, second_operand])

            # Infinite-arity operators (SMOOSH, ALL_OF, ANY_OF)
            if op in infinite_ops:
                operands = [first_operand]
                while self.get_current_token() == "AN":  # Keep consuming operands
                    self.consume("AN")
                    operands.append(self.parse_value_or_expression())
                # Optional MKAY terminator
                if op in {'ALL_OF', 'ANY_OF'} and self.get_current_token() == "MKAY":
                    self.consume("MKAY")
                if len(operands) < 2:
                    row = self.rows[self.current_token_index]
                    col = self.columns[self.current_token_index]
                    raise SyntaxError(
                        f"Operator '{op.replace('_',' ')}' expects 2 or more operands "
                        f"(line {row}, col {col})"
                    )
                return Expression(op=op, operands=operands)
            
            raise SyntaxError(f"Unexpected operator '{op_tok}' in expression.")

        # If no operator, treat as literal/variable
        return self.parse_value_or_expression()

    # Parse VISIBLE statements (print)
    def parse_print(self):
        self.consume('VISIBLE')                     # Consume keyword
        operands = [self.parse_value_or_expression()]  # First expression

        # Handle concatenation with PLUS or AN
        while self.get_current_token() in ['PLUS', 'AN']:
            self.consume(self.get_current_token())
            operands.append(self.parse_value_or_expression())
        return Print(operands=operands)

    # Parse SMOOSH (string concatenation)
    def parse_smoosh(self):
        self.consume("SMOOSH")
        operands = [self.parse_value_or_expression()] # First operand
        while self.get_current_token() == "AN":
            self.consume("AN")
            operands.append(self.parse_value_or_expression())
        if self.get_current_token() == 'MKAY':
            self.consume('MKAY')                   # Optional end marker
        return Expression(op='SMOOSH', operands=operands)

    # Parse assignments
    def parse_assignment(self):
        target = self.consume('ID')                 # Variable being assigned
        tok = self.get_current_token()
        if tok == 'R':                              # Regular assignment
            self.consume('R')
            # Handle type casting assignment
            if self.get_current_token() in ('MAEK', 'MAEK_A'):
                self.consume(self.get_current_token())
                source = self.consume('ID')
                target_type = self.consume(self.get_current_token())
                return TypeCastAssignment(target=target, source=source, target_type=target_type)
            else:
                value = self.parse_value_or_expression()
                return Assignment(target=target, value=value)
        elif tok == 'IS_NOW_A':                     # Change variable type
            self.consume('IS_NOW_A')
            new_type = self.consume(self.get_current_token())
            return TypeOnlyAssignment(target=target, new_type=new_type)
        else:
            row = self.rows[self.current_token_index] if self.current_token_index < len(self.rows) else 0
            col = self.columns[self.current_token_index] if self.current_token_index < len(self.columns) else 0
            raise SyntaxError(f"Unexpected token '{tok}' after variable '{target}' at line {row}, col {col}")

    # Parse GIMMEH (user input) statements
    def parse_gimmeh(self):
        self.consume("GIMMEH")
        if self.get_current_token() == 'ID':
            target = self.consume("ID")
            return Gimmeh(target=target)
        else:
            row = self.rows[self.current_token_index] if self.rows else 0
            col = self.columns[self.current_token_index] if self.columns else 0
            raise SyntaxError(
                f"Expected variable name after GIMMEH at line {row}, column {col}, "
                f"found '{self.get_current_token()}'"
            )

    # Parses O_RLY ... YA_RLY / MEBBE / NO_WAI ... OIC conditional blocks
    def parse_o_rly(self, condition_expr: Optional[ASTNode] = None):
        self.consume('O_RLY')  # Start of if-like block

        # YA_RLY block (main "if" block)
        if self.get_current_token() == 'YA_RLY':
            self.consume('YA_RLY')
            ya_block = self.parse_statements(stop_tokens=['MEBBE', 'NO_WAI', 'OIC'])

        # Optional MEBBE blocks (like "else if")
        mebbe_blocks = []
        while self.get_current_token() == 'MEBBE':
            self.consume('MEBBE')
            mebbe_cond = self.parse_value_or_expression()  # Condition for MEBBE
            mebbe_body = self.parse_statements(stop_tokens=['MEBBE', 'NO_WAI', 'OIC'])
            mebbe_blocks.append((mebbe_cond, mebbe_body))

        # Optional NO_WAI block (like "else")
        nowai_block = None
        if self.get_current_token() == 'NO_WAI':
            self.consume('NO_WAI')
            nowai_block = self.parse_statements(stop_tokens=['OIC'])

        self.consume('OIC')  # End of O_RLY block
        return IfStmt(condition=condition_expr, ya_block=ya_block,
                    mebbe_blocks=mebbe_blocks, nowai_block=nowai_block)

    # Parses WTF (switch-case) statement
    def parse_wtf(self):
        if self.get_current_token() == 'WTF':
            self.consume('WTF')
        
        cases = []
        default = None
        while self.get_current_token() == 'OMG':  # Case blocks
            self.consume('OMG')
            lit = self.parse_value_or_expression()  # Case literal
            body = self.parse_statements(stop_tokens=['OMG', 'OMGWTF', 'OIC'])
            cases.append((lit, body))
            if self.get_current_token() == 'GTFO':  # Optional break from case
                self.consume('GTFO')

        # Default block
        if self.get_current_token() == 'OMGWTF':
            self.consume('OMGWTF')
            default = self.parse_statements(stop_tokens=['OIC'])

        self.consume('OIC')  # End of WTF block
        return SwitchCase(cases=cases, default=default)

    # Parses loops: IM IN YR ... IM OUTTA YR
    def parse_loop(self):
        self.consume('IM_IN_YR')  # Start of loop
        loop_name = self.consume("ID")  # Loop identifier

        mode = None
        iterator = None
        condition = None

        # Optional increment/decrement (UPPIN/NERFIN)
        if self.get_current_token() in ("UPPIN", "NERFIN"):
            mode = self.consume(self.get_current_token())  # UPPIN or NERFIN
            self.consume("YR")
            iterator = self.consume("ID")                  # Iterator variable

        # Optional conditional loops: WILE (while) or TIL (until)
        if self.get_current_token() == "WILE":
            self.consume("WILE")
            condition = self.parse_value_or_expression()
        elif self.get_current_token() == "TIL":
            self.consume("TIL")
            condition = self.parse_value_or_expression()

        # Parse loop body
        body = self.parse_statements(stop_tokens=["IM_OUTTA_YR"])
        
        # End of loop
        self.consume("IM_OUTTA_YR")
        end_name = self.consume("ID")  # Must match starting loop name

        if end_name != loop_name:  # Validate loop names
            raise SyntaxError(f"Loop name mismatch: started {loop_name}, ended {end_name}")
        
        return Loop(name=loop_name, mode=mode, iterator=iterator,
                    condition=condition, body=body)

    # Parses function definitions: HOW_IZ_I ... IF_U_SAY_SO
    def parse_function_def(self):
        self.consume("HOW_IZ_I")          # Function start
        name = self.consume("ID")          # Function name

        # Parse parameters
        params = []
        if self.get_current_token() == "YR":
            params.append(self.parse_param())
            while self.get_current_token() == "AN":
                self.consume("AN")
                params.append(self.parse_param())

        # Parse function body
        body = []
        return_expr = None
        while self.get_current_token() not in ("FOUND_YR", "IF_U_SAY_SO"):
            body.append(self.parse_statement())

        # Optional return statement
        if self.get_current_token() == "FOUND_YR":
            self.consume("FOUND_YR")
            return_expr = self.parse_value_or_expression()

        self.consume("IF_U_SAY_SO")        # End of function
        return FunctionDef(name=name, params=params, body=body, return_expr=return_expr)

    # Parses function calls: I_IZ ... MKAY
    def parse_function_call(self):
        self.consume("I_IZ")               # Function call start
        name = self.consume("ID")           # Function name

        args = []
        if self.get_current_token() == "YR":
            args.append(self.parse_call_arg())
            while self.get_current_token() == "AN":
                self.consume("AN")
                args.append(self.parse_call_arg())

        if self.get_current_token() == 'MKAY':  # Optional terminator
            self.consume("MKAY")

        return FunctionCall(name=name, args=args)

    # Parse a single function call argument
    def parse_call_arg(self):
        self.consume("YR")                    # Argument starts with YR
        return self.parse_value_or_expression()  # Expression as argument

    # Parse a function parameter in definition
    def parse_param(self):
        self.consume("YR")                    # Parameter starts with YR
        return self.consume("ID")             # Parameter name
