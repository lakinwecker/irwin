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
    host: str = "0.0.0.0"
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


class IrwinModelBasicTrainingSettings(BaseSettings):
    """Basic model training settings. Used by: webapp (training only)"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_MODEL_BASIC_TRAINING_')
    epochs: int = 20
    sample_size: int = 1000


class IrwinModelAnalysedTrainingSettings(BaseSettings):
    """Analysed model training settings. Used by: webapp (training only)"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_MODEL_ANALYSED_TRAINING_')
    epochs: int = 20
    sample_size: int = 1000


class IrwinModelBasicSettings(BaseSettings):
    """Basic model settings. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_MODEL_BASIC_')
    file: str = "modules/irwin/models/basicGame.h5"
    training: IrwinModelBasicTrainingSettings = Field(default_factory=IrwinModelBasicTrainingSettings)


class IrwinModelAnalysedSettings(BaseSettings):
    """Analysed model settings. Used by: webapp, lichess-listener"""
    model_config = SettingsConfigDict(env_prefix='IRWIN_MODEL_ANALYSED_')
    file: str = "modules/irwin/models/analysedGame.h5"
    training: IrwinModelAnalysedTrainingSettings = Field(default_factory=IrwinModelAnalysedTrainingSettings)


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


def _collect_env_mappings(cls, path: list[str] | None = None) -> Dict[str, list[str]]:
    """Collect mapping of env var names to config paths by introspecting pydantic models."""
    if path is None:
        path = []

    mappings: Dict[str, list[str]] = {}

    prefix = ''
    if hasattr(cls, 'model_config'):
        mc = cls.model_config
        if isinstance(mc, dict):
            prefix = mc.get('env_prefix', '')
        elif hasattr(mc, 'get'):
            prefix = mc.get('env_prefix', '') or ''

    for field_name, field_info in cls.model_fields.items():
        current_path = path + [field_name]
        field_type = field_info.annotation

        origin = getattr(field_type, '__origin__', None)
        if origin is not None:
            args = getattr(field_type, '__args__', ())
            field_type = next((a for a in args if a is not type(None)), field_type)

        if hasattr(field_type, 'model_fields'):
            nested_mappings = _collect_env_mappings(field_type, current_path)
            mappings.update(nested_mappings)
        else:
            env_var = f"{prefix}{field_name}".upper()
            mappings[env_var] = current_path

    return mappings


def _get_by_path(d: Dict, path: list[str]):
    """Get a value from a nested dict by path."""
    for key in path:
        if not isinstance(d, dict):
            return None
        d = d.get(key, {})
    return d


def _set_by_path(d: Dict, path: list[str], value):
    """Set a value in a nested dict by path, creating intermediate dicts as needed."""
    for key in path[:-1]:
        d = d.setdefault(key, {})
    d[path[-1]] = value


def _merge_env_over_file(file_config: Dict, env_config: Dict, mappings: Dict[str, list[str]]) -> Dict:
    """Merge env config over file config, but only for env vars that are actually set."""
    result = json.loads(json.dumps(file_config))

    for env_var, path in mappings.items():
        if env_var in os.environ:
            value = _get_by_path(env_config, path)
            _set_by_path(result, path, value)

    return result


class ConfigWrapper:
    """
    Wrapper that provides backward-compatible access to settings.
    Supports both attribute access (conf.api.url) and key access (conf["api url"]).
    """
    def __init__(self, d: Dict):
        self.d = d

    @staticmethod
    def new(filename: str) -> 'ConfigWrapper':
        """Load from file with env vars taking precedence, or just env vars if no file."""
        env_settings = Settings()
        env_config = env_settings.model_dump(by_alias=True)

        if not os.path.exists(filename):
            return ConfigWrapper(env_config)

        with open(filename) as confFile:
            file_config = json.load(confFile)

        mappings = _collect_env_mappings(Settings)
        merged = _merge_env_over_file(file_config, env_config, mappings)
        return ConfigWrapper(merged)

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
