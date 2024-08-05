import  logging

from sqlalchemy import select

from cognee.infrastructure.databases.relational import get_relational_engine
from ...models.User import User
from ...models.ACL import ACL

logger = logging.getLogger(__name__)

class PermissionDeniedException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


async def check_permissions_on_documents(user: User, permission_type: str, document_ids: list[str], session):

    logging.info("This is the user: %s", user.__dict__)
    try:
        user_group_ids = [group.id for group in user.groups]

        acls = await session.execute(
            select(ACL)
            .join(ACL.permission)
            .where(ACL.principal_id.in_([user.id, *user_group_ids]))
            .where(ACL.permission.has(name=permission_type))
        )
        resource_ids = [resource.resource_id for acl in acls.scalars().all() for resource in acl.resources]
        has_permissions = all(document_id in resource_ids for document_id in document_ids)

        if not has_permissions:
            raise PermissionDeniedException(f"User {user.username} does not have {permission_type} permission on documents")
    except Exception as error:
        logger.error("Error checking permissions on documents: %s", str(error))
        raise

