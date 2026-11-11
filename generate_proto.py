from pathlib import Path

from grpc_tools import protoc


BASE_DIR = Path(__file__).resolve().parent
PROTO_DIR = BASE_DIR / "proto"
OUTPUT_DIR = BASE_DIR / "generated"
PROTO_FILE = PROTO_DIR / "prime.proto"


def fix_generated_import():
    grpc_file = OUTPUT_DIR / "prime_pb2_grpc.py"

    if not grpc_file.exists():
        raise FileNotFoundError(
            f"Generated file not found: {grpc_file}"
        )

    content = grpc_file.read_text(
        encoding="utf-8"
    )

    old_import = "import prime_pb2 as prime__pb2"

    new_import = (
        "from . import prime_pb2 as prime__pb2"
    )

    if old_import in content:
        content = content.replace(
            old_import,
            new_import,
        )

        grpc_file.write_text(
            content,
            encoding="utf-8",
        )

        print(
            "Fixed import inside prime_pb2_grpc.py"
        )

    elif new_import in content:
        print(
            "Generated import is already correct."
        )

    else:
        raise RuntimeError(
            "Could not locate the prime_pb2 import "
            "inside prime_pb2_grpc.py"
        )


def verify_generated_import():
    grpc_file = OUTPUT_DIR / "prime_pb2_grpc.py"

    content = grpc_file.read_text(
        encoding="utf-8"
    )

    expected_import = (
        "from . import prime_pb2 as prime__pb2"
    )

    if expected_import not in content:
        raise RuntimeError(
            "Generated import correction failed."
        )

    print(
        "Verified generated package import."
    )


def generate_proto_files():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    init_file = OUTPUT_DIR / "__init__.py"
    init_file.touch(exist_ok=True)

    result = protoc.main(
        [
            "grpc_tools.protoc",
            f"-I{PROTO_DIR}",
            f"--python_out={OUTPUT_DIR}",
            f"--grpc_python_out={OUTPUT_DIR}",
            str(PROTO_FILE),
        ]
    )

    if result != 0:
        raise RuntimeError(
            "Proto generation failed with "
            f"exit code {result}"
        )

    fix_generated_import()
    verify_generated_import()

    print("Generated gRPC files successfully.")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_proto_files()