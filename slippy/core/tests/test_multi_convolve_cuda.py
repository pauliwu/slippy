import slippy
import slippy.core as core
import numpy as np
import numpy.testing as npt
import itertools


def test_basic_multi_convolve_cuda():
    try:
        import cupy as cp
        slippy.CUDA = True
    except ImportError:
        return
    comps = [a + b for a, b in itertools.product('xyz', 'xyz')]
    ims = np.array([core.elastic_influence_matrix(comp, (64, 64), [1e-6] * 2, 200e9, 0.3) for comp in comps])
    loads = np.zeros_like(ims[0])
    loads[31, 31] = 1
    out = core.plan_multi_convolve(loads, ims, circular=True)(loads)
    for expt, got in zip(ims, out):
        npt.assert_allclose(cp.asnumpy(got), cp.asnumpy(expt), atol=1e-30)


def test_vs_sequential():
    try:
        import cupy as cp
        slippy.CUDA = True
    except ImportError:
        return
    periodics = [(False, False), (True, False), (False, True), (True, True)]
    domains = (None, 0.5 > np.random.rand(16, 16))
    comps = ['xz', 'zz']
    loads = np.random.rand(16, 16)
    for p, d in itertools.product(periodics, domains):
        im_shape = tuple((2-p)*s for p, s in zip(p, loads.shape))
        ims = np.array([core.elastic_influence_matrix(comp, im_shape, [1e-6] * 2, 200e9, 0.3) for comp in comps])
        multi_func = core.plan_multi_convolve(loads, ims, d, p)
        if d is None:
            multi_result = multi_func(loads)
        else:
            multi_result = multi_func(loads[d])
        single_results = np.zeros_like(multi_result)
        single_funcs = []
        for i in range(2):
            single_func = core.plan_convolve(loads, ims[i], d, p)
            if d is None:
                single_results[i] = single_func(loads)
            else:
                single_results[i] = single_func(loads[d])
            single_funcs.append(single_func)

        npt.assert_allclose(cp.asnumpy(multi_result), cp.asnumpy(single_results), atol=1e-30)

        if d is not None:
            multi_result = multi_func(loads[d], ignore_domain=True)
            single_results = np.zeros_like(multi_result)
            for i in range(2):
                single_results[i] = single_funcs[i](loads[d], ignore_domain=True)

            npt.assert_allclose(cp.asnumpy(multi_result), cp.asnumpy(single_results), atol=1e-30)
