'''
Add in /edx/app/edxapp/edx-platform/lms/envs/aws.py:
ORA2_SWIFT_URL = AUTH_TOKENS["ORA2_SWIFT_URL"]
ORA2_SWIFT_KEY = AUTH_TOKENS["ORA2_SWIFT_KEY"]

Add in /edx/app/edxapp/lms.auth.json
"ORA2_SWIFT_URL": "https://EXAMPLE",
"ORA2_SWIFT_KEY": "EXAMPLE",

ORA2_SWIFT_KEY should correspond to Meta Temp-Url-Key configure in swift. Run
'swift stat -v' to get it.
'''

import logging
from django.conf import settings
import swiftclient
import urlparse
import requests


logger = logging.getLogger("openassessment.fileupload.api")

from .base import BaseBackend
from ..exceptions import FileUploadInternalError


class Backend(BaseBackend):
    """
    Upload openassessment student files to swift
    """

    def get_upload_url(self, key, content_type):
        bucket_name, key_name = self._retrieve_parameters(key)
        key, url = get_settings()
        try:
            temp_url = swiftclient.utils.generate_temp_url(
                path='%s/%s/%s' % (url.path, bucket_name, key_name),
                key=key,
                method='PUT',
                seconds=self.UPLOAD_URL_TIMEOUT)
            return '%s://%s%s' % (url.scheme, url.netloc, temp_url)
        except Exception as ex:
            logger.exception(
                u"An internal exception occurred while generating an upload URL."
            )
            raise FileUploadInternalError(ex)

    def get_download_url(self, key):
        bucket_name, key_name = self._retrieve_parameters(key)
        key, url = get_settings()
        try:
            temp_url = swiftclient.utils.generate_temp_url(
                path='%s/%s/%s' % (url.path, bucket_name, key_name),
                key=key,
                method='GET',
                seconds=self.DOWNLOAD_URL_TIMEOUT)
            download_url = '%s://%s%s' % (url.scheme, url.netloc, temp_url)
            response = requests.get(download_url)
            return download_url if response.status_code == 200 else ""
        except Exception as ex:
            logger.exception(
                u"An internal exception occurred while generating a download URL."
            )
            raise FileUploadInternalError(ex)


def get_settings():
    """
    Returns the swift key and a parsed url.
    Both are generated from django settings.
    """

    url = getattr(settings, 'ORA2_SWIFT_URL', None)
    key = getattr(settings, 'ORA2_SWIFT_KEY', None)
    url = urlparse.urlparse(url)
    return key, url
