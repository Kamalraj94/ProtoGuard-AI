# ProtoGuard-AI
ProtoGuard AI explores how generative AI can transform quality engineering for modern gRPC-based applications while maintaining deterministic technical controls. The approach treats the application's Protocol Buffer contract as an active quality asset rather than simply an interface definition used during development.

                    gRPC Application
                         |
                         v
                  proto/*.proto
                         |
             +-----------+------------+
             |                        |
             v                        v
      gRPC Code Generation      AI Test Generator
      generate_proto.py          generator.py
             |                        |
             v                        v
      generated/*_pb2.py      Detect Proto Changes
      generated/*_grpc.py             |
                                      v
                             Build Proto Descriptors
                                      |
                                      v
                              contracts.pb
                                      |
                                      v
                           AI / Mock Scenario Provider
                                      |
                                      v
                           Validate AI Scenarios
                                      |
                                      v
                             scenarios.json
                                      |
                                      v
                       test_generated_grpc.py
                                      |
                                      v
                                  pytest
                                      |
                                      v
                           Generic gRPC Runtime
                                      |
                                      v
                       Running gRPC Server :50051
                                      |
                               +------+------+
                               |             |
                               v             v
                         Prime Checker   Odd/Even Checker

1.Setting up the environment 
Make sure Python is installed and the project virtual environment has been created. 

Execute the below commands step by step 
cd C:\Users\UM393CD\gRPC

Activate the virtual environment:
.\.venv\Scripts\Activate.ps1

After activation, the terminal should look similar to:
(.venv) PS C:\Users\UM393CD\gRPC>

Whenever proto is created or modified, regenerate the Python gRPC classes.
python generate_proto.py

Verify the generated proto 
python -c "from generated import prime_pb2, prime_pb2_grpc; print('Proto imports working')"

Expected : Proto imports working

2.Start the GRPC server 

.\.venv\Scripts\Activate.ps1
python server.py

Expected output : 
 gRPC server started
Server address: localhost:50051
Service: XXXXXX
Method: XXXXX


3.Generate automated scripts 

Open terminal 2 in VS code 

.\.venv\Scripts\Activate.ps1
python .\proto-test-generator\generator.py

4.Execute automated scripts 

python -m pytest `
    .\proto-test-generator\generated_tests `
    -v -s `
    --html=.\proto-test-generator\reports\html\grpc-test-report.html `
    --self-contained-html

5. Check the reports

Start-Process `
    .\proto-test-generator\reports\html\grpc-test-report.html

Read every .proto file from the root proto folder.
Compile the proto files into a descriptor set.
Extract services, RPCs, request types, response types, fields, enums, and streaming information.
Send both the proto content and structured descriptor summary to the LLM.
Require generic JSON scenarios containing request payloads and expected response assertions.
Generate a generic pytest class.
Execute unary RPCs dynamically, without hardcoding PrimeCheckerServiceStub.