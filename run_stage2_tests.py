"""Exact-output regression tests. Use lli by default, or --engine jit for local QA."""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(command, stdin=b''):
    return subprocess.run(command, input=stdin, capture_output=True, cwd=ROOT, timeout=15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=['lli', 'jit', 'native'], default='lli')
    args = parser.parse_args()
    if args.engine == 'lli' and shutil.which('lli') is None:
        print('ERROR: lli not found. Install LLVM or use --engine jit for local QA.')
        return 1
    if args.engine == 'native' and shutil.which('cc') is None:
        print('ERROR: cc not found. Native QA requires a C linker driver.')
        return 1
    engine = (['lli'] if args.engine == 'lli' else
              [sys.executable, str(ROOT / ('tools/run_native.py' if args.engine == 'native' else 'tools/run_ir.py'))])
    passed = failed = 0
    totals = {}
    with tempfile.TemporaryDirectory(prefix='stage2_tests_') as directory:
        output = Path(directory) / 'program.ll'
        cases = []
        for source in sorted((ROOT/'tests/ok').glob('*.txt')):
            cases.extend([('ast', source), ('valid', source)])
        for source in sorted((ROOT/'tests/ast_err').glob('*.txt')):
            cases.append(('ast_error', source))
        for source in sorted((ROOT/'tests/err').glob('*.txt')):
            cases.append(('invalid', source))
        for source in sorted((ROOT/'tests/stage2/ok').glob('*.txt')):
            cases.extend([('ast', source), ('valid', source)])
        for source in sorted((ROOT/'tests/stage2/err').glob('*.txt')):
            cases.append(('invalid', source))
        for source in sorted((ROOT/'tests/stage2/runtime').glob('*.txt')):
            cases.append(('runtime', source))
        for kind, source in cases:
            try:
                if kind in {'ast', 'ast_error'}:
                    actual = run([sys.executable, str(ROOT/'compiler.py'), '--ast', str(source)])
                    expected = source.with_suffix('.ast' if kind == 'ast' else '.expected').read_bytes()
                    if kind == 'ast':
                        good = actual.returncode == 0 and not actual.stderr and actual.stdout == expected
                    else:
                        good = actual.returncode != 0 and not actual.stdout and actual.stderr == expected
                else:
                    # Seed an old output to verify that a failing compilation removes it.
                    output.write_text('stale output')
                    compiled = run([sys.executable, str(ROOT/'compiler.py'), str(source), str(output)])
                    actual = compiled
                    if kind == 'invalid':
                        good = (compiled.returncode != 0 and not compiled.stdout and not output.exists()
                                and compiled.stderr == source.with_suffix('.expected').read_bytes())
                    else:
                        good = compiled.returncode == 0 and not compiled.stdout and not compiled.stderr and output.exists()
                        if good:
                            stdin = source.with_suffix('.in').read_bytes() if source.with_suffix('.in').exists() else b''
                            actual = run(engine + [str(output)], stdin)
                            if kind == 'valid':
                                good = actual.returncode == 0 and not actual.stderr and actual.stdout == source.with_suffix('.expected').read_bytes()
                            else:
                                good = (actual.returncode != 0
                                        and actual.stderr == source.with_suffix('.expected').read_bytes()
                                        and actual.stdout == source.with_suffix('.out').read_bytes())
                if not good:
                    print('FAIL', kind, source.relative_to(ROOT))
                    print('  return code:', actual.returncode)
                    print('  stdout:', repr(actual.stdout))
                    print('  stderr:', repr(actual.stderr))
                else:
                    print('PASS', kind, source.relative_to(ROOT))
            except (OSError, subprocess.TimeoutExpired) as error:
                good = False
                print('FAIL', kind, source.relative_to(ROOT), error)
            passed += int(good)
            failed += int(not good)
            counts = totals.setdefault(kind, [0, 0])
            counts[0 if good else 1] += 1
    print('\nCategory: passed / failed')
    for kind, counts in totals.items():
        print(f'{kind}: {counts[0]} / {counts[1]}')
    print(f'Passed: {passed}\nFailed: {failed}')
    return int(failed != 0)


if __name__ == '__main__':
    raise SystemExit(main())
