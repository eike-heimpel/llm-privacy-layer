# LLM Privacy Layer Tests

This directory contains tests for the LLM Privacy Layer application.

## Running Tests

To run all tests:

```bash
make test
```

This will:
1. Build and run the test container
2. Execute all tests with pytest
3. Generate test results in `test_reports/test_results.md`

## Test Structure

The tests are organized as follows:

- `utils/test_anonymizer.py`: Tests for the anonymizer module
  - Basic anonymization tests
  - Deanonymization tests
  - Custom entities tests
  - Entity-specific threshold tests
  - Skip terms tests

## Key Tests

### Basic Functionality Tests
- **test_basic_anonymization**: Tests that basic PII is detected and anonymized
- **test_deanonymization**: Tests that anonymized content can be properly restored
- **test_non_pii_content**: Tests that non-PII content is preserved unchanged

### Advanced Feature Tests
- **test_custom_entities**: Tests that custom entities from profiles are properly anonymized
- **test_entity_specific_thresholds**: Tests that different thresholds for different entity types work correctly
- **test_skip_terms**: Tests that terms in the skip_terms list are not anonymized

## Adding New Tests

When adding new tests:

1. Add the test function to `tests/utils/test_anonymizer.py`
2. Use the `write_to_results()` function to document test inputs/outputs
3. Include assertions to validate the test expectations
4. Make sure to use the standard test format:
   ```python
   def test_something():
       """Test description"""
       write_to_results("## Your Test Name\n")
       
       # Test code here
       
       # Document results
       write_to_results(f"**Some result:**\n```\n{your_result}\n```\n")
   ```

## LLM Evaluation

Some tests use the `evaluate_with_llm()` function to get qualitative feedback on anonymization quality. This requires an OpenRouter API key in the environment variables. 