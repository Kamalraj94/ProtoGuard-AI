from math import isqrt

from generated import prime_pb2
from generated import prime_pb2_grpc


def is_prime_number(number: int) -> bool:
    """Check whether the supplied integer is prime."""

    if number <= 1:
        return False

    if number == 2:
        return True

    if number % 2 == 0:
        return False

    maximum_divisor = isqrt(number)

    for divisor in range(3, maximum_divisor + 1, 2):
        if number % divisor == 0:
            return False

    return True


class PrimeCheckerService(
    prime_pb2_grpc.PrimeCheckerServiceServicer
):
    """Implementation of the PrimeCheckerService."""

    def CheckPrime(self, request, context):
        number = request.number
        result = is_prime_number(number)

        if result:
            message = f"{number} is a prime number."
        else:
            message = f"{number} is not a prime number."

        print(
            f"Request received: number={number}, "
            f"is_prime={result}"
        )

        return prime_pb2.PrimeResponse(
            number=number,
            is_prime=result,
            message=message,
        )