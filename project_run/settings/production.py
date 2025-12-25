import os

from .base import *

# Не редактируйте этот production файл, что не сломать наш продакшн сайт!

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "db_name"),
        "USER": os.environ.get("DB_USER", "db_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "db_pass"),
        "HOST": os.environ.get("DB_HOST", "https://db_host_example.com"),
        "PORT": "5432",
    }
}

AWS_STORAGE_BUCKET_NAME = "zappa-ymqd03cou"
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
AWS_DEFAULT_ACL = None

# Static files (CSS, JavaScript, Images)
STATIC_LOCATION = "static"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
