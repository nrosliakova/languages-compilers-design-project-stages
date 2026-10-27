#!/usr/bin/env bash
set -u
cd "$(dirname "$0")" || exit 1

work=$(mktemp -d) || exit 1
trap 'rm -rf "$work"' EXIT
passed=0
failed=0

for source in tests/ok/*.txt tests/ast_err/*.txt; do
    case "$source" in
        tests/ok/*)
            expected="${source%.txt}.ast"
            valid=1
            ;;
        *)
            expected="${source%.txt}.expected"
            valid=0
            ;;
    esac

    if [ ! -f "$expected" ]; then
        echo "FAIL: $source — missing expected file"
        failed=$((failed + 1))
        continue
    fi

    python3 src/compiler.py --ast "$source" \
        > "$work/out" 2> "$work/err"
    code=$?
    success=0

    if [ "$valid" -eq 1 ]; then
        if [ "$code" -eq 0 ] &&
           [ ! -s "$work/err" ] &&
           diff -u "$expected" "$work/out"; then
            success=1
        fi
    else
        if [ "$code" -ne 0 ] &&
           [ ! -s "$work/out" ] &&
           diff -u "$expected" "$work/err"; then
            success=1
        fi
    fi

    if [ "$success" -eq 1 ]; then
        echo "PASS: $source"
        passed=$((passed + 1))
    else
        echo "FAIL: $source"
        echo "Exit code: $code"
        cat "$work/out" "$work/err"
        failed=$((failed + 1))
    fi
done

echo
echo "Passed: $passed"
echo "Failed: $failed"
[ "$failed" -eq 0 ]
