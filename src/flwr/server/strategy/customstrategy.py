import os
import json
from datetime import datetime
from collections import namedtuple

import pickle
from typing import Dict, List, Optional, Tuple
from logging import DEBUG, ERROR

from flwr.server.strategy.fedavg import FedAvg
from flwr.common import (
    Weights,
)
from flwr.server.fdprocess import FDProcess
from flwr.common.logger import log

# Costum strategy to save global model weights
class SaveModelStrategy(FedAvg):
    def aggregate_fit(
        self, save_fd: bool, save_weights_dir: str, rnd: int, results, failures,
    ) -> Optional[Weights]:

        weights_prime = super().aggregate_fit(rnd, results, failures)

        if weights_prime is None:
            return None

        if not save_fd:
            return weights_prime
    
        # Save weights
        try:
            log(DEBUG, f'Save weights to {save_weights_dir}')
            fs = open(save_weights_dir, '+wb')
            pickle.dump(weights_prime, fs)
            fs.close()
        except:
            log(ERROR, 'Error when trying to saving weights to {weights_path}')

        return weights_prime
