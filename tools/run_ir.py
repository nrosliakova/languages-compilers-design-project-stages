"""Local Linux LLVM-JIT test helper; not a replacement for testing with lli."""
import ctypes
import sys

import llvmlite.binding as llvm


def main():
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    libc = ctypes.CDLL(None)
    for name in ['printf', 'scanf', 'exit', 'write']:
        address = ctypes.cast(getattr(libc, name), ctypes.c_void_p).value
        llvm.add_symbol(name, address)
    with open(sys.argv[1], encoding='utf-8') as source:
        module = llvm.parse_assembly(source.read())
    module.verify()
    machine = llvm.Target.from_default_triple().create_target_machine()
    engine = llvm.create_mcjit_compiler(module, machine)
    engine.finalize_object()
    engine.run_static_constructors()
    result = ctypes.CFUNCTYPE(ctypes.c_int)(engine.get_function_address('main'))()
    libc.fflush(None)
    return result


if __name__ == '__main__':
    raise SystemExit(main())
