from gitbook.endpoint import Endpoint
from gitbook.models import user

USER = Endpoint("GET", "user", user.User)
