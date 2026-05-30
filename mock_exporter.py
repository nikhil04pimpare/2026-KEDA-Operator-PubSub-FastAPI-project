import http.server
import os
from google.cloud import pubsub_v1

class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            try:
                # Synchronously poll the local emulator subscription backlog
                subscriber = pubsub_v1.SubscriberClient()
                sub_path = subscriber.subscription_path("local-project", "demo-sub")
                
                # Pull without acking to see if messages are present
                response = subscriber.pull(
                    request={"subscription": sub_path, "max_messages": 100, "return_immediately": True},
                    timeout=2.0
                )
                backlog_count = len(response.received_messages)
                
                # Format as a standard Prometheus plaintext gauge metric
                output = f"# HELP pubsub_backlog Number of unacked messages\n# TYPE pubsub_backlog gauge\npubsub_backlog {backlog_count}\n"
                
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(output.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    print("Starting mock metrics exporter on port 8000...")
    server = http.server.HTTPServer(('0.0.0.0', 8000), MetricsHandler)
    server.serve_forever()