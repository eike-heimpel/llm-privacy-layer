# Anonymizer Test Results

This file contains the results of running the anonymizer tests.

## Basic Anonymization Test

**Original message:**
```
My name is John Smith and my email is john.smith@example.com.
```

**Anonymized message:**
```
My name is <PERSON_19f07a38> and my email is <EMAIL_ADDRESS_79b162d8>.
```

## Deanonymization Test

**Original message:**
```
My phone number is 555-123-4567 and I live in New York.
```

**Anonymized message:**
```
My phone number is <PHONE_NUMBER_90d667d4> and I live in <LOCATION_c3083341>.
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

**user**: Hi, I'm <PERSON_2709899c>.

**assistant**: Hello <PERSON_6ad01561>, how can<DATE_TIME_c1046069>lp you today?

**user**: I need to send money to my friend. His account is <DATE_TIME_6be8df91> at Chase Bank.

**assistant**: I understand you want to send money to your friend's account <DATE_TIME_e7d40f6a> at Chase Bank.


### LLM Evaluation:

The anonymized text is generally readable, although the placeholder format can be a little disruptive. The use of `<PERSON_id>` is understandable, but the repeated use of `<DATE_TIME_id>` for what is clearly bank account information creates ambiguity. The context of a user initiating a conversation and wanting to send money is still preserved. The primary source of confusion lies in the mislabeling of bank account information as dates/times.


## Non-PII Content Test

### Original message:

**user**: What is the capital of France?


### Anonymized message (should be identical):

**user**: What is the capital of <LOCATION_5e713efd>?

