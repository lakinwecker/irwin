## Typing and enforcing of types
from typing import NamedTuple, TypeVar, NewType, Iterable, List, Dict, Tuple
from typing import Optional as Opt

from numpy import float16, float32, float64

Number = TypeVar('Number', int, float, float16, float32, float64)

## Logging
import logging

## Tools
notNone = lambda x: x is not None