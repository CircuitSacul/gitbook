from gitbook.endpoint import PaginatedEndpoint, SingleEndpoint
from gitbook.models import space, user

CURRENT_USER = SingleEndpoint("GET", "user", user.User)
USER = SingleEndpoint("GET", "user/{id}", user.User)
SPACES = PaginatedEndpoint("GET", "user/spaces", space.Space)
