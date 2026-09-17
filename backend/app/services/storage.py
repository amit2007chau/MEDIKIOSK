"""A local mirror makes development reliable; MinIO receives objects when reachable."""
from pathlib import Path
from app.core.config import settings


class DocumentStorage:
    def mirror_and_store(self, document_id: str, filename: str, content: bytes) -> str:
        local_path = settings.upload_dir / f"{document_id}_{Path(filename).name}"
        local_path.write_bytes(content)
        try:
            from minio import Minio
            client = Minio(settings.minio_endpoint, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, secure=False)
            if not client.bucket_exists(settings.minio_bucket_documents):
                client.make_bucket(settings.minio_bucket_documents)
            client.put_object(settings.minio_bucket_documents, f"{document_id}/{Path(filename).name}", data=__import__("io").BytesIO(content), length=len(content), content_type="application/octet-stream")
        except Exception:
            # Local fallback intentionally preserves a working no-infrastructure demo.
            pass
        return str(local_path)
