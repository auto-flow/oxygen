#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : qichun tang
# @Contact    : qichun.tang@bupt.edu.cn
from ultraopt.benchmarks.synthetic_functions.bohachevsky import Bohachevsky
from ultraopt.benchmarks.synthetic_functions.camelback import Camelback
from ultraopt.benchmarks.synthetic_functions.hartmann3 import Hartmann3
from ultraopt.benchmarks.synthetic_functions.hartmann6 import Hartmann6
from ultraopt.benchmarks.synthetic_functions.levy import Levy3D, Levy6D, Levy9D
from ultraopt.benchmarks.synthetic_functions.rosenbrock import Rosenbrock2D
from ultraopt.benchmarks.synthetic_functions.sin_two import SinTwo

from ultraopt.utils.config_space import CS2HyperoptSpace

synthetic_functions = [
    Bohachevsky,
    Camelback,
    Hartmann3,
    Hartmann6,
    Levy3D,
    Levy6D,
    Levy9D,
    Rosenbrock2D,
    SinTwo,
]
import json
from pathlib import Path
from hyperopt import tpe, fmin, Trials

import numpy as np
import pandas as pd
from ConfigSpace import ConfigurationSpace, Configuration
from functools import partial


def raw2min(df: pd.DataFrame):
    df_m = pd.DataFrame(np.zeros_like(df.values), columns=df.columns)
    for i in range(df.shape[0]):
        df_m.loc[i, :] = df.loc[:i, :].min()
    return df_m


final_result = {}
repetitions = 20
base_random_state = 50
base_max_iter = 200


def main():
    for synthetic_function_cls in synthetic_functions:
        meta_info = synthetic_function_cls.get_meta_information()
        if "num_function_evals" in meta_info:
            max_iter = meta_info["num_function_evals"]
        else:
            max_iter = base_max_iter
        # 构造超参空间
        config_space = ConfigurationSpace()
        config_space.generate_all_continuous_from_bounds(synthetic_function_cls.get_meta_information()['bounds'])
        synthetic_function = synthetic_function_cls()
        space = CS2HyperoptSpace(config_space)

        # 定义目标函数
        def evaluation(config: dict):
            config = Configuration(config_space, values=config)
            return synthetic_function.objective_function(config)["function_value"] - \
                   synthetic_function.get_meta_information()["f_opt"]

        res = pd.DataFrame(columns=[f"trial-{i}" for i in range(repetitions)], index=range(max_iter))
        for trial in range(repetitions):
            random_state = base_random_state + trial * 10
            # 设置超参空间的随机种子（会影响后面的采样）
            config_space.seed(random_state)
            trials = Trials()
            best = fmin(
                evaluation, space, algo=partial(tpe.suggest, n_startup_jobs=20), max_evals=max_iter,
                rstate=np.random.RandomState(random_state), trials=trials,
            )
            losses = trials.losses()
            res[f"trial-{trial}"] = losses
        res = raw2min(res)
        m = res.mean(1)
        s = res.std(1)
        name = synthetic_function.get_meta_information()["name"]
        final_result[name] = {"mean": m.tolist(), "std": s.tolist(), "q25": res.quantile(0.25, 1).tolist(),
                              "q75": res.quantile(0.75, 1).tolist(), "q90": res.quantile(0.90, 1).tolist()}
    Path("hyperopt.json").write_text(json.dumps(final_result))


if __name__ == '__main__':
    main()
