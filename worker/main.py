import os
import time
from google.cloud import pubsub_v1

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "local-project")
SUB_ID = os.getenv("GCP_SUB_ID", "demo-sub")

def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUB_ID)

    print(f"Worker started. Pulling 1 message from {subscription_path}...")

    # Pull exactly 1 message
    response = subscriber.pull(
        request={
            "subscription": subscription_path,
            "max_messages": 1,
            "return_immediately": False,
        },
        timeout=10.0
    )

    if not response.received_messages:
        print("No messages found. Exiting gracefully.")
        return

    received_message = response.received_messages[0]
    message_data = received_message.message.data.decode("utf-8")
    ack_id = received_message.ack_id

    print(f"Processing message: {message_data}")
    
    # Simulate CPU-bound or intensive batch work
    time.sleep(5) 

    # Acknowledge the message
    subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": [ack_id]})
    print("Message acknowledged successfully. Job complete.")

if __name__ == "__main__":
    main()