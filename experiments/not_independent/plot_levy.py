#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : qichun tang
# @Contact    : qichun.tang@bupt.edu.cn
import json
import sys
from pathlib import Path

import numpy as np
import pylab as plt

# benchmark = sys.argv[1]
benchmark = 'rosenbrock'

info = {
    f"hyperopt_{benchmark}": ("HyperOpt-TPE", "purple",),
    f"ultraopt_{benchmark}_multival": ("UltraOpt-ETPE", "b"),
    f"bohb_{benchmark}": ("BOHB-KDE", "orange"),
    f"ultraopt_{benchmark}_3": ("UltraOpt-ETPE_3", "r",),
    f"optuna_{benchmark}_multival": ("Optuna-TPE", "g",),
    f"random_{benchmark}": ("Random", "brown",),
    # f"ultraopt_{benchmark}_6": ("UltraOpt-ETPE_6", "b",),
    # f"ultraopt_{benchmark}_8": ("UltraOpt-ETPE_8", "k",),
}

cls=benchmark[0].upper()+benchmark[1:]
benchs=[f"{cls}{x}D" for x in range(2,21)]

# benchs = list(json.loads(Path(f"{info.copy().popitem()[0]}.json").read_text()).keys())  # [:9]

cols = int(np.sqrt(len(benchs)))
rows = int(np.ceil(len(benchs) / cols))
# 设置字体样式
plt.rcParams['font.family'] = 'YaHei Consolas Hybrid'
plt.rcParams['figure.figsize'] = (30, 25)


for log_scale in [False]:
    plt.close()
    index = 1
    for bench in benchs:
        plt.subplot(rows, cols, index)
        for fname, (name, color,) in info.items():
            # todo: IO太多了
            mean_std = json.loads(Path(f"{fname}.json").read_text())[bench]
            mean = np.array(mean_std["mean"])
            q1 = np.array(mean_std["q25"])
            qm = np.array(mean_std["q25"])
            if log_scale:
                q2 = np.array(mean_std["q90"])
            else:
                q2 = np.array(mean_std["q75"])
            iters = range(len(mean))
            # if not log_scale:
            plt.fill_between(
                iters, q1, q2, alpha=0.1,
                color=color
            )
            plt.plot(
                iters, mean, color=color, label=name, alpha=0.9
            )
        plt.title(bench)
        index += 1
        plt.xlabel("iterations")
        plt.ylabel("loss")
        if log_scale:
            plt.yscale("log")
        plt.grid(alpha=0.4)
        plt.legend(loc="best")
    title = "Comparison between Optimizers"
    if log_scale:
        title += "(log-scaled)"
    # plt.suptitle(title)
    plt.tight_layout()
    fname = "synthetic_benchmarks"
    if log_scale:
        fname += "_log"
    for suffix in ["pdf", "png"]:
        plt.savefig(f"{fname}_{benchmark}.{suffix}")
    plt.show()
