# Privacy Container for OpenWebUI

An external privacy filter API for OpenWebUI that anonymizes sensitive information in prompts before sending them to language models and deanonymizes responses.

## Overview

Privacy Container is a FastAPI-based application that acts as a middleware between OpenWebUI and language models. It provides:

- **Privacy protection**: Automatically detects and anonymizes personally identifiable information (PII) in user prompts
- **Response deanonymization**: Restores original information in model responses for a seamless user experience
- **Seamless integration**: Works alongside OpenWebUI as an external filter

## How It Works

1. When a user sends a prompt to OpenWebUI, it passes through the Privacy Container's `inlet` filter
2. PII such as names, email addresses, phone numbers, and locations are detected and replaced with anonymized placeholders
3. The anonymized prompt is sent to the language model
4. When the model responds, the response passes through the Privacy Container's `outlet` filter
5. Anonymized placeholders in the response are replaced with the original data
6. The deanonymized response is returned to the user

## Features

- Built with FastAPI for high performance
- Uses Microsoft Presidio for robust PII detection and anonymization
- Configurable confidence threshold for PII detection
- Maintains a mapping between original data and anonymized placeholders
- Provides detailed logging with performance metrics
- Docker containerized for easy deployment

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
- OpenWebUI with filter support

## Installation

### Using Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/privacy-container.git
   cd privacy-container
   ```

2. Create a `.env` file based on the `.env.example` template:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Build and start the container:
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

4. Start the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8010
   ```

## Integration with OpenWebUI

1. Configure OpenWebUI to use this service as an external filter
2. Set the filter URL to `http://your-server:8010`

## API Endpoints

- `POST /api/inlet`: Processes incoming prompts and anonymizes PII
- `POST /api/outlet`: Processes model responses and deanonymizes placeholders
- `GET /health`: Health check endpoint

## Performance

The service is designed for minimal latency:
- Typical anonymization processing time: ~0.2 seconds for complex prompts
- Typical deanonymization processing time: <0.001 seconds

## Configuration

### Environment Variables

- `LOG_LEVEL`: Set logging level (default: INFO)
- `REMOTE_HOST`: For deployment script, the remote server hostname
- `REMOTE_USER`: For deployment script, the remote server username
- `REMOTE_DIR`: For deployment script, the remote directory path

### Code Configuration

The following settings can be adjusted in the code:

- **Confidence Threshold**: Currently set to 0.75 (in `anonymizer.py`). Higher values (e.g., 0.9) reduce false positives but may miss some PII. Lower values (e.g., 0.5) catch more potential PII but increase false positives.
- **Entity Types**: The specific types of PII to detect and anonymize can be modified in the `operators` dictionary.
- **Skip Terms**: Common terms that should never be treated as PII.

## Deployment

For deployment to a home server, a convenience script is included:

```bash
./deploy-to-homeserver.sh
```

The script uses environment variables from your `.env` file for configuration.

## Security Considerations

- By default, CORS is configured to allow all origins. In production, restrict this to your OpenWebUI URL.
- The service currently maintains anonymization mappings in memory. For production use, consider implementing a more persistent storage solution.
- No PII is stored permanently - mappings exist only for the duration of the request/response cycle.

## Troubleshooting

- Check logs for detailed information about detected entities and processing times
- If too many false positives are detected, increase the confidence threshold
- If important PII is being missed, decrease the confidence threshold

## License

[MIT License](LICENSE)

## Acknowledgements

- [Microsoft Presidio](https://github.com/microsoft/presidio) for PII detection and anonymization
- [FastAPI](https://fastapi.tiangolo.com/) framework 