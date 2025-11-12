import os
import boto3
from botocore.exceptions import ClientError
from io import BytesIO

class Storage:
    def __init__(self):
        self.bucket = os.environ["AWS_S3_BUCKET"]
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.client = boto3.client("s3", region_name=self.region)

    def upload_bytes(self, b: bytes, key: str, content_type: str = "application/octet-stream"):
        self.client.put_object(Bucket=self.bucket, Key=key, Body=b, ContentType=content_type)

    def download_stream(self, key: str):
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"]

    def presigned_url(self, key: str, expires_in=3600):
        return self.client.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in)