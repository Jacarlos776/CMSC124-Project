from parser import (
    Program, VarDecl, Assignment, TypeCastAssignment, TypeOnlyAssignment,
    Gimmeh, Print, IfStmt, Loop, SwitchCase, ImplicitIT,
    Expression, Literal, VarRef,
    FunctionDef, FunctionCall, ReturnStmt, BreakStmt
)
# Imports all necessary AST Node types defined in the parser module. 
# These classes represent the syntax of the LOLCODE program.

import sys

class LOLRuntimeError(Exception):
    """
    Custom exception for errors that occur during the execution phase (runtime).
    E.g., division by zero, accessing an undeclared variable, type cast errors.
    """
    pass


# ---

# === || Environment || ===
class Environment:
    """
    Manages variable storage and scope resolution (scoping) for LOLCODE. 
    It enables nested scopes (like local function variables) via the 'parent' link.
    This implements Lexical Scoping.
    """
    def __init__(self, parent=None):
        # Dictionary to hold variables in the current scope. 
        # Stores values as structured LOLCODE objects: {name: {"type": "...", "value": ...}}
        self.vars = {}
        # Reference to the enclosing (outer) environment, defining the scope chain.
        self.parent = parent

    def define(self, name, value):
        """
        Declares a new variable in the *current* scope. Used by 'I HAS A'.
        """
        self.vars[name] = value

    def set(self, name, value):
        """
        Assigns a new value to an *existing* variable. 
        Requires lookup to find the environment where the variable was originally declared.
        """
        env = self.lookup_env(name)
        if env is None:
            # Cannot assign to a variable that has not been declared.
            raise LOLRuntimeError(f"Variable '{name}' not declared.")
        env.vars[name] = value

    def get(self, name):
        """
        Retrieves the value of a variable, searching up the scope chain.
        """
        env = self.lookup_env(name)
        if env is None:
            # Cannot get the value of a variable that is not found in any active scope.
            raise LOLRuntimeError(f"Variable '{name}' not declared.")
        return env.vars[name]

    def lookup_env(self, name):
        """
        **Scope Resolution:** Searches for the environment object that holds the variable.
        Starts at the current environment and iteratively checks parents until the variable is found 
        or the global scope (parent is None) is reached.
        """
        env = self
        while env:
            if name in env.vars:
                return env
            env = env.parent # Move to the parent scope
        return None # Variable not found in any scope


# ---

# === || Interpreter || ===
class Interpreter:
    """
    The main execution engine. It traverses the Abstract Syntax Tree (AST) 
    and applies the semantic rules of LOLCODE.
    """
    def __init__(self, ast: Program):
        self.ast = ast # The root of the entire program AST.
        self.global_env = Environment() # The outermost environment for global variables.
        self.functions = {} # Dictionary to store FunctionDef AST nodes, indexed by name.
        # The 'It' variable (Implicit IT), which stores the result of the last operation.
        self.IT = {"type": "NOOB", "value": None} 

    # Use this to run the interpreter in main
    def run(self):
        """
        Initializes the program execution sequence.
        1. Initialize global variables (WAZZUP block).
        2. Register function definitions (HOW IZ I).
        3. Execute main program statements.
        """
        # load globals (var decls in WAZZUP)
        for d in self.ast.declarations:
            self.eval(d, self.global_env) # Evaluate declarations in the global scope.

        # register function definitions
        # Function AST nodes are stored for later lookup during a call.
        for fn in self.ast.functions:
            self.functions[fn.name] = fn

        print("Registered functions:", list(self.functions.keys()))

        # run main (skip function defs)
        for stmt in self.ast.statements:
            self.eval(stmt, self.global_env) # Execute main statements.

    # === || Eval Dispatcher || ===
    def eval(self, node, env):
        """
        **The core AST traversal method.** It pattern-matches the type of the AST node and delegates execution to 
        the specific handler method (e.g., eval_var_decl, eval_assignment, eval_expr).
        """
        if isinstance(node, VarDecl):
            return self.eval_var_decl(node, env)
        if isinstance(node, Assignment):
            return self.eval_assignment(node, env)
        # ... (Dispatcher for other statements: type casting, input, output, control flow) ...
        if isinstance(node, Literal):
            # Converts the raw literal value (token) into a structured LOLCODE object.
            return self.cast_literal(node.value)
        if isinstance(node, VarRef):
            # Handles variable reference lookup.
            if node.name == "IT": # for implicit IT
                return self.IT
            return env.get(node.name)
        # ... (Dispatcher for IfStmt, Loop, SwitchCase) ...
        if isinstance(node, FunctionDef):
            # Function definitions are handled in `run`; they are skipped here.
            return None
        if isinstance(node, FunctionCall):
            return self.eval_call(node, env)
        if isinstance(node, ReturnStmt):
            # Returns a special tuple ('RETURN', value) to signal control flow exit to the caller.
            return ("RETURN", self.eval(node.value, env))
        if isinstance(node, BreakStmt):
            # Returns a special tuple ('BREAK', None) to signal loop exit (GTFO).
            return ("BREAK", None)
        if isinstance(node, ImplicitIT):
            # Explicit reference to the IT variable.
            return self.IT

        raise LOLRuntimeError("Unhandled AST node type: " + str(type(node)))

    # ---

    # # === || Variable Declaration || ===
    def eval_var_decl(self, node, env):
        """
        Executes 'I HAS A' (variable declaration). Initializes the variable.
        """
        if node.init is None:
            # Default initialization is NOOB (null).
            env.define(node.name, {"type": "NOOB", "value": None})
        else:
            # Evaluate initializer expression and define variable with result.
            val = self.eval(node.init, env)
            env.define(node.name, val)

    # === || Assignment || ===
    def eval_assignment(self, node, env):
        """
        Executes assignments ('R'). Updates a variable and sets IT.
        """
        val = self.eval(node.value, env) # Evaluate the right-hand side.
        env.set(node.target, val)        # Update the variable value in scope.
        self.IT = val                    # Update the implicit IT variable.

    def eval_type_cast_assignment(self, node, env):
        """
        Executes type cast assignment (e.g., VAR R MAEK OTHER A NUMBR).
        """
        val = env.get(node.source)
        casted = self.typecast(val, node.target_type)
        env.set(node.target, casted)
        self.IT = casted

    def eval_type_only_assignment(self, node, env):
        """
        Executes in-place type cast (e.g., MAEK VAR A NUMBR).
        """
        var = env.get(node.target)
        casted = self.typecast(var, node.new_type)
        env.set(node.target, casted)
        self.IT = casted

    # === || Input (Gimmeh) || ===
    def eval_gimmeh(self, node, env):
        """
        Handles the 'GIMMEH' command (read from stdin). Input is always YARN.
        """
        raw = input()   # Uses Python's input function.
        # Assigns the raw input string as a YARN to the target variable.
        env.set(node.target, {"type": "YARN", "value": raw})
        self.IT = {"type": "YARN", "value": raw}

    # === || Print || ===
    def eval_print(self, node, env):
        """
        Handles the 'VISIBLE' command. Concatenates the YARN representation of all operands.
        """
        out = ""
        for op in node.operands:
            val = self.eval(op, env) # Evaluate each item to be printed.
            out += self.to_yarn(val) # Convert value to its YARN (string) representation.
        print(out)
        self.IT = {"type": "YARN", "value": out} # The result of VISIBLE is the printed YARN.

    # ---

    # === || Expressions & Operators || ===
    def eval_expr(self, node, env):
        """
        Evaluates a generic Expression node, delegating to specific operator handlers.
        """
        op = node.op

        # unary operators (e.g., NOT)
        if op == "NOT":
            v = self.eval(node.operands[0], env)
            # Operands are implicitly cast to boolean before the operation.
            return {"type": "TROOF", "value": not self.to_bool(v)}

        # infinite arity operators (e.g., SMOOSH)
        if op == "SMOOSH":
            parts = []
            for o in node.operands:
                parts.append(self.to_yarn(self.eval(o, env)))
            return {"type": "YARN", "value": "".join(parts)}

        # binary math/min/max operators (e.g., SUM OF)
        if op in ("SUM_OF", "DIFF_OF", "PRODUKT_OF", "QUOSHUNT_OF", "MOD_OF",
        "BIGGR_OF", "SMALLR_OF"):
            a = self.eval(node.operands[0], env)
            b = self.eval(node.operands[1], env)
            return self.math_eval(op, a, b) # Handles type coercion to NUMBR/NUMBAR.

        # binary boolean operators (e.g., BOTH OF)
        if op in ("BOTH_OF", "EITHER_OF", "WON_OF"):
            a = self.eval(node.operands[0], env)
            b = self.eval(node.operands[1], env)
            return self.bool_eval(op, a, b) # Handles type coercion to TROOF.

        # ALL OF / ANY OF (n-ary boolean operators)
        if op in ("ALL_OF", "ANY_OF"):
            return self.multi_bool_eval(op, [self.eval(x, env) for x in node.operands])

        # comparison operators (e.g., BOTH SAEM)
        if op in ("BOTH_SAEM", "DIFFRINT"):
            a = self.eval(node.operands[0], env)
            b = self.eval(node.operands[1], env)
            return self.compare_eval(op, a, b) # Handles strict type comparison.

        raise LOLRuntimeError(f"Unknown operator {op}")

    # === || Math Operators || ===
    def math_eval(self, op, a, b):
        """
        Performs binary math operations. Logic relies on implicit type conversion to number.
        """
        ax = self.to_number(a) # Coerce A to a Python number.
        bx = self.to_number(b) # Coerce B to a Python number.

        # ... (Python math operations) ...

        # Decide NUMBR vs NUMBAR
        # The result type depends on whether the final result is an integer or a floating-point value.
        if isinstance(res, float) and not res.is_integer():
            return {"type": "NUMBAR", "value": float(res)} # Floating result is NUMBAR.
        # integer result check
        if float(res).is_integer():
            return {"type": "NUMBR", "value": int(res)}    # Integer result is NUMBR.
        # fallback (should be covered by the above)
        return {"type": "NUMBAR", "value": float(res)}

    # === || Boolean || ===
    def bool_eval(self, op, a, b):
        """
        Performs binary boolean operations (AND, OR, XOR).
        """
        A = self.to_bool(a) # Coerce A to Python boolean.
        B = self.to_bool(b) # Coerce B to Python boolean.

        if op == "BOTH_OF":
            return {"type": "TROOF", "value": A and B}
        # ... (EITHER_OF, WON_OF) ...

    def multi_bool_eval(self, op, vals):
        """
        Performs N-ary boolean operations (ALL OF, ANY OF).
        """
        bs = [self.to_bool(v) for v in vals] # Coerce all operands to booleans.
        if op == "ALL_OF":
            return {"type": "TROOF", "value": all(bs)}
        if op == "ANY_OF":
            return {"type": "TROOF", "value": any(bs)}

    # === || Comparison || ===
    def compare_eval(self, op, a, b):
        """
        Performs comparison operations (BOTH SAEM, DIFFRINT).
        LOLCODE comparison is type-strict (types must match first).
        """
        # direct type match only
        if a["type"] != b["type"]:
            # If types differ, they are considered unequal (DIFFRINT).
            return {"type": "TROOF", "value": (op == "DIFFRINT")}

        same = (a["value"] == b["value"]) # Compare the raw Python values if types match.
        if op == "BOTH_SAEM":
            return {"type": "TROOF", "value": same}
        else:
            return {"type": "TROOF", "value": not same}

    # === || If / O RLY? || ===
    def eval_if(self, node, env):
        """
        Handles conditional execution (O RLY?). Condition defaults to IT if not specified.
        """
        # Condition check: use IT or evaluate the explicit condition.
        cond = self.IT if node.condition is None else self.eval(node.condition, env)
        
        if self.to_bool(cond):
            # Execute the 'YA RLY' block.
            return self.eval_block(node.ya_block, env)
        if node.nowai_block:
            # Execute the 'NO WAI' block. (MEBBE blocks are assumed to be handled inside the AST structure).
            return self.eval_block(node.nowai_block, env)

    # === || Loop || ===
    def eval_loop(self, node, env):
        """
        Handles iteration (IM IN YR... IM OUTTA YR). Supports WILE, TIL, UPPIN, and NERFIN.
        """
        while True:
            # condition check
            if node.condition:
                cond = self.eval(node.condition, env)
                should_continue = self.to_bool(cond)

                if node.mode == "TIL":
                    # 'TIL' condition means loop while NOT true.
                    should_continue = not should_continue
                elif node.mode == "WILE":
                    # 'WILE' condition means loop while true.
                    pass

                if not should_continue:
                    break

            # body execution
            for stmt in node.body:
                res = self.eval(stmt, env)
                # Check for explicit loop break (GTFO).
                if isinstance(res, tuple) and res[0] == "BREAK":
                    return # Exit loop function.

            # update iterator (if loop has an iterator defined)
            if node.iterator:
                v = self.to_number(env.get(node.iterator))
                if node.mode == "UPPIN":
                    v += 1 # Increment.
                elif node.mode == "NERFIN":
                    v -= 1 # Decrement.
                env.set(node.iterator, {"type": "NUMBR", "value": v})

    # === || Switch / WTF? || ===
    def eval_switch(self, node, env):
        """
        Handles the switch statement (WTF?). Compares IT against case literals.
        """
        it_val = self.IT # The value to switch on.

        for lit, body in node.cases:
            case_val = self.eval(lit, env) # Evaluate the OMG case literal.
            # Comparison uses strict value equality.
            if case_val["value"] == it_val["value"]:
                return self.eval_block(body, env) # Execute the case block and exit.

        if node.default:
            # Execute the OMGWTF (default) block if no case matched.
            return self.eval_block(node.default, env)

    # === || Function call || ===
    def eval_call(self, node, env):
        """
        Handles function execution (I IZ...).
        Creates a new environment (static/global scope), binds parameters, and runs the body.
        """
        f = self.functions.get(node.name) # Get the FunctionDef AST node.
        if f is None:
            raise LOLRuntimeError(f"Function {node.name} not found.")

        # new local scope: New environment for function execution, parented to global scope.
        call_env = Environment(parent=self.global_env)

        # evaluate args and bind parameters
        if len(node.args) != len(f.params):
            raise LOLRuntimeError("Argument count mismatch.")

        for param, arg_expr in zip(f.params, node.args):
            # Evaluate arguments in the *caller's* environment ('env').
            # Define parameters in the *function's* local environment ('call_env').
            call_env.define(param, self.eval(arg_expr, env))

        # execute body
        for stmt in f.body:
            res = self.eval(stmt, call_env)
            # Check for return value (FOUND YR).
            if isinstance(res, tuple) and res[0] == "RETURN":
                self.IT = res[1] # Set IT to the return value.
                return res[1]    # Return to the caller.

        # no FOUND was encountered (implicit return)
        self.IT = {"type": "NOOB", "value": None}
        return self.IT # Implicitly returns NOOB.

    # === || Helpers || ===
    def eval_block(self, block, env):
        """
        Executes a sequence of statements (e.g., a function body or IF block).
        Stops execution if a control flow signal (RETURN or BREAK) is received.
        """
        for stmt in block:
            res = self.eval(stmt, env)
            if isinstance(res, tuple):
                return res # Propagate the control flow signal (RETURN/BREAK).

    def cast_literal(self, v):
        """
        Converts a raw literal string/value (from the lexer) into the internal LOLCODE object format.
        """
        if v.startswith('"'):
            # YARN
            return {"type": "YARN", "value": v.strip('"')}
        if v.upper() in ("WIN", "FAIL", "TRUE", "FALSE"):
            # TROOF
            return {"type": "TROOF", "value": (v.upper() in ("WIN", "TRUE"))}
        if "." in v:
            # NUMBAR (float)
            return {"type": "NUMBAR", "value": float(v)}
        # NUMBR (integer)
        return {"type": "NUMBR", "value": int(v)}

    def to_bool(self, val):
        """
        Performs implicit type conversion to TROOF (boolean), adhering to LOLCODE rules.
        """
        t, v = val["type"], val["value"]
        if t == "NOOB":
            return False # NOOB is FAIL.
        # ... (other type conversion rules: non-zero numbers are WIN, non-empty YARN is WIN, etc.) ...
        return False

    def to_number(self, val):
        """
        Performs implicit type conversion to NUMBR/NUMBAR (number).
        """
        t = val["type"]
        v = val["value"]

        # ... (NOOB, TROOF, NUMBR, NUMBAR conversions) ...

        if t == "YARN":
            s = str(v).strip()
            # YARN must be numeric-looking or error
            try:
                if '.' in s:
                    return float(s) # NUMBAR conversion.
                return int(s)       # NUMBR conversion.
            except ValueError:
                # Runtime error if YARN cannot be parsed as a number.
                raise LOLRuntimeError(f"Cannot cast YARN '{s}' to number.")

        raise LOLRuntimeError(f"Cannot convert {t} to number.")

    def to_yarn(self, val):
        """
        Performs implicit type conversion to YARN (string).
        """
        t = val["type"]
        v = val["value"]

        if t == "TROOF":
            return "WIN" if v == True else "FAIL" # TROOF values are converted to WIN/FAIL strings.

        if v is None:
            return "" # NOOB is converted to an empty string.

        return str(v)

    def typecast(self, val, t):
        """
        Handles explicit type casting (MAEK).
        TODO: The current implementation is a placeholder that only changes the type tag. 
        It needs to be expanded to execute the actual conversion logic (e.g., calling 
        to_bool/to_number/to_yarn based on the target type 't').
        """
        # TODO: implement explicit MAEK semantics
        # This line only updates the type field but keeps the old value, which is incomplete.
        return {"type": t, "value": val["value"]}