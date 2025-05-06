# Anonymizer Tests

Simple tests for the Privacy Container anonymizer functionality.

## Running Tests

The tests use Docker to ensure a consistent environment. Run them using:

```bash
# From the project root directory
make test
```

The test results will be saved to a markdown file (`results/test_results.md`) for easy reading.

To clean up test resources:
```bash
make test-clean
```

## Test Cases

The tests verify the following:

1. Basic anonymization: Checks if names and emails are properly anonymized
2. Deanonymization: Verifies that anonymized data can be restored to its original form
3. Complex conversations: Tests handling of multiple messages with different types of PII
4. Non-PII content: Ensures that content without PII remains unchanged

## LLM Evaluation

For the complex conversation test, we use an LLM (Google's Gemini 2.0 Flash via OpenRouter) to evaluate the readability and clarity of the anonymized text. The LLM provides a brief assessment addressing:

1. How readable/understandable the anonymized text is
2. Any confusing parts or ambiguities
3. Whether the context of the conversation is preserved despite anonymization

To use this feature, set your OpenRouter configuration in the `.env` file:

```
# In .env file
OPENROUTER_API_KEY=your_key_here
EVAL_MODEL=google/gemini-2.0-flash-001
```

## Configuration

All configuration is in the `.env` file, which is automatically loaded by Docker Compose:
- OpenRouter API key and model selection

The test results location is configured in the docker-compose.test.yml file. 