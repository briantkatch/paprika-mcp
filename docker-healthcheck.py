#!/usr/bin/env python3
"""Docker HEALTHCHECK: probe the plain-HTTP /healthz route.

The MCP endpoint (/mcp) requires a session initialize handshake and specific
Accept headers, so a one-shot probe can't use it. /healthz is a plain GET that
reports server liveness and whether Paprika credentials are configured. Exits 0
when it returns HTTP 200, 1 otherwise.
"""

import os
import sys
import urllib.request

port = os.environ.get("PORT", "8080")
url = f"http://localhost:{port}/healthz"

try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        if resp.status != 200:
            print(f"unhealthy: HTTP {resp.status}", file=sys.stderr)
            sys.exit(1)
except Exception as e:
    print(f"unhealthy: {e}", file=sys.stderr)
    sys.exit(1)
