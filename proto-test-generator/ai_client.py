import json
import os
import re

import requests


def build_ai_prompt(
    proto_sources: list[dict],
    contract_summary: dict,
) -> str:
    """
    Build a generic prompt for any gRPC proto contract.

    The LLM receives:
    - Original proto source
    - Parsed service and message metadata
    - Required output schema
    """

    proto_text = "\n\n".join(
        (
            f"FILE: {proto_source['file_name']}\n"
            f"{proto_source['content']}"
        )
        for proto_source in proto_sources
    )

    contract_json = json.dumps(
        contract_summary,
        indent=2,
    )

    return f"""
You are a senior gRPC API test automation engineer.

Analyze the supplied Protocol Buffer contracts and generate executable
test scenarios for every supported unary RPC.

The proto can represent any business functionality, including but not
limited to:

- prime-number validation
- odd/even validation
- palindrome checks
- customer APIs
- payment APIs
- order APIs
- calculation services
- text-processing services

Do not assume a specific business domain.

Derive test scenarios from:

1. Service names
2. RPC names
3. Request and response message names
4. Field names and field types
5. Enum definitions
6. Proto comments, when available
7. The apparent business meaning of the contract

Generate:

- positive scenarios
- negative scenarios
- boundary scenarios
- default-value scenarios
- empty-value scenarios when relevant
- enum scenarios
- repeated-field scenarios when relevant
- business-semantic scenarios inferred from method and field names

Return JSON only.

Do not include Markdown.
Do not include code fences.
Do not include explanations outside the JSON.
Do not invent services, RPCs, request fields, response fields, or enum
values that are absent from the supplied contract.
Use original proto field names in snake_case.

Required JSON structure:

{{
  "scenarios": [
    {{
      "scenario_id": "UNIQUE_SCENARIO_ID",
      "title": "Readable test title",
      "proto_file": "sample.proto",
      "service": "package.ServiceName",
      "rpc": "RpcName",
      "method_path": "/package.ServiceName/RpcName",
      "request_type": "package.RequestMessage",
      "response_type": "package.ResponseMessage",
      "request": {{
        "field_name": "value"
      }},
      "expected": {{
        "field_name": "expected value"
      }},
      "assertions": [
        {{
          "field": "field_name",
          "operator": "equals",
          "value": "expected value"
        }}
      ],
      "category": "POSITIVE"
    }}
  ]
}}

Supported assertion operators:

- equals
- not_equals
- contains
- not_empty
- is_true
- is_false
- greater_than
- less_than

Rules:

- Generate scenarios only for unary RPCs.
- Every scenario_id must be unique.
- request must contain only fields from request_type.
- expected and assertions must contain only fields from response_type.
- Use JSON Boolean values for protobuf Boolean fields.
- Use valid enum names from the descriptor.
- Do not include comments inside JSON.
- Generate between 3 and 12 scenarios per unary RPC.
- If the expected business outcome cannot be safely inferred, assert
  only structural response properties such as not_empty or equality
  for clearly echoed fields.
- Do not make unsafe or unsupported business assumptions.

Structured contract summary:

{contract_json}

Original proto contracts:

{proto_text}
""".strip()


def extract_message_content(response_json: dict) -> str:
    """
    Extract choices[0].message.content from the chat-completion
    response.
    """

    try:
        content = response_json[
            "choices"
        ][0][
            "message"
        ][
            "content"
        ]
    except (
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        raise RuntimeError(
            "Unexpected LLM response structure:\n"
            + json.dumps(response_json, indent=2)
        ) from error

    if not isinstance(content, str):
        raise RuntimeError(
            "LLM message content is not a string."
        )

    if not content.strip():
        raise RuntimeError(
            "LLM returned an empty message."
        )

    return content.strip()


def extract_json(content: str) -> dict:
    """
    Parse JSON even if the model unexpectedly returns Markdown
    code fences.
    """

    content = content.strip()

    fence_match = re.match(
        r"^```(?:json)?\s*(.*?)\s*```$",
        content,
        re.DOTALL | re.IGNORECASE,
    )

    if fence_match:
        content = fence_match.group(1).strip()

    first_brace = content.find("{")
    last_brace = content.rfind("}")

    if first_brace == -1 or last_brace == -1:
        raise RuntimeError(
            "No JSON object was found in the LLM response."
        )

    json_text = content[
        first_brace:last_brace + 1
    ]

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "The LLM returned invalid JSON.\n"
            f"Parsing error: {error}\n"
            f"Response content: {content}"
        ) from error


def get_ai_scenarios(
    proto_sources: list[dict],
    contract_summary: dict,
) -> dict:
    """
    Call the organization Incubator endpoint and return parsed
    scenario JSON.
    """

    endpoint = os.getenv(
        "INCUBATOR_ENDPOINT",
        "",
    ).strip()

    api_key = os.getenv(
        "INCUBATOR_KEY",
        "",
    ).strip()

    deployment = os.getenv(
        "INCUBATOR_DEPLOYMENT",
        "",
    ).strip()

    api_version = os.getenv(
        "INCUBATOR_API_VERSION",
        "2023-05-15",
    ).strip()

    timeout_seconds = int(
        os.getenv(
            "AI_TIMEOUT_SECONDS",
            "90",
        )
    )

    if not endpoint:
        raise RuntimeError(
            "INCUBATOR_ENDPOINT is missing from .env."
        )

    if not api_key:
        raise RuntimeError(
            "INCUBATOR_KEY is missing from .env."
        )

    if not deployment:
        raise RuntimeError(
            "INCUBATOR_DEPLOYMENT is missing from .env."
        )

    prompt = build_ai_prompt(
        proto_sources,
        contract_summary,
    )

    body = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You generate generic gRPC API test scenarios. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.1,
        "max_tokens": 6000,
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }

    query_params = {
        "api-version": api_version,
    }

    full_path = (
        endpoint.rstrip("/")
        + "/openai/deployments/"
        + deployment
        + "/chat/completions"
    )

    print("Calling AI scenario provider...")
    print(f"Deployment: {deployment}")
    print(f"API version: {api_version}")

    try:
        response = requests.post(
            full_path,
            json=body,
            headers=headers,
            params=query_params,
            timeout=timeout_seconds,
        )

    except requests.Timeout as error:
        raise RuntimeError(
            "The AI request timed out."
        ) from error

    except requests.ConnectionError as error:
        raise RuntimeError(
            "Unable to connect to the AI endpoint. "
            "Check VPN, proxy, endpoint, and network access."
        ) from error

    except requests.RequestException as error:
        raise RuntimeError(
            f"The AI request failed: {error}"
        ) from error

    if not response.ok:
        raise RuntimeError(
            "The AI endpoint returned an error.\n"
            f"HTTP status: {response.status_code}\n"
            f"Response: {response.text}"
        )

    try:
        response_json = response.json()
    except ValueError as error:
        raise RuntimeError(
            "The AI endpoint returned a non-JSON HTTP response.\n"
            f"Response: {response.text}"
        ) from error

    message_content = extract_message_content(
        response_json
    )

    return extract_json(
        message_content
    )