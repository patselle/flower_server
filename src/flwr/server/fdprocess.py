import os
import json

import pickle
from icecream import ic

from typing import List, Dict



# This class represents the data of a federated learning process.
# it contains some basic meta data information and the data path there the weights are stored
class FDProcess:
    def __init__(
        self,
        version: str, 
        date: str,
        num_participants: int,
        artifacts: List,
        weights: str,
        elapsed_time: float,
        failures: str,
    ):
        self.version = version
        self.date = date
        self.num_participants = num_participants
        self.artifacts = artifacts
        self.weights = weights
        self.elapsed_time = elapsed_time
        self.failures = failures


    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__, 
            sort_keys=True,
            indent=4)


    def saveJSON(self, filename):
        with open(filename, 'w') as fs:
            fs.write(self.toJSON())


    def print(self):
        print('Print informations')
        print(f'--- Version: {self.version}')
        print(f'--- Date: {self.date}')
        print(f'--- Weights: {self.weights}')







