"""Draft Escalation Note Script - renders the escalation note for a triaged alert.

Part of the Firewall Alert Analyst example agent. Formatting only: no model call, no
tenant call, no network, and nothing is written to the case.

The code check here is the only thing that actually constrains the agent. `isgeneratable`
does not: tested live, the agent supplied an escalation_code marked isgeneratable=false
without being asked for one. The flag is a marker, not a gate, so a bad code has to be
rejected in code or not at all.

The demisto imports MUST stay in their canonical unguarded form: the SDK's prepare
step regex-deletes exactly those lines (the server injects the modules), so wrapping
them leaves broken code after packing.
"""

import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401,F403

# The routing list from the Firewall Triage Worked Alerts collection. The on-call rota
# routes on these exact codes, which is why the agent may not invent one.
CODES = {
    "FW-ESC-4471": "on-call: confirmed external brute force against an admin service",
    "FW-ESC-4472": "on-call: confirmed data egress to an unrecognised external destination",
    "FW-ESC-4473": "on-call: confirmed inbound exploitation attempt carrying a signature",
    "FW-ESC-4480": "day-shift: suspicious but unresolved",
}

VERDICTS = ("benign", "suspicious", "malicious")


def render(summary, code, case_id, verdict, next_step):
    """Return (note, queue) for one escalation. Raises ValueError on a bad code/verdict."""
    code = str(code or "").strip().upper()
    if code not in CODES:
        raise ValueError(
            "unknown escalation code %r. Use one of: %s. Take the code from the worked-alerts "
            "collection; do not invent one, the on-call rota routes on it."
            % (code, ", ".join(sorted(CODES)))
        )

    verdict = str(verdict or "").strip().lower()
    if verdict not in VERDICTS:
        raise ValueError("verdict must be one of %s, got %r" % (", ".join(VERDICTS), verdict))

    queue = CODES[code].split(":", 1)[0]
    lines = [
        "### Escalation note",
        "",
        "**Case** %s" % case_id,
        "**Verdict** %s" % verdict,
        "**Code** %s (%s)" % (code, CODES[code]),
        "",
        str(summary or "").strip(),
    ]
    step = str(next_step or "").strip()
    if step and step.lower() != "none needed":
        lines += ["", "**Next** %s" % step]
    return "\n".join(lines), queue


def main():
    args = demisto.args()
    try:
        note, queue = render(
            args.get("summary"),
            args.get("escalation_code"),
            args.get("case_id"),
            args.get("verdict"),
            args.get("next_step"),
        )
    except ValueError as exc:
        return_error(str(exc))
        return

    return_results(
        CommandResults(
            outputs_prefix="FirewallAlert.Escalation",
            outputs={
                "note": note,
                "code": str(args.get("escalation_code") or "").strip().upper(),
                "queue": queue,
            },
            readable_output=note,
        )
    )


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
