# Cloud Document Processing System

A serverless cloud-based document management system built using
AWS services.

## Features

- Secure document upload
- Cloud-based file storage
- Automatic document processing
- File metadata tracking
- File type and size validation
- Serverless architecture
- Cloud monitoring
- REST API integration

## Technology Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- AWS Lambda

### AWS Services
- Amazon S3
- AWS Lambda
- Amazon DynamoDB
- Amazon API Gateway
- AWS IAM
- Amazon CloudWatch

## Architecture

User
↓
Frontend
↓
API Gateway
↓
AWS Lambda
↓
Amazon S3
↓
S3 Event
↓
AWS Lambda
↓
DynamoDB

## Security

- IAM least-privilege permissions
- Private S3 bucket
- Pre-signed S3 URLs
- File type validation
- File size validation
- API CORS configuration

## How It Works

1. User selects a document.
2. Frontend sends file information to API Gateway.
3. Lambda validates the file.
4. Lambda generates a secure pre-signed S3 URL.
5. The frontend uploads the file directly to S3.
6. S3 triggers Lambda automatically.
7. Lambda processes the uploaded file.
8. File metadata is stored in DynamoDB.
9. CloudWatch records application logs.
10. The frontend retrieves document information through API Gateway.

## AWS Services Used

| Service | Purpose |
|---|---|
| S3 | Document storage |
| Lambda | Serverless processing |
| DynamoDB | Metadata storage |
| API Gateway | REST API |
| IAM | Access control |
| CloudWatch | Monitoring and logs |

## Future Improvements

- User authentication
- Document preview
- Search and filtering
- PDF text extraction
- AWS Textract integration
- Document deletion
- Pagination
- Custom domain