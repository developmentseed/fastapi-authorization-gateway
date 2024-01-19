from typing import Callable, Coroutine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from fastapi import Request
import logging
from fastapi_route_authorization.auth import evaluate_request



class MutateRequestMiddleware:
    """
    A middleware that mutates the request to apply permissions boundaries
    """

    def __init__(self, app: ASGIApp, *, transform_request_body: Callable[[bytes], bytes]):
        self.app = app
        self.transform_request_body = transform_request_body

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        logging.info("MutateRequestMiddleware")
        if scope["type"] != "http":  # pragma: no cover
            await self.app(scope, receive, send)
            return
        
        message_body: bytes = b""

        async def mutate_request_body():
            logging.info("mutate_request_body")
            nonlocal message_body

            logging.info("Mutating request body")
            message = await receive()
            assert message["type"] == "http.request"
            message_body += message.get("body", b"")

            if not message.get("more_body", False):
                # message fully received
                logging.info("Request body fully received")
                logging.info(message_body)

                message["body"] = self.transform_request_body(message_body)
            return message
        
        logging.info("Calling app")
        await self.app(scope, mutate_request_body, send)


class AuthPolicyMiddleware(BaseHTTPMiddleware):
    """
    A middleware that attaches authorization policy to requests
    """

    def __init__(self, app: ASGIApp, policy_generator: Coroutine):
        super().__init__(app)
        self.policy_generator = policy_generator

    async def dispatch(self, request: Request, call_next) -> None:
        logging.info("AuthPolicyMiddleware")
        state = request.state

        # set policy on request state
        state.policy = await self.policy_generator(request)
        logging.info(f"Policy: {state.policy}")

        logging.info(f"Path: {request.scope}")

        response = await call_next(request)
        return response


class MutateRequestMiddlewareFastApi(BaseHTTPMiddleware):
    """
    A middleware that mutates the request to apply permissions boundaries
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> None:
        logging.info("MutateRequestMiddlewareFastApi")
        
        state = request.state
        if not hasattr(state, "policy"):
            logging.info("No policy found on request state")
            return await call_next(request)
        else:
            path = request.url.path
            for body_transformation in state.policy.request_body_transformations:
                if body_transformation.path_regex.match(path):
                    logging.info(f"Path {path} matches body transformation: {body_transformation.path_regex}")
                    request._body = body_transformation.transform(await request.body())
                    break
        response = await call_next(request)
        return response        

        