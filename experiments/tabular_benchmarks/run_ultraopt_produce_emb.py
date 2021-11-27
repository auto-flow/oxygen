#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : qichun tang
# @Date    : 2021-01-08
# @Contact    : qichun.tang@bupt.edu.cn
'''
--run_id=0 --benchmark=protein_structure --n_iters=100 --data_dir=/media/tqc/doc/Project/fcnet_tabular_benchmarks
'''
import argparse
import json
import os
import time

from tabular_benchmarks import FCNetProteinStructureBenchmark, FCNetSliceLocalizationBenchmark, \
    FCNetNavalPropulsionBenchmark, FCNetParkinsonsTelemonitoringBenchmark
from ultraopt import fmin
from ultraopt.multi_fidelity import HyperBandIterGenerator

parser = argparse.ArgumentParser()
parser.add_argument('--run_id', default=0, type=int, nargs='?', help='unique number to identify this run')
parser.add_argument('--max_groups', default=0, type=int, nargs='?', help='max_groups')
parser.add_argument('--optimizer', default="ETPE", type=str, nargs='?', help='Which optimizer to use')
parser.add_argument('--mode', default="default", type=str, nargs='?', help='mode: {default, univar, univar_cat}')
parser.add_argument('--benchmark', default="protein_structure", type=str, nargs='?', help='specifies the benchmark')
parser.add_argument('--n_iters', default=100, type=int, nargs='?', help='number of iterations for optimization method')
parser.add_argument('--output_path', default="./results", type=str, nargs='?',
                    help='specifies the path where the results will be saved')
parser.add_argument('--data_dir', default="./", type=str, nargs='?', help='specifies the path to the tabular data')

args = parser.parse_args()
mode = args.mode
if args.benchmark == "protein_structure":
    b = FCNetProteinStructureBenchmark(data_dir=args.data_dir)
elif args.benchmark == "slice_localization":
    b = FCNetSliceLocalizationBenchmark(data_dir=args.data_dir)
elif args.benchmark == "naval_propulsion":
    b = FCNetNavalPropulsionBenchmark(data_dir=args.data_dir)
elif args.benchmark == "parkinsons_telemonitoring":
    b = FCNetParkinsonsTelemonitoringBenchmark(data_dir=args.data_dir)
else:
    raise NotImplementedError

output_path = os.path.join(args.output_path, f"{args.benchmark}-ultraopt_{args.optimizer}_align")


def objective_function(config: dict, budget: int = 100):
    loss, cost = b.objective_function(config, int(budget))
    return float(loss)


max_groups = args.max_groups
limit_max_groups = max_groups > 0

cs = b.get_configuration_space()
HB = False
if args.optimizer == "BOHB":
    optimizer = "ETPE"
    iter_generator = HyperBandIterGenerator(min_budget=3, max_budget=100, eta=3)
    HB = True
elif args.optimizer == "HyperBand":
    optimizer = "Random"
    iter_generator = HyperBandIterGenerator(min_budget=3, max_budget=100, eta=3)
    HB = True
else:
    optimizer = args.optimizer
    iter_generator = None
from ultraopt.optimizer import ETPEOptimizer, ForestOptimizer

if mode != "default":
    output_path += f"_{mode}"

if limit_max_groups:
    output_path += f"_g{max_groups}"

os.makedirs(os.path.join(output_path), exist_ok=True)
from ultraopt.tpe import SampleDisign

min_points_in_model = int(os.getenv('min_points_in_model', '20'))
print(f'min_points_in_model={min_points_in_model}')
et_file = f'{args.benchmark}.txt'
pretrain = os.getenv('pretrain') == 'true'
scale = os.getenv('scale') == 'true'
print(f'pretrain = {pretrain}')
print(f'scale = {scale}')
if optimizer == "ETPE":
    if mode == 'univar':
        optimizer = ETPEOptimizer(
            multivariate=False,
            specific_sample_design=[
                SampleDisign(ratio=0.5, is_random=True)
            ]
        )
    elif mode == 'univar_cat':
        optimizer = ETPEOptimizer(
            min_points_in_model=min_points_in_model,
            multivariate=False,
            embed_catVar=False,
            specific_sample_design=[
                SampleDisign(ratio=0.5, is_random=True)
            ]
        )
    elif mode == "default":
        from tabular_nn import EmbeddingEncoder

        encoder = EmbeddingEncoder(
            max_epoch=150, n_jobs=1, verbose=1, weight_decay=2e-4,
            update_used_samples=500, update_epoch=20
        )
        optimizer = ETPEOptimizer(
            # limit_max_groups=limit_max_groups,
            min_points_in_model=min_points_in_model,
            limit_max_groups='auto',
            max_groups=max_groups,
            pretrained_emb=et_file if pretrain else None,
            scale_cont_var=scale,
            embedding_encoder=encoder,
        )
    else:
        raise NotImplementedError
elif optimizer == "Forest":
    if mode == "default":
        optimizer = ForestOptimizer(min_points_in_model=min_points_in_model)
    elif mode == "local_search":
        optimizer = ForestOptimizer(min_points_in_model=min_points_in_model, use_local_search=True)

ret = fmin(
    objective_function, cs, optimizer,
    n_iterations=args.n_iters, random_state=args.run_id,
    multi_fidelity_iter_generator=iter_generator)

ret.export_embedding_table(et_file)

print(ret)
if os.getenv('DEBUG') == 'true':
    exit(0)
# dump(fmin_result, os.path.join(output_path, 'run_%d.pkl' % args.run_id))
res = b.get_results()
fh = open(os.path.join(output_path, 'run_%d.json' % args.run_id), 'w')
json.dump(res, fh)
fh.close()
if HB:
    time.sleep(5)