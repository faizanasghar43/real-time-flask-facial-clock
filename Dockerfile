FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download insightface buffalo_sc models (~150MB) at build time
RUN python -c "from insightface.app import FaceAnalysis; a=FaceAnalysis(name='buffalo_sc',providers=['CPUExecutionProvider']); a.prepare(ctx_id=0,det_size=(320,320))"

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]
