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
        ("PRIME_001", "Verify smallest prime number", 2, True),
        ("PRIME_002", "Verify typical prime number", 17, True),
        ("PRIME_003", "Verify composite number", 25, False),
        ("PRIME_004", "Verify zero", 0, False),
        ("PRIME_005", "Verify one", 1, False),
        ("PRIME_006", "Verify negative number", -7, False),
        ("PRIME_007", "Verify even composite number", 4, False),
        ("PRIME_008", "Verify perfect square", 49, False),
        ("PRIME_009", "Verify larger prime", 97, True)
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
        f"Executing {scenario_id}: "
        f"{description}"
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
            f"{scenario_id}: "
            "Incorrect number returned"
        )

        assert (
            response.is_prime == expected
        ), (
            f"{scenario_id}: "
            f"Expected {expected}, "
            f"but received "
            f"{response.is_prime}"
        )

        assert (
            response.message
        ), (
            f"{scenario_id}: "
            "Response message is empty"
        )
