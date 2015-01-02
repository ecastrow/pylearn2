"""
Module to run jobman over NICE hypermarameters.
"""

import argparse
import logging

from jobman import api0
from jobman import sql
from jobman.tools import DD
from jobman.tools import expand
from jobman.tools import flatten
from jobman.tools import resolve

from math import exp
from math import log
import numpy as np
from os import path

from pylearn2.config import yaml_parse
from pylearn2.neuroimaging_utils.datasets import MRI
from pylearn2.neuroimaging_utils.dataset_utils import mri_nifti
from pylearn2.neuroimaging_utils.tutorials.jobman_mlp import mlp_experiment
from pylearn2.utils import serial


logging.basicConfig(format="[%(module)s:%(levelname)s]:%(message)s")
logger = logging.getLogger(__name__)

def hidden_generator(num, scale=100):
    assert num > 0
    assert isinstance(num, int)
    assert isinstance(scale, int)
    for hid in xrange(scale, scale * (num + 1), scale):
        yield hid

def learning_rate_generator(num, start, finish):
    assert num > 0
    assert start > 0
    assert finish > 0
    assert isinstance(num, int)
    for n in xrange(num):
        yield exp(log(start) + float(n) / float(num - 1) * (log(finish) - log(start)))

def load_experiments(args):
    dataset_name = "smri"
    db = sql.db("postgres://%(user)s@%(host)s:%(port)d/%(database)s?table=%(table)s"
                % {"user": args.user,
                   "host": args.host,
                   "port": args.port,
                   "database": args.database,
                   "table": args.table,
                   })

    logger.info("Getting dataset info for %s" % dataset_name)
    data_path = serial.preprocess("${PYLEARN2_NI_PATH}/" + dataset_name)
    mask_file = path.join(data_path, "mask.npy")
    mask = np.load(mask_file)
    input_dim = (mask == 1).sum()
    if input_dim % 2 == 1:
        input_dim -= 1
    mri = MRI.MRI_Standard(which_set="full",
                           dataset_name=dataset_name,
                           unit_normalize=True,
                           even_input=True,
                           apply_mask=True)
    variance_map_file = path.join(data_path, "variance_map.npy")
    mri_nifti.save_variance_map(mri, variance_map_file)

    for nhid1 in hidden_generator(4):
        for nhid2 in hidden_generator(4):
            for lr in learning_rate_generator(5, 0.1, 0.00001):
                logger.info("Adding MLP experiment with %d units on first hidden layer "
                            "and %d units on second and learning rate of %f"
                            % (nhid1, nhid2, lr))
                state = DD()
                
                experiment_hyperparams = mlp_experiment.default_hyperparams(input_dim)
                experiment_hyperparams["nhid1"] = nhid1
                experiment_hyperparams["nhid2"] = nhid2
                experiment_hyperparams["learning_rate"] = lr
                experiment_hyperparams["dataset_name"] = dataset_name

                h = abs(hash(frozenset(flatten(experiment_hyperparams).keys() +\
                                           flatten(experiment_hyperparams).values())))

                user = path.expandvars("$USER")
                save_path = serial.preprocess("/export/mialab/users/%s/pylearn2_outs/%d"
                                              % (user, h))

                file_params = {
                    "save_path": save_path,
                    "variance_map_file": variance_map_file,
                    }

                state.file_parameters = file_params
                state.hyper_parameters = experiment_hyperparams

                sql.insert_job(
                    mlp_experiment.experiment,
                    flatten(state),
                    db
                    )

    db.createView("%s_view" % args.table)

def make_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("user")
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument("database")
    parser.add_argument("table")
    parser.add_argument("-v", "--verbose", action="store_true")

    return parser

if __name__ == "__main__":
    parser = make_argument_parser()
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    load_experiments(args)
