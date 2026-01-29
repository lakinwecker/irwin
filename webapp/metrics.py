from prometheus_client import Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask import Response
from datetime import datetime
from typing import Dict

# Histogram for player report activations (0-100 range)
ACTIVATION_BUCKETS = (10, 20, 30, 40, 50, 60, 70, 80, 85, 90, 95, 100)

player_report_activation = Histogram(
    'irwin_player_report_activation',
    'Distribution of player report activation scores',
    buckets=ACTIVATION_BUCKETS
)

# Queue wait time buckets (minutes to weeks)
QUEUE_WAIT_BUCKETS = (
    300, 600, 1800,                 # 5min, 10min, 30min
    3600, 7200, 14400,              # 1hr, 2hr, 4hr
    28800, 43200, 86400,            # 8hr, 12hr, 1day
    172800, 345600, 604800,         # 2days, 4days, 1week
    1209600, 2592000,               # 2weeks, 1month
)

# Processing time buckets (seconds to hours)
PROCESSING_BUCKETS = (
    30, 60, 120, 300,               # 30s, 1min, 2min, 5min
    600, 900, 1200, 1800,           # 10min, 15min, 20min, 30min
    2700, 3600, 5400, 7200,         # 45min, 1hr, 1.5hr, 2hr
)

queue_wait_time = Histogram(
    'irwin_queue_wait_seconds',
    'Time players spend waiting in the engine analysis queue',
    buckets=QUEUE_WAIT_BUCKETS
)

processing_time = Histogram(
    'irwin_processing_seconds',
    'Time spent processing player analysis in deep-queue',
    buckets=PROCESSING_BUCKETS
)

# Track when jobs were started (playerId -> start time)
_job_start_times: Dict[str, datetime] = {}


def record_activation(activation: int) -> None:
    player_report_activation.observe(activation)


def record_job_started(player_id: str, queued_at: datetime) -> None:
    now = datetime.now()
    wait_seconds = (now - queued_at).total_seconds()
    queue_wait_time.observe(wait_seconds)
    _job_start_times[player_id] = now


def record_job_completed(player_id: str) -> None:
    start_time = _job_start_times.pop(player_id, None)
    if start_time is not None:
        elapsed = (datetime.now() - start_time).total_seconds()
        processing_time.observe(elapsed)


def metrics_response() -> Response:
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
