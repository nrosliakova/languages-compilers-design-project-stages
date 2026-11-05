"""Verify IR, emit native object code with LLVM, link with cc and execute."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import llvmlite.binding as llvm


def main():
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    module = llvm.parse_assembly(Path(sys.argv[1]).read_text(encoding='utf-8'))
    module.verify()
    machine = llvm.Target.from_default_triple().create_target_machine(reloc='pic')
    module.data_layout = str(machine.target_data)
    with tempfile.TemporaryDirectory(prefix='stage2_native_') as directory:
        obj = Path(directory) / 'program.o'
        binary = Path(directory) / 'program'
        obj.write_bytes(machine.emit_object(module))
        subprocess.run([os.environ.get('CC', 'cc'), str(obj), '-o', str(binary)], check=True)
        return subprocess.run([str(binary)]).returncode


if __name__ == '__main__':
    raise SystemExit(main())
