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
- Includes custom patterns for improved detection accuracy
- Maintains a mapping between original data and anonymized placeholders
- Provides detailed logging for troubleshooting
- Docker containerized for easy deployment

## Requirements

- Docker and Docker Compose (for containerized deployment)
- OpenWebUI with filter support

## Installation

### Using Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/privacy-container.git
   cd privacy-container
   ```

2. Build and start the container:
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

## Deployment

For deployment to a home server, a convenience script is included:

```bash
./deploy-to-homeserver.sh
```

Update the configuration variables in this script to match your environment.

## Configuration

Configuration options are available via environment variables:

- `LOG_LEVEL`: Set logging level (default: INFO)

## Security Considerations

- By default, CORS is configured to allow all origins. In production, restrict this to your OpenWebUI URL.
- The service currently maintains anonymization mappings in memory. For production use, consider implementing a more persistent storage solution.

## License

[MIT License](LICENSE)

## Acknowledgements

- [Microsoft Presidio](https://github.com/microsoft/presidio) for PII detection and anonymization
- [FastAPI](https://fastapi.tiangolo.com/) framework 