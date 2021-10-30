#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : qichun tang
# @Contact    : qichun.tang@bupt.edu.cn
from ultraopt.benchmarks.synthetic_functions import Forrester, Bohachevsky, Camelback

from ultraopt.optimizer.bo.sampling_sort_opt import SamplingSortOptimizer
from ultraopt.structure import Job

from ultraopt.benchmarks.synthetic_functions.goldstein_price import GoldsteinPrice
from ultraopt.benchmarks.synthetic_functions.hartmann3 import Hartmann3
from ultraopt.benchmarks.synthetic_functions.hartmann6 import Hartmann6
from ultraopt.benchmarks.synthetic_functions.levy import Levy1D
from ultraopt.benchmarks.synthetic_functions.rosenbrock import Rosenbrock2D
from ultraopt.benchmarks.synthetic_functions.sin_one import SinOne
from ultraopt.benchmarks.synthetic_functions.sin_two import SinTwo

synthetic_functions = [
    Bohachevsky,
    Camelback,
    Forrester,
    GoldsteinPrice,
    Hartmann3,
    Hartmann6,
    Levy1D,
    Rosenbrock2D,
    SinOne,
    SinTwo,
]
import json
from pathlib import Path

import numpy as np
import pandas as pd
from ConfigSpace import Configuration, ConfigurationSpace


def raw2min(df: pd.DataFrame):
    df_m = pd.DataFrame(np.zeros_like(df.values), columns=df.columns)
    for i in range(df.shape[0]):
        df_m.loc[i, :] = df.loc[:i, :].min()
    return df_m


final_result = {}


def main():
    for synthetic_function_cls in synthetic_functions:
        meta_info = synthetic_function_cls.get_meta_information()
        if "num_function_evals" in meta_info:
            max_iter = meta_info["num_function_evals"]
        else:
            max_iter = 200
        # 构造超参空间
        config_space = ConfigurationSpace()
        config_space.generate_all_continuous_from_bounds(synthetic_function_cls.get_meta_information()['bounds'])
        synthetic_function = synthetic_function_cls()

        # 定义目标函数
        def evaluation(config: dict):
            config = Configuration(config_space, values=config)
            return synthetic_function.objective_function(config)["function_value"] - \
                   synthetic_function.get_meta_information()["f_opt"]

        # 对experiment_param的删除等操作放在存储后面
        res = pd.DataFrame(columns=[f"trial-{i}" for i in range(10)], index=range(max_iter))
        for trial in range(10):
            random_state = 50 + trial * 10
            # 设置超参空间的随机种子（会影响后面的采样）
            config_space.seed(random_state)
            print("==========================")
            print(f"= Trial -{trial:01d}-               =")
            print("==========================")
            print('iter |  loss    | config origin')
            print('----------------------------')
            cg = SamplingSortOptimizer(
                config_space, [1], min_points_in_model=25, n_samples=2500
            )
            loss = np.inf
            for ix in range(max_iter):
                config, config_info = cg.get_config(1)
                cur_loss = evaluation(config)
                loss = min(loss, cur_loss)
                print(f" {ix:03d}   {loss:.4f}    {config_info.get('origin')}")
                job = Job("")
                job.result = {"loss": cur_loss}
                job.kwargs = {"budget": 1, "config": config, "config_info": config_info}
                cg.new_result(job)
                res.loc[ix, f"trial-{trial}"] = cur_loss
        res = raw2min(res)
        m = res.mean(1)
        s = res.std(1)
        name = synthetic_function.get_meta_information()["name"]
        final_result[name] = {"mean": m.tolist(), "std": s.tolist()}
    Path("EETPE.json").write_text(json.dumps(final_result))


if __name__ == '__main__':
    main()
