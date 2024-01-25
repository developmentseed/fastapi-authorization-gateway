# from fastapi import Request

# from fastapi_authorization_gateway.types import Policy

# def generate_read_only_policy(request: Request) -> Policy:
#     """
#     Generate a policy that grants read-only access to all routes.
#     """
#     all_routes = request.app.routes
#     return Policy(
#         allow=[
#             RoutePermission(
#                 path="/collections/{collection_id}",
#                 method="GET",
#                 path_params={
#                     "collection_id": Path(pattern=r"^(collection1|collection2)$")
#                 },
#             ),
#         ],
#         deny=[],
#     )
