# Anonymizer Test Results

This file contains the results of running the anonymizer tests.

## Basic Anonymization Test

**Original message:**
```
My name is John Smith and my email is john.smith@example.com.
```

**Anonymized message:**
```
My name is <PERSON_a1fbcb42> and my email is <EMAIL_ADDRESS_93f2364c>.
```

## Deanonymization Test

**Original message:**
```
My phone number is 555-123-4567 and I live in New York.
```

**Anonymized message:**
```
My phone number is <PHONE_NUMBER_0ad10e54> and I live in <LOCATION_6378f67f>.
```

**Deanonymized message:**
```
My phone number is 555-123-4567 and I live in New York.
```

## Complex Conversation Test

### Original Conversation:

**system**: You are a helpful assistant.

**user**: Hi, I'm Sarah Johnson.

**assistant**: Hello Sarah, how can I help you today?

**user**: I need to send money to my friend. His account is 12345678 at Chase Bank.

**assistant**: I understand you want to send money to your friend's account 12345678 at Chase Bank.


### Anonymized Conversation:

**system**: You are a helpful assistant.

**user**: Hi, I'm <PERSON_a61d0dbc>.

**assistant**: Hello <PERSON_7ebe1d4d>, how can<DATE_TIME_99257811>lp you today?

**user**: I need to send money to my friend. His account is <DATE_TIME_abc280d3> at Chase Bank.

**assistant**: I understand you want to send money to your friend's account <DATE_TIME_91dc34d1> at Chase Bank.


### LLM Evaluation:

Error during LLM evaluation: Completions.create() got an unexpected keyword argument 'headers'

## Non-PII Content Test

### Original message:

**user**: What is the capital of France?


### Anonymized message (should be identical):

**user**: What is the capital of <LOCATION_7468e363>?

