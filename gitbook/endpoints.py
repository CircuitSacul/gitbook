from gitbook.endpoint import PaginatedEndpoint, SingleEndpoint
from gitbook.models import organization, space, user

CURRENT_USER = SingleEndpoint("GET", "user", user.User)
USER = SingleEndpoint("GET", "users/{id}", user.User)
SPACES = PaginatedEndpoint("GET", "user/spaces", space.Space)
ORGANIZATIONS = PaginatedEndpoint("GET", "orgs", organization.Organization)
