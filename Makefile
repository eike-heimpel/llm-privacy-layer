# Configuration for anonymizer tests
RESULTS_DIR := test_reports
RESULTS_FILE := test_results.md

# Available targets:
# make test - Run the anonymizer tests
# make test-clean - Clean up test resources

.PHONY: test test-clean

test:
	@echo "=== Running Privacy Container Anonymizer Tests ==="
	@mkdir -p $(RESULTS_DIR)
	@docker-compose -f docker-compose.test.yml up --build
	@echo "=== Test Results ==="
	@echo "Results are available in $(RESULTS_DIR)/$(RESULTS_FILE)"

test-clean:
	@docker-compose -f docker-compose.test.yml down -v
	@rm -rf $(RESULTS_DIR)
	@echo "Cleaned up test resources" 