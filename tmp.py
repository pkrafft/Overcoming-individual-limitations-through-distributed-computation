
import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
import pandas as pd
import scipy.stats as stats

import utils

import importlib
importlib.reload(utils)

import os

#in_dir = '70f80fdf-rounds-10-evidence-1-population-5'
#in_dir = 'abf00068-rounds-10-evidence-4-population-5'
#in_dir = 'd75786f7-data-2018-01-25-big-experiment'
#in_dir = '18a75a2d-data-2018-03-19-big-experiment'
in_dir = '095ddcbc-rounds-10-evidence-4-big-experiment-high-prob'

#in_dir = 'd9145d2a-rounds-10-evidence-1-population-5'
#in_dir = 'b7d0390f-rounds-10-evidence-4-population-5'

n_evidence = 4

data,fails,parts = utils.parse_data(in_dir, n_evidence)
