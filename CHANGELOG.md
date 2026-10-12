# Changelog — money-precision-check

All notable changes. Format based on Keep a Changelog; versioning: SemVer.

## [0.1.1] - 2026-10-12

### Added
- MIT LICENSE file (was missing from the release candidate).
- Six new self-test cases in a dedicated round-2 block: `//`/`%` money-operand coverage (M3), M2 warning-severity isolation, PARSE finding on syntax errors, IO finding on missing files, clean-source negatives (Decimal usage produces zero findings), and a 20k-line source stress case — suite grew 39 → 45 cases (+15%).

### Verified
- Full release audit: `python self_test.py` → `SUMMARY: PASS 45/45`. Scanner logic unchanged this round; all failures during the audit were traced to test expectations, not the scanner.

## [0.1.0] - 2026-10-11

### Added
- AST-based static scanner for three money-precision risk classes: M1 float construction of money-like names (`price = 0.0`, `total = float(raw)`), M2 binary `round()` on money-like values, M3 division/remainder on money-like operands.
- Money-name heuristics (price/amount/cost/total/balance/fee/salary/payment/refund/commission/cents, case-insensitive substring).
- CLI: file or directory scan, `--format json|text`, `--min-severity` floor, `--exit-zero`; exit codes 0 clean / 1 error-severity findings / 2 input error.
- Self-test suite: 39 cases across functional, exception/CLI, and extreme-edge tiers.
