from __future__ import print_function

from pylearn2.models.dbm.dbm import DBM
from pylearn2.models.dbm.dbm import RBM
from pylearn2.models.dbm.layer import BinaryVector, BinaryVectorMaxPool, Softmax, GaussianVisLayer

__authors__ = "Ian Goodfellow"
__copyright__ = "Copyright 2012, Universite de Montreal"
__credits__ = ["Ian Goodfellow", "Devon Hjelm"]
__license__ = "3-clause BSD"
__maintainer__ = "LISA Lab"

import numpy as np
import random
assert hasattr(np, 'exp')

from theano.compat.six.moves import xrange
from theano import config
from theano import function
from theano import printing
from theano import tensor as T
from theano.sandbox.rng_mrg import MRG_RandomStreams

from pylearn2.expr.basic import is_binary
from pylearn2.expr.nnet import inverse_sigmoid_numpy
from pylearn2.costs.dbm import VariationalCD
from pylearn2.costs.dbm import BaseCD
from pylearn2.costs.dbm import PCD
import pylearn2.testing.datasets as datasets
from pylearn2.space import VectorSpace
from pylearn2.utils import sharedX
from pylearn2.utils import safe_zip
from pylearn2.utils.data_specs import DataSpecsMapping


class DummyLayer(object):
    """
    A layer that we build for the test that just uses a state
    as its downward message.
    """

    def downward_state(self, state):
        return state

    def downward_message(self, state):
        return state


class DummyDBM(object):
    """
    A dummy DBM for some of the tests below.
    """
    def __init__(self, rng):
        self.rng = rng


class TestBinaryVector:
    """
    Testing class for DBM BinaryVector.
    """
    def setUp(self):
        pass
    @staticmethod
    def check_samples(value, expected_shape, expected_mean, tol):
        """
        Tests that a matrix of binary samples (observations in rows, variables
        in columns)
        1) Has the right shape
        2) Is binary
        3) Converges to the right mean
        """
        assert value.shape == expected_shape
        assert is_binary(value)
        mean = value.mean(axis=0)
        max_error = np.abs(mean-expected_mean).max()
        print('Actual mean:')
        print(mean)
        print('Expected mean:')
        print(expected_mean)
        print('Maximal error:', max_error)
        if max_error > tol:
            raise ValueError("Samples don't seem to have the right mean.")

    def test_make_state(self):
        # Verifies that BinaryVector.make_state creates
        # a shared variable whose value passes check_samples

        n = 5
        num_samples = 1000
        tol = .04

        layer = BinaryVector(nvis = n)

        rng = np.random.RandomState([2012,11,1])

        mean = rng.uniform(1e-6, 1. - 1e-6, (n,))

        z = inverse_sigmoid_numpy(mean)

        layer.set_biases(z.astype(config.floatX))

        init_state = layer.make_state(num_examples=num_samples,
                                      numpy_rng=rng)

        value = init_state.get_value()

        TestBinaryVector.check_samples(value, (num_samples, n), mean, tol)

    def test_sample(self):
        # Verifies that BinaryVector.sample returns an expression
        # whose value passes check_samples

        assert hasattr(np, 'exp')

        n = 5
        num_samples = 1000
        tol = .04

        vis = BinaryVector(nvis=n)
        hid = DummyLayer()

        rng = np.random.RandomState([2012,11,1,259])

        mean = rng.uniform(1e-6, 1. - 1e-6, (n,))

        ofs = rng.randn(n)

        vis.set_biases(ofs.astype(config.floatX))

        z = inverse_sigmoid_numpy(mean) - ofs

        z_var = sharedX(np.zeros((num_samples, n)) + z)

        theano_rng = MRG_RandomStreams(2012+11+1)

        sample = vis.sample(state_above=z_var, layer_above=hid,
                            theano_rng=theano_rng)

        sample = sample.eval()

        TestBinaryVector.check_samples(sample, (num_samples, n), mean, tol)


<<<<<<< HEAD
class TestGaussianVisLayer:

    def setUp(self):
        pass
=======
def check_gaussian_samples(value, nsamples, nvis, rows, cols, channels, expected_mean, tol):
    """
    Tests that a matrix of Gaussian samples (observations in rows, variables
     in columns)
    1) Has the right shape
    2) Is not binary
    3) Converges to the right mean

    """
    if nvis:
        expected_shape = (nsamples, nvis)
    else:
        expected_shape = (nsamples,rows,cols,channels)
    assert value.shape == expected_shape
    assert not is_binary(value)
    mean = value.mean(axis=0)
    max_error = np.abs(mean-expected_mean).max()
    print('Actual mean:')
    print(mean)
    print('Expected mean:')
    print(expected_mean)
    print('Maximal error:', max_error)
    print('Tolerable variance:', tol)
    if max_error > tol:
        raise ValueError("Samples don't seem to have the right mean.")
    else:
        print('Mean is within expected range')


def test_gaussian_vis_layer_make_state():
    """
    Verifies that GaussianVisLayer.make_state creates
    a shared variable whose value passes check_gaussian_samples

    In this case the layer lives in a VectorSpace

    """
    n = 5
    rows = None
    cols = None
    channels = None
    num_samples = 1000
    tol = .042 # tolerated variance
    beta = 1/tol # precision parameter

    layer = GaussianVisLayer(nvis = n, init_beta=beta)

    rng = np.random.RandomState([2012,11,1])

    mean = rng.uniform(1e-6, 1. - 1e-6, (n,))

    z= mean

    layer.set_biases(z.astype(config.floatX))

    init_state = layer.make_state(num_examples=num_samples,
            numpy_rng=rng)

    value = init_state.get_value()

    check_gaussian_samples(value, num_samples, n, rows, cols, channels, mean, tol)

def test_gaussian_vis_layer_make_state_conv():
    """
    Verifies that GaussianVisLayer.make_state creates
    a shared variable whose value passes check_gaussian_samples

    In this case the layer lives in a Conv2DSpace

    """
    n = None
    rows = 3
    cols = 3
    channels = 3
    num_samples = 1000
    tol = .042  # tolerated variance
    beta = 1/tol  # precision parameter
    # axes for batch, rows, cols, channels, can be given in any order
    axes = ['b', 0, 1, 'c']
    random.shuffle(axes)
    axes = tuple(axes)
    print('axes:', axes)

    layer = GaussianVisLayer(rows=rows, cols=cols, channels=channels, init_beta=beta, axes=axes)

    # rng = np.random.RandomState([2012,11,1])
    rng = np.random.RandomState()
    mean = rng.uniform(1e-6, 1. - 1e-6, (rows, cols, channels))

    #z = inverse_sigmoid_numpy(mean)
    z= mean

    layer.set_biases(z.astype(config.floatX))

    init_state = layer.make_state(num_examples=num_samples,
            numpy_rng=rng)

    value = init_state.get_value()
>>>>>>> master

    @staticmethod
    def check_samples(value, nsamples, nvis, rows, cols, channels, expected_mean, tol):
        """
        Tests that a matrix of Gaussian samples (observations in rows, variables
        in columns)
        1) Has the right shape
        2) Is not binary
        3) Converges to the right mean

        """
        if nvis:
            expected_shape = (nsamples, nvis)
        else:
            expected_shape = (nsamples,rows,cols,channels)
        assert value.shape == expected_shape
        assert not is_binary(value)
        mean = value.mean(axis=0)
        max_error = np.abs(mean-expected_mean).max()
        print 'Actual mean:'
        print mean
        print 'Expected mean:'
        print expected_mean
        print 'Maximal error:', max_error
        print 'Tolerable variance:', tol
        if max_error > tol:
            raise ValueError("Samples don't seem to have the right mean.")
        else:
            print 'Mean is within expected range'

    def test_make_state(self, n=5, rows=None, cols=None, channels=None, num_samples=1000, tol=0.042):
        """
        Verifies that GaussianVisLayer.make_state.
        Verified that GaussianVisLayer creates a shared variable whose value passes check_samples.
        In this case the layer lives in a VectorSpace.

        """
        beta = 1/tol # precision parameter
        assert (n is None and (rows is not None and cols is not None and channels is not None)) or\
            (n is not None and (rows == cols == channels == None)),\
            "n must be None or rows, cols, and channels must be None"

        rng = np.random.RandomState([2012,11,1])
        if n is not None:
            layer = GaussianVisLayer(nvis = n, init_beta=beta)
            mean = rng.uniform(1e-6, 1. - 1e-6, (n,))
        else:
            # axes for batch, rows, cols, channels, can be given in any order
            axes = ['b', 0, 1, 'c']
            random.shuffle(axes)
            axes = tuple(axes)
            layer = GaussianVisLayer(rows=rows, cols=cols, channels=channels,
                                     init_beta=beta, axes=axes)
            mean = rng.uniform(1e-6, 1. - 1e-6, (rows, cols, channels))

        z = mean
        layer.set_biases(z.astype(config.floatX))
        init_state = layer.make_state(num_examples=num_samples,
                                      numpy_rng=rng)
        value = init_state.get_value()
        TestGaussianVisLayer.check_samples(value, num_samples, n, rows, cols, channels, mean, tol)

    def test_make_state_conv(self, n=None, rows=3, cols=3, channels=3, num_samples=1000, tol=0.042):
        """
        Verifies that GaussianVisLayer.make_state.
        Verifies that GaussianVisLayer.make_state creates a shared variable
        whose value passes check_samples. In this case the layer lives in a Conv2DSpace.

        Parameters:
        ----------
        n: detector layer dimension.
        num_samples: number of samples or observations over each dimension.
        tol: tolerace in comparisons
        rows: number of rows in convolutional detector. Must be None if n is not None
        cols: number of cols in convolutional detector. Must be None if n is not None
        channels: number of channels in convolutional detector. Must be None if n is not None
        """
        self.test_make_state(n, rows, cols, channels, num_samples, tol)

<<<<<<< HEAD
    def test_sample(self, n=5, rows=None, cols=None, channels=None, num_samples=1000, tol=0.042):
=======
        def downward_state(self, state):
            return state

        def downward_message(self, state):
            return state

    vis = GaussianVisLayer(nvis=n, init_beta=beta)
    hid = DummyLayer()

    rng = np.random.RandomState([2012,11,1,259])

    mean = rng.uniform(1e-6, 1. - 1e-6, (n,))

    ofs = rng.randn(n)

    vis.set_biases(ofs.astype(config.floatX))

    #z = inverse_sigmoid_numpy(mean) - ofs
    z=mean -ofs # linear activation function
    z_var = sharedX(np.zeros((num_samples, n)) + z)
    # mean will be z_var + mu

    theano_rng = MRG_RandomStreams(2012+11+1)

    sample = vis.sample(state_above=z_var, layer_above=hid,
            theano_rng=theano_rng)

    sample = sample.eval()

    check_gaussian_samples(sample, num_samples, n, rows, cols, channels, mean, tol)

def test_gaussian_vis_layer_sample_conv():
    """
    Verifies that GaussianVisLayer.sample returns an expression
    whose value passes check_gaussian_samples.

    In this case the layer lives in a Conv2DSpace

    """
    assert hasattr(np, 'exp')

    n = None
    num_samples = 1000
    tol = .042  # tolerated variance
    beta = 1/tol  # precision parameter
    rows = 3
    cols = 3
    channels = 3
    # axes for batch, rows, cols, channels, can be given in any order
    axes = ['b', 0, 1, 'c']
    random.shuffle(axes)
    axes = tuple(axes)
    print('axes:', axes)

    class DummyLayer(object):
>>>>>>> master
        """
        Verifies that GaussianVisLayer.sample returns an expression whose value passes check_samples.
        In this case the layer lives in a VectorSpace.

        Parameters:
        -----------
        n: detector layer dimension.
        num_samples: number of samples or observations over each dimension.
        tol: tolerace in comparisons
        rows: number of rows in convolutional detector.  Must be None if n is not None
        cols: number of cols in convolutional detector.  Must be None if n is not None
        channels: number of channels in convolutional detector.  Must be None if n is not None
        """
        assert hasattr(np, 'exp')

        beta = 1/tol  # precision parameter
        assert (n is None and (rows is not None and cols is not None and channels is not None)) or\
            (n is not None and (rows == cols == channels == None)),\
            "n must be None or rows, cols, and channels must be None"

        rng = np.random.RandomState([2012,11,1,259])
        if n is not None:
            vis = GaussianVisLayer(nvis=n, init_beta=beta)
            mean = rng.uniform(1e-6, 1. - 1e-6, (n,))
            ofs = rng.randn(n)
        else:
            # axes for batch, rows, cols, channels, can be given in any order
            axes = ['b', 0, 1, 'c']
            random.shuffle(axes)
            axes = tuple(axes)
            vis = GaussianVisLayer(nvis=None,rows=rows, cols=cols,
                                   channels=channels, init_beta=beta, axes=axes)
            mean = rng.uniform(1e-6, 1. - 1e-6, (rows, cols, channels))
            ofs = rng.randn(rows,cols,channels)

        hid = DummyLayer()
        vis.set_biases(ofs.astype(config.floatX))
        z=mean -ofs # linear activation function

        if n is not None:
            z_var = sharedX(np.zeros((num_samples, n)) + z)
        else:
            z_var = sharedX(np.zeros((num_samples, rows, cols, channels)) + z)

        theano_rng = MRG_RandomStreams(2012+11+1)
        sample = vis.sample(state_above=z_var, layer_above=hid,
                            theano_rng=theano_rng)
        sample = sample.eval()
        TestGaussianVisLayer.check_samples(sample, num_samples, n, rows, cols, channels, mean, tol)

    def test_sample_conv(self, n=None, rows=3, cols=3, channels=3, num_samples=1000, tol=0.042):
        """
        Verifies that GaussianVisLayer.sample returns an expression whose value passes check_samples.
        In this case the layer lives in a Conv2DSpace.

        Parameters:
        -----------
        n: detector layer dimension.  Set to None for convolutional.
        num_samples: number of samples or observations over each dimension.
        tol: tolerace in comparisons
        rows: number of rows in convolutional detector.  Must be None if n is not None
        cols: number of cols in convolutional detector.  Must be None if n is not None
        channels: number of channels in convolutional detector.  Must be None if n is not None
        """
        self.test_sample(n, rows, cols, channels, num_samples, tol)


def check_bvmp_samples(value, num_samples, n, pool_size, mean, tol):
    """
    bvmp=BinaryVectorMaxPool
    value: a tuple giving (pooled batch, detector batch)   (all made with same params)
    num_samples: number of samples there should be in the batch
    n: detector layer dimension
    pool_size: size of each pool region
    mean: (expected value of pool unit, expected value of detector units)
    tol: amount the emprical mean is allowed to deviate from the analytical expectation

    checks that:
        1) all values are binary
        2) detector layer units are mutually exclusive
        3) pooled unit is max of the detector units
        4) correct number of samples is present
        5) variables are of the right shapes
        6) samples converge to the right expected value
    """

    pv, hv = value

    assert n % pool_size == 0
    num_pools = n // pool_size

    assert pv.ndim == 2
    assert pv.shape[0] == num_samples
    assert pv.shape[1] == num_pools

    assert hv.ndim == 2
    assert hv.shape[0] == num_samples
    assert hv.shape[1] == n

    assert is_binary(pv)
    assert is_binary(hv)

    for i in xrange(num_pools):
        sub_p = pv[:,i]
        assert sub_p.shape == (num_samples,)
        sub_h = hv[:,i*pool_size:(i+1)*pool_size]
        assert sub_h.shape == (num_samples, pool_size)
        if not np.all(sub_p == sub_h.max(axis=1)):
            for j in xrange(num_samples):
                print(sub_p[j], sub_h[j,:])
                assert sub_p[j] == sub_h[j,:]
            assert False
        assert np.max(sub_h.sum(axis=1)) == 1

    p, h = mean
    assert p.ndim == 1
    assert h.ndim == 1
    emp_p = pv.mean(axis=0)
    emp_h = hv.mean(axis=0)

    max_diff = np.abs(p - emp_p).max()
    if max_diff > tol:
        print('expected value of pooling units: ',p)
        print('empirical expectation: ',emp_p)
        print('maximum difference: ',max_diff)
        raise ValueError("Pooling unit samples have an unlikely mean.")
    max_diff = np.abs(h - emp_h).max()
    if max_diff > tol:
        assert False

def test_bvmp_make_state():

    # Verifies that BinaryVector.make_state creates
    # a shared variable whose value passes check_binary_samples

    num_pools = 3
    num_samples = 1000
    tol = .04
    rng = np.random.RandomState([2012,11,1,9])
    # pool_size=1 is an important corner case
    for pool_size in [1, 2, 5]:
        n = num_pools * pool_size

        layer = BinaryVectorMaxPool(
                detector_layer_dim=n,
                layer_name='h',
                irange=1.,
                pool_size=pool_size)

        # This is just to placate mf_update below
        input_space = VectorSpace(1)
        class DummyDBM(object):
            def __init__(self):
                self.rng = rng
        layer.set_dbm(DummyDBM())
        layer.set_input_space(input_space)

        layer.set_biases(rng.uniform(-pool_size, 1., (n,)).astype(config.floatX))

        # To find the mean of the samples, we use mean field with an input of 0
        mean = layer.mf_update(
                state_below=T.alloc(0., 1, 1),
                state_above=None,
                layer_above=None)

        mean = function([], mean)()

        mean = [ mn[0,:] for mn in mean ]

        state = layer.make_state(num_examples=num_samples,
                numpy_rng=rng)

        value = [elem.get_value() for elem in state]

        check_bvmp_samples(value, num_samples, n, pool_size, mean, tol)


def make_random_basic_binary_dbm(
        rng,
        pool_size_1,
        num_vis = None,
        num_pool_1 = None,
        num_pool_2 = None,
        pool_size_2 = None,
        center = False
        ):
    """
    Makes a DBM with BinaryVector for the visible layer,
    and two hidden layers of type BinaryVectorMaxPool.
    The weights and biases are initialized randomly with
    somewhat large values (i.e., not what you'd want to
    use for learning)

    rng: A numpy RandomState.
    pool_size_1: The size of the pools to use in the first
                 layer.
    """

    if num_vis is None:
        num_vis = rng.randint(1,11)
    if num_pool_1 is None:
        num_pool_1 = rng.randint(1,11)
    if num_pool_2 is None:
        num_pool_2 = rng.randint(1,11)
    if pool_size_2 is None:
        pool_size_2 = rng.randint(1,6)

    num_h1 = num_pool_1 * pool_size_1
    num_h2 = num_pool_2 * pool_size_2

    v = BinaryVector(num_vis, center=center)
    v.set_biases(rng.uniform(-1., 1., (num_vis,)).astype(config.floatX), recenter=center)

    h1 = BinaryVectorMaxPool(
            detector_layer_dim = num_h1,
            pool_size = pool_size_1,
            layer_name = 'h1',
            center = center,
            irange = 1.)
    h1.set_biases(rng.uniform(-1., 1., (num_h1,)).astype(config.floatX), recenter=center)

    h2 = BinaryVectorMaxPool(
            center = center,
            detector_layer_dim = num_h2,
            pool_size = pool_size_2,
            layer_name = 'h2',
            irange = 1.)
    h2.set_biases(rng.uniform(-1., 1., (num_h2,)).astype(config.floatX), recenter=center)

    dbm = DBM(visible_layer = v,
            hidden_layers = [h1, h2],
            batch_size = 1,
            niter = 50)

    return dbm


def test_bvmp_mf_energy_consistent():

    # A test of the BinaryVectorMaxPool class
    # Verifies that the mean field update is consistent with
    # the energy function

    # Specifically, in a DBM consisting of (v, h1, h2), the
    # lack of intra-layer connections means that
    # P(h1|v, h2) is factorial so mf_update tells us the true
    # conditional.
    # We also know P(h1[i] | h1[-i], v)
    #  = P(h, v) / P(h[-i], v)
    #  = P(h, v) / sum_h[i] P(h, v)
    #  = exp(-E(h, v)) / sum_h[i] exp(-E(h, v))
    # So we can check that computing P(h[i] | v) with both
    # methods works the same way

    rng = np.random.RandomState([2012,11,1,613])

    def do_test(pool_size_1):

        # Make DBM and read out its pieces
        dbm = make_random_basic_binary_dbm(
                rng = rng,
                pool_size_1 = pool_size_1,
                )

        v = dbm.visible_layer
        h1, h2 = dbm.hidden_layers

        num_p = h1.get_output_space().dim

        # Choose which unit we will test
        p_idx = rng.randint(num_p)

        # Randomly pick a v, h1[-p_idx], and h2 to condition on
        # (Random numbers are generated via dbm.rng)
        layer_to_state = dbm.make_layer_to_state(1)
        v_state = layer_to_state[v]
        h1_state = layer_to_state[h1]
        h2_state = layer_to_state[h2]

        # Debugging checks
        num_h = h1.detector_layer_dim
        assert num_p * pool_size_1 == num_h
        pv, hv = h1_state
        assert pv.get_value().shape == (1, num_p)
        assert hv.get_value().shape == (1, num_h)

        # Infer P(h1[i] | h2, v) using mean field
        expected_p, expected_h = h1.mf_update(
                state_below = v.upward_state(v_state),
                state_above = h2.downward_state(h2_state),
                layer_above = h2)

        expected_p = expected_p[0, p_idx]
        expected_h = expected_h[0, p_idx * pool_size : (p_idx + 1) * pool_size]

        expected_p, expected_h = function([], [expected_p, expected_h])()

        # Infer P(h1[i] | h2, v) using the energy function
        energy = dbm.energy(V = v_state,
                hidden = [h1_state, h2_state])
        unnormalized_prob = T.exp(-energy)
        assert unnormalized_prob.ndim == 1
        unnormalized_prob = unnormalized_prob[0]
        unnormalized_prob = function([], unnormalized_prob)

        p_state, h_state = h1_state

        def compute_unnormalized_prob(which_detector):
            write_h = np.zeros((pool_size_1,))
            if which_detector is None:
                write_p = 0.
            else:
                write_p = 1.
                write_h[which_detector] = 1.

            h_value = h_state.get_value()
            p_value = p_state.get_value()

            h_value[0, p_idx * pool_size : (p_idx + 1) * pool_size] = write_h
            p_value[0, p_idx] = write_p

            h_state.set_value(h_value)
            p_state.set_value(p_value)

            return unnormalized_prob()

        off_prob = compute_unnormalized_prob(None)
        on_probs = [compute_unnormalized_prob(idx) for idx in xrange(pool_size)]
        denom = off_prob + sum(on_probs)
        off_prob /= denom
        on_probs = [on_prob / denom for on_prob in on_probs]
        assert np.allclose(1., off_prob + sum(on_probs))

        # np.asarray(on_probs) doesn't make a numpy vector, so I do it manually
        wtf_numpy = np.zeros((pool_size_1,))
        for i in xrange(pool_size_1):
            wtf_numpy[i] = on_probs[i]
        on_probs = wtf_numpy

        # Check that they match
        if not np.allclose(expected_p, 1. - off_prob):
            print('mean field expectation of p:',expected_p)
            print('expectation of p based on enumerating energy function values:',1. - off_prob)
            print('pool_size_1:',pool_size_1)

            assert False
        if not np.allclose(expected_h, on_probs):
            print('mean field expectation of h:',expected_h)
            print('expectation of h based on enumerating energy function values:',on_probs)
            assert False

    # 1 is an important corner case
    # We must also run with a larger number to test the general case
    for pool_size in [1, 2, 5]:
        do_test(pool_size)


def test_bvmp_mf_energy_consistent_center():
    """
    A test of the BinaryVectorMaxPool class
    Verifies that the mean field update is consistent with
    the energy function when using Gregoire Montavon's centering
    trick.

    Specifically, in a DBM consisting of (v, h1, h2), the
    lack of intra-layer connections means that
    P(h1|v, h2) is factorial so mf_update tells us the true
    conditional.
    We also know P(h1[i] | h1[-i], v)
    = P(h, v) / P(h[-i], v)
    = P(h, v) / sum_h[i] P(h, v)
    = exp(-E(h, v)) / sum_h[i] exp(-E(h, v))
    So we can check that computing P(h[i] | v) with both
    methods works the same way

    :return:
    """
    rng = np.random.RandomState([2012,11,1,613])

    def do_test(pool_size_1):

        # Make DBM and read out its pieces
        dbm = make_random_basic_binary_dbm(
                rng = rng,
                pool_size_1 = pool_size_1,
                pool_size_2 = 1, # centering is only updated for pool size 1
                center = True
                )

        v = dbm.visible_layer
        h1, h2 = dbm.hidden_layers

        num_p = h1.get_output_space().dim

        # Choose which unit we will test
        p_idx = rng.randint(num_p)

        # Randomly pick a v, h1[-p_idx], and h2 to condition on
        # (Random numbers are generated via dbm.rng)
        layer_to_state = dbm.make_layer_to_state(1)
        v_state = layer_to_state[v]
        h1_state = layer_to_state[h1]
        h2_state = layer_to_state[h2]

        # Debugging checks
        num_h = h1.detector_layer_dim
        assert num_p * pool_size_1 == num_h
        pv, hv = h1_state
        assert pv.get_value().shape == (1, num_p)
        assert hv.get_value().shape == (1, num_h)

        # Infer P(h1[i] | h2, v) using mean field
        expected_p, expected_h = h1.mf_update(
                state_below = v.upward_state(v_state),
                state_above = h2.downward_state(h2_state),
                layer_above = h2)

        expected_p = expected_p[0, p_idx]
        expected_h = expected_h[0, p_idx * pool_size_1 : (p_idx + 1) * pool_size_1]

        expected_p, expected_h = function([], [expected_p, expected_h])()

        # Infer P(h1[i] | h2, v) using the energy function
        energy = dbm.energy(V = v_state,
                hidden = [h1_state, h2_state])
        unnormalized_prob = T.exp(-energy)
        assert unnormalized_prob.ndim == 1
        unnormalized_prob = unnormalized_prob[0]
        unnormalized_prob = function([], unnormalized_prob)

        p_state, h_state = h1_state

        def compute_unnormalized_prob(which_detector):
            write_h = np.zeros((pool_size_1,))
            if which_detector is None:
                write_p = 0.
            else:
                write_p = 1.
                write_h[which_detector] = 1.

            h_value = h_state.get_value()
            p_value = p_state.get_value()

            h_value[0, p_idx * pool_size_1 : (p_idx + 1) * pool_size_1] = write_h
            p_value[0, p_idx] = write_p

            h_state.set_value(h_value)
            p_state.set_value(p_value)

            return unnormalized_prob()

        off_prob = compute_unnormalized_prob(None)
        on_probs = [compute_unnormalized_prob(idx) for idx in xrange(pool_size_1)]
        denom = off_prob + sum(on_probs)
        off_prob /= denom
        on_probs = [on_prob / denom for on_prob in on_probs]
        assert np.allclose(1., off_prob + sum(on_probs))

        # np.asarray(on_probs) doesn't make a numpy vector, so I do it manually
        wtf_numpy = np.zeros((pool_size_1,))
        for i in xrange(pool_size_1):
            wtf_numpy[i] = on_probs[i]
        on_probs = wtf_numpy

        # Check that they match
        if not np.allclose(expected_p, 1. - off_prob):
            print('mean field expectation of p:',expected_p)
            print('expectation of p based on enumerating energy function values:',1. - off_prob)
            print('pool_size_1:',pool_size_1)

            assert False
        if not np.allclose(expected_h, on_probs):
            print('mean field expectation of h:',expected_h)
            print('expectation of h based on enumerating energy function values:',on_probs)
            assert False

    # 1 is the only pool size for which centering is implemented
    do_test(1)

def test_bvmp_mf_sample_consistent():

    # A test of the BinaryVectorMaxPool class
    # Verifies that the mean field update is consistent with
    # the sampling function

    # Specifically, in a DBM consisting of (v, h1, h2), the
    # lack of intra-layer connections means that
    # P(h1|v, h2) is factorial so mf_update tells us the true
    # conditional.
    # We can thus use mf_update to compute the expected value
    # of a sample of h1 from v and h2, and check that samples
    # drawn using the layer's sample method convert to that
    # value.

    rng = np.random.RandomState([2012,11,1,1016])
    theano_rng = MRG_RandomStreams(2012+11+1+1036)
    num_samples = 1000
    tol = .042

    def do_test(pool_size_1):

        # Make DBM and read out its pieces
        dbm = make_random_basic_binary_dbm(
                rng = rng,
                pool_size_1 = pool_size_1,
                )

        v = dbm.visible_layer
        h1, h2 = dbm.hidden_layers

        num_p = h1.get_output_space().dim

        # Choose which unit we will test
        p_idx = rng.randint(num_p)

        # Randomly pick a v, h1[-p_idx], and h2 to condition on
        # (Random numbers are generated via dbm.rng)
        layer_to_state = dbm.make_layer_to_state(1)
        v_state = layer_to_state[v]
        h1_state = layer_to_state[h1]
        h2_state = layer_to_state[h2]

        # Debugging checks
        num_h = h1.detector_layer_dim
        assert num_p * pool_size_1 == num_h
        pv, hv = h1_state
        assert pv.get_value().shape == (1, num_p)
        assert hv.get_value().shape == (1, num_h)

        # Infer P(h1[i] | h2, v) using mean field
        expected_p, expected_h = h1.mf_update(
                state_below = v.upward_state(v_state),
                state_above = h2.downward_state(h2_state),
                layer_above = h2)

        expected_p = expected_p[0, :]
        expected_h = expected_h[0, :]

        expected_p, expected_h = function([], [expected_p, expected_h])()

        # copy all the states out into a batch size of num_samples
        cause_copy = sharedX(np.zeros((num_samples,))).dimshuffle(0,'x')
        v_state = v_state[0,:] + cause_copy
        p, h = h1_state
        h1_state = (p[0,:] + cause_copy, h[0,:] + cause_copy)
        p, h = h2_state
        h2_state = (p[0,:] + cause_copy, h[0,:] + cause_copy)

        h1_samples = h1.sample(state_below = v.upward_state(v_state),
                            state_above = h2.downward_state(h2_state),
                            layer_above = h2, theano_rng = theano_rng)

        h1_samples = function([], h1_samples)()


        check_bvmp_samples(h1_samples, num_samples, num_h, pool_size, (expected_p, expected_h), tol)


    # 1 is an important corner case
    # We must also run with a larger number to test the general case
    for pool_size in [1, 2, 5]:
        do_test(pool_size)

def check_multinomial_samples(value, expected_shape, expected_mean, tol):
    """
    Tests that a matrix of multinomial samples (observations in rows, variables
        in columns)
    1) Has the right shape
    2) Is binary
    3) Has one 1 per row
    4) Converges to the right mean
    """
    assert value.shape == expected_shape
    assert is_binary(value)
    assert np.all(value.sum(axis=1) == 1)
    mean = value.mean(axis=0)
    max_error = np.abs(mean-expected_mean).max()
    if max_error > tol:
        print('Actual mean:')
        print(mean)
        print('Expected mean:')
        print(expected_mean)
        print('Maximal error:', max_error)
        raise ValueError("Samples don't seem to have the right mean.")

def test_softmax_make_state():

    # Verifies that BinaryVector.make_state creates
    # a shared variable whose value passes check_multinomial_samples

    n = 5
    num_samples = 1000
    tol = .04

    layer = Softmax(n_classes = n, layer_name = 'y')

    rng = np.random.RandomState([2012, 11, 1, 11])

    z = 3 * rng.randn(n)

    mean = np.exp(z)
    mean /= mean.sum()

    layer.set_biases(z.astype(config.floatX))

    state = layer.make_state(num_examples=num_samples,
            numpy_rng=rng)

    value = state.get_value()

    check_multinomial_samples(value, (num_samples, n), mean, tol)

def test_softmax_mf_energy_consistent():

    # A test of the Softmax class
    # Verifies that the mean field update is consistent with
    # the energy function

    # Since a Softmax layer contains only one random variable
    # (with n_classes possible values) the mean field assumption
    # does not impose any restriction so mf_update simply gives
    # the true expected value of h given v.
    # We also know P(h |  v)
    #  = P(h, v) / P( v)
    #  = P(h, v) / sum_h P(h, v)
    #  = exp(-E(h, v)) / sum_h exp(-E(h, v))
    # So we can check that computing P(h | v) with both
    # methods works the same way

    rng = np.random.RandomState([2012,11,1,1131])

    # Make DBM
    num_vis = rng.randint(1,11)
    n_classes = rng.randint(1, 11)

    v = BinaryVector(num_vis)
    v.set_biases(rng.uniform(-1., 1., (num_vis,)).astype(config.floatX))

    y = Softmax(
            n_classes = n_classes,
            layer_name = 'y',
            irange = 1.)
    y.set_biases(rng.uniform(-1., 1., (n_classes,)).astype(config.floatX))

    dbm = DBM(visible_layer = v,
            hidden_layers = [y],
            batch_size = 1,
            niter = 50)

    # Randomly pick a v to condition on
    # (Random numbers are generated via dbm.rng)
    layer_to_state = dbm.make_layer_to_state(1)
    v_state = layer_to_state[v]
    y_state = layer_to_state[y]

    # Infer P(y | v) using mean field
    expected_y = y.mf_update(
            state_below = v.upward_state(v_state))

    expected_y = expected_y[0, :]

    expected_y = expected_y.eval()

    # Infer P(y | v) using the energy function
    energy = dbm.energy(V = v_state,
            hidden = [y_state])
    unnormalized_prob = T.exp(-energy)
    assert unnormalized_prob.ndim == 1
    unnormalized_prob = unnormalized_prob[0]
    unnormalized_prob = function([], unnormalized_prob)

    def compute_unnormalized_prob(which):
        write_y = np.zeros((n_classes,))
        write_y[which] = 1.

        y_value = y_state.get_value()

        y_value[0, :] = write_y

        y_state.set_value(y_value)

        return unnormalized_prob()

    probs = [compute_unnormalized_prob(idx) for idx in xrange(n_classes)]
    denom = sum(probs)
    probs = [on_prob / denom for on_prob in probs]

    # np.asarray(probs) doesn't make a numpy vector, so I do it manually
    wtf_numpy = np.zeros((n_classes,))
    for i in xrange(n_classes):
        wtf_numpy[i] = probs[i]
    probs = wtf_numpy

    if not np.allclose(expected_y, probs):
        print('mean field expectation of h:',expected_y)
        print('expectation of h based on enumerating energy function values:',probs)
        assert False

def test_softmax_mf_energy_consistent_centering():

    # A test of the Softmax class
    # Verifies that the mean field update is consistent with
    # the energy function when using the centering trick

    # Since a Softmax layer contains only one random variable
    # (with n_classes possible values) the mean field assumption
    # does not impose any restriction so mf_update simply gives
    # the true expected value of h given v.
    # We also know P(h |  v)
    #  = P(h, v) / P( v)
    #  = P(h, v) / sum_h P(h, v)
    #  = exp(-E(h, v)) / sum_h exp(-E(h, v))
    # So we can check that computing P(h | v) with both
    # methods works the same way

    rng = np.random.RandomState([2012,11,1,1131])

    # Make DBM
    num_vis = rng.randint(1,11)
    n_classes = rng.randint(1, 11)

    v = BinaryVector(num_vis, center=True)
    v.set_biases(rng.uniform(-1., 1., (num_vis,)).astype(config.floatX), recenter=True)

    y = Softmax(
            n_classes = n_classes,
            layer_name = 'y',
            irange = 1., center=True)
    y.set_biases(rng.uniform(-1., 1., (n_classes,)).astype(config.floatX), recenter=True)

    dbm = DBM(visible_layer = v,
            hidden_layers = [y],
            batch_size = 1,
            niter = 50)

    # Randomly pick a v to condition on
    # (Random numbers are generated via dbm.rng)
    layer_to_state = dbm.make_layer_to_state(1)
    v_state = layer_to_state[v]
    y_state = layer_to_state[y]

    # Infer P(y | v) using mean field
    expected_y = y.mf_update(
            state_below = v.upward_state(v_state))

    expected_y = expected_y[0, :]

    expected_y = expected_y.eval()

    # Infer P(y | v) using the energy function
    energy = dbm.energy(V = v_state,
            hidden = [y_state])
    unnormalized_prob = T.exp(-energy)
    assert unnormalized_prob.ndim == 1
    unnormalized_prob = unnormalized_prob[0]
    unnormalized_prob = function([], unnormalized_prob)

    def compute_unnormalized_prob(which):
        write_y = np.zeros((n_classes,))
        write_y[which] = 1.

        y_value = y_state.get_value()

        y_value[0, :] = write_y

        y_state.set_value(y_value)

        return unnormalized_prob()

    probs = [compute_unnormalized_prob(idx) for idx in xrange(n_classes)]
    denom = sum(probs)
    probs = [on_prob / denom for on_prob in probs]

    # np.asarray(probs) doesn't make a numpy vector, so I do it manually
    wtf_numpy = np.zeros((n_classes,))
    for i in xrange(n_classes):
        wtf_numpy[i] = probs[i]
    probs = wtf_numpy

    if not np.allclose(expected_y, probs):
        print('mean field expectation of h:',expected_y)
        print('expectation of h based on enumerating energy function values:',probs)
        assert False

def test_softmax_mf_sample_consistent():

    # A test of the Softmax class
    # Verifies that the mean field update is consistent with
    # the sampling function

    # Since a Softmax layer contains only one random variable
    # (with n_classes possible values) the mean field assumption
    # does not impose any restriction so mf_update simply gives
    # the true expected value of h given v.
    # We can thus use mf_update to compute the expected value
    # of a sample of y conditioned on v, and check that samples
    # drawn using the layer's sample method convert to that
    # value.

    rng = np.random.RandomState([2012,11,1,1154])
    theano_rng = MRG_RandomStreams(2012+11+1+1154)
    num_samples = 1000
    tol = .042

    # Make DBM
    num_vis = rng.randint(1,11)
    n_classes = rng.randint(1, 11)

    v = BinaryVector(num_vis)
    v.set_biases(rng.uniform(-1., 1., (num_vis,)).astype(config.floatX))

    y = Softmax(
            n_classes = n_classes,
            layer_name = 'y',
            irange = 1.)
    y.set_biases(rng.uniform(-1., 1., (n_classes,)).astype(config.floatX))

    dbm = DBM(visible_layer = v,
            hidden_layers = [y],
            batch_size = 1,
            niter = 50)

    # Randomly pick a v to condition on
    # (Random numbers are generated via dbm.rng)
    layer_to_state = dbm.make_layer_to_state(1)
    v_state = layer_to_state[v]
    y_state = layer_to_state[y]

    # Infer P(y | v) using mean field
    expected_y = y.mf_update(
            state_below = v.upward_state(v_state))

    expected_y = expected_y[0, :]

    expected_y = expected_y.eval()

    # copy all the states out into a batch size of num_samples
    cause_copy = sharedX(np.zeros((num_samples,))).dimshuffle(0,'x')
    v_state = v_state[0,:] + cause_copy
    y_state = y_state[0,:] + cause_copy

    y_samples = y.sample(state_below = v.upward_state(v_state), theano_rng=theano_rng)

    y_samples = function([], y_samples)()

    check_multinomial_samples(y_samples, (num_samples, n_classes), expected_y, tol)


def test_make_symbolic_state():
    # Tests whether the returned p_sample and h_sample have the right
    # dimensions
    num_examples = 40
    theano_rng = MRG_RandomStreams(2012+11+1)

    visible_layer = BinaryVector(nvis=100)
    rval = visible_layer.make_symbolic_state(num_examples=num_examples,
                                             theano_rng=theano_rng)

    hidden_layer = BinaryVectorMaxPool(detector_layer_dim=500,
                                       pool_size=1,
                                       layer_name='h',
                                       irange=0.05,
                                       init_bias=-2.0)
    p_sample, h_sample = hidden_layer.make_symbolic_state(num_examples=num_examples,
                                                          theano_rng=theano_rng)

    softmax_layer = Softmax(n_classes=10, layer_name='s', irange=0.05)
    h_sample_s = softmax_layer.make_symbolic_state(num_examples=num_examples,
                                                   theano_rng=theano_rng)

    required_shapes = [(40, 100), (40, 500), (40, 500), (40, 10)]
    f = function(inputs=[],
                 outputs=[rval, p_sample, h_sample, h_sample_s])

    for s, r in zip(f(), required_shapes):
        assert s.shape == r



def check_gradients(expected_grad, actual_grad, corr_tol=0.8, mean_tol=0.05):
    corr = np.corrcoef(expected_grad.flatten(), actual_grad.flatten())[0,1]
    assert corr >= corr_tol,\
        ("Correlation did not pass: (%.2f > %.2f)\n" % (corr_tol, corr)) +\
        ("Expected:\n %r\n" % expected_grad) +\
        ("Actual:\n %r" % actual_grad)
    assert (abs(np.mean(expected_grad) - np.mean(actual_grad)) /
            (np.mean(expected_grad) + np.mean(actual_grad))) < mean_tol,\
            "Mean did not pass (%.2f expected vs %.2f actual)" %\
            (np.mean(expected_grad), np.mean(actual_grad))

def make_rbm(num_visible, num_hidden, batch_size, n_classes=0, center=False, rng=None):
    if rng is None:
        rng = np.random.RandomState([2014,10,7])

    visible_layer = BinaryVector(nvis=num_visible)
    visible_layer.set_biases(rng.uniform(-1., 1., (num_visible,)).astype(config.floatX))
    hidden_layer = BinaryVectorMaxPool(detector_layer_dim=num_hidden,
                                                                pool_size=1,
                                                                layer_name='h',
                                                                irange=0.05,
                                                                init_bias=-2.0,
                                                                center=center)
    hidden_layer.set_biases(rng.uniform(-1., 1., (num_hidden,)).astype(config.floatX), recenter=center)
    if n_classes > 0:
        label_layer = Softmax(n_classes=n_classes,
                              layer_name = 'y',
                              irange = 1.)
    model = RBM(visible_layer=visible_layer,
                           hidden_layer=hidden_layer,
                           batch_size=batch_size, niter=1)

    return model

class Test_CD(object):
    """
    Class to test contrastive divergence.
    """

    @staticmethod
    def check_rbm_pos_phase(rbm, cost, X, Y=None, tol=0.8):
        if rbm.label_layer is not None:
            assert Y is not None
        else:
            assert Y is None

        pos_grads, updates = cost._get_positive_phase(rbm, X)

        visible_layer = rbm.visible_layer
        hidden_layer = rbm.hidden_layers[0]
        label_layer = rbm.label_layer
        P_H0_given_X = hidden_layer.mf_update(state_below=visible_layer.upward_state(X),
                                              state_above=None, layer_above=None)[1]

        dW_pos_exp = -1 * np.dot(X.eval().T, P_H0_given_X.eval()) / rbm.batch_size
        dW_pos_act = pos_grads[hidden_layer.transformer.get_params()[0]].eval()
        check_gradients(dW_pos_exp, dW_pos_act, corr_tol=tol)

        dvb_pos_exp = -np.mean(X.eval(), axis=0)
        dvb_pos_act = pos_grads[visible_layer.bias].eval()
        check_gradients(dvb_pos_exp, dvb_pos_act, corr_tol=tol)

        dvh_pos_exp = -np.mean(P_H0_given_X.eval(), axis=0)
        dvh_pos_act = pos_grads[hidden_layer.b].eval()
        check_gradients(dvh_pos_exp, dvh_pos_act, corr_tol=tol)

        return pos_grads, updates

    @staticmethod
    def check_rbm_neg_phase(rbm, cost, X, Y=None, theano_rng=None, tol=0.85):
        if rbm.label_layer is not None:
            assert Y is not None
        else:
            assert Y is None

        assert theano_rng is not None

        neg_grads, updates = cost._get_negative_phase(rbm, X)

        visible_layer = rbm.visible_layer
        hidden_layer = rbm.hidden_layers[0]

        P_H0_given_X = hidden_layer.mf_update(state_below = visible_layer.upward_state(X),
                                              state_above=None, layer_above=None)[1]
        H0 = hidden_layer.sample(state_below=visible_layer.upward_state(X),
                                 state_above=None, layer_above=None,
                                 theano_rng=theano_rng)[1]
        V1 = visible_layer.sample(state_above=H0, layer_above=hidden_layer,
                                  theano_rng=theano_rng)
        P_H1_given_V1 = hidden_layer.mf_update(state_below=visible_layer.upward_state(V1),
                                               state_above=None, layer_above=None)[1]
        dW_neg_act = neg_grads[hidden_layer.transformer.get_params()[0]].eval()
        dW_neg_exp = np.dot(V1.eval().T, P_H1_given_V1.eval()) / rbm.batch_size
        check_gradients(dW_neg_exp, dW_neg_act, corr_tol=tol)

        dvb_neg_exp = np.mean(V1.eval(), axis=0)
        dvb_neg_act = neg_grads[visible_layer.bias].eval()
        check_gradients(dvb_neg_exp, dvb_neg_act, corr_tol=tol)

        dvh_neg_exp = np.mean(P_H1_given_V1.eval(), axis=0)
        dvh_neg_act = neg_grads[hidden_layer.b].eval()
        check_gradients(dvh_neg_exp, dvh_neg_act, corr_tol=tol)

        return neg_grads, updates

    def test_rbm(self, num_visible=100, num_hidden=50, batch_size=5000, variational=False):
        rng = np.random.RandomState([2014,10,7])
        theano_rng = MRG_RandomStreams(2024+30+9)

        # Set up the RBM (One hidden layer DBM)
        rbm = make_rbm(num_visible, num_hidden, batch_size, rng=rng)

        if variational:
            cost = VariationalCD(num_gibbs_steps=1)
        else:
            cost = BaseCD(num_gibbs_steps=1)

        # Set the data
        X = sharedX(rng.randn(batch_size, num_visible))
        # Get the gradients from the cost function
        grads, updates = cost.get_gradients(rbm, X)
        Test_CD.check_rbm_pos_phase(rbm, cost, X)
        Test_CD.check_rbm_neg_phase(rbm, cost, X, theano_rng=theano_rng)

    def test_rbm_varational(self, num_visible=100, num_hidden=50, batch_size=200):
        self.test_rbm(num_visible, num_hidden, batch_size, variational=True)
"""
    def test_variational_cd(self):

        # Verifies that VariationalCD works well with make_layer_to_symbolic_state
        visible_layer = BinaryVector(nvis=100)
        hidden_layer = BinaryVectorMaxPool(detector_layer_dim=500,
                                           pool_size=1,
                                           layer_name='h',
                                           irange=0.05,
                                           init_bias=-2.0)
        model = DBM(visible_layer=visible_layer,
                    hidden_layers=[hidden_layer],
                    batch_size=100,
                    niter=1)

        cost = VariationalCD(num_chains=100, num_gibbs_steps=2)

        data_specs = cost.get_data_specs(model)
        mapping = DataSpecsMapping(data_specs)
        space_tuple = mapping.flatten(data_specs[0], return_tuple=True)
        source_tuple = mapping.flatten(data_specs[1], return_tuple=True)

        theano_args = []
        for space, source in safe_zip(space_tuple, source_tuple):
            name = '%s' % (source)
            arg = space.make_theano_batch(name=name)
            theano_args.append(arg)
        theano_args = tuple(theano_args)
        nested_args = mapping.nest(theano_args)

        grads, updates = cost.get_gradients(model, nested_args)
"""
"""
class TestLabels(object):
    def test_label_equivalence(self, num_visible=100, num_hidden=50, num_labels=10, batch_size=200):
        #Tests steps of learning with labels.
        rng = np.random.RandomState([2014,10,7])
        theano_rng = MRG_RandomStreams(2024+30+9)

        # Set up the RBM (One hidden layer DBM)
        rbm = make_rbm(num_visible, num_hidden, num_labels, batch_size, rng=rng)

        cost = BaseCD(num_gibbs_steps=1)

        # Set the data
        X = sharedX(rng.randn(batch_size, num_visible))
        Y = sharedX(rng.randint(0,10), batch_size)
        Test_CD.check_rbm_pos_phase(rbm, cost, X, Y)
        Test_CD.check_rbm_neg_phase(rbm, cost, X, Y, theano_rng=theano_rng)
"""

def test_extra():
    """
    Test functionality that remains private, if available.
    """

    try:
        import galatea
    except ImportError:
        return
    from galatea.dbm.pylearn2_bridge import run_unit_tests
    run_unit_tests()
