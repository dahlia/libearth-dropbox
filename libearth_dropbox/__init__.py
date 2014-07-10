import os
from contextlib import closing
from StringIO import StringIO
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse
try:
    import Queue
except:
    import queue as Queue

import dropbox
import logging
import threading
from libearth.repository import (FileNotFoundError, NotADirectoryError,
                                 Repository, RepositoryKeyError)

__all__ = 'AuthorizationError', 'DropboxRepository'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DropboxRepository(Repository):

    client = None
    path = None
    buffer = {}
    remained_keys = Queue.Queue()

    @classmethod
    def from_url(cls, url):
        if not isinstance(url, urlparse.ParseResult):
            raise TypeError(
                'url must be an instance of {0.__module__}.{0.__name__}, '
                'not {1!r}'.format(urlparse.ParseResult, url)
            )
        if url.scheme != 'dropbox':
            raise ValueError('{0.__module__}.{0.__name__} only accepts '
                             'dropbox:// scheme'.format(DropboxRepository))
        elif hasattr(url, 'host') or url.port or url.params or url.query or \
                url.fragment:
            raise ValueError('dropbox:// must not contain any host/port/'
                             'parameters/query/fragment')
        access_token = url.username or url.password
        if not access_token:
            raise ValueError('dropbox:// must contain access token as '
                             'username e.g. dropbox://yourtoken@/path/')
        return cls(access_token, url.path)

    def __init__(self, access_token, path):
        try:
            client = dropbox.client.DropboxClient(access_token)
            metadata = client.metadata(path)
            if not metadata['is_dir']:
                raise NotADirectoryError(repr(path) + 'is not a directory')
        except dropbox.rest.ErrorResponse as e:
            if e.status == '404':
                raise FileNotFoundError(repr(path) + 'does not exists')
            raise AuthorizationError(
                e.message
            )

        self.client = client
        self.path = path

        worker = threading.Thread(target=self._thread_upload)
        worker.setDaemon(True)
        worker.start()

    def to_url(self, scheme):
        super(DropboxRepository, self).to_url(scheme)
        return '{0}://{1.session.access_token}@{1.path}'.format(scheme, self)

    def read(self, key):
        super(DropboxRepository, self).read(key)
        t_key = tuple(key)
        path = self._get_path(key)
        try:
            revision = self.client.metadata(path)['revision']
        except dropbox.rest.ErrorResponse as e:
            if e.status == 404:
                raise RepositoryKeyError(repr(path) + 'does not exists')

        if t_key in self.buffer.keys():
            if self.buffer[t_key]['revision'] in (revision, None):
                logger.info('read from memory: {0!s}'.format(t_key))
                return self.buffer[t_key]['data']

        try:
            logger.info('read from network: {0!s}'.format(t_key))
            data = ''
            with closing(self.client.get_file(path)) as fp:
                while 1:
                    chunk = fp.read(1024)
                    if not chunk:
                        break
                    data += chunk

                self.buffer[t_key] = {
                    'revision': revision,
                    'data': data,
                }
                return data

        except dropbox.rest.ErrorResponse as e:
            raise RepositoryKeyError(key, str(e))

    def write(self, key, iterable):
        super(DropboxRepository, self).write(key, iterable)
        t_key = tuple(key)
        data = ''.join(iterable)
        self.buffer[t_key] = {
            'revision': None,
            'data': data,
        }
        self.remained_keys.put(t_key)

    def exists(self, key):
        path = self._get_path(key)
        try:
            self.client.metadata(path)
            return True
        except dropbox.rest.ErrorResponse as e:
            if e.status == 404:
                return False
            else:
                raise e

    def list(self, key):
        super(DropboxRepository, self).list(key)
        path = self._get_path(key)
        try:
            metadata = self.client.metadata(path)
            if not metadata['is_dir']:
                raise RepositoryKeyError(key, "{0} is not a directory".format(
                    path
                ))
            return [self._get_filename(obj['path'])
                    for obj in metadata['contents']]
        except dropbox.rest.ErrorResponse as e:
            raise RepositoryKeyError(key, str(e))


    @staticmethod
    def get_authorization_url(app_key, app_secret):
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        authorize_url = flow.start()
        return authorize_url;

    @staticmethod
    def authorize(app_key, app_secret, code):
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        access_token, user_id = flow.finish(code)
        return access_token, user_id

    def _get_path(self, key):
        return os.path.join(self.path, *key).replace('\\', '/')

    def _get_filename(self, path):
        return path[path.rfind('/')+1:]

    def _thread_upload(self):
        while 1:
            key = self.remained_keys.get()
            path = self._get_path(key)

            if self.buffer[key]['revision']:
                self.remained_keys.task_done()
                continue

            logger.info('Writing file: {0!s}'.format(key))
            data = self.buffer[key]['data']
            fp = StringIO(data)
            #FIXME: Use upload chunk instead of put_file
            response = self.client.put_file(path, fp, overwrite=True)
            self.buffer[key]['revision'] = response['revision']
            self.remained_keys.task_done()


    def __repr__(self):
        return '{0.__module__}.{0.__name__}({1!r} {2!r})'.format(
            type(self),
            self.client.account_info()['display_name'],
            self.path
        )


class AuthorizationError(IOError):
    """Raised when Authorization failed."""
