# LLM Privacy Layer

A standalone privacy filter API that anonymizes sensitive information in JSON data before it's sent to language models and deanonymizes responses, designed to work with any LLM application as an external service.

## Overview

LLM Privacy Layer is a FastAPI-based service that acts as a privacy filter for LLM applications. It provides:

- **Privacy preprocessing**: Automatically detects and anonymizes personally identifiable information (PII) in data before it's sent to language models
- **Response postprocessing**: Restores original information in model responses for a seamless user experience
- **External service architecture**: Works as a separate service that doesn't require tight integration with your application code
- **JSON processing**: Handles any JSON structure for flexible integration

## How It Works

1. Your application calls the Privacy Layer's `inlet` endpoint with the data that would normally go directly to your LLM provider
2. The Privacy Layer detects and replaces PII with anonymized placeholders
3. The service returns the anonymized data to your application, which then sends it to your LLM provider
4. When your application receives a response from the LLM, it sends this response to the Privacy Layer's `outlet` endpoint
5. The Privacy Layer replaces anonymized placeholders with the original data
6. The deanonymized response is returned to your application

This way, sensitive information never reaches the LLM provider's systems.

## Features

- Built with FastAPI for high performance
- Uses Microsoft Presidio for robust PII detection and anonymization
- Configurable profiles with custom entity lists and thresholds
- Maintains a mapping between original data and anonymized placeholders
- Provides detailed logging with performance metrics
- Docker containerized for easy deployment
- Runs as a standalone service without dependencies on specific LLM libraries

## Entity Types Detected

The service currently detects the following types of sensitive information:

- Person names
- Email addresses
- Phone numbers
- Locations
- Dates and times
- IP addresses
- Domain names
- URLs
- Numeric patterns (NRP)

## Requirements

- Python 3.10+
- Docker and Docker Compose (for containerized deployment)
- An LLM application that can call external services

## Installation

### Using Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/llm-privacy-layer.git
   cd llm-privacy-layer
   ```

2. Create a `.env` file based on the `.env.example` template:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Create your profiles configuration file:
   ```bash
   cp app/config/example_profiles.yaml app/config/profiles.yaml
   # Edit profiles.yaml with your preferred configuration (optional)
   ```

4. Build and start the container:
   ```bash
   docker-compose up -d
   ```

### Manual Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. Create your profiles configuration file:
   ```bash
   cp app/config/example_profiles.yaml app/config/profiles.yaml
   # Edit profiles.yaml with your preferred configuration
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8010
   ```

## Integration with Your Application

The privacy layer operates as a stateless API that your application calls in this sequence:

1. Before sending data to an LLM:
   ```
   POST /api/inlet with your JSON payload
   ```

2. After receiving a response from an LLM:
   ```
   POST /api/outlet with the LLM's response
   ```

The privacy mappings are maintained between these calls using a unique identifier automatically added to the metadata.

### Example Integration Flow

```
Your App → LLM Privacy Layer (inlet) → Your App → LLM Provider → Your App → LLM Privacy Layer (outlet) → Your App → User
```

### Example Integration with OpenWebUI

OpenWebUI has a built-in external filter feature that can be configured to use LLM Privacy Layer:

1. Enter the LLM Privacy Layer URL (e.g., `http://localhost:8010`) in OpenWebUI's filter settings
2. Enable the external filter feature

## API Endpoints

- `POST /api/inlet`: Processes incoming data and anonymizes PII
- `POST /api/outlet`: Processes LLM responses and deanonymizes placeholders
- `GET /health`: Health check endpoint

## Performance

The service is designed for minimal latency:
- Typical anonymization processing time: ~0.2 seconds for complex prompts
- Typical deanonymization processing time: <0.001 seconds

## Configuration

### Environment Variables

- `LOG_LEVEL`: Set logging level (default: INFO)
- `LLM_PRIVACY_PROFILE_PATH`: Path to the profiles configuration file (default: app/config/profiles.yaml)
- `LLM_PRIVACY_DEFAULT_PROFILE`: Name of the default profile to use (default: default)
- `LLM_PRIVACY_CACHE_MAPPINGS`: Whether to cache mappings (default: true)
- `LLM_PRIVACY_CACHE_TTL`: Time-to-live for cached mappings in seconds (default: 3600)
- `REMOTE_HOST`: For deployment script, the remote server hostname
- `REMOTE_USER`: For deployment script, the remote server username
- `REMOTE_DIR`: For deployment script, the remote directory path

### Profiles Configuration

The anonymizer supports profiles for customized anonymization behavior. Profiles are defined in YAML format and stored in `app/config/profiles.yaml`. Each profile can specify:

> **Note:** The `profiles.yaml` file is included in `.gitignore` and must be created from `example_profiles.yaml` as described in the Installation section.

- **Custom Entity Lists**: Predefined entities to always anonymize 
- **Entity-Specific Thresholds**: Different confidence thresholds for different entity types
- **Skip Terms**: Terms that should never be anonymized
- **Fuzzy Matching**: Settings for fuzzy matching of custom entities

Example profile configuration:

```yaml
profiles:
  default:
    thresholds:
      PERSON: 0.85
      EMAIL_ADDRESS: 0.75
      LOCATION: 0.90
      DEFAULT: 0.85
    custom_entities:
      PERSON:
        - "John Doe"
        - "Jane Smith"
      ORGANIZATION:
        - "Acme Corporation"
    fuzzy_match:
      enabled: true
      thresholds:
        PERSON: 85
        DEFAULT: 80
    skip_terms:
      - "monday"
      - "tuesday"
      - "user"
      - "assistant"
  
  high_security:
    description: "Profile with lower thresholds to catch more potential PII"
    thresholds:
      DEFAULT: 0.6
```

### Anonymization Control

You can control anonymization behavior through profiles:

- **Disable Entity Type**: Set threshold to 1.0 to effectively disable detection for a specific entity type
- **Aggressive Anonymization**: Set threshold below 0.5 for maximum (but potentially noisy) PII detection
- **Custom Skip Terms**: Add domain-specific terms that should never be anonymized
- **Custom Entities**: Add known PII entities that should always be anonymized

### Code Configuration

The following settings can be adjusted in the code:

- **Confidence Threshold**: Default thresholds are defined in the profiles. Higher values reduce false positives but may miss some PII. Lower values catch more potential PII but increase false positives.
- **Entity Types**: The specific types of PII to detect and anonymize can be modified in the `operators` dictionary.

## Deployment

For deployment to a home server, a convenience script is included:

```bash
./deploy-to-homeserver.sh
```

The script uses environment variables from your `.env` file for configuration.

## Security Considerations

- By default, CORS is configured to allow all origins. In production, restrict this to your application URL.
- The service currently maintains anonymization mappings in memory. For production use, consider implementing a more persistent storage solution.
- No PII is stored permanently - mappings exist only for the duration of the request/response cycle.

## Troubleshooting

- Check logs for detailed information about detected entities and processing times
- If too many false positives are detected, increase the confidence threshold
- If important PII is being missed, decrease the confidence threshold

## Testing

Run the test suite to verify anonymization and deanonymization:

```bash
make test
```

Test results will be available in `test_reports/test_results.md`.

## License

[MIT License](LICENSE)

## Acknowledgements

- [Microsoft Presidio](https://github.com/microsoft/presidio) for PII detection and anonymization
- [FastAPI](https://fastapi.tiangolo.com/) framework 