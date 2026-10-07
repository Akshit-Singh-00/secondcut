"""Local SQLite development storage or private S3 deployment storage."""
import json
import os
import sqlite3
import threading
from pathlib import Path


class ProjectStore:
    def __init__(self):
        self.bucket=os.environ.get('SECONDCUT_BUCKET')
        self.lock=threading.Lock()
        if self.bucket:
            import boto3
            self.s3=boto3.client('s3')
        else:
            root=Path(__file__).resolve().parents[1]
            data=Path(os.environ.get('SECONDCUT_DATA',str(root/'artifacts'/'runtime')))
            data.mkdir(parents=True,exist_ok=True)
            self.db=sqlite3.connect(data/'projects.sqlite3',check_same_thread=False)
            self.db.execute('CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            self.db.commit()

    def save(self,project):
        payload=json.dumps(project)
        if self.bucket:
            self.s3.put_object(Bucket=self.bucket,Key=f"projects/{project['id']}.json",Body=payload.encode(),ContentType='application/json',ServerSideEncryption='AES256')
        else:
            with self.lock:
                self.db.execute('INSERT OR REPLACE INTO projects VALUES (?,?)',(project['id'],payload))
                self.db.commit()

    def get(self,project_id):
        import uuid
        try:
            uuid.UUID(project_id)
        except ValueError:
            return None
        if self.bucket:
            from botocore.exceptions import ClientError
            try:
                data=self.s3.get_object(Bucket=self.bucket,Key=f'projects/{project_id}.json')['Body'].read()
                return json.loads(data)
            except ClientError as e:
                if e.response['Error']['Code'] in ('NoSuchKey','404'):
                    return None
                raise
        with self.lock:
            row=self.db.execute('SELECT payload FROM projects WHERE id=?',(project_id,)).fetchone()
        return json.loads(row[0]) if row else None
