import dropbox
import os
from libearth.repository import (FileNotFoundError, NotADirectoryError,
                                 Repository, RepositoryKeyError)

__all__ = 'AuthorizationError', 'DropboxRepository'


class DropboxRepository(Repository):

    client = None
    path = None

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

    def read(self, key):
        super(DropboxRepository, self).read(key)
        try:
            path = self._get_path(key)
            with self.client.get_file(path) as fp:
                while 1:
                    chunk = fp.read(1024)
                    if not chunk:
                        break
                    yield chunk

        except dropbox.rest.ErrorResponse as e:
            raise RepositoryKeyError(key, str(e))

    def write(self, key, iterable):
        pass

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
