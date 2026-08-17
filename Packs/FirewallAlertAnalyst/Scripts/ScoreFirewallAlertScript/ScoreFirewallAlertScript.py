"""Score Firewall Alert Script - deterministic risk scoring for a single firewall alert.

Part of the Firewall Alert Analyst example agent. Everything here is arithmetic on
fields the alert already carries: no model call, no tenant call, no network. The
agent uses this for the parts of triage that must be reproducible, and the
prompt-backed Triage Firewall Alert action for the parts that need judgment.

The demisto imports MUST stay in their canonical unguarded form: the SDK's prepare
step regex-deletes exactly those lines (the server injects the modules), so wrapping
them leaves broken code after packing.
"""

import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401,F403

import json

# Weights are additive and capped at 100. Kept small and explicit on purpose: the
# point of this script is that two runs on the same alert give the same number.
WEIGHTS = {
    "action_deny": 10,
    "action_reset": 15,
    "external_source": 20,
    "admin_port": 25,
    "high_byte_count": 15,
    "repeat_offender": 25,
    "threat_signature": 30,
}

ADMIN_PORTS = {22, 23, 445, 3389, 5900}
HIGH_BYTES = 10_000_000
PRIVATE_PREFIXES = ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.")


def _is_external(ip):
    return bool(ip) and not str(ip).startswith(PRIVATE_PREFIXES)


def score_alert(alert, baseline_days):
    """Return (score, band, reasons) for one alert dict."""
    reasons = []
    score = 0

    action = str(alert.get("action", "")).lower()
    if action == "deny":
        score += WEIGHTS["action_deny"]
        reasons.append("action=deny (+%d)" % WEIGHTS["action_deny"])
    elif action in ("reset", "reset-both", "drop"):
        score += WEIGHTS["action_reset"]
        reasons.append("action=%s (+%d)" % (action, WEIGHTS["action_reset"]))

    if _is_external(alert.get("src_ip")):
        score += WEIGHTS["external_source"]
        reasons.append("source is external (+%d)" % WEIGHTS["external_source"])

    try:
        port = int(alert.get("dst_port") or 0)
    except (TypeError, ValueError):
        port = 0
    if port in ADMIN_PORTS:
        score += WEIGHTS["admin_port"]
        reasons.append("destination port %d is an admin service (+%d)" % (port, WEIGHTS["admin_port"]))

    try:
        num_bytes = int(alert.get("bytes") or 0)
    except (TypeError, ValueError):
        num_bytes = 0
    if num_bytes > HIGH_BYTES:
        score += WEIGHTS["high_byte_count"]
        reasons.append("transfer above %d bytes (+%d)" % (HIGH_BYTES, WEIGHTS["high_byte_count"]))

    try:
        prior = int(alert.get("prior_hits") or 0)
    except (TypeError, ValueError):
        prior = 0
    if prior > 0:
        score += WEIGHTS["repeat_offender"]
        reasons.append(
            "source seen %d time(s) in the last %d days (+%d)"
            % (prior, baseline_days, WEIGHTS["repeat_offender"])
        )

    if alert.get("threat_id") or alert.get("signature"):
        score += WEIGHTS["threat_signature"]
        reasons.append("carries a threat signature (+%d)" % WEIGHTS["threat_signature"])

    score = min(score, 100)
    if score >= 70:
        band = "high"
    elif score >= 40:
        band = "medium"
    elif score > 0:
        band = "low"
    else:
        band = "informational"
    if not reasons:
        reasons.append("no scoring signal present in the alert")
    return score, band, reasons


def main():
    args = demisto.args()

    raw = args.get("alert") or "{}"
    try:
        alert = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError as exc:
        return_error("alert is not valid JSON: %s" % exc)
        return
    if not isinstance(alert, dict):
        return_error("alert must be a JSON object describing ONE alert")
        return

    try:
        baseline_days = int(args.get("baseline_days") or 7)
    except (TypeError, ValueError):
        baseline_days = 7

    score, band, reasons = score_alert(alert, baseline_days)

    outputs = {
        "score": score,
        "band": band,
        "reasons": reasons,
    }
    # Surfaced only when the caller asks; the action keeps this argument hidden.
    if argToBoolean(args.get("debug") or False):
        outputs["raw_debug"] = json.dumps({"weights": WEIGHTS, "alert": alert}, sort_keys=True)

    readable = "### Firewall alert score\n**%d / 100 (%s)**\n\n%s" % (
        score,
        band,
        "\n".join("- %s" % r for r in reasons),
    )
    return_results(
        CommandResults(
            outputs_prefix="FirewallAlert.Score",
            outputs=outputs,
            readable_output=readable,
        )
    )


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
