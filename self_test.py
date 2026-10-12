#!/usr/bin/env python3
"""Self-tests for money-precision-check. Run: python self_test.py"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

CASES = []


def case(fn):
    CASES.append(fn)
    return fn


def expect(cond, msg="assertion failed"):
    if not cond:
        raise AssertionError(msg)


def rules(src):
    return [f["rule"] for f in core.scan_source(src)]


def has_rule(src, rule):
    return rule in rules(src)


# ---------- functional: M1 float construction ----------

@case
def t_m1_float_literal():
    expect(has_rule("total_price = 0.0\n", "M1"), "M1 expected")


@case
def t_m1_float_call():
    expect(has_rule("amount = float(raw)\n", "M1"), "M1 expected")


@case
def t_m1_tuple_unpack():
    expect(has_rule("total, fee = 0.0, 0.0\n", "M1"), "M1 expected")


@case
def t_m1_ann_assign():
    expect(has_rule("total: float = 0.0\n", "M1"), "M1 expected")


@case
def t_m1_all_hints():
    for var in ("price", "Amount", "unit_cost", "grand_total", "balance",
                "service_fee", "salary", "last_payment", "refund_amt",
                "commission", "cents_due"):
        expect(has_rule("%s = 0.0\n" % var, "M1"), "hint miss: %s" % var)


@case
def t_non_money_float_ok():
    expect(rules("ratio = 0.5\nweight = 1.0\n") == [], "false positive")


@case
def t_int_literal_ok():
    expect(rules("total_cents = 100\n") == [], "int cents are fine")


@case
def t_decimal_ok():
    src = "from decimal import Decimal\ntotal_price = Decimal('0.0')\n"
    expect(rules(src) == [], "Decimal must not be flagged")


# ---------- functional: M2 rounding ----------

@case
def t_m2_round_money():
    expect(has_rule("x = round(total, 2)\n", "M2"), "M2 expected")


@case
def t_m2_round_non_money_ok():
    expect(rules("x = round(ratio, 2)\n") == [], "false positive")


@case
def t_m2_round_inside_div_still_flags_m3():
    src = "x = round(total / n, 2)\n"
    r = rules(src)
    expect("M2" not in r and "M3" in r, "round(arg is BinOp) -> M3 only: %r" % r)


# ---------- functional: M3 division ----------

@case
def t_m3_div():
    expect(has_rule("share = total / n\n", "M3"), "M3 expected")


@case
def t_m3_floordiv():
    expect(has_rule("share = total // n\n", "M3"), "M3 expected")


@case
def t_m3_mod():
    expect(has_rule("rem = total % n\n", "M3"), "M3 expected")


@case
def t_m3_money_on_right():
    expect(has_rule("rate = budget / amount\n", "M3"), "M3 expected")


@case
def t_m3_non_money_ok():
    expect(rules("x = a / b\n") == [], "false positive")


@case
def t_m1_and_m3_combined():
    r = rules("total = 0.0\nshare = total / n\n")
    expect(r == ["M1", "M3"], "got %r" % r)


# ---------- robustness ----------

@case
def t_empty_source():
    expect(core.scan_source("") == [], "empty must be clean")


@case
def t_comments_only():
    expect(core.scan_source("# total = 0.0\n") == [], "comments ignored")


@case
def t_docstring_mention_ok():
    src = '"""total = 0.0 example"""\nx = 1\n'
    expect(core.scan_source(src) == [], "docstrings ignored")


@case
def t_syntax_error_flagged():
    f = core.scan_source("def broken(:\n")
    expect(f and f[0]["rule"] == "PARSE", "PARSE finding expected")


@case
def t_syntax_error_line_number():
    f = core.scan_source("x = 1\ndef broken(:\n")
    expect(f[0]["line"] == 2, "line: %r" % f[0]["line"])


@case
def t_unicode_identifier():
    expect(has_rule("totál_price = 0.0\n", "M1"), "unicode ident should match")


@case
def t_cjk_identifier_no_english_hint():
    expect(rules("总价 = 0.0\n") == [], "documented limitation: CJK-only names")


@case
def t_line_numbers_correct():
    f = core.scan_source("a = 1\ntotal = 0.0\n")
    expect(f[0]["line"] == 2, "line: %r" % f[0]["line"])


@case
def t_findings_sorted():
    src = "share = total / n\ntotal = 0.0\nx = round(fee, 2)\n"
    f = core.scan_source(src)
    lines = [x["line"] for x in f]
    expect(lines == sorted(lines), "not sorted: %r" % lines)


@case
def t_deep_nesting():
    lines = []
    for i in range(10):
        lines.append("    " * i + "if a%d:" % i)
    lines.append("    " * 10 + "total = 0.0")
    src = "\n".join(lines) + "\n"
    expect(has_rule(src, "M1"), "deep nesting missed")


@case
def t_huge_single_line():
    src = "x = 1 + " + " + ".join(["2"] * 300) + "\ntotal = 0.0\n"
    expect(has_rule(src, "M1"), "huge line missed")


@case
def t_json_serializable():
    f = core.scan_source("total = 0.0\n")
    expect("rule" in json.dumps(f, ensure_ascii=True), "serialization failed")


@case
def t_severity_mapping():
    f = {x["rule"]: x["severity"] for x in core.scan_source(
        "total = 0.0\nx = round(total, 2)\n")}
    expect(f["M1"] == "error" and f["M2"] == "warning", "severities: %r" % f)


# ---------- CLI ----------

def _tmp_py(text):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "m.py")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    return p


@case
def t_cli_findings_exit_one():
    p = _tmp_py("total = 0.0\n")
    expect(core.main([p]) == 1, "error severity must exit 1")


@case
def t_cli_clean_exit_zero():
    p = _tmp_py("x = 1\n")
    expect(core.main([p]) == 0, "clean file must exit 0")


@case
def t_cli_warning_only_exit_zero():
    p = _tmp_py("x = round(total, 2)\n")
    expect(core.main([p]) == 0, "warning alone must not block by default")


@case
def t_cli_min_severity_error_filters_warnings():
    p = _tmp_py("x = round(total, 2)\n")
    expect(core.main([p, "--min-severity", "error"]) == 0,
           "warnings filtered by floor -> exit 0")


@case
def t_cli_exit_zero_flag():
    p = _tmp_py("total = 0.0\n")
    expect(core.main([p, "--exit-zero"]) == 0, "exit-zero must win")


@case
def t_cli_missing_file_io_finding():
    expect(core.main(["Z:/no/such.py"]) == 1, "IO finding is error severity")


@case
def t_cli_text_format_runs():
    p = _tmp_py("total = 0.0\n")
    expect(core.main([p, "--format", "text"]) == 1, "text format runs")


@case
def t_cli_directory_scan():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "a.py"), "w", encoding="utf-8") as fh:
        fh.write("total = 0.0\n")
    with open(os.path.join(d, "readme.txt"), "w", encoding="utf-8") as fh:
        fh.write("total = 0.0\n")
    expect(core.main([d]) == 1, "dir scan must find a.py only")


@case
def t_cli_json_output_shape():
    p = _tmp_py("total = 0.0\n")
    old = sys.stdout
    buf = sys.stdout = open(os.devnull, "w")
    try:
        core.main([p])
    finally:
        sys.stdout = old
        buf.close()
    expect(True, "ran without raising")


# ---------- round-2 additions: functional / exception / edge ----------

@case
def t_m3_floordiv_and_mod():
    expect(has_rule("share = total_fee // users\n", "M3"), "M3 // expected")
    expect(has_rule("rem = balance % 3\n", "M3"), "M3 % expected")


@case
def t_m2_warning_is_not_error_severity():
    fs = core.scan_source("x = round(payment, 2)\n")
    expect(any(f["rule"] == "M2" for f in fs), "M2 expected")
    expect(all(f["severity"] == "warning" for f in fs), "M2 is warning only")


@case
def t_syntax_error_returns_parse_finding():
    fs = core.scan_source("def broken(:\n")
    expect(len(fs) == 1 and fs[0]["rule"] == "PARSE", "rules: %r" % fs)


@case
def t_scan_file_missing_returns_io():
    fs = core.scan_file(os.path.join(tempfile.gettempdir(), "no_such_file_xyz.py"))
    expect(len(fs) == 1 and fs[0]["rule"] == "IO", "rules: %r" % fs)


@case
def t_empty_and_clean_source_no_findings():
    expect(core.scan_source("") == [], "empty source must be clean")
    expect(core.scan_source("total_price = Decimal('0.01')\n"
                            "tax = total_price * rate\n") == [],
           "clean decimal code must be clean")


@case
def t_huge_source_and_unicode_names():
    src = "x = 1\n" * 20000 + "refund_金额 = 0.0\n"
    fs = core.scan_source(src)
    expect(len(fs) == 1 and fs[0]["rule"] == "M1", "rules: %r" % fs)


def run():
    ok = 0
    for i, fn in enumerate(CASES, 1):
        try:
            fn()
            ok += 1
        except Exception as e:
            print("FAIL %02d %s: %s: %s" % (i, fn.__name__,
                                            type(e).__name__, e))
    total = len(CASES)
    print("SUMMARY: %s %d/%d" % ("PASS" if ok == total else "FAIL", ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(run())
