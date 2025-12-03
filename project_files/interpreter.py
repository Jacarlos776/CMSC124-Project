from parser import (
    Program, VarDecl, Assignment, TypeCastAssignment, TypeOnlyAssignment,
    Gimmeh, Print, IfStmt, Loop, SwitchCase, ImplicitIT,
    Expression, Literal, VarRef,
    FunctionDef, FunctionCall, ReturnStmt, BreakStmt
)

import sys

class LOLRuntimeError(Exception):
    pass

# === || Environment || ===
class Environment:
    def __init__(self, parent=None, symbol_callback=None):
        self.vars = {}          # {name: {"type": "...", "value": ...}}
        self.parent = parent
        self.symbol_callback = symbol_callback

    def define(self, name, value):
        self.vars[name] = value
        if self.symbol_callback:
            try:
                self.symbol_callback(name, value)
            except Exception:
                pass

    def set(self, name, value):
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
        env = self.lookup_env(name)
        if env is None:
            raise LOLRuntimeError(f"Variable '{name}' not declared.")
        return env.vars[name]

    def lookup_env(self, name):
        env = self
        while env:
            if name in env.vars:
                return env
            env = env.parent
        return None


# === || Interpreter || ===
class Interpreter:
    def __init__(self, ast: Program, *, on_output=None, on_input=None, on_symbol_update=None):
        self.ast = ast
        # pass symbol update callback to environments so they can notify GUI
        self.on_symbol_update = on_symbol_update
        self.global_env = Environment(symbol_callback=self.on_symbol_update)
        self.functions = {}
        self.IT = {"type": "NOOB", "value": None}
        # I/O callbacks
        self.on_output = on_output
        self.on_input = on_input

    # run interpreter in main program
    def run(self):
        # load globals (var decls in WAZZUP)
        for d in self.ast.declarations:
            self.eval(d, self.global_env)

        # register function definitions
        for fn in self.ast.functions:
            self.functions[fn.name] = fn

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
            return self.cast_literal(node.value)
        if isinstance(node, VarRef):
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
            return None
        if isinstance(node, FunctionCall):
            return self.eval_call(node, env)
        if isinstance(node, ReturnStmt):
            return ("RETURN", self.eval(node.value, env))
        if isinstance(node, BreakStmt):
            return ("BREAK", None)
        if isinstance(node, ImplicitIT):
            return self.IT

        raise LOLRuntimeError("Unhandled AST node type: " + str(type(node)))

    # # === || Variable Declaration || ===
    def eval_var_decl(self, node, env):
        if node.init is None:
            env.define(node.name, {"type": "NOOB", "value": None})
        else:
            val = self.eval(node.init, env)
            env.define(node.name, val)

    # === || Assignment || ===
    def eval_assignment(self, node, env):
        val = self.eval(node.value, env)
        env.set(node.target, val)
        self.IT = val

    def eval_type_cast_assignment(self, node, env):
        val = env.get(node.source)
        casted = self.typecast(val, node.target_type)
        env.set(node.target, casted)
        self.IT = casted

    def eval_type_only_assignment(self, node, env):
        var = env.get(node.target)
        casted = self.typecast(var, node.new_type)
        env.set(node.target, casted)
        self.IT = casted

    # === || Input (Gimmeh) || ===
    def eval_gimmeh(self, node, env):
        if self.on_input:
            raw = self.on_input()
        else:
            raw = input()
        env.set(node.target, {"type": "YARN", "value": raw})
        self.IT = {"type": "YARN", "value": raw}

    # === || Print || ===
    def eval_print(self, node, env):
        out = ""
        for op in node.operands:
            val = self.eval(op, env)
            out += self.to_yarn(val)
        if self.on_output:
            try:
                self.on_output(out)
            except Exception:
                pass
        else:
            print(out)
        self.IT = {"type": "YARN", "value": out}

    # === || Expressions & Operators || ===
    def eval_expr(self, node, env):
        op = node.op

        # unary
        if op == "NOT":
            v = self.eval(node.operands[0], env)
            res = {"type": "TROOF", "value": not self.to_bool(v)}
            self.IT = res
            return res

        # infinite arity
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

        # ALL OF / ANY OF
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

        raise LOLRuntimeError(f"Unknown operator {op}")

    # === || Math Operators || ===
    def math_eval(self, op, a, b):
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
        # If both inputs were NUMBR and result is integer -> NUMBR
        # If either input is NUMBAR -> NUMBAR
        if isinstance(res, float) and not res.is_integer():
            return {"type": "NUMBAR", "value": float(res)}
        # integer result
        if float(res).is_integer():
            return {"type": "NUMBR", "value": int(res)}
        # fallback
        return {"type": "NUMBAR", "value": float(res)}

    # === || Boolean || ===
    def bool_eval(self, op, a, b):
        A = self.to_bool(a)
        B = self.to_bool(b)

        if op == "BOTH_OF":
            return {"type": "TROOF", "value": A and B}
        if op == "EITHER_OF":
            return {"type": "TROOF", "value": A or B}
        if op == "WON_OF":
            return {"type": "TROOF", "value": A ^ B}

    def multi_bool_eval(self, op, vals):
        bs = [self.to_bool(v) for v in vals]
        if op == "ALL_OF":
            return {"type": "TROOF", "value": all(bs)}
        if op == "ANY_OF":
            return {"type": "TROOF", "value": any(bs)}

    # === || Comparison || ===
    def compare_eval(self, op, a, b):
        # direct type match only
        if a["type"] != b["type"]:
            return {"type": "TROOF", "value": (op == "DIFFRINT")}

        same = (a["value"] == b["value"])
        if op == "BOTH_SAEM":
            return {"type": "TROOF", "value": same}
        else:
            return {"type": "TROOF", "value": not same}

    # === || If / O RLY? || ===
    def eval_if(self, node, env):
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
        while True:
            # condition check
            if node.condition:
                cond = self.eval(node.condition, env)
                should_continue = self.to_bool(cond)

                if node.mode == "TIL":
                    should_continue = not should_continue
                elif node.mode == "WILE":
                    pass

                if not should_continue:
                    break

            # body
            for stmt in node.body:
                res = self.eval(stmt, env)
                if isinstance(res, tuple) and res[0] == "BREAK":
                    return

            # update iterator
            if node.iterator:
                v = self.to_number(env.get(node.iterator))
                if node.mode == "UPPIN":
                    v += 1
                elif node.mode == "NERFIN":
                    v -= 1
                env.set(node.iterator, {"type": "NUMBR", "value": v})

    # === || Switch / WTF? || ===
    def eval_switch(self, node, env):
        it_val = self.IT

        for lit, body in node.cases:
            case_val = self.eval(lit, env)
            if case_val["value"] == it_val["value"]:
                return self.eval_block(body, env)

        if node.default:
            return self.eval_block(node.default, env)

    # === || Function call || ===
    def eval_call(self, node, env):
        f = self.functions.get(node.name)
        if f is None:
            raise LOLRuntimeError(f"Function {node.name} not found.")

        # new local scope
        call_env = Environment(parent=self.global_env)

        # evaluate args
        if len(node.args) != len(f.params):
            raise LOLRuntimeError("Argument count mismatch.")

        for param, arg_expr in zip(f.params, node.args):
            call_env.define(param, self.eval(arg_expr, env))

        # execute body
        for stmt in f.body:
            res = self.eval(stmt, call_env)
            if isinstance(res, tuple) and res[0] == "RETURN":
                self.IT = res[1]
                return res[1]
        
        # in case there's no body but there is a return expression. 
        if f.return_expr is not None:
            val = self.eval(f.return_expr, call_env)
            self.IT = val
            return val
        # no FOUND
        self.IT = {"type": "NOOB", "value": None}
        return self.IT

    # === || Helpers || ===
    def eval_block(self, block, env):
        for stmt in block:
            res = self.eval(stmt, env)
            if isinstance(res, tuple):
                return res

    def cast_literal(self, v):
        if v.startswith('"'):
            return {"type": "YARN", "value": v.strip('"')}
        if v.upper() in ("WIN", "FAIL", "TRUE", "FALSE"):
            return {"type": "TROOF", "value": (v.upper() in ("WIN", "TRUE"))}
        if "." in v:
            return {"type": "NUMBAR", "value": float(v)}
        return {"type": "NUMBR", "value": int(v)}

    def to_bool(self, val):
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
                raise LOLRuntimeError(f"Cannot cast YARN '{s}' to number.")

        raise LOLRuntimeError(f"Cannot convert {t} to number.")

    def to_yarn(self, val):
        t = val["type"]
        v = val["value"]

        if t == "TROOF":
            return "WIN" if v == True else "FAIL"

        if v is None:
            return ""

        return str(v)

    def typecast(self, val, target_type):
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
                return {"type": "NUMBR", "value": int(src_v)}  # truncate

            if target_type == "YARN":
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
                    raise LOLRuntimeError(f"Cannot cast YARN '{src_v}' to {target_type}")

            if target_type == "TROOF":
                # Empty string → FAIL; else → WIN
                return {"type": "TROOF", "value": (src_v != "")}

            raise LOLRuntimeError(f"Cannot cast YARN to {target_type}")

        raise LOLRuntimeError(f"Unknown source type {src_t}")