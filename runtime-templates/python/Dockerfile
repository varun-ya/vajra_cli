FROM python:3.11-slim

WORKDIR /app

# Copy requirements if exists
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Copy function code
COPY . .

# Set environment variables
ENV FUNCTION_TARGET={{HANDLER}}
ENV FUNCTION_SIGNATURE_TYPE=http

# Install Vajra runtime
RUN pip install flask google-cloud-logging

# Copy runtime wrapper
COPY vajra_runtime.py .

EXPOSE 8080

CMD ["python", "vajra_runtime.py"]