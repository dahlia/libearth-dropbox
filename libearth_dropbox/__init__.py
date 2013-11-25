import dropbox
import os
from libearth.repository import Repository, RepositoryKeyError

__all__ = 'AuthorizationError', 'DropboxRepository'


class DropboxRepository(Repository):

    client = None
    path = None

    def __init__(self, access_token, path):
        try:
            client = dropbox.client.DropboxClient(access_token)
            client.account_info()
        except dropbox.rest.ErrorResponse as e:
            raise AuthorizationError(
                e.message
            )

        self.client = client
        self.path = path

    def read(self, key):
        super(DropboxRepository, self).read(key)
        try:
            path = os.path.join(self.path, *key).replace('\\', '/')
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
        pass

    def list(self, key):
        pass

    @staticmethod
    def get_authorization_url(app_key, app_secret):
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        authorize_url = flow.start()
        return authorize_url;

    def authorize(app_key, app_secret, code):
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        access_token, user_id = flow.finish(code)
        return access_token, user_id

    def __repr__(self):
        return '{0.__module__}.{0.__name__}({1!r} {2!r})'.format(
            type(self),
            self.client.account_info()['display_name'],
            self.path
        )


class AuthorizationError(IOError):
    """Raised when Authorization failed."""
