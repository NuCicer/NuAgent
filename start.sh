docker stop graph-agent || true
docker rm graph-agent || true
docker build -t graph-agent .
docker run --name gradio-agent -d -p 7860:7860 graph-agent