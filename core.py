#!/usr/bin/env python3
"""money-precision-check: static scanner for money-precision risks in
Python source code. Detects float construction of money-like values (M1),
binary rounding of money-like values (M2), and division/remainder on
money-like values (M3). AST-based, pure standard library, offline.
"""
import argparse
import ast
import json
import os
import sys

MONEY_HINTS = ("price", "amount", "cost", "total", "balance", "fee",
               "salary", "payment", "refund", "commission", "cents")

RULES = {
    "M1": ("error", "float construction of a money-like value"),
    "M2": ("warning", "binary rounding (round) applied to a money-like value"),
    "M3": ("error", "division/remainder on a money-like value"),
}
SEVERITY_ORDER = {"warning": 0, "error": 1}


def is_money(name):
    if not isinstance(name, str):
        return False
    low = name.lower()
    return any(h in low for h in MONEY_HINTS)


def _target_names(node):
    if isinstance(node, ast.Tuple):
        out = []
        for e in node.elts:
            out.extend(_target_names(e))
        return out
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Starred):
        return _target_names(node.value)
    return []


class Scanner(ast.NodeVisitor):
    def __init__(self, filename="<source>"):
        self.findings = []
        self.filename = filename

    def _add(self, node, rule, detail):
        severity, desc = RULES[rule]
        self.findings.append({
            "file": self.filename,
            "line": getattr(node, "lineno", 0),
            "col": getattr(node, "col_offset", 0),
            "rule": rule,
            "severity": severity,
            "message": "%s (%s)" % (desc, detail),
        })

    def visit_Assign(self, node):
        names = []
        for t in node.targets:
            names.extend(_target_names(t))
        self._check_assignment(node.value, names, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if node.value is not None:
            self._check_assignment(node.value, _target_names(node.target), node)
        self.generic_visit(node)

    def _check_assignment(self, value, names, node):
        money = [n for n in names if is_money(n)]
        if not money:
            return
        if isinstance(value, ast.Tuple):
            if all(isinstance(e, ast.Constant) and isinstance(e.value, float)
                   for e in value.elts) and len(value.elts) == len(names):
                self._add(node, "M1",
                          "float literal tuple -> %s" % ", ".join(money))
            return
        if isinstance(value, ast.Constant) and isinstance(value.value, float):
            self._add(node, "M1", "float literal -> %s" % ", ".join(money))
        elif (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
              and value.func.id == "float"):
            self._add(node, "M1", "float() -> %s" % ", ".join(money))

    def visit_Call(self, node):
        if (isinstance(node.func, ast.Name) and node.func.id == "round"
                and node.args):
            arg = node.args[0]
            if isinstance(arg, ast.Name) and is_money(arg.id):
                self._add(node, "M2", "round(%s, ...)" % arg.id)
        self.generic_visit(node)

    def visit_BinOp(self, node):
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            names = _target_names(node.left) + _target_names(node.right)
            if any(is_money(n) for n in names):
                if isinstance(node.op, ast.Div):
                    op = "/"
                elif isinstance(node.op, ast.FloorDiv):
                    op = "//"
                else:
                    op = "%"
                self._add(node, "M3", "money-like operand in '%s'" % op)
        self.generic_visit(node)


def scan_source(src, filename="<source>"):
    """Scan Python source text; returns a list of finding dicts."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [{"file": filename, "line": e.lineno or 0, "col": 0,
                 "rule": "PARSE", "severity": "error",
                 "message": "syntax error: %s" % (e.msg or "invalid syntax")}]
    scanner = Scanner(filename)
    scanner.visit(tree)
    scanner.findings.sort(key=lambda f: (f["line"], f["col"], f["rule"]))
    return scanner.findings


def scan_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return scan_source(f.read(), path)
    except OSError as e:
        return [{"file": path, "line": 0, "col": 0, "rule": "IO",
                 "severity": "error", "message": str(e)}]


def scan_path(path):
    findings = []
    if os.path.isdir(path):
        for root, _dirs, files in os.walk(path):
            for fn in sorted(files):
                if fn.endswith(".py"):
                    findings.extend(scan_file(os.path.join(root, fn)))
    else:
        findings.extend(scan_file(path))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="money-precision-check",
        description="Static scan for float-money precision risks (M1/M2/M3).")
    parser.add_argument("paths", nargs="+", help=".py files or directories")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--min-severity", choices=("warning", "error"),
                        default="warning")
    parser.add_argument("--exit-zero", action="store_true",
                        help="always exit 0 when scan completed")
    args = parser.parse_args(argv)

    findings = []
    for p in args.paths:
        findings.extend(scan_path(p))
    floor = SEVERITY_ORDER[args.min_severity]
    findings = [f for f in findings if SEVERITY_ORDER[f["severity"]] >= floor]

    if args.format == "text":
        for f in findings:
            print("%s:%d:%d %s[%s] %s" % (f["file"], f["line"], f["col"],
                                          f["rule"], f["severity"],
                                          f["message"]))
        print("findings: %d" % len(findings))
    else:
        print(json.dumps({"findings": findings, "count": len(findings)},
                         ensure_ascii=True, indent=2, sort_keys=True))
    blocking = any(f["severity"] == "error" for f in findings)
    if args.exit_zero:
        return 0
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
