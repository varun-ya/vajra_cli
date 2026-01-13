#!/bin/bash

PROJECT_ID="vajra-proj-123"
REGION="us-central1"

echo "🚀 Deploying Vajra Serverless Platform..."

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com storage.googleapis.com firestore.googleapis.com

# Deploy infrastructure
cd terraform
terraform init
terraform apply -auto-approve
cd ..

# Build and deploy API Gateway
cd api-gateway
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/vajra-repo/api-gateway
gcloud run deploy vajra-api-gateway \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/vajra-repo/api-gateway \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated
cd ..

# Build function runtime image
cd function-runtime
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/vajra-repo/function-runtime
cd ..

echo "✅ Deployment complete!"
echo "API Gateway URL: $(gcloud run services describe vajra-api-gateway --region=$REGION --format='value(status.url)')"