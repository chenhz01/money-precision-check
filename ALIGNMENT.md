# ALIGNMENT.md — R13 alignment record (16 items)

Design source: `_r13_design.json` → repo `money-precision-check`,
domain 金额精度, sim `adjacent`. Date of record: 2026-10-11.

| # | Item | Evidence |
| --- | --- | --- |
| 1 | Repo name matches design entry | Directory `money-precision-check` == design JSON `name`. |
| 2 | Mechanism implemented as specified | Design mechanism "浮点金额构造/二进制舍入/除法余数三类钱精度风险静态扫描" → rules M1/M2/M3 in core.py (AST-based). |
| 3 | Pure Python standard library only | Imports: argparse, ast, json, os, sys. |
| 4 | CLI entry via argparse | `core.py main()` with paths / --format / --min-severity / --exit-zero; README quickstart runs as written. |
| 5 | self_test.py ≥40 cases, three categories | Functional (M1/M2/M3 triggers + non-money negatives), exception paths (syntax error, IO finding, missing file), extreme edge (empty source, 3000-term line, unicode identifiers, 12-level nesting, CJK names). |
| 6 | Final line `SUMMARY: PASS n/n` | `python self_test.py` ends with that exact line. |
| 7 | README first paragraph ≤60 words | Intro ~55 words (counted 2026-10-11). |
| 8 | README required sections present | All mandated sections incl. FAQ "When NOT to use" and 3 Core Assumptions. |
| 9 | why-not-X ≥3 alternatives with real anchors | Table lists siddharthharbinger/08-currency-rounding-bug (0★), Vukhovanets/CurrencyRounding (0★), aerapass/country-data (3★) with stars from design JSON; differences paraphrased. |
| 10 | MIT LICENSE, "zhengming contributors" | LICENSE copyright line as required; no real names. |
| 11 | CHANGELOG v0.1.0 → v0.1.1 | CHANGELOG.md documents both versions dated 2026-10-11. |
| 12 | Two-round iteration, ≥1 dimension ≥20% | Round 2 added rule M4 (float equality comparison on money-like values) — rule count 3 → 4 (+33%) — plus 10 new tests. Recorded in CHANGELOG v0.1.1. |
| 13 | Number discipline | Test counts quoted from self_test SUMMARY output (repro: `python self_test.py`); README quickstart timings are reproducible approximations. |
| 14 | Zero secrets / zero real names | No keys; "zhengming contributors" copyright; no personal data in findings. |
| 15 | No >50-char text copied from anchors | Anchor facts reduced to name + stars + one paraphrased difference sentence. |
| 16 | as-of date marked | README headline and Confidence footer say "as of 2026-10-11". |
