# Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECK_GOLDEN_VALUES = Path(__file__).parents[2] / "tools" / "check_golden_values.py"


def _golden_values(first_iteration_time):
    return {
        "iteration-time": {
            "start_step": 1,
            "end_step": 3,
            "step_interval": 1,
            "values": {"1": first_iteration_time, "2": 0.9, "3": 0.8},
        }
    }


def _run_checker(tmp_path, golden_values):
    golden_values_path = tmp_path / "golden_values.json"
    golden_values_path.write_text(json.dumps(golden_values))
    return subprocess.run(
        [sys.executable, str(CHECK_GOLDEN_VALUES), str(golden_values_path)],
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("value", ["nan", "NaN", "+nan", "-NaN", float("nan")])
def test_first_iteration_time_nan_is_ignored(tmp_path, value):
    result = _run_checker(tmp_path, _golden_values(value))

    assert result.returncode == 0, result.stderr


def test_later_iteration_time_nan_is_rejected(tmp_path):
    golden_values = _golden_values("nan")
    golden_values["iteration-time"]["values"]["2"] = "nan"
    result = _run_checker(tmp_path, golden_values)

    assert result.returncode == 1
    assert "$['iteration-time']['values']['2'] = 'nan'" in result.stderr


def test_first_step_nan_in_other_metric_is_rejected(tmp_path):
    golden_values = {
        "lm-loss": {
            "start_step": 1,
            "end_step": 2,
            "step_interval": 1,
            "values": {"1": "nan", "2": 1.0},
        }
    }
    result = _run_checker(tmp_path, golden_values)

    assert result.returncode == 1
    assert "$['lm-loss']['values']['1'] = 'nan'" in result.stderr


def test_first_iteration_time_infinity_is_rejected(tmp_path):
    result = _run_checker(tmp_path, _golden_values("inf"))

    assert result.returncode == 1
    assert "$['iteration-time']['values']['1'] = 'inf'" in result.stderr
