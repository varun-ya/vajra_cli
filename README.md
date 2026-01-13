# Vajra Serverless Platform

AWS Lambda clone built on Google Cloud Platform.

## Architecture
- **API Gateway**: Cloud Run (HTTP endpoints)
- **Function Runtime**: Cloud Run (dynamic containers)
- **Storage**: Cloud Storage (function code)
- **Database**: Firestore (metadata)
- **Build**: Cloud Build (CI/CD)

## Components
- `api-gateway/` - REST API for function management
- `function-runtime/` - Function execution environment
- `deployment-service/` - Function deployment pipeline
- `web-ui/` - Management dashboard
- `terraform/` - Infrastructure as code