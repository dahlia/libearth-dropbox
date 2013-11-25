import dropbox
from libearth.repository import Repository

__all__ = 'AuthorizationError', 'DropboxRepository'


class DropboxRepository(Repository):

    client = None
    path = None

    def __init(self, access_token, path):
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
        pass

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
        return '{0.__module__}.{0.__name__}({1!r})'.format(
            type(self),
            self.path
        )


class AuthorizationError(IOError):
    """Raised when Authorization failed."""
