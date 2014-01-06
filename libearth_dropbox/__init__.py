import os
from contextlib import closing
from StringIO import StringIO
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse

import dropbox
from libearth.repository import (FileNotFoundError, NotADirectoryError,
                                 Repository, RepositoryKeyError)

__all__ = 'AuthorizationError', 'DropboxRepository'


class DropboxRepository(Repository):

    client = None
    path = None

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

    def to_url(self, scheme):
        super(DropboxRepository, self).to_url(scheme)
        return '{0}://{1.session.access_token}@{1.path}'.format(scheme, self)

    def read(self, key):
        super(DropboxRepository, self).read(key)
        try:
            path = self._get_path(key)
            with closing(self.client.get_file(path)) as fp:
                while 1:
                    chunk = fp.read(1024)
                    if not chunk:
                        break
                    yield chunk

        except dropbox.rest.ErrorResponse as e:
            raise RepositoryKeyError(key, str(e))

    def write(self, key, iterable):
        super(DropboxRepository, self).write(key, iterable)
        #FIXME: Use upload chunk instead of put_file
        path = self._get_path(key)
        fp = StringIO(''.join(iterable))
        self.client.put_file(path, fp, overwrite=True)

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

    def __repr__(self):
        return '{0.__module__}.{0.__name__}({1!r} {2!r})'.format(
            type(self),
            self.client.account_info()['display_name'],
            self.path
        )


class AuthorizationError(IOError):
    """Raised when Authorization failed."""
