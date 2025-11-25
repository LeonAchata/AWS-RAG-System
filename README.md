# AWS RAG System 🚀

A production-ready serverless Retrieval-Augmented Generation (RAG) system built entirely on AWS infrastructure using Infrastructure as Code (CDK). This system enables intelligent document processing, semantic search, and AI-powered question answering using state-of-the-art language models.

[![AWS](https://img.shields.io/badge/AWS-Cloud-orange?logo=amazon-aws)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![CDK](https://img.shields.io/badge/AWS_CDK-2.0-green)](https://aws.amazon.com/cdk/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)](https://www.postgresql.org/)

## 🌟 Features

- **🤖 Advanced AI Integration**: Amazon Bedrock with Claude 3 Sonnet for natural language understanding and Titan Embeddings v2 for semantic search
- **📚 Intelligent Document Processing**: Automatic extraction and chunking of PDFs, DOCX, and TXT files with metadata preservation
- **🔍 Vector Semantic Search**: PostgreSQL 15 with pgvector extension for efficient similarity search
- **⚡ Serverless Architecture**: AWS Lambda functions with optimized layers for fast, scalable processing
- **🏗️ Infrastructure as Code**: Complete AWS CDK implementation for reproducible deployments
- **💰 Cost-Optimized**: Free Tier compatible design using RDS t3.micro, Lambda, and S3
- **🔐 Secure by Design**: AWS Secrets Manager for credentials, IAM roles with least privilege
- **📊 RESTful API**: API Gateway endpoints for document ingestion and querying
- **🎯 Production Ready**: Error handling, logging, monitoring, and retry mechanisms

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   S3 Bucket │─────▶│   Ingestion  │─────▶│   PostgreSQL    │
│  (Documents)│      │    Lambda    │      │   + pgvector    │
└─────────────┘      └──────────────┘      └─────────────────┘
                            │                        │
                            ▼                        │
                     ┌──────────────┐                │
                     │   Bedrock    │                │
                     │  Embeddings  │                │
                     └──────────────┘                │
                                                     │
┌─────────────┐      ┌──────────────┐                │
│     User    │─────▶│    Query     │◀───────────────┘
│   (Client)  │      │    Lambda    │
└─────────────┘      └──────────────┘
      ▲                     │
      │                     ▼
      │              ┌──────────────┐
      └──────────────│   Bedrock    │
                     │  Claude LLM  │
                     └──────────────┘
```

### Components

- **S3 Buckets**: Raw document storage with automatic Lambda triggers
- **Ingestion Lambda**: PDF/DOCX text extraction, intelligent chunking, embedding generation
- **PostgreSQL RDS**: Vector database with pgvector for similarity search
- **Query Lambda**: Query processing, semantic search, LLM response generation
- **API Gateway**: RESTful endpoints (`/ingest`, `/query`) with throttling
- **Bedrock**: AI services (Titan Embeddings v2, Claude 3 Sonnet)
- **Secrets Manager**: Secure credential management
- **Lambda Layers**: Shared dependencies (psycopg2, pdfplumber, shared utilities)

## 📋 Prerequisites

- **AWS Account** with Bedrock access (us-east-1 region)
- **AWS CLI** configured with credentials
- **Node.js** 18+ and npm
- **Python** 3.11+
- **AWS CDK** 2.0+
- **Docker Desktop** (for building Lambda layers)
- **Conda** or venv for Python environment management

## 🚀 Quick Start

### 1. Clone and Setup Environment

```bash
git clone https://github.com/LeonAchata/AWS-RAG-System.git
cd AWS-RAG-System

# Create Python environment
conda create -n CDK_env python=3.11
conda activate CDK_env

# Install dependencies
pip install -r requirements.txt
cd infrastructure
pip install -r requirements.txt
```

### 2. Bootstrap AWS CDK

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Verify CDK setup
cdk synth
```

### 3. Build Lambda Layer

The Lambda layer includes all Python dependencies compiled for Linux (Lambda runtime):

```bash
# Using Docker (recommended)
cd ..
.\scripts\build_layer_docker.ps1

# This creates layer_build/ with:
# - psycopg2-binary (PostgreSQL driver)
# - pdfplumber, pypdf2 (PDF processing)
# - python-docx (Word documents)
# - shared utilities (Bedrock, PostgreSQL clients)
```

### 4. Deploy Infrastructure

```bash
cd infrastructure
cdk deploy --require-approval never

# Deployment creates:
# ✅ RDS PostgreSQL instance with pgvector
# ✅ S3 buckets for document storage
# ✅ Lambda functions (Ingestion, Query)
# ✅ API Gateway with REST endpoints
# ✅ IAM roles and Secrets Manager
```

### 5. Test the System

**Upload a document:**

```bash
# Get bucket name
aws cloudformation describe-stacks --stack-name RagSystemStack \
  --query 'Stacks[0].Outputs[?OutputKey==`RawBucketName`].OutputValue' --output text

# Upload PDF
aws s3 cp your-document.pdf s3://BUCKET_NAME/documents/
```

**Query the system:**

```powershell
# Get API endpoint
$QUERY_URL = aws cloudformation describe-stacks --stack-name RagSystemStack `
  --query 'Stacks[0].Outputs[?OutputKey==`QueryEndpoint`].OutputValue' --output text

# Make a query
$body = @{ query = "What is this document about?" } | ConvertTo-Json
Invoke-RestMethod -Uri $QUERY_URL -Method Post -Body $body -ContentType "application/json"
```

## 📁 Project Structure

```
AWS-RAG-System/
├── infrastructure/           # AWS CDK Infrastructure
│   ├── app.py               # CDK app entry point
│   ├── stacks/
│   │   └── rag_stack.py     # Main stack definition
│   └── config/
│       └── stack_config.py  # Configuration settings
├── lambda/                  # Lambda function code
│   ├── ingestion/
│   │   ├── handler.py       # Document processing logic
│   │   └── utils/           # Text extraction, chunking
│   └── query/
│       ├── handler.py       # Query processing logic
│       └── utils/           # Prompt building, caching
├── shared/                  # Shared utilities (included in layer)
│   ├── utils/
│   │   ├── bedrock_client.py      # Bedrock API wrapper
│   │   └── postgres_client.py     # PostgreSQL + pgvector
│   └── config/
│       └── settings.py      # Shared configuration
├── scripts/                 # Deployment & utility scripts
│   ├── build_layer_docker.ps1    # Build Lambda layer
│   ├── deploy.ps1          # Deployment automation
│   └── validate_cdk_v2.py  # CDK validation
├── docs/                    # Documentation
│   ├── SETUP.md            # Detailed setup guide
│   └── QUICK_START.md      # Quick start tutorial
└── requirements.txt         # Python dependencies
```

## 🛠️ Configuration

### Environment Variables (Lambda)

**Ingestion Lambda:**
- `DB_SECRET_ARN`: Secrets Manager ARN for database credentials
- `DB_NAME`: PostgreSQL database name (default: `ragdb`)
- `BEDROCK_EMBEDDING_MODEL`: Embedding model ID (default: `amazon.titan-embed-text-v2:0`)
- `CHUNK_SIZE`: Text chunk size (default: `800`)
- `CHUNK_OVERLAP`: Overlap between chunks (default: `100`)

**Query Lambda:**
- `DB_SECRET_ARN`: Secrets Manager ARN
- `DB_NAME`: Database name
- `BEDROCK_EMBEDDING_MODEL`: Embedding model
- `BEDROCK_LLM_MODEL`: LLM model (default: `anthropic.claude-3-sonnet-20240229-v1:0`)
- `TOP_K`: Number of documents to retrieve (default: `5`)
- `MIN_SIMILARITY`: Minimum similarity threshold (default: `0.1`)

### Adjustable Parameters

Edit `infrastructure/stacks/rag_stack.py` to customize:

```python
# Database configuration
instance_type=ec2.InstanceType.of(
    ec2.InstanceClass.BURSTABLE3,
    ec2.InstanceSize.MICRO  # Change to SMALL/MEDIUM for more capacity
)

# Lambda memory and timeout
memory_size=2048,  # Increase for larger documents
timeout=Duration.minutes(5)  # Adjust processing time

# Chunk configuration
"CHUNK_SIZE": "800",  # Smaller = more precise, larger = more context
"CHUNK_OVERLAP": "100"
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Test document processing locally
python scripts/test_system.py
```

## 💰 Cost Estimation

**Free Tier Usage (Monthly):**
- RDS t3.micro: ~$15 (750 hours free first year)
- Lambda: Free (1M requests, 400,000 GB-seconds)
- S3: Free (5GB storage, 20,000 GET requests)
- Bedrock: Pay per use (~$0.008/1K tokens for Claude 3 Sonnet)
- API Gateway: Free (1M requests/month)

**Estimated Monthly Cost:** $15-25 for moderate usage (after Free Tier)

## 🔧 Troubleshooting

**Lambda Import Errors:**
- Ensure Docker is running when building layer
- Layer must be built for Linux (manylinux)
- Check Lambda logs: `aws logs tail /aws/lambda/FUNCTION_NAME --follow`

**Database Connection Issues:**
- Verify RDS is publicly accessible
- Check security group allows port 5432
- Confirm Secrets Manager has correct credentials

**Low Similarity Scores:**
- Adjust `MIN_SIMILARITY` environment variable
- Try different chunking strategies (size/overlap)
- Ensure embeddings are generated correctly

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Leon Achata**
- GitHub: [@LeonAchata](https://github.com/LeonAchataS)
- LinkedIn: [linkedin.com/in/leonachata](https://www.linkedin.com/in/leonachata)
- Email: leonyemin@gmail.com

## 🙏 Acknowledgments

- AWS CDK and serverless architecture patterns
- Amazon Bedrock for accessible AI models
- PostgreSQL pgvector extension for efficient vector search
- Open-source community for PDF processing libraries

## 📚 Further Reading

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [pgvector Extension](https://github.com/pgvector/pgvector)
- [RAG Pattern Best Practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/)
