# irwin
irwin is the AI that learns cheating patterns, marks cheaters, and assists moderators in assessing potential cheaters.

![screenshot of Irwin report](https://i.imgur.com/UcVlDK3.png)

![screenshot of companion WebApp](https://i.imgur.com/LQtSQAh.png)

## Dependencies
Compatible with Python 3.x

### Python Libraries
```sh
pip3 install pymongo python-chess numpy requests
```
- **tensorflow** : [tensorflow installation guide](https://www.tensorflow.org/install)

### Database
- **mongodb** : [mongodb installation guide](https://docs.mongodb.com/manual/installation/)

## Configuration

Configure via environment variables (or legacy `conf/server_config.json` / `conf/client_config.json`):

| Variable | Default | Description |
|----------|---------|-------------|
| `IRWIN_API_URL` | `https://lichess.org/` | Lichess API URL |
| `IRWIN_API_TOKEN` | | Lichess API token |
| `IRWIN_DB_HOST` | `localhost` | MongoDB host |
| `IRWIN_DB_PORT` | `27017` | MongoDB port |
| `IRWIN_DB_DATABASE` | `irwin` | MongoDB database name |
| `IRWIN_DB_AUTHENTICATE` | `false` | Enable MongoDB auth |
| `IRWIN_DB_AUTH_USERNAME` | | MongoDB username |
| `IRWIN_DB_AUTH_PASSWORD` | | MongoDB password |
| `IRWIN_STOCKFISH_THREADS` | `4` | Stockfish threads |
| `IRWIN_STOCKFISH_MEMORY` | `2048` | Stockfish hash memory (MB) |
| `IRWIN_STOCKFISH_NODES` | `4500000` | Stockfish nodes per position |
| `IRWIN_LOGLEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
### Build a database of analysed players
If you do not already have a database of analysed players, it will be necessary to analyse
a few hundred players to train the neural networks on.
`python3 main.py --no-assess --no-report`

## About
Irwin (named after Steve Irwin, the Crocodile Hunter) started as the name of the server that the original
cheatnet ran on (now deprecated). This is the successor to cheatnet.

Similar to cheatnet, it works on a similar concept of analysing the available PVs of a game to determine
the odds of cheating occurring.

This bot makes improvements over cheatnet by taking a dramatically more modular approach to software design.
`modules/core` contains most of the generic datatypes, BSON serialisation handlers and database interface
layers. It is also significantly faster due to a simplified approach to using stockfish analysis.

`modules/irwin` contains the brains of irwin, this is where the tensorflow learning and application takes place.

Irwin has been designed so that `modules/irwin` can be replaced with other approaches to player assessment.

`Env.py` contains all of the tools to interact with lichess, irwin, and the database handlers.

`main.py` covers accessing the lichess API (`modules/Api.py`) via Env to get player data; pulling records from mongodb,
analysing games using stockfish, assessing those games using tensorflow and then posting the final assessments.
