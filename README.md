# Flower Server

Flower ist ein Federated Learning Framework (siehe: [Flower](https://github.com/adap/flower)). <br>
Hier ist das Release 0.13.0 umgesetzt und fuer AutoVikki angepasst.

## Installation und Test

- Conda Environment mit Python 3.7
- Installieren der requirements: `pip install -r requirements.txt`
- Starten des Servers: `python examples/server.py`

## Note

- Die maximale Laenge der gRPC Messages ist auf 512MB festgelegt (definiert in `flwr/common/__init__.py: GRPC_MAX_MESSAGE_LENGTH, default: 536_870_912, this equals 512MB`).<br> Fuer das Trainieren groeßere Modelle muss diese Groeße eventuell angepasst werden. <br> The Flower server needs to be started with the same value (see `flwr.server.start_server`).

## ToDo

- Festlegen der Serveradresse, derzeit wird eine default Serveradresse verwendet (server: `examples/server.py`, client: `examples/client.py`)
