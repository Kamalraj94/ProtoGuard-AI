import hashlib
import json
from pathlib import Path


# --------------------------------------------------
# Folder configuration
# --------------------------------------------------

CURRENT_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = CURRENT_FOLDER.parent

PROTO_FILE = PROJECT_FOLDER / "proto" / "prime.proto"

MOCK_FILE = CURRENT_FOLDER / "mock_scenarios.json"

GENERATED_TEST_FOLDER = (
    CURRENT_FOLDER / "generated_tests"
)

GENERATED_TEST_FILE = (
    GENERATED_TEST_FOLDER
    / "test_prime_generated.py"
)

HASH_FILE = CURRENT_FOLDER / ".proto_hash"


# --------------------------------------------------
# Read proto
# --------------------------------------------------

def read_proto():

    if not PROTO_FILE.exists():
        raise FileNotFoundError(
            f"Proto file not found: {PROTO_FILE}"
        )

    content = PROTO_FILE.read_text(
        encoding="utf-8"
    )

    print(f"Proto found: {PROTO_FILE}")

    return content


# --------------------------------------------------
# Detect proto change
# --------------------------------------------------

def calculate_hash(content):

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def detect_change(current_hash):

    if not HASH_FILE.exists():
        return "NEW_PROTO"

    previous_hash = HASH_FILE.read_text(
        encoding="utf-8"
    ).strip()

    if previous_hash == current_hash:
        return "NO_CHANGE"

    return "MODIFIED_PROTO"


def save_hash(current_hash):

    HASH_FILE.write_text(
        current_hash,
        encoding="utf-8"
    )


# --------------------------------------------------
# MOCK AI RESPONSE
# --------------------------------------------------

def get_mock_scenarios():

    print(
        "Using MOCK scenario generator..."
    )

    with MOCK_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# --------------------------------------------------
# FUTURE AI IMPLEMENTATION
# --------------------------------------------------

def get_ai_scenarios(proto_content):

    """
    FUTURE IMPLEMENTATION.

    Enable only after receiving approved
    organization AI API access.
    """

    # import os
    # import requests

    # api_key = os.getenv(
    #     "PROTOGUARD_AI_API_KEY"
    # )

    # endpoint = os.getenv(
    #     "PROTOGUARD_AI_ENDPOINT"
    # )

    # prompt = f"""
    # Analyze the following gRPC proto contract.
    #
    # Generate positive, negative and boundary
    # test scenarios.
    #
    # Return JSON containing:
    #
    # id
    # description
    # request value
    # expected result
    #
    # Proto:
    #
    # {proto_content}
    # """

    # response = requests.post(
    #     endpoint,
    #     headers={
    #         "Authorization":
    #             f"Bearer {api_key}"
    #     },
    #     json={
    #         "prompt": prompt
    #     },
    #     timeout=60
    # )

    # response.raise_for_status()

    # return response.json()

    raise NotImplementedError(
        "AI integration not enabled."
    )


# --------------------------------------------------
# Choose scenario source
# --------------------------------------------------

def get_scenarios(proto_content):

    # ==============================================
    # CURRENT DEMO
    # ==============================================

    scenarios = get_mock_scenarios()

    # ==============================================
    # FUTURE AI
    # ==============================================

    # Comment above MOCK line
    # and uncomment below after getting AI access.

    # scenarios = get_ai_scenarios(
    #     proto_content
    # )

    return scenarios


# --------------------------------------------------
# Generate pytest test class
# --------------------------------------------------

def generate_test_file(data):

    GENERATED_TEST_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    scenarios = data["scenarios"]

    parameter_rows = []

    for scenario in scenarios:

        scenario_id = scenario["id"]
        description = scenario["description"]
        number = scenario["number"]
        expected = scenario["expected"]

        parameter_rows.append(
            f'        '
            f'("{scenario_id}", '
            f'"{description}", '
            f'{number}, '
            f'{expected})'
        )

    parameter_text = ",\n".join(
        parameter_rows
    )

    test_code = f'''\
"""
AUTO-GENERATED TEST FILE.

Source:
    proto/prime.proto

Scenario Provider:
    Mock AI response

Do not manually modify this file.
"""

import sys
from pathlib import Path

import grpc
import pytest


PROJECT_ROOT = (
    Path(__file__).resolve()
    .parents[2]
)

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from generated import prime_pb2
from generated import prime_pb2_grpc


SERVER = "localhost:50051"


@pytest.mark.parametrize(
    "scenario_id, description, number, expected",
    [
{parameter_text}
    ]
)
def test_check_prime(
    scenario_id,
    description,
    number,
    expected
):

    print()
    print(
        f"Executing {{scenario_id}}: "
        f"{{description}}"
    )

    with grpc.insecure_channel(
        SERVER
    ) as channel:

        stub = (
            prime_pb2_grpc
            .PrimeCheckerServiceStub(channel)
        )

        request = prime_pb2.PrimeRequest(
            number=number
        )

        response = stub.CheckPrime(
            request,
            timeout=5
        )

        assert (
            response.number == number
        ), (
            f"{{scenario_id}}: "
            "Incorrect number returned"
        )

        assert (
            response.is_prime == expected
        ), (
            f"{{scenario_id}}: "
            f"Expected {{expected}}, "
            f"but received "
            f"{{response.is_prime}}"
        )

        assert (
            response.message
        ), (
            f"{{scenario_id}}: "
            "Response message is empty"
        )
'''

    GENERATED_TEST_FILE.write_text(
        test_code,
        encoding="utf-8"
    )

    print(
        "Generated test file:"
    )

    print(
        GENERATED_TEST_FILE
    )


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print()
    print("=" * 60)
    print("gRPC AI Test Generator")
    print("=" * 60)

    proto_content = read_proto()

    current_hash = calculate_hash(
        proto_content
    )

    status = detect_change(
        current_hash
    )

    print(
        f"Proto status: {status}"
    )

    if status == "NO_CHANGE":

        print(
            "No proto changes detected."
        )

        print(
            "Test generation skipped."
        )

        return

    scenario_data = get_scenarios(
        proto_content
    )

    print(
        "Number of scenarios generated:",
        len(scenario_data["scenarios"])
    )

    generate_test_file(
        scenario_data
    )

    save_hash(
        current_hash
    )

    print()
    print(
        "Test generation completed."
    )

    print("=" * 60)


if __name__ == "__main__":
    main()