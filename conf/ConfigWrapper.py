from typing import Dict
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os


class ApiSettings(BaseSettings):
    """Lichess API settings. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_API_')
    url: str = "https://lichess.org/"
    token: str = ""


class StockfishSettings(BaseSettings):
    """Stockfish engine settings. Used by: deep-queue"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_STOCKFISH_')
    threads: int = 4
    memory: int = 2048
    nodes: int = 4500000
    update: bool = False
    path: str = ""  # If set, use this path instead of auto-detecting


class DbAuthSettings(BaseSettings):
    """MongoDB auth settings. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_DB_AUTH_')
    username: str = ""
    password: str = ""


class DbSettings(BaseSettings):
    """MongoDB settings. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_DB_')
    host: str = "localhost"
    port: int = 27017
    database: str = "irwin"
    authenticate: bool = False
    authentication: DbAuthSettings = Field(default_factory=DbAuthSettings)


class QueueCollSettings(BaseSettings):
    """Queue collection names. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_QUEUE_COLL_')
    engine: str = "engineQueue"
    irwin: str = "irwinQueue"


class QueueSettings(BaseSettings):
    """Queue settings. Used by: webapp, lichess-listener"""
    coll: QueueCollSettings = Field(default_factory=QueueCollSettings)


class GameCollSettings(BaseSettings):
    """Game collection names. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_GAME_COLL_')
    game: str = "game"
    analysed_game: str = "gameAnalysis"
    player: str = "player"
    analysed_position: str = "analysedPosition"


class GameSettings(BaseSettings):
    """Game settings. Used by: webapp, lichess-listener"""
    coll: GameCollSettings = Field(default_factory=GameCollSettings)


class ServerSettings(BaseSettings):
    """Webapp server settings. Used by: deep-queue (to connect to webapp)"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_SERVER_')
    protocol: str = "http"
    domain: str = "localhost"
    port: int = 5000


class AuthCollSettings(BaseSettings):
    """Auth collection names. Used by: webapp"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_AUTH_COLL_')
    user: str = "user"
    token: str = "token"


class AuthSettings(BaseSettings):
    """Auth settings. Used by: deep-queue (token), webapp (collections)"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_AUTH_')
    token: str = ""
    coll: AuthCollSettings = Field(default_factory=AuthCollSettings)


class IrwinCollSettings(BaseSettings):
    """Irwin collection names. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_IRWIN_COLL_')
    analysed_game_activation: str = "analysedGameActivation"
    basic_game_activation: str = "basicGameActivation"


class IrwinModelTrainingSettings(BaseSettings):
    """Model training settings. Used by: webapp (training only)"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_MODEL_TRAINING_')
    epochs: int = 20
    sample_size: int = 1000


class IrwinModelBasicSettings(BaseSettings):
    """Basic model settings. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_MODEL_BASIC_')
    file: str = "modules/irwin/models/basicGame.h5"
    training: IrwinModelTrainingSettings = Field(default_factory=IrwinModelTrainingSettings)


class IrwinModelAnalysedSettings(BaseSettings):
    """Analysed model settings. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_MODEL_ANALYSED_')
    file: str = "modules/irwin/models/analysedGame.h5"
    training: IrwinModelTrainingSettings = Field(default_factory=IrwinModelTrainingSettings)


class IrwinModelSettings(BaseSettings):
    """Model settings. Used by: webapp, lichess-listener"""
    basic: IrwinModelBasicSettings = Field(default_factory=IrwinModelBasicSettings)
    analysed: IrwinModelAnalysedSettings = Field(default_factory=IrwinModelAnalysedSettings)


class IrwinTrainSettings(BaseSettings):
    """Training settings. Used by: webapp (training only)"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_TRAIN_')
    batchSize: int = 2500
    cycles: int = 20


class IrwinTestingSettings(BaseSettings):
    """Testing/evaluation settings. Used by: webapp (eval only)"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_TESTING_')
    eval_size: int = 1000


class IrwinSettings(BaseSettings):
    """Irwin AI settings. Used by: webapp, lichess-listener"""
    coll: IrwinCollSettings = Field(default_factory=IrwinCollSettings)
    model: IrwinModelSettings = Field(default_factory=IrwinModelSettings)
    train: IrwinTrainSettings = Field(default_factory=IrwinTrainSettings)
    testing: IrwinTestingSettings = Field(default_factory=IrwinTestingSettings)
    evalSize: int = 1000


class Settings(BaseSettings):
    """Root settings container."""
    model_config = SettingsConfigDict(env_prefix='IRWIN_')
    api: ApiSettings = Field(default_factory=ApiSettings)
    stockfish: StockfishSettings = Field(default_factory=StockfishSettings)
    db: DbSettings = Field(default_factory=DbSettings)
    queue: QueueSettings = Field(default_factory=QueueSettings)
    game: GameSettings = Field(default_factory=GameSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    irwin: IrwinSettings = Field(default_factory=IrwinSettings)
    loglevel: str = "INFO"


class ConfigWrapper:
    """
    Wrapper that provides backward-compatible access to settings.
    Supports both attribute access (conf.api.url) and key access (conf["api url"]).
    """
    def __init__(self, d: Dict):
        self.d = d

    @staticmethod
    def new(filename: str) -> 'ConfigWrapper':
        """Load from file if it exists, otherwise from environment variables."""
        if os.path.exists(filename):
            with open(filename) as confFile:
                return ConfigWrapper(json.load(confFile))
        return ConfigWrapper.from_env()

    @staticmethod
    def from_env() -> 'ConfigWrapper':
        """Build config from environment variables using pydantic-settings."""
        settings = Settings()
        return ConfigWrapper(settings.model_dump(by_alias=True))

    def __getitem__(self, key: str):
        """Allows accessing like conf["api url"] or conf["stockfish threads"]"""
        try:
            head, tail = key.split(' ', 1)
            return self.__getattr__(head)[tail]
        except ValueError:
            return self.__getattr__(key)

    def __getattr__(self, key: str):
        """Allows accessing like conf.api.url"""
        r = self.d.get(key)
        if isinstance(r, dict):
            return ConfigWrapper(r)
        return r

    def asdict(self) -> Dict:
        return self.d

    def __repr__(self):
        return f"ConfigWrapper({self.d})"
