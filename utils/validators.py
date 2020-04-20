import os
from django.core.exceptions import ValidationError
from utils.constants import IMAGE_ALLOWED_EXTS


def image_size(value):
    if value.size > 2*1000*1000:
        raise ValidationError('invalid file size')


def image_extension(value):
    ext = os.path.splitext(value.name)[1]

    if not ext.lower() in IMAGE_ALLOWED_EXTS:
        raise ValidationError(f'not allowed ext, allowed ({IMAGE_ALLOWED_EXTS})')

