# The parser class implements a Recursive Descent Parser (RDP). It works by taking the stream of tokens from the lexer then checking if the sequence conforms to the grammar we set.
# 
from dataclasses import dataclass, field
from typing import Any, List, Optional

# === || AST node classes || ===
@dataclass
class ASTNode:
    """The abstract base class for all nodes in the Abstract Syntax Tree."""
    pass 

@dataclass
class Program(ASTNode):
    """Represents the entire LOLCODE program (HAI ... KTHXBYE)."""
    declarations: List[ASTNode] # WAZZUP block contents.
    statements: List[ASTNode]   # Main execution code.
    functions: List[ASTNode]    # HOW IZ I blocks.
@dataclass
class VarDecl(ASTNode):
    """Represents a variable declaration (I HAS A name [ITZ value])."""
    name: str
    init: Optional[ASTNode] # The initializer expression. None defaults to NOOB.

@dataclass
class Assignment(ASTNode):
    """Represents a simple variable assignment (target R value)."""
    target: str
    value: ASTNode

@dataclass
class TypeCastAssignment(ASTNode):
    """Represents assignment with cast: VAR R MAEK OTHER A TYPE."""
    target: str
    source: str
    target_type: str

@dataclass
class TypeOnlyAssignment(ASTNode):
    """Represents in-place type casting: VAR IS NOW A TYPE."""
    target: str
    new_type: str

@dataclass
class Gimmeh(ASTNode):
    """Represents user input: GIMMEH target."""
    target: str

@dataclass
class Print(ASTNode):
    """Represents output: VISIBLE operands [PLUS operands]..."""
    operands: List[ASTNode]

@dataclass
class IfStmt(ASTNode):
    """Represents the conditional structure (O RLY? YA RLY...)."""
    condition: Optional[ASTNode] # Condition evaluated before O RLY?
    ya_block: List[ASTNode]      # The 'YA RLY' block.
    mebbe_blocks: List[tuple]    # List of (condition, block) tuples for 'MEBBE'.
    nowai_block: Optional[List[ASTNode]] # The 'NO WAI' block.

@dataclass
class Loop(ASTNode):
    """Represents the loop structure (IM IN YR...IM OUTTA YR)."""
    name: str
    mode: str # UPPIN, NERFIN, or None.
    iterator: str # The loop variable ID.
    condition: Optional[ASTNode] # The WILE or TIL condition expression.
    body: List[ASTNode]

@dataclass
class SwitchCase(ASTNode):
    """Represents the switch structure (WTF? OMG ... OMGWTF ... OIC)."""
    cases: List[tuple] # List of (literal, block) tuples for 'OMG'.
    default: Optional[List[ASTNode]] # The 'OMGWTF' block.

@dataclass
class Expression(ASTNode):
    """Represents an operation (e.g., SUM OF, BOTH OF)."""
    op: Optional[str] # The operator token type.
    operands: List[Any] = field(default_factory=list)

@dataclass
class Literal(ASTNode):
    """Represents a constant value (NUMBR_LIT, YARN_LIT, etc.)."""
    value: Any

@dataclass
class VarRef(ASTNode):
    """Represents a variable name reference (ID)."""
    name: str

# Added for 10_functions.lol testcase
@dataclass
class FunctionDef(ASTNode):
    """Represents a function definition (HOW IZ I ... IF U SAY SO)."""
    name: str
    params: List[str]
    body: List[ASTNode]
    return_expr: Optional[ASTNode]

@dataclass
class FunctionCall(ASTNode):
    """Represents a function call (I IZ name [YR arg AN YR arg ...])."""
    name: str
    args: List[ASTNode]

@dataclass
class ReturnStmt(ASTNode):
    """Represents function return (FOUND YR expression)."""
    value: ASTNode

@dataclass
class BreakStmt(ASTNode):
    """Represents loop termination (GTFO)."""
    pass

@dataclass
class ImplicitIT(ASTNode):
    """Represents a reference to the implicit variable 'IT'."""
    pass
# ---

### 2. Parser Class (Parsing Logic)


# === || Parser || ===
class Parser:
    def __init__(self, tokens, lexemes, rows, columns):
        """
        Initializes the parser with the token stream provided by the Lexer.
        """
        self.tokens = tokens
        self.lexemes = lexemes
        self.rows = rows
        self.columns = columns

        # Pointer to current token 
        self.current_token_index = 0
        
    def get_current_token(self):
        """Returns the type of the token at the current pointer position. 'EOF' if stream ends."""
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return 'EOF'
    
    # Helper function to look at next token    
    def lookahead(self, k=1):
        """
        Peeks ahead 'k' tokens without advancing the pointer. 
        Crucial for resolving grammar ambiguities (e.g., ID being assignment vs. expression).
        """
        i = self.current_token_index + k
        if i < len(self.tokens):
            return self.tokens[i]
        return 'EOF'
    
    # Matches and consumes expected token, else returns an error
    def consume(self, expected_token_type):
        """
        The fundamental operation: checks the current token type, advances the pointer, and returns the lexeme value.
        Raises SyntaxError if the token does not match the expected type.
        """
        current_token = self.get_current_token()

        if expected_token_type is None or current_token == expected_token_type:
            value = self.lexemes[self.current_token_index]
            self.current_token_index += 1
            # print(f"Parsed: {current_token} -> {value}")
            return value
        else:
            # Error reporting logic.
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
        """
        Parses the program structure: HAI -> [WAZZUP] -> [HOW_IZ_I] -> [Statements] -> KTHXBYE.
        """
        self.consume('HAI')
        
        declarations = []
        # Variable declaration block (WAZZUP ... BUHBYE) is optional.
        if self.get_current_token() == 'WAZZUP':
            declarations = self.parse_declaration_block()
        
        # Functions can be defined before the main statements.
        functions = []
        while self.get_current_token() == 'HOW_IZ_I':
            functions.append(self.parse_function_def())
        
        # Actual main code.
        statements = self.parse_statements()
        
        self.consume('KTHXBYE')
        
        # Check for trailing junk after the program terminator.
        if self.get_current_token() != 'EOF':
            raise SyntaxError("Syntax Error: Extra tokens found after KTHXBYE.")
        
        return Program(declarations=declarations, statements=statements, functions=functions)
    
    # Parses through the declaration block
    def parse_declaration_block(self):
        """
        Parses WAZZUP -> [I_HAS_A]... -> BUHBYE.
        """
        self.consume("WAZZUP")
        decls = []
        while self.get_current_token() == 'I_HAS_A':
            decls.append(self.parse_variable_declaration())
        if self.get_current_token() == 'BUHBYE':
            self.consume("BUHBYE")
        else:
            # Enforce BUHBYE as the mandatory declaration block terminator.
            raise SyntaxError("Syntax Error: Did not end declaration block with BUHBYE or added a non-declaring keyword inside of declaration block")
        return decls
        
    # Parses through Statements -> <statement> <linebreak> <statements> <comment> | ε
    def parse_statements(self, stop_tokens: Optional[List[str]] = None):
        """
        Parses a sequence of statements until an EOF or a block terminator (e.g., OIC, IM_OUTTA_YR) is reached.
        """
        if stop_tokens is None:
            stop_tokens = []

        nodes = []
        while True:
            tok = self.get_current_token()
            if tok in ('KTHXBYE', 'EOF') or tok in stop_tokens:
                break
            # Delegate parsing to the individual statement handler.
            nodes.append(self.parse_statement())
        return nodes
    
    def parse_statement(self):
        """
        The main statement dispatcher. Uses the current token to determine which specific parsing function to call.
        """
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
            return BreakStmt() # Loop break statement.
        elif tok == "I_IZ":
            return self.parse_function_call()
        elif tok == "VISIBLE":
            return self.parse_print()
        elif tok == "GIMMEH":
            return self.parse_gimmeh()
        elif tok == "ID":
            # Ambiguity resolved by lookahead: ID R... or ID IS_NOW_A... (assignment) vs. ID (expression).
            if self.lookahead() in ("R", "IS_NOW_A"):
                return self.parse_assignment()
            else:
                # If not an assignment, treat ID as the start of an expression (likely just a variable ref or part of a chain).
                expr = self.parse_expression()
                return expr
        # Direct expression start (e.g., SUM OF 1 2) is a valid standalone statement.
        if tok in (
            'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF', 'BIGGR_OF', 'SMALLR_OF',
            'SMOOSH', 'BOTH_OF', 'EITHER_OF', 'WON_OF', 'ANY_OF', 'ALL_OF', 'NOT', 'BOTH_SAEM', 'DIFFRINT'
        ):
            expr = self.parse_expression()
            return expr
        
        # Control flow statements
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
        """Parses: I_HAS_A ID [ITZ value_or_expression]."""
        self.consume('I_HAS_A')
        id_lexeme = self.lexemes[self.current_token_index] # Store lexeme for context/future checks.
        name = self.consume('ID') 
        
        init_node = None
        # Check for optional initialization.
        if self.get_current_token() == "ITZ":
            self.consume("ITZ")
            init_node = self.parse_value_or_expression()
            
        return VarDecl(name=name, init=init_node)
    
    def parse_value_or_expression(self):
        """
        Parses a terminal value: a Literal, a Variable Reference, or the start of a nested Expression.
        This function handles the recursion depth for expressions.
        """
        tok = self.get_current_token()
        # Literal values
        if tok in ('NUMBR_LIT', 'NUMBAR_LIT', 'YARN_LIT', 'TROOF_LIT'):
            val = self.consume(tok)
            return Literal(value=val)
        # Variable references (ID or IT)
        if tok == 'ID':
            name = self.consume('ID')
            if name == "IT":
                return ImplicitIT() # Treat the literal "IT" as a special reference.
            return VarRef(name=name)
        # Start of a nested expression
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
        """
        Parses an expression starting with an operator. Handles unary (NOT), binary (SUM OF), 
        and n-ary (SMOOSH, ALL OF) operators, including the required 'AN' separators.
        """
        op_tok = self.get_current_token()

        # If the expression begins with an operator
        if op_tok in (
            'NOT', 'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF',
            'BIGGR_OF', 'SMALLR_OF', 'SMOOSH', 'BOTH_OF', 'EITHER_OF', 'WON_OF',
            'ANY_OF', 'ALL_OF', 'BOTH_SAEM', 'DIFFRINT'
        ):
            op = op_tok
            self.consume(op_tok)

            # Unary operator (NOT)
            if op == 'NOT':
                operand = self.parse_value_or_expression() # Only one operand expected.
                return Expression(op=op, operands=[operand])

            # First Operand (mandatory for binary/n-ary)
            first_operand = self.parse_value_or_expression()

            binary_ops = { # Operators requiring exactly two operands.
                'SUM_OF', 'DIFF_OF', 'PRODUKT_OF', 'QUOSHUNT_OF', 'MOD_OF',
                'BIGGR_OF', 'SMALLR_OF', 'BOTH_OF', 'EITHER_OF', 'WON_OF',
                'BOTH_SAEM', 'DIFFRINT'
            }

            infinite_ops = {'SMOOSH', 'ALL_OF', 'ANY_OF'} # Operators requiring two or more operands.

            # For binary operators
            if op in binary_ops:
                # Must have exactly 1 AN
                if self.get_current_token() != "AN":
                    # Error if the mandatory 'AN' is missing.
                    row = self.rows[self.current_token_index]
                    col = self.columns[self.current_token_index]
                    raise SyntaxError(
                        f"Operator '{op.replace('_',' ')}' requires 'AN <operand>' "
                        f"(line {row}, col {col})"
                    )

                self.consume("AN")
                second_operand = self.parse_value_or_expression()

                # Returns the complete expression node with two operands.
                return Expression(op=op, operands=[first_operand, second_operand])

            # For more than 2 operators (n-ary)
            if op in infinite_ops:
                operands = [first_operand]

                # Consume "AN <operand>" repeatedly until 'AN' is no longer found.
                while self.get_current_token() == "AN":
                    self.consume("AN")
                    operands.append(self.parse_value_or_expression())

                # Optional MKAY terminator on ALL_OF / ANY_OF (SMOOSH accepts it optionally too)
                if op in {'ALL_OF', 'ANY_OF'} and self.get_current_token() == "MKAY":
                    self.consume("MKAY")

                # Must have at least 2 operands in total.
                if len(operands) < 2:
                    row = self.rows[self.current_token_index]
                    col = self.columns[self.current_token_index]
                    raise SyntaxError(
                        f"Operator '{op.replace('_',' ')}' expects 2 or more operands "
                        f"(line {row}, col {col})"
                    )

                return Expression(op=op, operands=operands)
            
            raise SyntaxError(f"Unexpected operator '{op_tok}' in expression.")

        # Else its a literal or variable (this path is usually covered by parse_value_or_expression, but serves as a fallback)
        return self.parse_value_or_expression()
    
    def parse_print(self):
        """Parses: VISIBLE <value_or_expression> [PLUS/AN <value_or_expression>]..."""
        self.consume('VISIBLE')
        operands = [self.parse_value_or_expression()]
        
        # VISIBLE allows multiple operands separated by 'PLUS' or 'AN' (concatenation).
        while self.get_current_token() in ['PLUS', 'AN']:
            self.consume(self.get_current_token())
            operands.append(self.parse_value_or_expression())
        return Print(operands=operands)
    
    def parse_smoosh(self):
        """Parses: SMOOSH <operand> [AN <operand>]... [MKAY]."""
        self.consume("SMOOSH")
        operands = [self.parse_value_or_expression()] # first operand is mandatory.
        
        # Collects all subsequent operands separated by 'AN'.
        while self.get_current_token() == "AN":
            self.consume("AN")
            operands.append(self.parse_value_or_expression())
        if self.get_current_token() == 'MKAY':
            self.consume('MKAY') # Optional terminator.
            
        return Expression(op='SMOOSH', operands=operands)
    
    def parse_assignment(self):
        """
        Parses the three forms of assignment:
        1. target R value/expression
        2. target R MAEK source A TYPE (TypeCastAssignment)
        3. target IS_NOW_A TYPE (TypeOnlyAssignment)
        """
        target = self.consume('ID')
        tok = self.get_current_token()
        
        if tok == 'R':
            self.consume('R')
            if self.get_current_token() in ('MAEK', 'MAEK_A'):
                # Form 2: TypeCastAssignment
                self.consume(self.get_current_token())
                source = self.consume('ID')
                target_type = self.consume(self.get_current_token()) # Consume the TYPE_LIT
                return TypeCastAssignment(target=target, source=source, target_type=target_type)
            else:
                # Form 1: Simple Assignment
                value = self.parse_value_or_expression()
                return Assignment(target=target, value=value)
        
        elif tok == 'IS_NOW_A':
            # Form 3: TypeOnlyAssignment
            self.consume('IS_NOW_A')
            new_type = self.consume(self.get_current_token()) # Consume the TYPE_LIT
            return TypeOnlyAssignment(target=target, new_type=new_type)
        else:
            # Should have been caught by lookahead, but serves as a detailed error check.
            row = self.rows[self.current_token_index] if self.current_token_index < len(self.rows) else 0
            col = self.columns[self.current_token_index] if self.current_token_index < len(self.columns) else 0
            raise SyntaxError(f"Unexpected token '{tok}' after variable '{target}' at line {row}, col {col}")
        
    def parse_gimmeh(self): #User Input
        """Parses: GIMMEH ID (Read input into variable)."""
        self.consume("GIMMEH")
        
        if self.get_current_token() == 'ID':
            target = self.consume('ID')
            return Gimmeh(target=target)
        else:
            # Error if GIMMEH is not followed by a variable name.
            row = self.rows[self.current_token_index] if self.rows else 0
            col = self.columns[self.current_token_index] if self.columns else 0
            raise SyntaxError(
                f"Expected variable name after GIMMEH at line {row}, column {col}, "
                f"found '{self.get_current_token()}'"
            )

    def parse_o_rly(self, condition_expr: Optional[ASTNode] = None): # Optional conditional expression in o rly
        """
        Parses conditional block: O_RLY -> YA_RLY block -> [MEBBE]... -> [NO_WAI] -> OIC.
        Note: The condition is often implicitly IT, set by a preceding expression.
        """
        self.consume('O_RLY')
        
        # parse YA RLY (mandatory)
        if self.get_current_token() == 'YA_RLY':
            self.consume('YA_RLY')
            # Parse statements, stopping at block terminators.
            ya_block = self.parse_statements(stop_tokens=['MEBBE', 'NO_WAI', 'OIC'])
        
        # optional multiple MEBBE blocks (elif)
        mebbe_blocks = []
        while self.get_current_token() == 'MEBBE':
            self.consume('MEBBE')
            mebbe_cond = self.parse_value_or_expression() # Condition for this MEBBE block.
            mebbe_body = self.parse_statements(stop_tokens=['MEBBE', 'NO_WAI', 'OIC'])
            mebbe_blocks.append((mebbe_cond, mebbe_body))
        
        # optional else block (NO WAI)
        nowai_block = None
        if self.get_current_token() == 'NO_WAI':
            self.consume('NO_WAI')
            nowai_block = self.parse_statements(stop_tokens=['OIC'])

        self.consume('OIC') # Mandatory block end.
        return IfStmt(condition=condition_expr, ya_block=ya_block, mebbe_blocks=mebbe_blocks, nowai_block=nowai_block)
    
    # parse statement wtf
    def parse_wtf(self):
        """Parses the switch statement: WTF? -> [OMG literal block [GTFO]]... -> [OMGWTF block] -> OIC."""
        if self.get_current_token() in ['WTF']:
            self.consume(self.get_current_token())
        
        cases = []
        default = None
        while self.get_current_token() == 'OMG':
            self.consume('OMG')
            lit = self.parse_value_or_expression() # Case value (must be a literal).
            # Parse block, stopping at the next case/default/end.
            body = self.parse_statements(stop_tokens=['OMG', 'OMGWTF', 'OIC'])
            cases.append((lit, body))
            # Check for optional GTFO (break) after a case block.
            if self.get_current_token() == 'GTFO':
                self.consume('GTFO')
                
        if self.get_current_token() == 'OMGWTF':
            self.consume('OMGWTF')
            default = self.parse_statements(stop_tokens=['OIC'])

        self.consume('OIC')
        return SwitchCase(cases=cases, default=default)

    # parses through loop
    def parse_loop(self):
        """Parses: IM_IN_YR ID [UPPIN/NERFIN YR ID] [WILE/TIL expr] body IM_OUTTA_YR ID."""
        self.consume('IM_IN_YR')
        loop_name = self.consume("ID")

        mode = None
        iterator = None
        condition = None
        
        # Optional UPPIN / NERFIN iterator definition
        if self.get_current_token() in ("UPPIN", "NERFIN"):
            mode = self.consume(self.get_current_token()) # UPPIN or NERFIN
            self.consume("YR")
            iterator = self.consume("ID")
            
        # Optional WILE or TIL conditional expression
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
        
        # check if loop names match (mandatory)
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
        """Parses: HOW_IZ_I ID [YR ID AN YR ID...] body [FOUND_YR expr] IF_U_SAY_SO."""
        self.consume("HOW_IZ_I")
        
        name = self.consume("ID")
        
        params = []
        # Parse parameters
        if self.get_current_token() == "YR":
            params.append(self.parse_param())
            while self.get_current_token() == "AN":
                self.consume("AN")
                params.append(self.parse_param())
        
        body = []
        return_expr = None
        
        # Parse function body statements
        while self.get_current_token() not in ("FOUND_YR", "IF_U_SAY_SO"):
            body.append(self.parse_statement())
            
        if self.get_current_token() == "FOUND_YR":
            self.consume("FOUND_YR")
            return_expr = self.parse_value_or_expression() # The return value expression.
            
        self.consume("IF_U_SAY_SO")
        
        return FunctionDef(name=name, params=params, body=body, return_expr=return_expr)
    
    # Function calls
    def parse_function_call(self):
        """Parses: I_IZ ID [YR arg AN YR arg...] [MKAY]."""
        self.consume("I_IZ")
        name = self.consume("ID")

        args = []
        # Parse arguments
        if self.get_current_token() == "YR":
            args.append(self.parse_call_arg())
            while self.get_current_token() == "AN":
                self.consume("AN")
                args.append(self.parse_call_arg())
                
        if self.get_current_token() == 'MKAY':
            self.consume("MKAY") # Optional terminator for function arguments.
            
        return FunctionCall(name=name, args=args)
    
    def parse_call_arg(self):
        """Helper to parse 'YR <argument>' in a function call."""
        self.consume("YR")
        return self.parse_value_or_expression()
    
    def parse_param(self):
        """Helper to parse 'YR <parameter_name>' in a function definition."""
        self.consume("YR")
        return self.consume("ID")
    # Function functions (lol)
    def parse_function_call(self):
        """
        Parses a function call statement: I_IZ <ID> [YR <arg> AN YR <arg>...] [MKAY].

        Example: I IZ "myFunc" YR 1 AN YR "hello" MKAY
        """
        self.consume("I_IZ") # Match the function call initiator.
        name = self.consume("ID") # Consume and store the function name.

        args = []
        # Check for the start of arguments (optional).
        if self.get_current_token() == "YR":
            args.append(self.parse_call_arg()) # Consume the first argument.
            
            # Consume subsequent arguments separated by 'AN'.
            while self.get_current_token() == "AN":
                self.consume("AN")
                args.append(self.parse_call_arg())
                
        if self.get_current_token() == 'MKAY':
            self.consume("MKAY") # Consume the optional terminator for function arguments.
            
        # Create the FunctionCall AST node.
        return FunctionCall(name=name, args=args)
    
    def parse_call_arg(self):
        """
        Helper method to parse a single function call argument, which starts with 'YR'.

        Grammar: YR <value_or_expression>
        """
        self.consume("YR") # Match the argument indicator.
        # Arguments can be any literal, variable, or nested expression.
        return self.parse_value_or_expression()
    
    def parse_param(self):
        """
        Helper method to parse a single function definition parameter.

        Grammar: YR <ID>
        """
        self.consume("YR") # Match the parameter indicator.
        # Parameters must be simple identifiers (variable names).
        return self.consume("ID")