import os
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from google.cloud import pubsub_v1
from google.api_core.exceptions import AlreadyExists

app = FastAPI(title="KEDA Pub/Sub Publisher Demo")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "local-project")
TOPIC_ID = os.getenv("GCP_TOPIC_ID", "demo-topic")
SUB_ID = os.getenv("GCP_SUB_ID", "demo-sub")

publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
subscription_path = subscriber.subscription_path(PROJECT_ID, SUB_ID)

@app.on_event("startup")
def setup_pubsub():
    try:
        publisher.create_topic(request={"name": topic_path})
    except AlreadyExists:
        pass
    try:
        subscriber.create_subscription(request={"name": subscription_path, "topic": topic_path})
    except AlreadyExists:
        pass

class MessageData(BaseModel):
    data: str

@app.post("/publish")
async def publish_message(payload: MessageData):
    try:
        data_bytes = payload.data.encode("utf-8")
        future = publisher.publish(topic_path, data_bytes)
        return {"status": "success", "message_id": future.result()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
def get_metrics():
    try:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 100, "return_immediately": True},
            timeout=1.0
        )
        backlog_count = len(response.received_messages)
    except Exception:
        backlog_count = 0
    
    # Return a clean JSON key-value object
    return {"backlog": backlog_count}