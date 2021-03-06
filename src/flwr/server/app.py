# Copyright 2020 Adap GmbH. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Flower server app."""


from logging import INFO
from typing import Dict, Optional, Tuple
from icecream import ic
ic.configureOutput(includeContext=True)

from flwr.common import GRPC_MAX_MESSAGE_LENGTH
from flwr.common.logger import log
from flwr.server.client_manager import SimpleClientManager
from flwr.server.grpc_server.grpc_server import start_insecure_grpc_server
from flwr.server.server import Server
from flwr.server.strategy import FedAvg, Strategy
from flwr.server.fdprocess import FDProcess

from flwr.common import (
    EvaluateRes,
)

DEFAULT_SERVER_ADDRESS = "[::]:8080"


def start_server(
    server_address: str = DEFAULT_SERVER_ADDRESS,
    server: Optional[Server] = None,
    config: Optional[Dict[str, int]] = None,
    strategy: Optional[Strategy] = None,
    save_fd: bool = None,
    load_weights_dir: str = None,
    save_weights_dir: str = None,
    process_history: FDProcess = None,
    grpc_max_message_length: int = GRPC_MAX_MESSAGE_LENGTH,
) -> None:
    """Start a Flower server using the gRPC transport layer.

    Arguments:
        server_address: Optional[str] (default: `"[::]:8080"`). The IPv6
            address of the server.
        server: Optional[flwr.server.Server] (default: None). An implementation
            of the abstract base class `flwr.server.Server`. If no instance is
            provided, then `start_server` will create one.
        config: Optional[Dict[str, int]] (default: None). The only currently
            supported values is `num_rounds`, so a full configuration object
            instructing the server to perform three rounds of federated
            learning looks like the following: `{"num_rounds": 3}`.
        strategy: Optional[flwr.server.Strategy] (default: None). An
            implementation of the abstract base class `flwr.server.Strategy`.
            If no strategy is provided, then `start_server` will use
            `flwr.server.strategy.FedAvg`.
        grpc_max_message_length: int (default: 536_870_912, this equals 512MB).
            The maximum length of gRPC messages that can be exchanged with the
            Flower clients. The default should be sufficient for most models.
            Users who train very large models might need to increase this
            value. Note that the Flower clients need to be started with the
            same value (see `flwr.client.start_client`), otherwise clients will
            not know about the increased limit and block larger messages.

    Returns:
        None.
    """

    initialized_server, initialized_config = _init_defaults(server, config, strategy, save_fd, load_weights_dir, save_weights_dir)

    # Start gRPC server
    grpc_server = start_insecure_grpc_server(
        client_manager=initialized_server.client_manager(),
        server_address=server_address,
        max_message_length=grpc_max_message_length,
    )
    log(
        INFO,
        "Flower server running (insecure, %s rounds)",
        initialized_config["num_rounds"],
    )
    
    _fl(server=initialized_server, config=initialized_config, process_history=process_history)

    # Stop the gRPC server
    grpc_server.stop(1)


def _init_defaults(
    server: Optional[Server],
    config: Optional[Dict[str, int]],
    strategy: Optional[Strategy],
    save_fd: bool,
    load_weights_dir: str,
    save_weights_dir: str,
) -> Tuple[Server, Dict[str, int]]:
    # Create server instance if none was given
    if server is None:
        log(INFO, 'No server found, create new client manager')
        client_manager = SimpleClientManager()

        if strategy is None:
            log(INFO, 'No srategy found, use FedAvg')
            strategy = FedAvg()

        server = Server(client_manager=client_manager, save_fd=save_fd, strategy=strategy, load_weights_dir=load_weights_dir, save_weights_dir=save_weights_dir)

    # Set default config values
    if config is None:
        config = {}
    if "num_rounds" not in config:
        config["num_rounds"] = 1

    return server, config


def _fl(server: Server, config: Dict[str, int], process_history: FDProcess) -> None:
    # Fit model
    hist, elapsed_time = server.fit(num_rounds=config["num_rounds"])
    # hist, fd_info = server.fit(num_rounds=config["num_rounds"])
    log(INFO, "app_fit: losses_distributed %s", str(hist.losses_distributed))
    log(INFO, "app_fit: accuracies_distributed %s", str(hist.accuracies_distributed))
    log(INFO, "app_fit: losses_centralized %s", str(hist.losses_centralized))
    log(INFO, "app_fit: accuracies_centralized %s", str(hist.accuracies_centralized))

    # Temporary workaround to force distributed evaluation
    server.strategy.eval_fn = None  # type: ignore

    # Evaluate the final trained model and push end results
    # Artifacts
    artifacts = []
    res = server.evaluate(rnd=1)
    
    if res is not None:
        loss, (results, failures) = res

        if len(results) > 1:
            for client_res in results:
                address = client_res[0].cid
                mdict = eval(client_res[1].metrics['custom_metric'])
                mdict['address'] = address
                artifacts.append(mdict)
        else:
            mdict = eval(results[0][1].metrics['custom_metric'])
            address = results[0][0].cid
            mdict['address'] = address
            artifacts.append(mdict)
            
        process_history.failures = str(failures)
        process_history.elapsed_time = elapsed_time
        process_history.artifacts = artifacts

        log(INFO, "app_evaluate: federated loss: %s", str(loss))
        log(INFO, "app_evaluate: results %s", str([(res[0].cid, res[1]) for res in results]),)
        log(INFO, "app_evaluate: failures %s", str(failures))
    else:
        log(INFO, "app_evaluate: no evaluation result")

    # Graceful shutdown
    server.disconnect_all_clients()