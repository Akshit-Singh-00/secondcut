import os
if not os.environ.get('SECONDCUT_PASSWORD'):
    raise RuntimeError('AWS deployment requires a judge password.')
if not os.environ.get('SECONDCUT_BUCKET'):
    raise RuntimeError('AWS deployment requires durable S3 storage.')
from mangum import Mangum
from .app import app
handler=Mangum(app,lifespan='off')
