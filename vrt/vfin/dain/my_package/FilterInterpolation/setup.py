import json
from setuptools import setup

from torch.utils.cpp_extension import BuildExtension, CUDAExtension

with open('../../compiler_args.json') as f:
    extra_compile_args = json.load(f)
setup(
    name='filterinterpolation_cuda',
    ext_modules=[
        CUDAExtension('filterinterpolation_cuda', [
            'filterinterpolation_cuda.cc',
            'filterinterpolation_cuda_kernel.cu'
        ], extra_compile_args=extra_compile_args)
    ],
    cmdclass={
        'build_ext': BuildExtension
    })
