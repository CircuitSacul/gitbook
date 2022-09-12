from gitbook.endpoint import PaginatedEndpoint, SingleEndpoint
from gitbook.models import space, user

USER = SingleEndpoint("GET", "user", user.User)
SPACES = PaginatedEndpoint("GET", "user/spaces", space.Space)
