"""MCP server for Paprika recipe manager."""

import asyncio
import contextlib
import logging
import os

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import Prompt, Tool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Mount, Route

from .prompts import PROMPTS
from .tools import TOOLS
from .utils import get_credentials

logger = logging.getLogger(__name__)

# Create server instance
app = Server("paprika")


@app.list_prompts()
async def list_prompts():
    """List available prompts."""
    return [Prompt(**prompt["definition"]) for prompt in PROMPTS.values()]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict = None):
    """Get prompt content."""
    if name in PROMPTS:
        return await PROMPTS[name]["handler"](arguments or {})
    raise ValueError(f"Unknown prompt: {name}")


@app.list_tools()
async def list_tools():
    """List available tools."""
    return [Tool(**tool["definition"]) for tool in TOOLS.values()]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name in TOOLS:
        try:
            return await TOOLS[name]["handler"](arguments)
        except Exception as e:
            logger.error(f"Error in {name}: {e}", exc_info=True)
            from mcp.types import TextContent

            return [TextContent(type="text", text=f"Error: {str(e)}")]
    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def run():
    """Entry point for the stdio server."""
    asyncio.run(main())


def build_http_app() -> Starlette:
    """Build a Starlette app exposing the MCP server over Streamable HTTP.

    The MCP endpoint is mounted at ``/mcp``; clients connect with an HTTP
    (URL) transport. A plain ``/healthz`` route provides a Docker liveness
    probe that bypasses the MCP session handshake.
    """
    session_manager = StreamableHTTPSessionManager(app=app)

    async def handle_mcp(scope, receive, send):
        await session_manager.handle_request(scope, receive, send)

    async def healthz(request: Request) -> Response:
        """Liveness/readiness probe.

        Confirms the HTTP server is serving and that Paprika credentials are
        configured. It deliberately does not perform a network login on every
        probe, which would risk rate limiting.
        """
        try:
            get_credentials()
        except ValueError as e:
            return PlainTextResponse(f"unhealthy: {e}", status_code=503)
        return JSONResponse({"status": "ok"})

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette):
        async with session_manager.run():
            yield

    return Starlette(
        routes=[
            Route("/healthz", healthz, methods=["GET"]),
            Mount("/mcp", app=handle_mcp),
        ],
        lifespan=lifespan,
    )


def run_http(host: str | None = None, port: int | None = None) -> None:
    """Entry point for the HTTP server."""
    import uvicorn

    host = host or os.environ.get("HOST", "0.0.0.0")
    port = port or int(os.environ.get("PORT", "8080"))
    logger.info("Starting Paprika MCP HTTP server on %s:%d (endpoint /mcp)", host, port)
    uvicorn.run(build_http_app(), host=host, port=port)


if __name__ == "__main__":
    run()
