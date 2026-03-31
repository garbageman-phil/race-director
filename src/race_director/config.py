from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml


_DEFAULT_CONFIG_NAME = "config.yaml"
_EXAMPLE_CONFIG_NAME = "config.example.yaml"


@dataclass(frozen=True)
class Config:
    team_names: list[str] = field(default_factory=list)

    def team_names_lower(self) -> set[str]:
        return {name.lower() for name in self.team_names}


def load_config(config_path: Path | None = None) -> Config:
    """Load and validate configuration from a YAML file.

    Looks for ``config.yaml`` in the current directory by default.
    """
    if config_path is None:
        config_path = Path.cwd() / _DEFAULT_CONFIG_NAME

    if not config_path.exists():
        example = Path.cwd() / _EXAMPLE_CONFIG_NAME
        hint = (
            f" Copy {_EXAMPLE_CONFIG_NAME} to {_DEFAULT_CONFIG_NAME} and edit it."
            if example.exists()
            else ""
        )
        print(
            f"Error: config file not found at {config_path}.{hint}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    with open(config_path, "r") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        print(
            f"Error: {config_path} must be a YAML mapping (got {type(raw).__name__}).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    names = raw.get("team_names")
    if not names or not isinstance(names, list):
        print(
            f"Error: {config_path} must contain a 'team_names' list with at least one entry.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    bad = [n for n in names if not isinstance(n, str) or not n.strip()]
    if bad:
        print(
            f"Error: all entries in 'team_names' must be non-empty strings. Invalid: {bad}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return Config(team_names=[n.strip() for n in names])
