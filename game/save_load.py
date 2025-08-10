import json
import time
from .entities import Entity
from .resources import Resource

def make_save_state(resource: Resource, workers: list) -> dict:
    return {
        "version": 1,
        "resource": resource.to_dict(),
        "workers": [w.to_dict() for w in workers],
        "timestamp": time.time(),
    }

def save_game(filename: str, resource: Resource, workers: list) -> None:
    state = make_save_state(resource, workers)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def load_game(filename: str):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        resource = Resource.from_dict(data.get("resource", {}))
        workers_data = data.get("workers", [])
        workers = [Entity.from_dict(wd) for wd in workers_data]
        return resource, workers
    except (FileNotFoundError, json.JSONDecodeError):
        return None

