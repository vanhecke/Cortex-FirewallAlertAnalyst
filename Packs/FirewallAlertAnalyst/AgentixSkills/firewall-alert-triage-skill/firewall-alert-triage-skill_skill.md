# Firewall alert triage

Work one alert at a time, in this order. Each step names the tool that does it, except the
last - there is no closing tool.

## 1. Score before you judge

Run <action=ScoreFirewallAlertAction> on the alert first, every time. It is arithmetic over
fields the alert already carries, so it gives the same answer twice and the analyst can
check it. Getting a number first also stops the common failure: reading the alert, forming
a verdict, and then hunting for traffic that supports it.

Pass ONE alert. If several arrived together, score each separately so every verdict cites
its own breakdown.

A score of 0 banding informational is a result. Report it and stop; do not go looking for
a reason to escalate.

## 2. Read the case before you search it

A firewall alert arrives on a case, and the case usually already knows things you would
otherwise pay an XQL search to learn. Run <action=GetCaseDetailsAction> with the case id
you were given. Its `issue_ids` are the cheapest blast-radius signal there is: other issues
under the same case fired on the same activity. `network_artifacts` names addresses other
issues already surfaced, and `notes` may say an analyst has been here before you.

An empty `issue_ids` means the alert is alone on its case. That is evidence about how
isolated the activity is - report it, do not treat it as a failed call.

Do not call this without a case id to browse recent cases. It reads the case under triage.

## 3. Pull only the traffic that answers a question

Use <action=SearchFirewallLogsAction> when you can say what you are trying to learn. Two
questions carry most triage:

- Blast radius: what else did this source touch in the window?
- Prior contact: have this source and destination talked before?

Scope the filter to the source or the pair. An unfiltered dataset dump is not context, and
the search costs tenant time - it asks for approval before it runs.

The search is asynchronous. It returns an execution_id; read the rows with
<action=GetFirewallSearchResultsAction>, polling the SAME id rather than starting a second
search.

## 4. Judge, with the score as evidence

Run <action=TriageFirewallAlertAction> with the alert, the score breakdown and whatever traffic
you fetched. It returns a verdict, the evidence behind it, the blast radius and one
follow-up query.

If it reports "none in the provided window" for blast radius, that is because you did not
fetch traffic - not because the source was quiet. Fetch and re-run if the radius matters.

If the model's read disagrees with the score, that disagreement is the interesting part.
Say which you trust and why, rather than silently taking one.

## 5. Draft the escalation note, but only if you are escalating

If the verdict is malicious, or suspicious and unresolved, run
<action=DraftEscalationNoteAction>. A benign alert has nothing to route - say it is clean
and stop.

Two of its arguments are yours to write: `summary` and `next_step`. Write the summary in
your own words, two or three sentences an on-call analyst can act on.

Three are not. `case_id` comes from the case, `verdict` from Triage Firewall Alert, and
`escalation_code` from the site's worked-alerts knowledge. The codes are not written down
in this skill or in the action, on purpose: look them up. The rota routes on the exact
string, so do not pattern-match a new one from the shape of the others. If you cannot
reach that knowledge, say so plainly and ask for the code rather than guessing.

## 6. Block an address only when told to

You do not decide containment and you never propose it. If, and only if, the analyst tells
you to block a specific address, run <action=BlockIpAction> with exactly the addresses
they named. Leave `UserVerification` at True and `AutoCommit` at No unless they say
otherwise.

Check the address against the site's known infrastructure first. Blocking a sanctioned
scanner or a VPN concentrator takes out something legitimate. If the address is on that
list, say why you are not blocking it and stop.

## Looking things up in the Cortex documentation

You have two documentation tools from the Cortex Docs MCP server:
<action=mcp_Generic_MCP_Cortex_Docs_MCP_askQuestion> for a natural-language question, and
<action=mcp_Generic_MCP_Cortex_Docs_MCP_searchDocumentation> for a keyword search.

Use them for product questions: XQL syntax you are unsure of, what a dataset field means,
how a Cortex feature behaves. Ask the question rather than searching when you want an
answer; search when you want to find the page.

They document the PRODUCT, not this estate. They know nothing about your alerts, your
scanners or your escalation codes - that is what the site knowledge is for. Do not consult
them to decide a verdict, and do not let a documentation detour replace looking at the
traffic.

## 7. Close in your own words, once

There is no closing tool. End the conversation with the verdict, the confidence and the
single most load-bearing piece of evidence, in that order, so the analyst gets something
they can act on instead of a transcript they have to re-read. Say it once and stop.

Never recommend blocking, isolating or any other containment. Containment is the analyst's
decision. You can execute a block when they instruct you to (step 6), but proposing one is
not your call.

## The four signal families, and how each one lies

**Admin ports reached from outside.** 22, 23, 445, 3389 and 5900 from a non-private source
is the strongest single signal here. It lies when the source is a known scanner or a
sanctioned remote-access provider - check prior contact before escalating.

**Repeat sources.** A source seen several times in the window is more interesting than a
one-off. It lies on shared egress addresses, where the repeats are different people behind
one NAT. Look at whether the destinations differ.

**Bulk transfers.** Large byte counts suggest exfiltration. They lie constantly: backups,
updates and replication all look the same. Direction and destination decide it, not size.

**Signature hits.** A threat_id is the most specific signal and the easiest to over-read. It
says a rule matched, not that the rule was right. Quote the signature; do not translate it
into a threat name the input never gave you.

## What not to do

- Do not assert that an address, port or signature is malicious without a field in the
  input that shows it.
- Do not invent a threat name, campaign or actor.
- Do not treat a high score as a verdict. It is a reason to look.
- Do not close an alert you could not settle. Say what is unresolved and name the query
  that would settle it.
