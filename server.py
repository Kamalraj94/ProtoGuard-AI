from concurrent import futures
import logging

import grpc
from grpc_reflection.v1alpha import reflection

from generated import prime_pb2
from generated import prime_pb2_grpc
from prime_service import PrimeCheckerService


HOST = "[::]"
PORT = 50051


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    prime_pb2_grpc.add_PrimeCheckerServiceServicer_to_server(
        PrimeCheckerService(),
        server,
    )

    service_names = (
        prime_pb2.DESCRIPTOR.services_by_name[
            "PrimeCheckerService"
        ].full_name,
        reflection.SERVICE_NAME,
    )

    reflection.enable_server_reflection(
        service_names,
        server,
    )

    server.add_insecure_port(f"{HOST}:{PORT}")
    server.start()
 
    print("=" * 50)
    print("Prime Checker gRPC server started")
    print(f"Address: localhost:{PORT}")
    print("Service: prime.PrimeCheckerService")
    print("Method: CheckPrime")
    print("Reflection: Enabled")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping gRPC server...")
        server.stop(grace=5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()