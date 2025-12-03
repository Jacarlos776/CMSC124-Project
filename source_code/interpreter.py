from parser import (
    Program, VarDecl, Assignment, TypeCastAssignment, TypeOnlyAssignment,
    Gimmeh, Print, IfStmt, Loop, SwitchCase, ImplicitIT,
    Expression, Literal, VarRef,
    FunctionDef, FunctionCall, ReturnStmt, BreakStmt
)

import sys

class LOLRuntimeError(Exception):
    # <<< explanation >>>
    # Custom runtime error type for interpreter-specific errors.
    # Using a dedicated exception class makes it easier to catch interpreter-related
    # issues separately from system exceptions if a GUI or harness wants to.
    pass

# === || Environment || ===
class Environment:
    def __init__(self, parent=None, symbol_callback=None):
        # <<< explanation >>>
        # Each Environment instance holds a map of variables defined in that scope.
        # `parent` allows nested scopes (lexical chaining). `symbol_callback` is an
        # optional hook used to notify external UI components (e.g. debugger or GUI)
        # when symbols are created/updated.
        self.vars = {}          # {name: {"type": "...", "value": ...}}
        self.parent = parent
        self.symbol_callback = symbol_callback

    def define(self, name, value):
        # <<< explanation >>>
        # Create a new variable in THIS environment only. This does not search parent scopes.
        # `value` is expected to be a dict like {"type": "NUMBR", "value": 5}
        self.vars[name] = value
        if self.symbol_callback:
            try:
                # <<< explanation >>>
                # Fire-and-forget callback: GUI updates should not crash interpreter.
                # That's why exceptions are swallowed safely.
                self.symbol_callback(name, value)
            except Exception:
                pass

    def set(self, name, value):
        # <<< explanation >>>
        # Update an existing variable in nearest enclosing environment that defines it.
        # If not found, that's an error (no implicit global creation here).
        env = self.lookup_env(name)
        if env is None:
            raise LOLRuntimeError(f"Variable '{name}' not declared.")
        env.vars[name] = value
        if env.symbol_callback:
            try:
                env.symbol_callback(name, value)
            except Exception:
                pass

    def get(self, name):
        # <<< explanation >>>
        # Retrieve a variable's value from the nearest environment that defines it.
        env = self.lookup_env(name)
        if env is None:
            raise LOLRuntimeError(f"Variable '{name}' not declared.")
        return env.vars[name]

    def lookup_env(self, name):
        # <<< explanation >>>
        # Walk upwards through parent chain to find environment that holds `name`.
        # Returns None if variable is not defined in any accessible scope.
        env = self
        while env:
            if name in env.vars:
                return env
            env = env.parent
        return None


# === || Interpreter || ===
class Interpreter:
    def __init__(self, ast: Program, *, on_output=None, on_input=None, on_symbol_update=None):
        # <<< explanation >>>
        # `ast` is the parsed Program object. Callbacks:
        # - on_output: function(str) for output (VISIBLE)
        # - on_input: function() -> str for GIMMEH input
        # - on_symbol_update: function(name, value) for live variable updates (GUI)
        self.ast = ast
        # pass symbol update callback to environments so they can notify GUI
        self.on_symbol_update = on_symbol_update
        self.global_env = Environment(symbol_callback=self.on_symbol_update)
        # Function table stores FunctionDef nodes; actual body executed on call
        self.functions = {}
        # Special implicit variable IT: used for expressions like O RLY? and implicit returns
        self.IT = {"type": "NOOB", "value": None}
        # I/O callbacks
        self.on_output = on_output
        self.on_input = on_input

    # run interpreter in main program
    def run(self):
        # <<< explanation >>>
        # Two pre-run phases:
        # 1) Evaluate global var declarations (so top-level declarations exist)
        # 2) Register function definitions (so calls can be performed later)
        # Then execute statements (skips function defs during execution).
        for d in self.ast.declarations:
            self.eval(d, self.global_env)

        # register function definitions
        for fn in self.ast.functions:
            self.functions[fn.name] = fn

        # <<< explanation >>>
        # Friendly output of registered functions for debugging / REPL feedback.
        if self.on_output:
            try:
                self.on_output("Registered functions: " + str(list(self.functions.keys())))
            except Exception:
                pass
        else:
            print("Registered functions:", list(self.functions.keys()))

        # run main (skip function defs)
        for stmt in self.ast.statements:
            self.eval(stmt, self.global_env)

    # === || Eval Dispatcher || ===
    def eval(self, node, env):
        # <<< explanation >>>
        # Central dispatch method. It routes AST node instances to the appropriate
        # evaluator. Returning values are consistent across evaluators:
        # - Expressions/assignments return a value {"type": ..., "value": ...}
        # - Control flow signals can return tuples like ("RETURN", value) or ("BREAK", None)
        # - Many statements return None (normal flow)
        if isinstance(node, VarDecl):
            return self.eval_var_decl(node, env)
        if isinstance(node, Assignment):
            return self.eval_assignment(node, env)
        if isinstance(node, TypeCastAssignment):
            return self.eval_type_cast_assignment(node, env)
        if isinstance(node, TypeOnlyAssignment):
            return self.eval_type_only_assignment(node, env)
        if isinstance(node, Gimmeh):
            return self.eval_gimmeh(node, env)
        if isinstance(node, Print):
            return self.eval_print(node, env)
        if isinstance(node, Expression):
            return self.eval_expr(node, env)
        if isinstance(node, Literal):
            # <<< explanation >>>
            # Literals are leaf nodes; cast_literal converts source lexeme (string)
            # to internal typed representation (e.g. "42" -> {"type":"NUMBR","value":42})
            return self.cast_literal(node.value)
        if isinstance(node, VarRef):
            # <<< explanation >>>
            # A VarRef is a variable reference. Special-case "IT" to allow implicit
            # usage (some LOLCode constructs refer to IT implicitly).
            if node.name == "IT": # for implicit IT
                return self.IT
            return env.get(node.name)
        if isinstance(node, IfStmt):
            return self.eval_if(node, env)
        if isinstance(node, Loop):
            return self.eval_loop(node, env)
        if isinstance(node, SwitchCase):
            return self.eval_switch(node, env)
        if isinstance(node, FunctionDef):
            # <<< explanation >>>
            # Function definitions are registered in `run` — evaluating a def is a no-op.
            return None
        if isinstance(node, FunctionCall):
            return self.eval_call(node, env)
        if isinstance(node, ReturnStmt):
            # <<< explanation >>>
            # Return produces a control-flow tuple that bubbles up to the caller.
            return ("RETURN", self.eval(node.value, env))
        if isinstance(node, BreakStmt):
            # <<< explanation >>>
            # Break signals the loop to terminate via a control tuple.
            return ("BREAK", None)
        if isinstance(node, ImplicitIT):
            # <<< explanation >>>
            # Nodes that explicitly request the implicit IT return that value.
            return self.IT

        # <<< explanation >>>
        # Defensive: unknown node types are programmer errors — surface clearly.
        raise LOLRuntimeError("Unhandled AST node type: " + str(type(node)))

    # # === || Variable Declaration || ===
    def eval_var_decl(self, node, env):
        # <<< explanation >>>
        # Two forms: declaration with initializer or without. Without initializer,
        # variables get NOOB type/value which mirrors LOLCode semantics.
        if node.init is None:
            env.define(node.name, {"type": "NOOB", "value": None})
        else:
            val = self.eval(node.init, env)
            env.define(node.name, val)

    # === || Assignment || ===
    def eval_assignment(self, node, env):
        # <<< explanation >>>
        # Regular assignment: evaluate RHS then set the variable in the correct scope.
        val = self.eval(node.value, env)
        env.set(node.target, val)
        # Update implicit IT to the assigned value (common in LOLCode)
        self.IT = val

    def eval_type_cast_assignment(self, node, env):
        # <<< explanation >>>
        # Assignment that casts the source variable to target_type and stores into target.
        # This expects node.source to be a variable name (not an expression).
        val = env.get(node.source)
        casted = self.typecast(val, node.target_type)
        env.set(node.target, casted)
        self.IT = casted

    def eval_type_only_assignment(self, node, env):
        # <<< explanation >>>
        # Change only the type on an existing variable (node.target) to new_type,
        # preserving value by converting it via typecast rules.
        var = env.get(node.target)
        casted = self.typecast(var, node.new_type)
        env.set(node.target, casted)
        self.IT = casted

    # === || Input (Gimmeh) || ===
    def eval_gimmeh(self, node, env):
        # <<< explanation >>>
        # Read input via callback if provided; otherwise use builtin input().
        # Always store as YARN (string); this mirrors typical LOLCode behavior.
        if self.on_input:
            raw = self.on_input()
        else:
            raw = input()
        env.set(node.target, {"type": "YARN", "value": raw})
        self.IT = {"type": "YARN", "value": raw}

    # === || Print || ===
    def eval_print(self, node, env):
        # <<< explanation >>>
        # Evaluate each operand and convert to yarn via to_yarn then concatenate.
        out = ""
        for op in node.operands:
            val = self.eval(op, env)
            out += self.to_yarn(val)
        if self.on_output:
            try:
                self.on_output(out)
            except Exception:
                # <<< explanation >>>
                # Don't let output callback exceptions kill execution.
                pass
        else:
            print(out)
        # Update implicit IT to the resulting printed string
        self.IT = {"type": "YARN", "value": out}

    # === || Expressions & Operators || ===
    def eval_expr(self, node, env):
        # <<< explanation >>>
        # Evaluate expressions. `node.op` decides the operation and arity.
        # Operators map closely to LOLCode keywords.
        op = node.op

        # unary
        if op == "NOT":
            v = self.eval(node.operands[0], env)
            res = {"type": "TROOF", "value": not self.to_bool(v)}
            self.IT = res
            return res

        # infinite arity (concatenation)
        if op == "SMOOSH":
            parts = []
            for o in node.operands:
                parts.append(self.to_yarn(self.eval(o, env)))
            res = {"type": "YARN", "value": "".join(parts)}
            self.IT = res
            return res

        # binary math
        if op in ("SUM_OF", "DIFF_OF", "PRODUKT_OF", "QUOSHUNT_OF", "MOD_OF",
        "BIGGR_OF", "SMALLR_OF"):
            a = self.eval(node.operands[0], env)
            b = self.eval(node.operands[1], env)
            res = self.math_eval(op, a, b)
            self.IT = res
            return res

        # boolean
        if op in ("BOTH_OF", "EITHER_OF", "WON_OF"):
            a = self.eval(node.operands[0], env)
            b = self.eval(node.operands[1], env)
            res = self.bool_eval(op, a, b)
            self.IT = res
            return res

        # ALL OF / ANY OF (n-ary boolean)
        if op in ("ALL_OF", "ANY_OF"):
            res = self.multi_bool_eval(op, [self.eval(x, env) for x in node.operands])
            self.IT = res
            return res

        # comparison
        if op in ("BOTH_SAEM", "DIFFRINT"):
            a = self.eval(node.operands[0], env)
            b = self.eval(node.operands[1], env)
            res = self.compare_eval(op, a, b)
            self.IT = res
            return res

        # <<< explanation >>>
        # If we reach here, the operator was not recognized. Raising an error
        # helps detect parser/AST inconsistencies early.
        raise LOLRuntimeError(f"Unknown operator {op}")

    # === || Math Operators || ===
    def math_eval(self, op, a, b):
        # <<< explanation >>>
        # Convert both inputs to numeric values first (to_number handles casting),
        # then perform the operation. Finally, determine NUMBR vs NUMBAR based on
        # result and original types/values.
        ax = self.to_number(a)
        bx = self.to_number(b)

        if op == "SUM_OF":
            res = ax + bx
        elif op == "DIFF_OF":
            res = ax - bx
        elif op == "PRODUKT_OF":
            res = ax * bx
        elif op == "QUOSHUNT_OF":
            if bx == 0:
                # <<< explanation >>>
                # Division by zero is explicitly trapped and turned into runtime error.
                raise LOLRuntimeError("Division by zero.")
            res = ax / bx
        elif op == "MOD_OF":
            res = ax % bx
        elif op == "BIGGR_OF":
            res = ax if ax >= bx else bx
        elif op == "SMALLR_OF":
            res = ax if ax <= bx else bx
        else:
            raise LOLRuntimeError(f"Unknown math operator {op}")

        # Decide NUMBR vs NUMBAR
        # If result is a float with fractional part -> NUMBAR
        if isinstance(res, float) and not res.is_integer():
            return {"type": "NUMBAR", "value": float(res)}
        # integer result -> NUMBR
        if float(res).is_integer():
            # <<< explanation >>>
            # Convert to int to avoid representing whole numbers as floats.
            return {"type": "NUMBR", "value": int(res)}
        # fallback -> NUMBAR
        return {"type": "NUMBAR", "value": float(res)}

    # === || Boolean || ===
    def bool_eval(self, op, a, b):
        # <<< explanation >>>
        # Convert operands to boolean using to_bool and apply logic.
        A = self.to_bool(a)
        B = self.to_bool(b)

        if op == "BOTH_OF":
            return {"type": "TROOF", "value": A and B}
        if op == "EITHER_OF":
            return {"type": "TROOF", "value": A or B}
        if op == "WON_OF":
            # <<< explanation >>>
            # XOR behavior: True when exactly one operand is True.
            return {"type": "TROOF", "value": A ^ B}

    def multi_bool_eval(self, op, vals):
        # <<< explanation >>>
        # Handle n-ary boolean operators (ALL_OF, ANY_OF).
        bs = [self.to_bool(v) for v in vals]
        if op == "ALL_OF":
            return {"type": "TROOF", "value": all(bs)}
        if op == "ANY_OF":
            return {"type": "TROOF", "value": any(bs)}

    # === || Comparison || ===
    def compare_eval(self, op, a, b):
        # <<< explanation >>>
        # Only consider equality when the types are identical. This matches a
        # stricter interpretation of LOLCode where comparison is type-aware.
        if a["type"] != b["type"]:
            # DIFFRINT true if different types (or different values)
            return {"type": "TROOF", "value": (op == "DIFFRINT")}

        same = (a["value"] == b["value"])
        if op == "BOTH_SAEM":
            return {"type": "TROOF", "value": same}
        else:
            return {"type": "TROOF", "value": not same}

    # === || If / O RLY? || ===
    def eval_if(self, node, env):
        # <<< explanation >>>
        # `node.condition == None` indicates the YA RLY branch should use previous IT value.
        # Support for MEBBE blocks: they are conditional elseif-style branches.
        # Finally, NO WAI is the else branch.
        # Evaluate in order: YA RLY → MEBBEs → NO WAI
        # If a branch executes and produces a control tuple (RETURN/BREAK), it is returned.
        # print(node)
        # added MEBBE block to eval_if
        # 1. Evaluate the YA RLY condition
        cond = self.IT if node.condition is None else self.eval(node.condition, env)
        # YA RLY branch
        if self.to_bool(cond):
            return self.eval_block(node.ya_block, env)

        # 2. Evaluate MEBBE blocks one by one
        for mebbe_cond, mebbe_block in node.mebbe_blocks:
            test_val = self.eval(mebbe_cond, env)
            if self.to_bool(test_val):
                return self.eval_block(mebbe_block, env)

        # 3. NO WAI block
        if node.nowai_block:
            return self.eval_block(node.nowai_block, env)

    # === || Loop || ===
    def eval_loop(self, node, env):
        # <<< explanation >>>
        # Implements several loop forms depending on node.mode:
        # - If node.condition is present: TIL/WILE semantics differ.
        #     - TIL: loop until condition becomes true (i.e., execute while not(condition))
        #     - WILE: loop while condition true
        # - If no condition provided: infinite loop until BREAK or return.
        # - iterator (optional): variable name used as loop counter to be incremented/decremented.
        while True:
            # condition check
            if node.condition:
                cond = self.eval(node.condition, env)
                should_continue = self.to_bool(cond)

                if node.mode == "TIL":
                    # TIL means: loop while NOT(condition). So invert it.
                    should_continue = not should_continue
                elif node.mode == "WILE":
                    # WILE means: loop while condition is true — keep should_continue as is.
                    pass

                if not should_continue:
                    break

            # body
            for stmt in node.body:
                res = self.eval(stmt, env)
                if isinstance(res, tuple) and res[0] == "BREAK":
                    # <<< explanation >>>
                    # BREAK returns control out of the loop. We preserve behavior by returning.
                    return

            # update iterator
            if node.iterator:
                # <<< explanation >>>
                # The iterator must be numeric. We read it from env, change it, and set it back.
                v = self.to_number(env.get(node.iterator))
                if node.mode == "UPPIN":
                    v += 1
                elif node.mode == "NERFIN":
                    v -= 1
                env.set(node.iterator, {"type": "NUMBR", "value": v})

    # === || Switch / WTF? || ===
    def eval_switch(self, node, env):
        """
        Evaluate a WTF? statement using IT as the switch value.
        Coerces IT to the type of each case literal if needed.
        """
        it_val = self.IT

        for lit, body in node.cases:
            case_val = self.eval(lit, env)

            # Coerce IT to case_val type if numeric
            it_cmp = it_val
            if case_val["type"] in ("NUMBR", "NUMBAR") and it_val["type"] == "YARN":
                try:
                    # distinguish int vs float
                    if case_val["type"] == "NUMBR":
                        it_cmp = {"type": "NUMBR", "value": int(it_val["value"])}
                    else:
                        it_cmp = {"type": "NUMBAR", "value": float(it_val["value"])}
                except ValueError:
                    # cannot convert input → skip this case
                    continue

            # Compare values
            if it_cmp["value"] == case_val["value"]:
                return self.eval_block(body, env)

        # default OMGWTF
        if node.default:
            return self.eval_block(node.default, env)


    # === || Function call || ===
    def eval_call(self, node, env):
        # <<< explanation >>>
        # Resolve function by name from the function registry built at startup.
        f = self.functions.get(node.name)
        if f is None:
            raise LOLRuntimeError(f"Function {node.name} not found.")

        # new local scope
        # <<< explanation >>>
        # Call environments use global_env as parent to allow function to access globals
        # but not the caller's locals. This is typical function-level scoping.
        call_env = Environment(parent=self.global_env)

        # evaluate args
        if len(node.args) != len(f.params):
            # <<< explanation >>>
            # Arity mismatch is a runtime error — consistent, explicit behavior.
            raise LOLRuntimeError("Argument count mismatch.")

        for param, arg_expr in zip(f.params, node.args):
            # <<< explanation >>>
            # Evaluate each argument in the caller's environment (env).
            # Store evaluated values in the callee's environment under param names.
            call_env.define(param, self.eval(arg_expr, env))

        # execute body
        for stmt in f.body:
            res = self.eval(stmt, call_env)
            if isinstance(res, tuple) and res[0] == "RETURN":
                # <<< explanation >>>
                # If a return statement was hit, set IT to the returned value and propagate it.
                self.IT = res[1]
                return res[1]
        
        # in case there's no body but there is a return expression. 
        if f.return_expr is not None:
            val = self.eval(f.return_expr, call_env)
            self.IT = val
            return val
        # no FOUND -> functions with no return produce NOOB
        self.IT = {"type": "NOOB", "value": None}
        return self.IT

    # === || Helpers || ===
    def eval_block(self, block, env):
        # <<< explanation >>>
        # Execute a sequence of statements. If a control tuple is returned it is
        # immediately propagated upward (so callers can handle RETURN/BREAK).
        for stmt in block:
            res = self.eval(stmt, env)
            if isinstance(res, tuple):
                return res

    def cast_literal(self, v):
        # <<< explanation >>>
        # Convert literal lexemes to internal typed values. The input `v` is expected
        # to be the string literal as produced by the parser (e.g. '"hello"', '42', '3.14', 'WIN')
        if v.startswith('"'):
            # strip the surrounding quotes for YARN
            return {"type": "YARN", "value": v.strip('"')}
        if v.upper() in ("WIN", "FAIL", "TRUE", "FALSE"):
            # tolerate alternate tokens that parsers or tests may use
            return {"type": "TROOF", "value": (v.upper() in ("WIN", "TRUE"))}
        if "." in v:
            return {"type": "NUMBAR", "value": float(v)}
        return {"type": "NUMBR", "value": int(v)}

    def to_bool(self, val):
        # <<< explanation >>>
        # Truthiness rules:
        # - NOOB is False
        # - TROOF uses its boolean value
        # - Numeric types: 0 is False, non-zero True
        # - YARN: empty string is False, non-empty True
        t, v = val["type"], val["value"]
        if t == "NOOB":
            return False
        if t == "TROOF":
            return v
        if t in ("NUMBR", "NUMBAR"):
            return v != 0
        if t == "YARN":
            return v != ""
        return False

    def to_number(self, val):
        # <<< explanation >>>
        # Convert internal typed values to numeric primitives for math operations.
        # Raises on invalid conversions (e.g. YARN not numeric).
        t = val["type"]
        v = val["value"]

        if t == "NUMBR":
            return int(v)

        if t == "NUMBAR":
            return float(v)

        if t == "TROOF":
            return 1 if v == True else 0

        if t == "NOOB":
            # NOOB → FAIL → 0
            return 0

        if t == "YARN":
            s = str(v).strip()
            # YARN must be numeric-looking or error
            try:
                if '.' in s:
                    return float(s)
                return int(s)
            except ValueError:
                # <<< explanation >>>
                # Strong error model: casting non-numeric string to number is an error.
                raise LOLRuntimeError(f"Cannot cast YARN '{s}' to number.")

        raise LOLRuntimeError(f"Cannot convert {t} to number.")

    def to_yarn(self, val):
        # <<< explanation >>>
        # Convert value to its string representation (YARN) for printing or SMOOSH.
        t = val["type"]
        v = val["value"]

        if t == "TROOF":
            return "WIN" if v == True else "FAIL"

        if v is None:
            # Represent NOOB-like or None values as empty string when printing
            return ""

        return str(v)

    def typecast(self, val, target_type):
        # <<< explanation >>>
        # Powerful helper that converts a typed value into target_type according
        # to rules. It handles explicit casts and some implicit conversions.
        # Raises on unsupported casts.
        src_t = val["type"]
        src_v = val["value"]

        # === NOOB ===
        if src_t == "NOOB":
            # Implicit casting only allowed to TROOF
            if target_type == "TROOF":
                return {"type": "TROOF", "value": False}

            # Explicit typecasting allowed → use empty/zero values
            if target_type == "NUMBR":
                return {"type": "NUMBR", "value": 0}
            if target_type == "NUMBAR":
                return {"type": "NUMBAR", "value": 0.0}
            if target_type == "YARN":
                return {"type": "YARN", "value": ""}

            raise LOLRuntimeError(f"Cannot cast NOOB to {target_type}")

        # === TROOF ===
        if src_t == "TROOF":
            if target_type == "TROOF":
                return {"type": "TROOF", "value": src_v}

            if target_type == "NUMBR":
                return {"type": "NUMBR", "value": 1 if src_v else 0}

            if target_type == "NUMBAR":
                return {"type": "NUMBAR", "value": 1.0 if src_v else 0.0}

            if target_type == "YARN":
                return {"type": "YARN", "value": ("WIN" if src_v else "FAIL")}

            raise LOLRuntimeError(f"Cannot cast TROOF to {target_type}")

        # === NUMBR ===
        if src_t == "NUMBR":
            if target_type == "NUMBR":
                return {"type": "NUMBR", "value": int(src_v)}

            if target_type == "NUMBAR":
                return {"type": "NUMBAR", "value": float(src_v)}

            if target_type == "YARN":
                return {"type": "YARN", "value": str(src_v)}

            if target_type == "TROOF":
                return {"type": "TROOF", "value": (src_v != 0)}

            raise LOLRuntimeError(f"Cannot cast NUMBR to {target_type}")

        # === NUMBAR ===
        if src_t == "NUMBAR":
            if target_type == "NUMBAR":
                return {"type": "NUMBAR", "value": float(src_v)}

            if target_type == "NUMBR":
                # <<< explanation >>>
                # Truncate float when converting to integer NUMBR; this beats rounding
                # in terms of predictable behavior for language semantics.
                return {"type": "NUMBR", "value": int(src_v)}  # truncate

            if target_type == "YARN":
                # <<< explanation >>>
                # Format to at most two decimal places and trim trailing zeros/dot.
                # This yields concise human-readable strings like "3.5" or "2".
                return {"type": "YARN", "value": f"{src_v:.2f}".rstrip('0').rstrip('.')}

            if target_type == "TROOF":
                return {"type": "TROOF", "value": (src_v != 0.0)}

            raise LOLRuntimeError(f"Cannot cast NUMBAR to {target_type}")

        # === YARN ===
        if src_t == "YARN":
            if target_type == "YARN":
                return {"type": "YARN", "value": src_v}

            if target_type in ("NUMBR", "NUMBAR"):
                s = src_v.strip()
                # validate numeric string
                try:
                    if '.' in s:
                        return {"type": "NUMBAR", "value": float(s)}
                    else:
                        return {"type": "NUMBR", "value": int(s)}
                except ValueError:
                    # <<< explanation >>>
                    # Invalid numeric content in a YARN cannot be converted to numbers.
                    raise LOLRuntimeError(f"Cannot cast YARN '{src_v}' to {target_type}")

            if target_type == "TROOF":
                # Empty string → FAIL; else → WIN
                return {"type": "TROOF", "value": (src_v != "")}

            raise LOLRuntimeError(f"Cannot cast YARN to {target_type}")

        # <<< explanation >>>
        # If we reach here, source type is unknown — defensive programming to help debugging.
        raise LOLRuntimeError(f"Unknown source type {src_t}")
