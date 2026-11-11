import json
from pathlib import Path
from typing import Any

import grpc
from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
from google.protobuf import json_format
from google.protobuf import message_factory


def load_descriptor_pool(
    descriptor_file: Path,
) -> descriptor_pool.DescriptorPool:
    """
    Load the compiled FileDescriptorSet into a descriptor pool.
    """

    descriptor_set = (
        descriptor_pb2.FileDescriptorSet()
    )

    descriptor_set.ParseFromString(
        descriptor_file.read_bytes()
    )

    pool = descriptor_pool.DescriptorPool()

    remaining_files = list(
        descriptor_set.file
    )

    while remaining_files:
        progress_made = False

        for file_descriptor in remaining_files[:]:
            try:
                pool.Add(file_descriptor)
                remaining_files.remove(file_descriptor)
                progress_made = True
            except Exception:
                # Dependency might not have been added yet.
                continue

        if not progress_made:
            unresolved = [
                file_descriptor.name
                for file_descriptor in remaining_files
            ]

            raise RuntimeError(
                "Could not load descriptor dependencies: "
                + ", ".join(unresolved)
            )

    return pool


def create_message(
    pool: descriptor_pool.DescriptorPool,
    message_type: str,
    values: dict,
):
    """
    Dynamically construct a protobuf message from its fully
    qualified type name and JSON-style values.
    """

    message_descriptor = (
        pool.FindMessageTypeByName(
            message_type
        )
    )

    message_class = (
        message_factory.GetMessageClass(
            message_descriptor
        )
    )

    message = message_class()

    json_format.ParseDict(
        values,
        message,
        ignore_unknown_fields=False,
        descriptor_pool=pool,
    )

    return message


def invoke_unary_rpc(
    server_address: str,
    descriptor_file: Path,
    method_path: str,
    request_type: str,
    response_type: str,
    request_values: dict,
    timeout_seconds: int = 5,
) -> dict:
    """
    Invoke any unary gRPC RPC using its dynamic descriptors.
    """

    pool = load_descriptor_pool(
        descriptor_file
    )

    request_message = create_message(
        pool,
        request_type,
        request_values,
    )

    response_descriptor = (
        pool.FindMessageTypeByName(
            response_type
        )
    )

    response_class = (
        message_factory.GetMessageClass(
            response_descriptor
        )
    )

    with grpc.insecure_channel(
        server_address
    ) as channel:
        rpc_method = channel.unary_unary(
            method_path,
            request_serializer=lambda message: (
                message.SerializeToString()
            ),
            response_deserializer=(
                response_class.FromString
            ),
        )

        response = rpc_method(
            request_message,
            timeout=timeout_seconds,
        )

    return json_format.MessageToDict(
        response,
        preserving_proto_field_name=True,
        use_integers_for_enums=False,
        descriptor_pool=pool,
    )


def get_nested_value(
    response: dict,
    field_path: str,
) -> Any:
    """
    Resolve nested paths such as customer.address.city.
    """

    current_value: Any = response

    for path_part in field_path.split("."):
        if not isinstance(current_value, dict):
            raise AssertionError(
                f"Cannot resolve '{field_path}'. "
                f"'{path_part}' is not inside an object."
            )

        if path_part not in current_value:
            raise AssertionError(
                f"Response field was not found: "
                f"{field_path}"
            )

        current_value = current_value[
            path_part
        ]

    return current_value


def apply_assertion(
    response: dict,
    assertion: dict,
) -> None:
    """
    Apply one AI-generated assertion to the response.
    """

    field = assertion["field"]
    operator = assertion["operator"]

    actual_value = get_nested_value(
        response,
        field,
    )

    expected_value = assertion.get(
        "value"
    )

    if operator == "equals":
        assert actual_value == expected_value

    elif operator == "not_equals":
        assert actual_value != expected_value

    elif operator == "contains":
        assert expected_value in actual_value

    elif operator == "not_empty":
        assert actual_value not in (
            None,
            "",
            [],
            {},
        )

    elif operator == "is_true":
        assert actual_value is True

    elif operator == "is_false":
        assert actual_value is False

    elif operator == "greater_than":
        assert actual_value > expected_value

    elif operator == "less_than":
        assert actual_value < expected_value

    else:
        raise AssertionError(
            f"Unsupported assertion operator: "
            f"{operator}"
        )