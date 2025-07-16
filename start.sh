docker stop gradio-agent || true
docker rm gradio-agent || true
docker build -t gradio-agent .
docker run --name gradio-agent -d -p 7860:7860 graph-agent