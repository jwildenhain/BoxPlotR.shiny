# BoxPlotR deployment

The canonical source is `jwildenhain/BoxPlotR.shiny`. Deploy both interfaces
from the same reviewed commit. The R files and `www/` are the Shiny application;
`boxplotr_mcp_server.py` is the shared plotting worker and stdio MCP server;
`deploy/boxplotr_mcp/app.py` is the public HTTP gateway.

## Containers

For the website, build the root `Dockerfile` and expose port 3838. Its build
context must include the sample XLSX files and `www/` guide assets.

For the HTTP gateway:

```sh
docker build -f Dockerfile.mcp -t boxplotr-mcp:local .
docker run --rm -d --name boxplotr-mcp \
  --env MCP_IDENTITY_SECRET --publish 127.0.0.1:8765:8765 boxplotr-mcp:local
python3 tests/test_mcp_container.py
```

Set `MCP_IDENTITY_SECRET` to a random secret in the launching environment.
Keep it stable across restarts to preserve anonymous quota identities. The
container is intended to sit behind a trusted reverse proxy: do not expose
port 8765 directly to the internet. Persist `/var/lib/boxplotr-mcp` if quotas
and operational event history must survive container replacement.

## Existing systemd installation

On tyerschem2, the application lives in `/srv/shiny-server/boxplotr`, the gateway
in `/opt/boxplotr-mcp`, and state in `/var/lib/boxplotr-mcp`. Install Python
dependencies from `requirements-mcp.txt` into the gateway's `.venv`.
The service and Apache virtual-host templates are in this directory.
Provision the state directory and its `output/` subdirectory for user `shiny`.
Keep `/etc/boxplotr-mcp/keys.json` (an empty object for keyless-only use) and
runtime/analytics environment files outside the repository and readable only
by the appropriate service account. TLS certificate paths and DNS names in
the Apache template are specific to Chemgrid.

The public route `/boxplotr/` proxies to the internal `/mcp/` route; `/health`
is the internal health endpoint. Anonymous access uses a hashed client-IP
quota. Optional bearer keys remain supported. Analytics secrets are optional;
`MCP_IDENTITY_SECRET` is required for anonymous requests.

`legacy/` preserves the earlier key issuance utilities found on the server.
The current gateway does not import or mount the self-service email handlers.
These utilities are not included in the container or enabled by this merge.
Never commit issued keys, access databases, environment files, or certificates.

## Validation

```sh
python3 -m unittest discover -s tests -p test_mcp_regressions.py -v
Rscript -e 'testthat::test_dir("tests")'
```

The Python render tests require R and the plotting packages from
`Dockerfile.mcp`. The R suite additionally requires `testthat`. The container
workflow verifies HTTP initialization, rendering, and rejected invalid input.
The legacy `codex/fix-review-findings` branch contains additional unmerged
behavior changes; it is not a deployed release and is tracked separately in
the consolidation record.
