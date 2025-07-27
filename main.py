from fastapi import FastAPI, Request
from pydantic import BaseModel
from vertex_vision_detect import run_object_detection, send_alert

app = FastAPI()

class AlertPayload(BaseModel):
    count: int

@app.post("/alert")
def trigger_alert(payload: AlertPayload):
    count = payload.count
    send_alert(count)
    return {"message": f"Alert sent for count = {count}"}

@app.get("/test-vertex")
def test_vertex_detection():
    count = run_object_detection()
    send_alert(count)
    return {"people_count": count}
