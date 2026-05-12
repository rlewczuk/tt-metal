#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


OPERATIONS_DIR = Path("ttnn/cpp/ttnn/operations")
RELEVANT_COMMANDS = {"install", "target_sources"}
HEADER_SUFFIXES = (".h", ".hh", ".hpp", ".hxx")

# Paths relative to tt-metal project root. Add CMakeLists.txt paths here to skip them.
exclusions = set()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def as_project_relative(path: str, root: Path) -> Path | None:
    try:
        return Path(path).resolve().relative_to(root)
    except ValueError:
        return None


def is_operations_cmake_file(path: Path) -> bool:
    return path.name == "CMakeLists.txt" and (path == OPERATIONS_DIR / "CMakeLists.txt" or OPERATIONS_DIR in path.parents)


def relevant_record(record: dict, root: Path) -> tuple[str, dict] | None:
    command = record.get("cmd")
    if command not in RELEVANT_COMMANDS:
        return None

    file_name = record.get("file")
    if not isinstance(file_name, str):
        return None

    rel_path = as_project_relative(file_name, root)
    if rel_path is None or not is_operations_cmake_file(rel_path):
        return None

    rel_path_str = rel_path.as_posix()
    if rel_path_str in exclusions:
        return None

    args = record.get("args", [])
    if not isinstance(args, list):
        args = []

    return rel_path_str, {"cmd": command, "args": args}


def read_records(events_file: Path, root: Path) -> dict[str, list[dict]]:
    records_by_file = defaultdict(list)

    with events_file.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"{events_file}:{line_number}: invalid JSON: {e}", file=sys.stderr)
                continue

            relevant = relevant_record(record, root)
            if relevant is None:
                continue

            rel_path, filtered_record = relevant
            records_by_file[rel_path].append(filtered_record)

    return dict(records_by_file)


def has_install_api_file_set(records: list[dict]) -> bool:
    for record in records:
        if record["cmd"] != "install":
            continue
        args = record["args"]
        if "TARGETS" in args and contains_file_set(args, "api"):
            return True
    return False


def contains_file_set(args: list[str], name: str) -> bool:
    for index, arg in enumerate(args[:-1]):
        if arg == "FILE_SET" and args[index + 1] == name:
            return True
    return False


def has_target_sources_api_headers(records: list[dict]) -> bool:
    for record in records:
        if record["cmd"] != "target_sources":
            continue
        if target_sources_contains_api_headers(record["args"]):
            return True
    return False


def target_sources_contains_api_headers(args: list[str]) -> bool:
    index = 0
    while index < len(args):
        if args[index] == "FILE_SET" and index + 1 < len(args) and args[index + 1] == "api":
            next_file_set = find_next(args, "FILE_SET", index + 2)
            files_index = find_next(args, "FILES", index + 2, next_file_set)
            if files_index is not None:
                files_end = next_file_set if next_file_set is not None else len(args)
                if contains_header(args[files_index + 1 : files_end]):
                    return True
            index = next_file_set if next_file_set is not None else len(args)
            continue
        index += 1
    return False


def find_next(args: list[str], token: str, start: int, end: int | None = None) -> int | None:
    if end is None:
        end = len(args)
    for index in range(start, end):
        if args[index] == token:
            return index
    return None


def contains_header(args: list[str]) -> bool:
    return any(is_header(arg) for arg in args)


def is_header(arg: str) -> bool:
    return Path(arg).suffix.lower() in HEADER_SUFFIXES


def report_violations(records_by_file: dict[str, list[dict]]) -> int:
    violations = 0

    for cmake_file in sorted(records_by_file):
        records = records_by_file[cmake_file]
        if not has_install_api_file_set(records):
            print(f"{cmake_file}\tmissing install(TARGETS ... FILE_SET api ...)")
            violations += 1
        if not has_target_sources_api_headers(records):
            print(f"{cmake_file}\tmissing target_sources(... FILE_SET api ... FILES <headers> ...)")
            violations += 1

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check ttnn operations CMake api FILE_SET rules from a CMake events JSONL file.")
    parser.add_argument("events_file", nargs="?", default="build/tt-metal-trace.json", help="CMake events JSONL file")
    args = parser.parse_args(argv)

    root = project_root()
    events_file = Path(args.events_file)
    if not events_file.is_absolute():
        events_file = root / events_file

    records_by_file = read_records(events_file, root)
    violations = report_violations(records_by_file)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
