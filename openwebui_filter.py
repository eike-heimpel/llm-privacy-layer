from pydantic import BaseModel
import requests
from typing import Dict, Any, Optional
import logging
import time


class Filter:
    class Valves(BaseModel):
        PRIVACY_API_URL: str = "http://localhost:8000"
        LOG_LEVEL: str = "INFO"
        TIMEOUT_SECONDS: int = 5

    def __init__(self):
        self.valves = self.Valves()

        # Set up logging
        self.logger = logging.getLogger("privacy_filter")
        if not self.logger.handlers:  # Only add handler if not already configured
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.setLevel(getattr(logging, self.valves.LOG_LEVEL))
        self.logger.info(
            f"Privacy filter initialized with API URL: {self.valves.PRIVACY_API_URL}"
        )

    def inlet(
        self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process and anonymize the input data"""
        start_time = time.time()
        self.logger.info("Starting inlet processing")

        try:
            self.logger.info(
                f"Sending request to {self.valves.PRIVACY_API_URL}/api/inlet"
            )

            response = requests.post(
                f"{self.valves.PRIVACY_API_URL}/api/inlet",
                json=body,
                timeout=self.valves.TIMEOUT_SECONDS,
            )

            elapsed = time.time() - start_time
            self.logger.info(
                f"Received response in {elapsed:.2f}s with status: {response.status_code}"
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.info("Successfully anonymized data")
                return result
            else:
                self.logger.error(f"Error from privacy API: {response.status_code}")
                self.logger.error(f"Response content: {response.text}")
                return body

        except Exception as e:
            self.logger.error(f"Error in inlet: {str(e)}")
            return body
        finally:
            self.logger.info(
                f"Inlet processing completed in {time.time() - start_time:.2f}s"
            )

    def outlet(
        self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process and deanonymize the output data"""
        start_time = time.time()
        self.logger.info("Starting outlet processing")

        # Check if we have a privacy mapping ID in the metadata
        if "metadata" in body and "privacy_mapping_id" in body["metadata"]:
            self.logger.info(
                f"Found privacy mapping ID: {body['metadata']['privacy_mapping_id']}"
            )
        else:
            self.logger.info(
                "No privacy mapping ID found, may not have anonymized data"
            )

        try:
            self.logger.info(
                f"Sending request to {self.valves.PRIVACY_API_URL}/api/outlet"
            )

            response = requests.post(
                f"{self.valves.PRIVACY_API_URL}/api/outlet",
                json=body,
                timeout=self.valves.TIMEOUT_SECONDS,
            )

            elapsed = time.time() - start_time
            self.logger.info(
                f"Received response in {elapsed:.2f}s with status: {response.status_code}"
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.info("Successfully deanonymized data")
                return result
            else:
                self.logger.error(f"Error from privacy API: {response.status_code}")
                self.logger.error(f"Response content: {response.text}")
                return body

        except Exception as e:
            self.logger.error(f"Error in outlet: {str(e)}")
            return body
        finally:
            self.logger.info(
                f"Outlet processing completed in {time.time() - start_time:.2f}s"
            )
