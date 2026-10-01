# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Blob Storage Tests."""

import os
import re
from datetime import datetime
from pathlib import Path

from graphrag_storage.file_storage import (
    FileStorage,
)

__dirname__ = os.path.dirname(__file__)


async def test_find():
    storage = FileStorage(base_dir="tests/fixtures/text/input")
    items = list(storage.find(file_pattern=re.compile(r".*\.txt$")))
    assert items == [str(Path("dulce.txt"))]
    output = await storage.get("dulce.txt")
    assert len(output) > 0

    await storage.set("test.txt", "Hello, World!", encoding="utf-8")
    output = await storage.get("test.txt")
    assert output == "Hello, World!"
    await storage.delete("test.txt")
    output = await storage.get("test.txt")
    assert output is None


async def test_find_returns_only_files_with_native_relative_keys(tmp_path: Path):
    archive = tmp_path / "archive.txt"
    archive.mkdir()
    nested_file = archive / "document.txt"
    nested_file.write_text("nested document", encoding="utf-8")
    root_file = tmp_path / nested_file.name
    root_file.write_text("root document", encoding="utf-8")

    storage = FileStorage(base_dir=str(tmp_path))
    items = sorted(storage.find(re.compile(r".*\.txt$")))

    nested_key = str(Path("archive.txt") / "document.txt")
    assert items == sorted([root_file.name, nested_key])
    assert os.sep in nested_key
    assert await storage.get(root_file.name) == "root document"
    assert await storage.get(nested_key) == "nested document"


def test_find_matches_nested_path_pattern_against_relative_key(tmp_path: Path):
    for group in ("group-a", "group-b"):
        group_dir = tmp_path / group
        group_dir.mkdir()
        (group_dir / "document.txt").write_text(group, encoding="utf-8")

    storage = FileStorage(base_dir=str(tmp_path))
    pattern = re.compile(rf"^group-a{re.escape(os.sep)}.*\.txt$")
    items = list(storage.find(pattern))

    assert items == [str(Path("group-a") / "document.txt")]


def test_find_does_not_match_base_directory_prefix(tmp_path: Path):
    base_dir = tmp_path / "storage.txt"
    base_dir.mkdir()
    (base_dir / "document.bin").write_text("binary document", encoding="utf-8")

    storage = FileStorage(base_dir=str(base_dir))
    items = list(storage.find(re.compile(r"storage\.txt")))

    assert items == []


def test_find_returns_empty_when_matching_directory_has_no_files(tmp_path: Path):
    (tmp_path / "archive.txt").mkdir()

    storage = FileStorage(base_dir=str(tmp_path))
    items = list(storage.find(re.compile(r".*\.txt$")))

    assert items == []


async def test_get_creation_date():
    storage = FileStorage(
        base_dir="tests/fixtures/text/input",
    )

    creation_date = await storage.get_creation_date("dulce.txt")

    datetime_format = "%Y-%m-%d %H:%M:%S %z"
    parsed_datetime = datetime.strptime(creation_date, datetime_format).astimezone()

    assert parsed_datetime.strftime(datetime_format) == creation_date


async def test_child():
    storage = FileStorage(base_dir="")
    storage = storage.child("tests/fixtures/text/input")
    items = list(storage.find(re.compile(r".*\.txt$")))
    assert items == [str(Path("dulce.txt"))]

    output = await storage.get("dulce.txt")
    assert len(output) > 0

    await storage.set("test.txt", "Hello, World!", encoding="utf-8")
    output = await storage.get("test.txt")
    assert output == "Hello, World!"
    await storage.delete("test.txt")
    output = await storage.get("test.txt")
    assert output is None
