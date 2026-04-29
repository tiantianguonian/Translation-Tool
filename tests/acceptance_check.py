#!/usr/bin/env python3
"""
acceptance_check.py — Structure safety acceptance tests for Game Translation V3.5.

Validates that translated output preserves:
- Placeholder identity and count ({0}, %s, {name}, etc.)
- Newline count
- || pipe-field structure
- unit_talk tags
"""

import re
import sys
import json


# --- Placeholder patterns ---
PLACEHOLDER_PATTERNS = [
    re.compile(r'\{\d+\}'),          # {0}, {1}, ...
    re.compile(r'%[sd]'),            # %s, %d
    re.compile(r'\{[a-zA-Z_]\w*\}'), # {name}, {value}, ...
]


def extract_placeholders(text: str) -> list:
    """Extract all placeholders from text in order of appearance."""
    found = []
    for pattern in PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            found.append((match.start(), match.group()))
    found.sort(key=lambda x: x[0])
    return [f[1] for f in found]


def check_placeholder_count(source: str, target: str) -> tuple[bool, str]:
    """Placeholder count must match."""
    src_ph = extract_placeholders(source)
    tgt_ph = extract_placeholders(target)
    if len(src_ph) != len(tgt_ph):
        return False, f"Placeholder count mismatch: source={len(src_ph)}, target={len(tgt_ph)}"
    return True, ""


def check_placeholder_identity(source: str, target: str) -> tuple[bool, str]:
    """Every placeholder in source must exist in target."""
    src_ph = set(extract_placeholders(source))
    tgt_ph = set(extract_placeholders(target))
    missing = src_ph - tgt_ph
    if missing:
        return False, f"Missing placeholders in target: {missing}"
    extra = tgt_ph - src_ph
    if extra:
        return False, f"Extra placeholders in target: {extra}"
    return True, ""


def check_newline_count(source: str, target: str) -> tuple[bool, str]:
    """Newline count must match."""
    src_nl = source.count('\n')
    tgt_nl = target.count('\n')
    if src_nl != tgt_nl:
        return False, f"Newline count mismatch: source={src_nl}, target={tgt_nl}"
    return True, ""


def check_pipe_fields(source: str, target: str) -> tuple[bool, str]:
    """Pipe-field count must match (|| separator)."""
    src_fields = source.count('||') + 1
    tgt_fields = target.count('||') + 1
    if src_fields != tgt_fields:
        return False, f"Pipe-field count mismatch: source={src_fields}, target={tgt_fields}"
    return True, ""


def check_unit_talk(source: str, target: str) -> tuple[bool, str]:
    """All [unit_talk:XXX] tags must be preserved exactly."""
    pattern = re.compile(r'\[unit_talk:[^\]]+\]')
    src_tags = pattern.findall(source)
    tgt_tags = pattern.findall(target)
    if set(src_tags) != set(tgt_tags):
        missing = set(src_tags) - set(tgt_tags)
        extra = set(tgt_tags) - set(src_tags)
        msgs = []
        if missing:
            msgs.append(f"Missing unit_talk tags: {missing}")
        if extra:
            msgs.append(f"Extra unit_talk tags: {extra}")
        return False, "; ".join(msgs)
    return True, ""


def run_all_checks(source: str, target: str) -> dict:
    """Run all structure safety checks. Returns dict with results."""
    checks = {
        "placeholder_count": check_placeholder_count(source, target),
        "placeholder_identity": check_placeholder_identity(source, target),
        "newline_count": check_newline_count(source, target),
        "pipe_fields": check_pipe_fields(source, target),
        "unit_talk": check_unit_talk(source, target),
    }

    results = {
        "all_pass": True,
        "checks": {},
        "failures": [],
    }

    for name, (passed, message) in checks.items():
        results["checks"][name] = {"passed": passed, "message": message}
        if not passed:
            results["all_pass"] = False
            results["failures"].append({"check": name, "message": message})

    return results


# --- Self-tests ---
def run_self_tests():
    """Self-test the acceptance checks."""
    errors = []

    # Test 1: Identical text passes all checks
    text = "Hello {0} world\nSecond line||field1||field2"
    result = run_all_checks(text, text)
    if not result["all_pass"]:
        errors.append("Self-test 1 failed: identical text should pass all checks")

    # Test 2: Missing placeholder detected
    result = run_all_checks("Hello {0}", "Hello ")
    if result["checks"]["placeholder_count"]["passed"]:
        errors.append("Self-test 2 failed: missing placeholder should be detected")

    # Test 3: Newline mismatch detected
    result = run_all_checks("Line1\nLine2", "Line1Line2")
    if result["checks"]["newline_count"]["passed"]:
        errors.append("Self-test 3 failed: newline mismatch should be detected")

    # Test 4: Pipe-field mismatch detected
    result = run_all_checks("a||b||c", "a||b")
    if result["checks"]["pipe_fields"]["passed"]:
        errors.append("Self-test 4 failed: pipe-field mismatch should be detected")

    # Test 5: unit_talk tag mismatch detected
    result = run_all_checks("Hello [unit_talk:12345]", "Hello ")
    if result["checks"]["unit_talk"]["passed"]:
        errors.append("Self-test 5 failed: missing unit_talk tag should be detected")

    # Test 6: Multiple placeholder types
    result = run_all_checks("Hello {0} and %s", "Bonjour {0} et %s")
    if not result["all_pass"]:
        errors.append(f"Self-test 6 failed: {result['failures']}")

    if errors:
        print("SELF-TEST FAILURES:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("All self-tests passed.")
        return True


if __name__ == "__main__":
    if "--self-test" in sys.argv or "-t" in sys.argv:
        success = run_self_tests()
        sys.exit(0 if success else 1)
    else:
        # External invocation: print results as JSON
        print(json.dumps({"status": "ready", "checks_available": [
            "placeholder_count", "placeholder_identity",
            "newline_count", "pipe_fields", "unit_talk"
        ]}))
