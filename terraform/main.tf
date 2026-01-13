terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "vajra-proj-123"
  region  = "us-central1"
}

# Cloud Storage bucket for function code
resource "google_storage_bucket" "functions" {
  name     = "vajra-functions-${random_id.bucket_suffix.hex}"
  location = "US"
}

resource "random_id" "bucket_suffix" {
  byte_length = 8
}

# Firestore database
resource "google_firestore_database" "default" {
  project     = "vajra-proj-123"
  name        = "(default)"
  location_id = "us-central1"
  type        = "FIRESTORE_NATIVE"
}

# Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  location      = "us-central1"
  repository_id = "vajra-repo"
  description   = "Vajra serverless platform images"
  format        = "DOCKER"
}

# Cloud Run service for API Gateway
resource "google_cloud_run_service" "api_gateway" {
  name     = "vajra-api-gateway"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "us-central1-docker.pkg.dev/vajra-proj-123/vajra-repo/api-gateway:latest"
        ports {
          container_port = 8080
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# IAM for public access
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.api_gateway.name
  location = google_cloud_run_service.api_gateway.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  
  service = each.value
}

# IAM for Cloud Build
resource "google_project_iam_member" "cloudbuild_editor" {
  project = "vajra-proj-123"
  role    = "roles/editor"
  member  = "user:navchetna.official.llp@gmail.com"
}