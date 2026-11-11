import json
import os
import sys
from pathlib import Path

import pytest


TEST_FILE = Path(__file__).resolve()
GENERATOR_FOLDER = TEST_FILE.parents[1]
PROJECT_FOLDER = GENERATOR_FOLDER.parent

sys.path.insert(
    0,
    str(GENERATOR_FOLDER),
)

from grpc_test_runtime import (
    apply_assertion,
    invoke_unary_rpc,
)


SCENARIO_FILE = (
    GENERATOR_FOLDER
    / "generated"
    / "scenarios.json"
)

DESCRIPTOR_FILE = (
    GENERATOR_FOLDER
    / "generated"
    / "contracts.pb"
)

SERVER_ADDRESS = (
    os.getenv("GRPC_HOST", "localhost")
    + ":"
    + os.getenv("GRPC_PORT", "50051")
)


def load_scenarios():
    scenario_data = json.loads(
        SCENARIO_FILE.read_text(
            encoding="utf-8"
        )
    )

    return scenario_data["scenarios"]


SCENARIOS = load_scenarios()


@pytest.mark.parametrize(
    "scenario",
    SCENARIOS,
    ids=lambda scenario: (
        scenario["scenario_id"]
    ),
)
def test_generated_grpc_scenario(
    scenario,
):
    print()
    print(
        f"Executing "
        f"{scenario['scenario_id']}: "
        f"{scenario['title']}"
    )

    response = invoke_unary_rpc(
        server_address=SERVER_ADDRESS,
        descriptor_file=DESCRIPTOR_FILE,
        method_path=scenario[
            "method_path"
        ],
        request_type=scenario[
            "request_type"
        ],
        response_type=scenario[
            "response_type"
        ],
        request_values=scenario[
            "request"
        ],
        timeout_seconds=5,
    )

    print(
        "Response:",
        json.dumps(
            response,
            indent=2,
        ),
    )

    for assertion in scenario[
        "assertions"
    ]:
        apply_assertion(
            response,
            assertion,
        )
