# Kafka delivery
Disable automatic consumer offset commits. Persist events to PostgreSQL before committing Kafka offsets. A crash after database commit can replay an event; a unique event_id makes storage idempotent.
