import json
import boto3
import uuid
import logging
from datetime import datetime, timezone
from urllib.parse import unquote_plus
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("DocumentMetadata")

BUCKET_NAME = "cloud-document-processing-harshita"

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
}


def decimal_default(obj):

    if isinstance(obj, Decimal):
        return float(obj)

    raise TypeError


def response(status_code, body):

    return {
        "statusCode": status_code,

        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },

        "body": json.dumps(
            body,
            default=decimal_default
        )
    }


def lambda_handler(event, context):

    logger.info("Received request")
    logger.info(json.dumps(event))

    # ==========================================
    # GET /documents
    # ==========================================

    if event.get("httpMethod") == "GET":

        logger.info(
            "Fetching documents from DynamoDB"
        )

        result = table.scan()

        documents = result.get("Items", [])

        return response(
            200,
            documents
        )

    # ==========================================
    # POST /upload
    # ==========================================

    if event.get("httpMethod") == "POST":

        try:

            body = json.loads(
                event.get("body", "{}")
            )

            file_name = body.get("fileName")
            file_size = int(
                body.get("fileSize", 0)
            )
            content_type = body.get(
                "contentType",
                "application/octet-stream"
            )

            # -----------------------------
            # Validate file name
            # -----------------------------

            if not file_name:

                return response(
                    400,
                    {
                        "message":
                        "File name is required"
                    }
                )

            # -----------------------------
            # Validate file type
            # -----------------------------

            if content_type not in ALLOWED_TYPES:

                return response(
                    400,
                    {
                        "message":
                        "File type not supported"
                    }
                )

            # -----------------------------
            # Validate file size
            # -----------------------------

            if file_size <= 0:

                return response(
                    400,
                    {
                        "message":
                        "Invalid file size"
                    }
                )

            if file_size > MAX_FILE_SIZE:

                return response(
                    400,
                    {
                        "message":
                        "File size must be less than 10 MB"
                    }
                )

            # -----------------------------
            # Generate unique ID
            # -----------------------------

            file_id = str(uuid.uuid4())

            object_key = (
                f"uploads/{file_id}/{file_name}"
            )

            logger.info(
                f"Creating upload URL for {file_name}"
            )

            # -----------------------------
            # Generate pre-signed URL
            # -----------------------------

            upload_url = s3.generate_presigned_url(
                "put_object",

                Params={
                    "Bucket": BUCKET_NAME,
                    "Key": object_key,
                    "ContentType": content_type
                },

                ExpiresIn=300
            )

            # -----------------------------
            # Create initial DynamoDB record
            # -----------------------------

            item = {

                "fileId": file_id,

                "fileName": file_name,

                "fileType": content_type,

                "fileSize": file_size,

                "uploadTime":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),

                "status": "Processing",

                "s3Bucket": BUCKET_NAME,

                "s3Key": object_key
            }

            table.put_item(
                Item=item
            )

            return response(
                200,
                {
                    "uploadUrl":
                        upload_url,

                    "fileId":
                        file_id,

                    "s3Key":
                        object_key
                }
            )

        except Exception as error:

            logger.exception(
                "Upload preparation failed"
            )

            return response(
                500,
                {
                    "message":
                    "Internal server error"
                }
            )

    # ==========================================
    # S3 EVENT
    # ==========================================

    if "Records" in event:

        for record in event["Records"]:

            if record.get("eventSource") != "aws:s3":

                continue

            bucket_name = record["s3"]["bucket"]["name"]

            object_key = unquote_plus(
                record["s3"]["object"]["key"]
            )

            logger.info(
                f"Processing S3 object: {object_key}"
            )

            # ----------------------------------
            # Extract fileId from:
            # uploads/{fileId}/{fileName}
            # ----------------------------------

            key_parts = object_key.split("/")

            if len(key_parts) < 3:

                logger.warning(
                    "Invalid S3 object path"
                )

                continue

            file_id = key_parts[1]

            # ----------------------------------
            # Get actual file information
            # ----------------------------------

            file_info = s3.head_object(
                Bucket=bucket_name,
                Key=object_key
            )

            actual_size = file_info.get(
                "ContentLength",
                0
            )

            actual_type = file_info.get(
                "ContentType",
                "unknown"
            )

            # ----------------------------------
            # Update DynamoDB record
            # ----------------------------------

            table.update_item(

                Key={
                    "fileId": file_id
                },

                UpdateExpression="""
                    SET #status = :status,
                        fileSize = :size,
                        fileType = :type
                """,

                ExpressionAttributeNames={
                    "#status": "status"
                },

                ExpressionAttributeValues={
                    ":status": "Processed",
                    ":size": actual_size,
                    ":type": actual_type
                }
            )

            logger.info(
                f"Successfully processed: {object_key}"
            )

        return response(
            200,
            {
                "message":
                "File processed successfully"
            }
        )

    # ==========================================
    # OPTIONS / Unknown request
    # ==========================================

    if event.get("requestContext"):

        return response(
            200,
            {
                "message": "OK"
            }
        )

    return response(
        400,
        {
            "message":
            "Unsupported event"
        }
    )