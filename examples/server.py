import os
import sys
import glob
import json
from datetime import datetime
import argparse

from icecream import ic

ROOT_DIR = os.path.dirname(os.getcwd())
FLWR_DIR = os.path.join(ROOT_DIR, 'src')
HISTORY_DIR = os.path.join(ROOT_DIR, 'federated', 'history')

sys.path.append(ROOT_DIR)
sys.path.append(FLWR_DIR)

import flwr as fl
#from flwr.server.strategy import FedAvg
from flwr.server.strategy import SaveModelStrategy
from flwr.server.fdprocess import FDProcess

def _read_json():
    # Read all fd history files
    files = sorted(glob.glob(os.path.join(HISTORY_DIR, '*.json')))
    print('### Prepare for federated learning ###')    
    try:
        with open(files[-1], 'r') as fs:
            fd_dict = json.load(fs)
    except IOError:
        ic('Error loading the json')
        return None

    previous_fd = None
    try:
        previous_fd =  FDProcess(**fd_dict)
    except:
        ic('Value parse error')
        return None
    
    # Print version, date and path of weights
    previous_fd.print()

    # return path of weights and version number from previous fd process
    return previous_fd.version, previous_fd.weights


    

if __name__ == "__main__":

    # Instantiate the parser
    parser = argparse.ArgumentParser(description='Optional app description')

    ### Add Arguments
    parser.add_argument('--ip', type=str, required=True, help='Enter Server IP')
    parser.add_argument('--port', type=str, default='8080', help='Enter Server Port, default: 8080')
    parser.add_argument('--timeout', type=int, default=86400, help='Specify timeout (seconds) after federated learning starts automatically, default: 86400')
    parser.add_argument('--num_rounds', type=int, default='1', help='Enter Number of Rounds of Federated Learning, default: 1')
    parser.add_argument('--history', type=str, default=HISTORY_DIR, help=f'Enter path of history, default {HISTORY_DIR}')
    parser.add_argument('--min_clients', type=int, default=1, help=f'Enter min number of clients participating on federated learning, default: 1')
    parser.add_argument('--save_fd', action='store_true', help=f'Save federated learning informations and weights, default: False')

    # Parse
    args = parser.parse_args()

    # Load previous federated learning process history and get the version number
    version, weights = _read_json()

    # Before starting the server create a new fd history file
    cur_version=str(int(version) + 1).zfill(5)
    cur_fd = FDProcess(
        version=cur_version,
        date=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        num_participants=0,
        artifacts=[],
        weights=os.path.join('data', f'{cur_version}.weights'),
        elapsed_time=0,
        failures=" ",
    )

    # Create a custom strategy
    strategy = SaveModelStrategy(
        fraction_fit=1.0,
        fraction_eval=1.0,
        min_fit_clients=args.min_clients, 
        min_eval_clients=args.min_clients,
        min_available_clients=1
    )

    
    # Start Flower server for three rounds of federated learning
    fl.server.start_server(
        server_address=f"{args.ip}:{args.port}",
        server=None,
        timeout=args.timeout,
        config={"num_rounds": args.num_rounds},
        strategy=strategy,
        save_fd=args.save_fd,
        load_weights_dir=os.path.join(args.history, weights),
        save_weights_dir=os.path.join(args.history, cur_fd.weights),
        process_history=cur_fd,
        grpc_max_message_length=536_870_912) # this is equal to 512MB


    # Fill more informations

    # Serialize class and save them
    if args.save_fd:
        cur_fd.saveJSON(os.path.join(args.history, f'{cur_version}.json'))

    
