# SteadyCron Python SDK

`steadycron` is the official Python code-monitoring SDK for [SteadyCron](https://steadycron.com).

Wrap your scheduled jobs with `@steadycron.job` and SteadyCron will:
- Know when a job **started**, **succeeded**, or **failed**
- Alert you when a job **doesn't run** on time (missed heartbeat)
- Detect **stuck runs** that start but never finish

The monitor must already exist — create it in the Dashboard, via YAML manifest, or Terraform.
The SDK never creates monitors. For a fully code-driven workflow, declare the monitor in your
Terraform configuration or YAML manifest and reference it from your application by key:
the cron schedule, alert rules, and SDK instrumentation all live in the same repository.

---

## Installation

```bash
pip install steadycron
```

No runtime dependencies — uses Python's standard library only.

---

## Quick start

```python
import steadycron

steadycron.api_key = "sc_ro_..."  # read-only key; or set STEADYCRON_API_KEY env var

@steadycron.job("nightly-db-backup")
def backup():
    run_backup()   # start on entry, success on return, fail (+re-raise) on exception
```

### Context manager

```python
with steadycron.monitor("nightly-db-backup"):
    run_backup()
```

### Manual pings

```python
m = steadycron.Monitor("nightly-db-backup")
m.ping()                           # bare success heartbeat
m.ping(state="start")
m.ping(state="fail", message="disk full")
```

---

## Authentication

The SDK uses a **read-only** API key to resolve monitor keys to ping tokens at startup. Create one in:

**SteadyCron Dashboard → Settings → API keys → New key → Scope: Read-only**

Set it via:
- Environment variable: `STEADYCRON_API_KEY=sc_ro_...`
- Module attribute: `steadycron.api_key = "sc_ro_..."`
- `steadycron.configure(api_key="sc_ro_...")`

---

## Configuration

```python
import steadycron

steadycron.configure(
    api_key="sc_ro_...",
    environment="production",   # optional — sent on every ping
    capture_errors=True,        # include exception message on fail pings (default False)
    ping_timeout=5.0,           # seconds (default 5)
    resolve_cache_ttl=3600.0,   # seconds (default 3600 = 1 hour)
)
```

| Setting | Default | Env var fallback |
|---|---|---|
| `api_key` | `None` | `STEADYCRON_API_KEY` |
| `api_url` | `https://api.steadycron.com` | `STEADYCRON_API_URL` |
| `ping_url` | `https://ping.steadycron.com` | `STEADYCRON_PING_URL` |
| `environment` | `None` | `STEADYCRON_ENVIRONMENT` |
| `capture_errors` | `False` | — |
| `ping_timeout` | `5.0` s | — |
| `resolve_cache_ttl` | `3600.0` s | — |

---

## How it works

1. On first use, the SDK calls `GET /api/monitors/resolve?key=<your-key>` with the read-only API key to retrieve the ping token. The token is cached for 1 hour (configurable).
2. All pings are fire-and-forget: a bounded `ping_timeout` is applied; any error is logged via `logging.getLogger("steadycron")` at WARNING and discarded. They never raise.
3. Resolution errors (404 unknown key, 409 ambiguous key, wrong kind) raise immediately — they indicate misconfiguration.
4. On exception, a `fail` ping is sent and the **original exception is re-raised unchanged**.

---

## Direct / token mode (hardened path)

If you cannot use API key resolution (e.g. air-gapped environments), set the ping token directly:

```python
steadycron.monitors = {"nightly-db-backup": "hRkmWz8oZtlMFzvTAUdnRE"}
```

The token is visible via **Job detail → Code monitoring → Reveal ping token** in the Dashboard.

---

## Reliability contract

- **Ping failures are never raised.** A transport error, timeout, or non-2xx response is logged and discarded.
- **Resolution errors always raise.** A 404 or 409 from the resolve endpoint raises on first use; fix the key or remove the decorator.
- **Original exceptions pass through unchanged.** The decorator and context manager do not wrap exceptions.
- **No runtime dependencies.** The SDK uses `urllib.request` from the standard library.

---

## License

MIT
