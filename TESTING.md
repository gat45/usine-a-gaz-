# HX365 Command Center - Test Suite

This repository contains the complete HX365 Command Center application with a comprehensive test suite.

## Test Suite Overview

The test suite includes:

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Full pipeline testing
3. **System Tests**: End-to-end functionality validation
4. **Performance Tests**: Hardware optimization validation
5. **Frontend Tests**: GUI and interface validation

## Running the Tests

### Quick Test Run
Execute the batch script to run all tests:
```bash
run_tests.bat
```

### Manual Test Run
Run the comprehensive test suite manually:
```bash
python test_comprehensive.py
```

### Individual Component Tests
Run specific test modules:
```bash
python -m pytest test_integration.py -v
```

## Test Reports

After running the tests, you'll receive:
- A detailed text report with all test results
- A JSON report with structured data
- Performance metrics and system information
- Dependency and compatibility checks

## Prerequisites

Before running the tests, ensure you have:

- Python 3.8 or higher
- All dependencies installed via `pip install -r requirements.txt`
- FastFlowLM running on port 52625 (optional for full functionality)
- FastFlow Companion running on port 52626 (optional for full functionality)

## Test Coverage

The test suite validates:

- **Backend Orchestration**: Service communication and state management
- **Hardware Optimization**: CPU affinity and NPU monitoring
- **RAG System**: Document ingestion and retrieval
- **API Endpoints**: OpenAI-compatible interface
- **Frontend Elements**: GUI functionality and responsiveness
- **Power User Features**: Commands and hybrid mode
- **Integration**: Full pipeline from input to response

## Expected Results

A successful test run should show:
- All components initializing correctly
- API endpoints responding properly
- Hardware optimization features working
- RAG system ingesting and retrieving documents
- Frontend elements loading and functioning
- No critical errors in the system logs

## Troubleshooting

If tests fail:

1. Check that all dependencies are installed
2. Verify that required services (FastFlowLM, Companion) are running
3. Review the generated reports for specific error details
4. Check system resources (CPU, memory, disk space)
5. Ensure you're running the tests from the correct directory

## Performance Benchmarks

The test suite measures:

- API response times
- RAG retrieval latency
- Hardware utilization rates
- Memory consumption
- System stability under load